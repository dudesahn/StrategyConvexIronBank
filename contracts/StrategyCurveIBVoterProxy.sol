// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {BaseStrategy} from "@yearnvaults/contracts/BaseStrategy.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/math/Math.sol";

import "./interfaces/curve.sol";
import "./interfaces/yearn.sol";
import {IUniswapV2Router02} from "./interfaces/uniswap.sol";


contract StrategyCurveIBVoterProxy is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address private uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address private sushiswapRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;
    address public crvRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F; // default to sushiswap

    address public constant crvIBgauge = address(0xF5194c3325202F456c95c1Cf0cA36f8475C1949F); // Curve Iron Bank Gauge contract, v2 is tokenized
    address public constant voter = address(0xF147b8125d2ef93FB6965Db97D6746952a133934); // Yearn's veCRV voter

    address[] public crvPath;
    address[] public crvPathDai;
    address[] public crvPathUsdc;
    address[] public crvPathUsdt;
    uint256 public keepCRV = 1000;
    uint256 public constant fee_denominator = 10000;

    ICurveFi public crvIBpool = ICurveFi(address(0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF)); // Curve Iron Bank Pool
    ICurveStrategyProxy public CurveProxy = ICurveStrategyProxy(address(0x9a3a03C614dc467ACC3e81275468e033c98d960E)); // Yearn's StrategyProxy
    ICrvV3 public Crv = ICrvV3(address(0xD533a949740bb3306d119CC777fa900bA034cd52)); // 1e18
    IERC20 public Dai = IERC20(address(0x6B175474E89094C44Da98b954EedeAC495271d0F)); // 1e18
    IERC20 public Usdc = IERC20(address(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)); // 1e6
    IERC20 public Usdt = IERC20(address(0xdAC17F958D2ee523a2206206994597C13D831ec7)); // 1e6
    IERC20 public Weth = IERC20(address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2)); // 1e18

    bool optimizePath = true;

    constructor(address _vault) public BaseStrategy(_vault) {
        // You can set these parameters on deployment to whatever you want
        // maxReportDelay = 6300;
        // profitFactor = 100;
        // debtThreshold = 0;

        // want = crvIB, Curve's Iron Bank pool (ycDai+ycUsdc+ycUsdt)
        want.safeApprove(address(CurveProxy), uint256(- 1));
        Dai.safeApprove(address(crvIBpool), uint256(- 1));
        Usdc.safeApprove(address(crvIBpool), uint256(- 1));
        Usdt.safeApprove(address(crvIBpool), uint256(- 1));
        Crv.approve(crvRouter, uint256(- 1));
        Crv.approve(voter, uint256(- 1));

        // using all unwrapped tokens since there is a risk of insufficient funds for wrapped if swapping directly (sushiswap)
        crvPathDai = new address[](3);
        crvPathDai[0] = address(Crv);
        crvPathDai[1] = address(Weth);
        crvPathDai[2] = address(Dai);

        crvPathUsdc = new address[](3);
        crvPathUsdc[0] = address(Crv);
        crvPathUsdc[1] = address(Weth);
        crvPathUsdc[2] = address(Usdc);

        crvPathUsdt = new address[](3);
        crvPathUsdt[0] = address(Crv);
        crvPathUsdt[1] = address(Weth);
        crvPathUsdt[2] = address(Usdt);

        crvPath = crvPathDai;
    }

    function name() external override view returns (string memory) {
        // Add your own name here, suggestion e.g. "StrategyCreamYFI"
        return "StrategyCurveIBVoterProxy";
    }
    
    function setProxy(address _proxy) external {
        require(msg.sender == governance, "!governance");
        CurveProxy = _proxy;
    }
    
    function setKeepCRV(uint256 _keepCRV) external {
        require(msg.sender == governance, "!governance");
        keepCRV = _keepCRV;
    }
    
    function estimatedTotalAssets() public override view returns (uint256) {
        return
        balanceOfStaked() +
        balanceOfPoolToken() +
        _optimalWant(balanceOfReward());
//        _optimalWant(balanceOfUnclaimedReward());
    }


    // balance of unstaked `want` tokens
    function balanceOfPoolToken() internal view returns (uint256){
        return want.balanceOf(address(this));
    }

    // in crv
    function balanceOfUnclaimedReward() public view returns (uint256){
        return IGauge(crvIBgauge).claimable_tokens(voter);
    }

    // in crv
    function balanceOfReward() internal view returns (uint256){
        return Crv.balanceOf(address(this));
    }

    // balance of gauge tokens staked. 1:1 with `want`
    function balanceOfStaked() public view returns (uint256){
        return CurveProxy.balanceOf(crvIBgauge);
        // uses a different nomenclature. This resolves to
        // => return IERC20(_gauge).balanceOf(address(proxy));
    }

    function prepareReturn(uint256 _debtOutstanding) internal override
    returns (
        uint256 _profit,
        uint256 _loss,
        uint256 _debtPayment
    ){
        // TODO: Do stuff here to free up any returns back into `want`
        // NOTE: Return `_profit` which is value generated by all positions, priced in `want`
        // NOTE: Should try to free up at least `_debtOutstanding` of underlying position

        if (balanceOfStaked() > 0) {
            CurveProxy.harvest(crvIBgauge);

            uint256 crvBalance = balanceOfReward();
            if (crvBalance > 0) {
            uint256 _keepCRV = crvBalance.mul(keepCRV).div(fee_denominator);
            IERC20(crv).safeTransfer(voter, _keepCRV);
            crvRemainder = crvBalance.sub(_keepCRV);
            
                _sell(crvRemainder);
            }
            uint256 daiBalance = Dai.balanceOf(address(this));
            uint256 usdcBalance = Usdc.balanceOf(address(this));
            uint256 usdtBalance = Usdt.balanceOf(address(this));

            crvIBpool.add_liquidity([daiBalance, usdcBalance, usdtBalance], 0, true);

            _profit = want.balanceOf(address(this));
        }

        if (_debtOutstanding > 0) {
            if (_debtOutstanding > _profit) {
                CurveProxy.withdraw(crvIBgauge, address(want), Math.min(balanceOfStaked(), _debtOutstanding));
            }

            _debtPayment = Math.min(_debtOutstanding, want.balanceOf(address(this)).sub(_profit));
        }
        return (_profit, _loss, _debtPayment);
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 _investAmount = want.balanceOf(address(this));
        // move everything to proxy
        want.safeTransfer(address(CurveProxy), _investAmount);
        CurveProxy.deposit(crvIBgauge, address(want));
    }

    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _liquidatedAmount, uint256 _loss){
        uint256 wantBal = want.balanceOf(address(this));

        if (_amountNeeded > wantBal) {
            CurveProxy.withdraw(crvIBgauge, address(want), Math.min(balanceOfStaked(), _amountNeeded - wantBal));
        }

        _liquidatedAmount = Math.min(_amountNeeded, want.balanceOf(address(this)));
        return (_liquidatedAmount, _loss);
    }


    function _sell(uint256 _amount) internal {
        if (optimizePath) {
            crvPath = _optimalPath(_amount);
        }
        IUniswapV2Router02(crvRouter).swapExactTokensForTokens(_amount, uint256(0), crvPath, address(this), now);
    }

    function setOptimizePath(bool _toOptimize) external onlyAuthorized {
        optimizePath = _toOptimize;
    }


    function setCrvRouter(bool isSushiswap, address[] calldata _path) public onlyGovernance {
        if (isSushiswap) {
            crvRouter = sushiswapRouter;
        } else {
            crvRouter = uniswapRouter;
        }
        crvPath = _path;
        Crv.approve(crvRouter, uint256(- 1));
    }

    function prepareMigration(address _newStrategy) internal override {
        // TODO: Transfer any non-`want` tokens to the new strategy
        // NOTE: `migrate` will automatically forward all `want` in this strategy to the new one
        prepareReturn(balanceOfStaked());
    }

    // crv rewards are always sold for underlying dai, usdc, usdt and immediately deposited back in to the pool
    function protectedTokens() internal override view returns (address[] memory) {
        address[] memory protected = new address[](1);
        protected[0] = crvIBgauge;
        return protected;
    }

    // optimal amount of `want` received if crv were sold
    function _optimalWant(uint256 _amount) public view returns (uint256){
        uint256[3] memory wants = _estimateCrvPrices(_amount);

        if (wants[0] >= wants[1] && wants[0] >= wants[2]) {
            return wants[0];
        } else if (wants[1] >= wants[0] && wants[1] >= wants[2]) {
            return wants[1];
        } else {
            return wants[2];
        }
    }

    // optimal path to sell crv to maximize `want`
    function _optimalPath(uint256 _amount) public returns (address[] memory){
        uint256[3] memory wants = _estimateCrvPrices(_amount);

        if (wants[0] >= wants[1] && wants[0] >= wants[2]) {
            return crvPathDai;
        } else if (wants[1] >= wants[0] && wants[1] >= wants[2]) {
            return crvPathUsdc;
        } else {
            return crvPathUsdt;
        }
    }

    // estimate amount of `want` back if crv were sold in each of the 3 pool tokens
    function _estimateCrvPrices(uint256 _amount) public view returns (uint256[3] memory){
        if (_amount <= 0) {
            return [uint256(0), uint256(0), uint256(0)];
        }

        uint256 outDai = IUniswapV2Router02(crvRouter).getAmountsOut(_amount, crvPathDai)[1];
        uint256 outUsdc = IUniswapV2Router02(crvRouter).getAmountsOut(_amount, crvPathUsdc)[1];
        uint256 outUsdt = IUniswapV2Router02(crvRouter).getAmountsOut(_amount, crvPathUsdt)[1];

        // amount of want tokens
        uint256 tokenDaiDeposit = crvIBpool.calc_token_amount([outDai, 0, 0], true);
        uint256 tokenUsdcDeposit = crvIBpool.calc_token_amount([0, outUsdc, 0], true);
        uint256 tokenUsdtDeposit = crvIBpool.calc_token_amount([0, 0, outUsdt], true);

        uint256[3] memory wants = [tokenDaiDeposit, tokenUsdcDeposit, tokenUsdtDeposit];
        return wants;
    }


    receive() external payable {}
}   
