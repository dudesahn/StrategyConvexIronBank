import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_operation(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, cvx, convexWhale, curveVoterProxyStrategy):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    starting_assets = vault.totalAssets()
        
    # tend our strategy 
    strategy.tend({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # harvest, store asset amount
    strategy.harvest({"from": dudesahn})
    # tx.call_trace(True)
    old_assets_dai = vault.totalAssets()
    assert old_assets_dai >= starting_assets

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # harvest after a day, store new asset amount
    tx = strategy.harvest({"from": dudesahn})
    # tx.call_trace(True)
    new_assets_dai = vault.totalAssets()
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 365) / (strategy.estimatedTotalAssets())))

    # set optimal to USDC. new_assets_dai is now our new baseline
    strategy.setOptimal(1, {"from": gov})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # harvest after a month, store new asset amount after switch to USDC
    strategy.harvest({"from": dudesahn})
    new_assets_usdc = vault.totalAssets()
    assert new_assets_usdc > new_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated USDC APR: ", "{:.2%}".format(((new_assets_usdc - new_assets_dai) * 365) / (strategy.estimatedTotalAssets())))

    # set optimal to USDT, new_assets_usdc is now our new baseline
    strategy.setOptimal(2, {"from": gov})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # harvest after a month, store new asset amount
    strategy.harvest({"from": dudesahn})
    new_assets_usdt = vault.totalAssets()
    assert new_assets_usdt > new_assets_usdc

    # Display estimated APR based on the past month
    print("\nEstimated USDT APR: ", "{:.2%}".format(((new_assets_usdt - new_assets_usdc) * 365) / (strategy.estimatedTotalAssets())))
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # test to make sure our strategy is selling convex properly. send it some from our whale.
    cvx.transfer(strategy, 1000e18, {"from": convexWhale})
    strategy.harvest({"from": dudesahn})
    new_assets_from_convex_sale = vault.totalAssets()
    assert new_assets_from_convex_sale > new_assets_usdt

    # Display estimated APR based on the past day
    print("\nEstimated CVX Donation APR: ", "{:.2%}".format(((new_assets_from_convex_sale - new_assets_usdt) * 365) / (strategy.estimatedTotalAssets())))

    # simulate a day of waiting for share price to bump back up
    curveVoterProxyStrategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 