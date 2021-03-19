import brownie
from brownie import Contract
from brownie import config


def test_operation_live(token, vault, strategy, dudesahn, whale, gaugeIB, strategyProxy, chain, voter, rando, gov, strategist_ms):
    # Update deposit limit to the vault since it's currently maxed out
    vault.setDepositLimit(100000000000000000000000000, {"from": strategist_ms})
    
    # Deposit to the vault and harvest
    amount = 100 * (10 ** 18)
    startingVault = vault.totalAssets()
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    holdings = amount + startingVault
    assert vault.totalAssets() == holdings

    # harvest, store asset amount
    strategy.harvest({"from": dudesahn})
    old_assets_dai = vault.totalAssets()
    # tx.call_trace(True)

    assert strategyProxy.balanceOf(gaugeIB) == holdings

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    tx = strategy.harvest({"from": dudesahn})
    # tx.call_trace(True)
    new_assets_dai = vault.totalAssets()

    # Check total assets in the vault + strategy
    print("\nOld Vault totalAssets: ", old_assets_dai)
    print("\nNew Vault totalAssets: ", new_assets_dai)

    # There are two ways to check gauge token balances. Either call from the gauge token contract gauge.balanceOf(voter), or call strategyProxy.balanceOf(gauge)
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 12) / (old_assets_dai)))

    # set optimal to USDC. new_assets_dai is now our new baseline
    strategy.setOptimal(1, {"from": dudesahn})

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount after switch to USDC
    strategy.harvest({"from": dudesahn})
    new_assets_usdc = vault.totalAssets()
    assert strategyProxy.balanceOf(gaugeIB) > holdings
    assert new_assets_usdc > new_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated USDC APR: ", "{:.2%}".format(((new_assets_usdc - new_assets_dai) * 12) / (new_assets_dai)))

    # set optimal to USDT, new_assets_usdc is now our new baseline
    strategy.setOptimal(2, {"from": dudesahn})

    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    strategy.harvest({"from": dudesahn})
    new_assets_usdt = vault.totalAssets()
    assert strategyProxy.balanceOf(gaugeIB) > holdings
    assert new_assets_usdt > new_assets_usdc

    # Display estimated APR based on the past month
    print("\nEstimated USDT APR: ", "{:.2%}".format(((new_assets_usdt - new_assets_usdc) * 12) / (new_assets_usdc)))

    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # give rando his money back, then he sends back to whale
    vault.withdraw({"from": rando})    
    assert token.balanceOf(rando) >= startingRando
    endingRando = token.balanceOf(rando)
    token.transfer(whale, endingRando, {"from": rando})  
