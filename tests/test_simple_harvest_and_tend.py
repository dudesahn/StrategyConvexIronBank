import brownie
from brownie import Contract
from brownie import config


def test_simple_harvest_and_tend(gov, token, vault, dudesahn, strategist, whale, strategy, voter, gaugeIB, chain, strategist_ms):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(1000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    
    # harvest, store asset amount
    strategy.harvest({"from": gov})
    old_assets_dai = strategy.estimatedTotalAssets()
    assert old_assets_dai > 0
    assert token.balanceOf(strategy) == 0
        
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # Test out our migrated strategy, confirm we're making a profit
    strategy.harvest({"from": gov})
    assert strategy.tendCounter() == 0
    vaultAssets_2 = strategy.estimatedTotalAssets()
    assert vaultAssets_2 > old_assets_dai
    print("\nAssets after 1 day harvest: ", vaultAssets_2)
    
    staked_LP = masterchef.getStakeTotalDeposited(strategy, 4)
    print("\nStaked LP: ", (staked_LP / 1e18))
    assert masterchef.getStakeTotalDeposited(strategy, 4) > 0

    # harvest after a day, store new asset amount
    strategy.harvest({"from": liveGov})
    # tx.call_trace(True)
    new_assets_dai = strategy.estimatedTotalAssets()
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past day
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 365) / (old_assets_dai)))

    # we lose 0.04% whenever we deposit into a curve pool or withdraw
    # withdraw whale's money and see if he's earned a profit (barely even with 0.08% loss)
    vault.withdraw({"from": whale})    
    print("This started as 1000 pool tokens", ( token.balanceOf(whale) - newWhale ) / 1e18)
    assert token.balanceOf(whale) > startingWhale    staked_LP = masterchef.getStakeTotalDeposited(strategy, 4)
    print("\nStaked LP: ", (staked_LP / 1e18))
    assert masterchef.getStakeTotalDeposited(strategy, 4) > 0

    # harvest after a day, store new asset amount
    strategy.harvest({"from": liveGov})
    # tx.call_trace(True)
    new_assets_dai = strategy.estimatedTotalAssets()
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past day
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 365) / (old_assets_dai)))

    # we lose 0.04% whenever we deposit into a curve pool or withdraw
    # withdraw whale's money and see if he's earned a profit (barely even with 0.08% loss)
    vault.withdraw({"from": whale})    
    print("This started as 1000 DAI", ( token.balanceOf(whale) - newWhale ) / 1e18)
    assert token.balanceOf(whale) > startingWhale