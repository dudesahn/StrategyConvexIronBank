// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

    /* ========== CORE LIBRARIES ========== */

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/math/Math.sol";

import "./interfaces/curve.sol";
import {IUniswapV2Router02} from "./interfaces/uniswap.sol";
import {
    BaseStrategy,
    StrategyParams
} from "@yearnvaults/contracts/BaseStrategy.sol";

    /* ========== INTERFACES ========== */

interface IConvexRewards {
	// staked balance
	function balanceOf(address account) external view returns (uint256);
	function earned(address account) external view returns (uint256);
    // stake a convex tokenized deposit
	function stake(uint256 _amount) external returns(bool);
    // withdraw to a convex tokenized deposit, probably never need to use this
    function withdraw(uint256 _amount, bool _claim) external returns(bool);
    // withdraw directly to curve LP token
    function withdrawAndUnwrap(uint256 _amount, bool _claim) external returns(bool);
    // claim rewards
	function getReward(address _account, bool _claimExtras) external returns(bool);
}

interface IConvexDeposit {
    //deposit into convex, receive a tokenized deposit.  parameter to stake immediately
	function deposit(uint256 _pid, uint256 _amount, bool _stake) external returns(bool);
    //burn a tokenized deposit to receive curve lp tokens back
	function withdraw(uint256 _pid, uint256 _amount) external returns(bool);
}

    /* ========== CONTRACT ========== */

contract StrategyConvexCurveLP is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    ICurveFi public constant curve = ICurveFi(address(0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF)); // Curve Iron Bank Pool, want to be able to set this for other strats. need this for buying more pool tokens
    address public crvRouter = address(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F); // default to sushiswap, more CRV liquidity there
    address public constant voter = address(0xF147b8125d2ef93FB6965Db97D6746952a133934); // Yearn's veCRV voter
    address[] public crvPath;
    address[] public convexTokenPath;
    
    address public depositContract = 0xF403C135812408BFbE8713b5A23a04b3D48AAE31; // this is the deposit contract that all pools seem to use, aka booster
    address public rewardsContract = 0x3E03fFF82F77073cc590b656D42FceB12E4910A8; // want to add this to the constructor or at least setter since this is unique to each pool. This one is for Iron Bank pool
    uint256 public pid = 29; // this is unique to each pool
    uint256 public optimal = 0; // this is the optimal token to deposit back to our curve pool

    // Swap stuff
    uint256 public keepCRV = 1000;
    uint256 public constant FEE_DENOMINATOR = 10000; // with this and the above, sending 15% of our CRV yield to our voter
    
    ICrvV3 public constant crv =
        ICrvV3(address(0xD533a949740bb3306d119CC777fa900bA034cd52));
    IERC20 public constant convexToken =
        IERC20(address(0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B));
    IERC20 public constant weth =
        IERC20(address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2));
    IERC20 public constant dai =
        IERC20(address(0x6B175474E89094C44Da98b954EedeAC495271d0F));
    IERC20 public constant usdc =
        IERC20(address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48));
    IERC20 public constant usdt =
        IERC20(address(0xdAC17F958D2ee523a2206206994597C13D831ec7));

    uint256 public USE_SUSHI = 1; // if 1, use sushiswap as our router for CRV or CVX sells
    address public constant sushiswapRouter =
        address(0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    address public constant uniswapRouter =
        address(0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
        
    // convex-specific variables
    bool public harvestExtras = true; // boolean to determine if we should always claim extra rewards
    bool public claimRewards = false; // boolean if we should always claim rewards when withdrawing, typically don't need to
    uint256 public convexMintRatio = 5000; // amount of CVX tokens minted per CRV rewards tokens, in basis points 

    // Keep3r stuff
    uint256 public manualKeep3rHarvest = 0;
    uint256 public harvestProfitFactor; 
    uint256 public tendCounter = 0;
    uint256 public tendsPerHarvest = 0; // how many tends we call before we harvest. set to 0 to never call tends.
    uint256 internal harvestNow = 0; // 0 for false, 1 for true if we are mid-harvest


	// TODO FOR ORB'S VAULTS– ADD CLONING 
    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        minReportDelay = 302400; // 3.5 days
        maxReportDelay = 1209600; // 14 days
        debtThreshold = 400 * 1e18; // we shouldn't ever have debt, but set a bit of a buffer
        profitFactor = 4000; // in this strategy, profitFactor is only used for telling keep3rs when to move funds from vault to strategy

        // want = crvIB, Curve's Iron Bank pool (ycDai+ycUsdc+ycUsdt)
        want.safeApprove(address(depositContract), uint256(-1));

        // add approvals for crv on sushiswap and uniswap due to weird crv approval issues for setCrvRouter
        // add approvals on all tokens
        crv.approve(uniswapRouter, uint256(-1));
        crv.approve(sushiswapRouter, uint256(-1));
        convexToken.approve(uniswapRouter, uint256(-1));
        convexToken.approve(sushiswapRouter, uint256(-1));
        dai.safeApprove(address(curve), uint256(-1));
        usdc.safeApprove(address(curve), uint256(-1));
        usdt.safeApprove(address(curve), uint256(-1));
        
        // crv token path
        crvPath = new address[](3);
        crvPath[0] = address(crv);
        crvPath[1] = address(weth);
        crvPath[2] = address(dai);
        
        // convex token path
        convexTokenPath = new address[](3);
        convexTokenPath[0] = address(convexToken);
        convexTokenPath[1] = address(weth);
        convexTokenPath[2] = address(dai);
    }

    function name() external view override returns (string memory) {
        return "StrategyConvexCurveLP";
    }

    // total assets held by strategy. loose funds in strategy and all staked funds
    function estimatedTotalAssets() public view override returns (uint256) {
        return IConvexRewards(rewardsContract).balanceOf(address(this)).add(want.balanceOf(address(this)));
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // TODO: Do stuff here to free up any returns back into `want`
        // NOTE: Return `_profit` which is value generated by all positions, priced in `want`
        // NOTE: Should try to free up at least `_debtOutstanding` of underlying position

        // if we have anything staked, then harvest CRV and CVX from the rewards contract
        uint256 stakedTokens = IConvexRewards(rewardsContract).balanceOf(address(this));
        uint256 claimableTokens = IConvexRewards(rewardsContract).earned(address(this));
        if (stakedTokens > 0 && claimableTokens > 0) {
        	// if for some reason we don't want extra rewards, make sure we don't harvest them
        	IConvexRewards(rewardsContract).getReward(address(this), harvestExtras);
        	
            uint256 crvBalance = crv.balanceOf(address(this));
            uint256 convexBalance = convexToken.balanceOf(address(this));

            uint256 _keepCRV = crvBalance.mul(keepCRV).div(FEE_DENOMINATOR);
            IERC20(address(crv)).safeTransfer(voter, _keepCRV);
            uint256 crvRemainder = crvBalance.sub(_keepCRV);

            _sellCrv(crvRemainder);
            _sellConvex(convexBalance);

            if (optimal == 0) {
                uint256 daiBalance = dai.balanceOf(address(this));
                curve.add_liquidity([daiBalance, 0, 0], 0, true);
            } else if (optimal == 1) {
                uint256 usdcBalance = usdc.balanceOf(address(this));
                curve.add_liquidity([0, usdcBalance, 0], 0, true);
            } else {
                uint256 usdtBalance = usdt.balanceOf(address(this));
                curve.add_liquidity([0, 0, usdtBalance], 0, true);
            }
        }
        // this is a harvest, so set our switch equal to 1 so this
        // performs as a harvest the whole way through
        harvestNow = 1;
        
        // if this was the result of a manual keep3r harvest, then reset our trigger
        if (manualKeep3rHarvest == 1) manualKeep3rHarvest = 0;
        
        // serious loss should never happen, but if it does (for instance, if Curve is hacked), let's record it accurately
        uint256 assets = estimatedTotalAssets();
        uint256 debt = vault.strategies(address(this)).totalDebt;

        // if assets are greater than debt, things are working great!
        if (assets > debt) {
            _profit = want.balanceOf(address(this));
        }
        // if assets are less than debt, we are in trouble
        else {
            _loss = debt.sub(assets);
            _profit = 0;
        }

        // debtOustanding will only be > 0 in the event of revoking or lowering debtRatio of a strategy
        if (_debtOutstanding > 0) {
    		IConvexRewards(rewardsContract).withdrawAndUnwrap(Math.min(stakedTokens, _debtOutstanding), true);

            _debtPayment = Math.min(
                _debtOutstanding,
                want.balanceOf(address(this))
            );
        }

        return (_profit, _loss, _debtPayment);
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        if (emergencyExit) {
            return;
        } else if (harvestNow == 1) {
            // if this is part of a harvest call, send all of our Iron Bank pool tokens to be deposited
            uint256 _toInvest = want.balanceOf(address(this));
            //deposit into convex and stake immediately
            IConvexDeposit(depositContract).deposit(pid, _toInvest, true);
            // since we've completed our harvest call, reset our tend counter and our harvest now
            tendCounter = 0;
            harvestNow = 0;
        } else {
            // This is our tend call. If we have anything staked, then harvest CRV and CVX from the rewards contract
        	uint256 stakedTokens = IConvexRewards(rewardsContract).balanceOf(address(this));
        	uint256 claimableTokens = IConvexRewards(rewardsContract).earned(address(this));
        	if (stakedTokens > 0 && claimableTokens > 0) {
        		// if for some reason we don't want extra rewards, make sure we don't harvest them
        		IConvexRewards(rewardsContract).getReward(address(this), harvestExtras);
        	
            	uint256 crvBalance = crv.balanceOf(address(this));
            	uint256 convexBalance = convexToken.balanceOf(address(this));

            	uint256 _keepCRV = crvBalance.mul(keepCRV).div(FEE_DENOMINATOR);
            	IERC20(address(crv)).safeTransfer(voter, _keepCRV);
            	uint256 crvRemainder = crvBalance.sub(_keepCRV);

            	_sellCrv(crvRemainder);
            	_sellConvex(convexBalance);
            	// increase our tend counter by 1 so we can know when we should harvest again
            	uint256 previousTendCounter = tendCounter;
            	tendCounter = previousTendCounter.add(1);
            }
        }
    }

    function liquidatePosition(uint256 _amountNeeded)
        internal
        override
        returns (uint256 _liquidatedAmount, uint256 _loss)
    {
        uint256 wantBal = want.balanceOf(address(this));
        if (_amountNeeded > wantBal) {
            uint256 stakedTokens = IConvexRewards(rewardsContract).balanceOf(address(this));
    		IConvexRewards(rewardsContract).withdrawAndUnwrap(Math.min(stakedTokens, _amountNeeded - wantBal), true);
    		
            uint256 withdrawnBal = want.balanceOf(address(this));
            _liquidatedAmount = Math.min(_amountNeeded, withdrawnBal);

            // if _amountNeeded != withdrawnBal, then we have an error
            if (_amountNeeded != withdrawnBal) {
                uint256 assets = estimatedTotalAssets();
                uint256 debt = vault.strategies(address(this)).totalDebt;
                _loss = debt.sub(assets);
            }
        }

        return (_liquidatedAmount, _loss);
    }

    // Sells our harvested CRV into the selected output (DAI, USDC, or USDT).
    function _sellCrv(uint256 _amount) internal {
        IUniswapV2Router02(crvRouter).swapExactTokensForTokens(
            _amount,
            uint256(0),
            crvPath,
            address(this),
            now
        );
    }
    
    // Sells our harvested CVX into the selected output (DAI, USDC, or USDT).
    function _sellConvex(uint256 _amount) internal {
        IUniswapV2Router02(cvxRouter).swapExactTokensForTokens(
            _amount,
            uint256(0),
            convexTokenPath,
            address(this),
            now
        );
    }

	// if we need to exit without claiming any rewards, this is probably the best way (anything with staking contract auto-triggers claiming, even if we don't get the rewards)
	// make sure to check claimRewards before this step if needed
    function emergencyWithdraw(uint256 _withdrawalMethod) external onlyAuthorized {
        uint256 stakedTokens = IConvexRewards(rewardsContract).balanceOf(address(this));
    	if (_withdrawalMethod == 0) { // this is withdrawing without touching rewards in any shape and completely avoids the staking contract
    		IConvexDeposit(depositContract).withdraw(pid, stakedTokens);
    	} else if (_withdrawalMethod == 1) { // this is withdrawing and unwrapping
    		IConvexRewards(rewardsContract).withdrawAndUnwrap(stakedTokens, claimRewards);
    	} else { // this is withdrawing to the wrapped cvx vault token
    		IConvexRewards(rewardsContract).withdraw(stakedTokens, claimRewards);
    	}
    }
	
	// migrate our want token to a new strategy if needed, make sure to check claimRewards first
    function prepareMigration(address _newStrategy) internal override {
        uint256 stakedTokens = IConvexRewards(rewardsContract).balanceOf(address(this));
        if (stakedTokens > 0) {
        	IConvexRewards(rewardsContract).withdrawAndUnwrap(stakedTokens, claimRewards);
        }
    }

	// we don't want for these tokens to be swept out
    function protectedTokens()
        internal
        view
        override
        returns (address[] memory)
    {
        address[] memory protected = new address[](5);
        protected[0] = address(convexToken);
        protected[1] = address(crv);
        protected[2] = address(dai);
        protected[3] = address(usdt);
        protected[4] = address(usdc);

        return protected;
    }
    
    /* ========== KEEP3RS ========== */

    function harvestTrigger(uint256 callCostinEth)
        public
        view
        override
        returns (bool)
    {
        StrategyParams memory params = vault.strategies(address(this));
        
        // have a manual toggle switch if needed since keep3rs are more efficient than manual harvest
        if (manualKeep3rHarvest == 1) return true;

        // Should not trigger if Strategy is not activated
        if (params.activation == 0) return false;

        // Should not trigger if we haven't waited long enough since previous harvest
        if (block.timestamp.sub(params.lastReport) < minReportDelay)
            return false;

        // Should trigger if hasn't been called in a while
        if (block.timestamp.sub(params.lastReport) >= maxReportDelay)
            return true;

        // If some amount is owed, pay it back
        // NOTE: Since debt is based on deposits, it makes sense to guard against large
        //       changes to the value from triggering a harvest directly through user
        //       behavior. This should ensure reasonable resistance to manipulation
        //       from user-initiated withdrawals as the outstanding debt fluctuates.
        uint256 outstanding = vault.debtOutstanding();
        if (outstanding > debtThreshold) return true;

        // Check for profits and losses
        uint256 total = estimatedTotalAssets();
        // Trigger if we have a loss to report
        if (total.add(debtThreshold) < params.totalDebt) return true;

        // no need to spend the gas to harvest every time; tend is much cheaper
        if (tendCounter < tendsPerHarvest) return false;
        
        // Trigger if it makes sense for the vault to send funds idle funds from the vault to the strategy, or to harvest.
        uint256 profit = 0;
        if (total > params.totalDebt) profit = total.sub(params.totalDebt); // We've earned a profit!
        
        // calculate how much the call costs in dollars (converted from ETH)
        uint256 callCost = ethToDollaBill(callCostinEth);

        // check if it makes sense to send funds from vault to strategy
        uint256 credit = vault.creditAvailable();
        return (profitFactor.mul(callCost) < credit.add(profit));
        
        // calculate how much profit we'll make if we harvest
        uint256 harvestProfit = claimableProfitInDolla();
        
        // check if we make enough from this to justify the harvest call
        return (harvestProfitFactor.mul(callCost)) < harvestProfit;
    }

    // set what will trigger keepers to call tend, which will harvest and sell CRV for optimal asset but not deposit or report profits
    function tendTrigger(uint256 callCostinEth)
        public
        view
        override
        returns (bool)
    {
        // we need to call a harvest every once in a while, every tendsPerHarvest number of tends
        if (tendCounter >= tendsPerHarvest) return false;

        StrategyParams memory params = vault.strategies(address(this));
        // Tend should trigger once it has been the minimum time between harvests divided by 1+tendsPerHarvest to space out tends equally
        // we multiply this number by the current tendCounter+1 to know where we are in time
        // we are assuming here that keepers will essentially call tend as soon as this is true
        if (
            block.timestamp.sub(params.lastReport) >
            (
                minReportDelay.div(
                    (tendCounter.add(1)).mul(tendsPerHarvest.add(1))
                )
            )
        ) return true;
    }

    // convert our keeper's eth cost into dai
    function ethToDollaBill(uint256 _ethAmount) internal view returns (uint256) {
        address[] memory ethPath = new address[](2);
        ethPath[0] = address(weth);
        ethPath[1] = address(dai);

        uint256[] memory callCostInDai = IUniswapV2Router02(crvRouter).getAmountsOut(_ethAmount, ethPath);

        return callCostInDai[callCostInDai.length - 1];
    	}

    // convert our unsold CRV and CVX into USD profit for our keep3r
    function claimableProfitInDolla() internal view returns (uint256) {
    	uint256 claimableCrv = IAlchemix(alchemixStaking).earned(address(this)); // how much CRV we can claim from the staking contract
    	uint256 mintableCvx = claimableCrv.mul(convexMintRatio).div(FEE_DENOMINATOR); // a set amount of CVX token is minted per CRV claimed
        
        uint256[] memory crvSwap = IUniswapV2Router02(crvRouter).getAmountsOut(claimableCrv, crvPath);
		uint256 crvValue = crvSwap[2];
		
		if (mintableCvx > 0) {
        	uint256[] memory cvxSwap = IUniswapV2Router02(cvxRouter).getAmountsOut(mintableCvx, convexTokenPath);
			uint256 cvxValue = cvxSwap[2];		
		}

        return crvValue.add(cvxValue); // dollar value of our harvest 
    	}

    // set number of tends before we call our next harvest
    function setTendsPerHarvest(uint256 _tendsPerHarvest)
        external
        onlyAuthorized
    {
        tendsPerHarvest = _tendsPerHarvest;
    }

	// set this to 1 if we want our keep3rs to manually harvest the strategy; keep3r harvest is more cost-efficient than strategist harvest
    function setKeep3rHarvest(uint256 _setKeep3rHarvest) external onlyAuthorized {
    	manualKeep3rHarvest = _setKeep3rHarvest;
    }

    /* ========== SETTERS ========== */
    
    // These functions are useful for setting parameters of the strategy that may need to be adjusted.

    // Set the amount of CRV to be locked in Yearn's veCRV voter from each harvest. Default is 10%.
    function setKeepCRV(uint256 _keepCRV) external onlyGovernance {
        keepCRV = _keepCRV;
    }

    // 1 is for TRUE value and 0 for FALSE to keep in sync with binary convention
    // Use SushiSwap for CRV Router = 1;
    // Use Uniswap for CRV Router = 0 (or anything else);
    function setCrvRouter(uint256 _isSushiswap) external onlyAuthorized {
        if (_isSushiswap == USE_SUSHI) {
            crvRouter = sushiswapRouter;
        } else {
            crvRouter = uniswapRouter;
        }
    }
    
    // 1 is for TRUE value and 0 for FALSE to keep in sync with binary convention
    // Use SushiSwap for CVX Router = 1;
    // Use Uniswap for CVX Router = 0 (or anything else);
    function setCvxRouter(uint256 _isSushiswap) external onlyAuthorized {
        if (_isSushiswap == USE_SUSHI) {
            cvxRouter = sushiswapRouter;
        } else {
            cvxRouter = uniswapRouter;
        }
    }
    
    // Unless contract is borked for some reason, we should always harvest extra tokens
    function setHarvestExtras(bool _harvestExtras) external onlyAuthorized {
            harvestExtras = _harvestExtras;
    }

    // We usually don't need to claim rewards on withdrawals, but might change our mind for migrations etc
    function setClaimRewards(bool _claimRewards) external onlyAuthorized {
            claimRewards = _claimRewards;
    }
    
    // Convex has said they will update over time how many CVX gets minted per CRV claimed, so we need to be able to update this
    function setConvexMintRatio(uint256 _amount) external onlyAuthorized {
            convexMintRatio = _amount;
    }

	// set this to the multiple we want to make on our harvests vs the cost
    function setharvestProfitFactor(uint256 _harvestProfitFactor) external onlyAuthorized {
    	harvestProfitFactor = _harvestProfitFactor;
    }

    // Set optimal token to sell harvested CRV into for depositing back to Iron Bank Curve pool.
    // Default is DAI, but can be set to USDC or USDT as needed by strategist or governance.
    function setOptimal(uint256 _optimal) external onlyAuthorized {
        crvPath = new address[](3);
        crvPath[0] = address(crv);
        crvPath[1] = address(weth);
        
        convexTokenPath = new address[](3);
        convexTokenPath[0] = address(convexToken);
        convexTokenPath[1] = address(weth);

        if (_optimal == 0) {
            crvPath[2] = address(dai);
            convexTokenPath[2] = address(dai);
            optimal = 0;
        } else if (_optimal == 1) {
            crvPath[2] = address(usdc);
            convexTokenPath[2] = address(usdc);
            optimal = 1;
        } else if (_optimal == 2) {
            crvPath[2] = address(usdt);
            convexTokenPath[2] = address(usdt);
            optimal = 2;
        } else {
            require(false, "incorrect token");
        }
    }
}
