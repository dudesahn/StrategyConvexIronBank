import brownie
# from helpers import showBalances
from brownie import Contract

# **** TEST ALL CONTRACT FUNCTIONS


def test_operation(token, vault, strategy, strategist, amount, whale, gauge, curve_proxy, chain):
    # Deposit to the vault, whale approves 10% of his stack and deposits it
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault) == amount

    # set optimal to decide which token to deposit into Curve pool for each harvest (DAI first)
    strategy.setOptimal(0)

    # harvest, store asset amount
    strategy.harvest({"from": strategist})
    old_assets = vault.totalAssets()
    assert curve_proxy.balanceOf(gauge) == amount

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    strategy.harvest({"from": strategist})
    new_assets = vault.totalAssets()
    assert curve_proxy.balanceOf(gauge) > amount
    
    
    genericStateOfStrat(strategy, currency, vault)
    genericStateOfVault(vault, currency)

    # Display estimated APR based on the past month
    print("\nEstimated APR: ", "{:.2%}".format(((vault.totalAssets()-assets)*12)/(assets)))
    
    
    


#     set optimal to USDC
#     strategy.setOptimal(1)
# 
#     harvest
#     strategy.harvest({"from": strategist})
#     assert token.balanceOf(strategy.address) == amount
# 
#     set optimal to USDT
#     strategy.setOptimal(2)
# 
#     harvest
#     strategy.harvest({"from": strategist})
#     assert token.balanceOf(strategy.address) == amount

    # tend()
    strategy.tend()

    # withdrawal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) != 0