import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_crv_cvx_yield(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, crv, cvx):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    
    # harvest, store asset amount
    strategy.harvest({"from": gov})
        
    # simulate one day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    strategy.harvest({"from": gov})
    
    cvx_holdings = cvx.balanceOf(strategy)/1e18
    crv_holdings = crv.balanceOf(strategy)/1e18

    print("\nCVX balance: ", cvx_holdings)    
    print("\nCRV balance: ", crv_holdings)
    
#     assert cvx_holdings > 0
#     assert crv_holdings > 0
    
    ## comment out this section of prepareReturn before running this test
#                 _sellCrv(crvRemainder);
#             _sellConvex(convexBalance);
# 
#             if (optimal == 0) {
#                 uint256 daiBalance = dai.balanceOf(address(this));
#                 curve.add_liquidity([daiBalance, 0, 0], 0, true);
#             } else if (optimal == 1) {
#                 uint256 usdcBalance = usdc.balanceOf(address(this));
#                 curve.add_liquidity([0, usdcBalance, 0], 0, true);
#             } else {
#                 uint256 usdtBalance = usdt.balanceOf(address(this));
#                 curve.add_liquidity([0, 0, usdtBalance], 0, true);
#             }