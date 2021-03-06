import brownie
# from helpers import showBalances
from brownie import Contract
# from useful_methods import genericStateOfStrat,genericStateOfVault


# **** TEST ALL CONTRACT FUNCTIONS


def test_operation(token, vault, strategy, strategist, amount, whale, gauge, strategyProxy, chain, voter):
    # Deposit to the vault, whale approves 10% of his stack and deposits it
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault) == amount

    # set optimal to decide which token to deposit into Curve pool for each harvest (DAI first)
    strategy.setOptimal(0)

    # harvest, store asset amount
    strategy.harvest({"from": strategist})
    old_assets_dai = vault.totalAssets()
    assert strategyProxy.balanceOf(gauge) == amount
    assert old_assets_dai == amount
    assert old_assets_dai == strategyProxy.balanceOf(gauge)

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    strategy.harvest({"from": strategist})
    new_assets_dai = vault.totalAssets()
    
    # There are two ways to check gauge token balances. Either call from the gauge token contract gauge.balanceOf(voter), or call strategyProxy.balanceOf(gauge)
    
    # assert strategyProxy.balanceOf(gauge) > amount
    assert strategyProxy.balanceOf(gauge) == new_assets_dai
    # assert gauge.balanceOf(voter) == strategyProxy.balanceOf(gauge)
    # assert strategyProxy.balanceOf(gauge) == new_assets_dai
    assert new_assets_dai > old_assets_dai
   
        
#     genericStateOfStrat(strategy, currency, vault)
#     genericStateOfVault(vault, currency)

    # Display estimated APR based on the past month
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai-old_assets_dai)*12)/(old_assets_dai)))
    
    
    # set optimal to USDC. new_assets_dai is now our new baseline
    strategy.setOptimal(1)

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount after switch to USDC
    strategy.harvest({"from": strategist})
    new_assets_usdc = vault.totalAssets()
    assert strategyProxy.balanceOf(gauge) > amount
    assert new_assets_usdc > new_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated USDC APR: ", "{:.2%}".format(((new_assets_usdc-new_assets_dai)*12)/(new_assets_dai)))

    # set optimal to USDT, new_assets_usdc is now our new baseline
    strategy.setOptimal(2)
    
    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    strategy.harvest({"from": strategist})
    new_assets_usdt = vault.totalAssets()
    assert strategyProxy.balanceOf(gauge) > amount
    assert new_assets_usdt > new_assets_usdc
    
    # Display estimated APR based on the past month
    print("\nEstimated USDT APR: ", "{:.2%}".format(((new_assets_usdt-new_assets_usdc)*12)/(new_assets_usdc)))

    # tend()
    strategy.tend()

    # withdrawal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) != 0