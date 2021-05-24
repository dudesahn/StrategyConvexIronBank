import brownie
from brownie import Contract
from brownie import config

# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!

# test passes as of 21-05-20
def test_migration(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, curveVoterProxyStrategy, StrategyConvexIronBank):
    # deploy our new strategy
    new_strategy = dudesahn.deploy(StrategyConvexIronBank, vault)
    total_old = strategy.estimatedTotalAssets()
    total_old_proxy = curveVoterProxyStrategy.estimatedTotalAssets()

    # migrate our old strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": gov})

    # assert that our old strategy is empty
    updated_total_old = strategy.estimatedTotalAssets()
    assert updated_total_old == 0

    # harvest to get funds back in strategy
    new_strategy.harvest({"from": dudesahn})
    new_strat_balance = new_strategy.estimatedTotalAssets()
    total_new_proxy = curveVoterProxyStrategy.estimatedTotalAssets()
    assert total_new_proxy == total_old_proxy
    assert new_strat_balance >= total_old
    
    startingVault = vault.totalAssets()
    print("\nVault starting assets with new strategy: ", startingVault)
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # test out tend
    new_strategy.tend({"from": dudesahn})
    assert new_strategy.tendCounter() == 1
    
    # simulate a day of waiting for share price to bump back up
    curveVoterProxyStrategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)
    
    # Test out our migrated strategy, confirm we're making a profit
    new_strategy.harvest({"from": dudesahn})
    assert new_strategy.tendCounter() == 0
    vaultAssets_2 = vault.totalAssets()
    assert vaultAssets_2 > startingVault
    print("\nAssets after 1 day harvest: ", vaultAssets_2)