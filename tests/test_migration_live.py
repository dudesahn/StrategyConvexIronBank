import brownie
from brownie import Contract
from brownie import config

# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!


def test_migration_live(token, vault, strategy, dudesahn, voter, gov, whale, StrategyCurveIBVoterProxy, strategyProxy, strategist_ms, rando, chain, gaugeIB):
    # Simulate ydaddy approving my strategy on the StrategyProxy (now commented out)
    # tx = strategyProxy.approveStrategy(strategy.gauge(), strategy, {"from": gov})
    # tx.call_trace(True)

    # Deposit to the vault and harvest
    startingVault = token.balanceOf(vault)
    amount = 100 * (10 ** 18)
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    strategy.harvest({"from": dudesahn})
    holdings = amount + startingVault
    
    print("\nStarting Vault Balance", startingVault) 
    # Check for any assets only in the vault, not in the strategy
    print("\nHoldings: ", holdings)
    
    assert strategy.estimatedTotalAssets() == holdings

    # deploy our new strategy
    new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)
    
    # prepare our old strategy to migrate
    vault.updateStrategyDebtRatio(strategy, 0, {"from": strategist_ms})
    vault.revokeStrategy(strategy.address, {"from": strategist_ms})
    strategy.harvest({"from": dudesahn})
    assert strategy.estimatedTotalAssets() == 0
    assert token.balanceOf(vault) >= holdings

    # migrate our old strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": strategist_ms})

    # approve on new strategy with proxy
    strategyProxy.approveStrategy(strategy.gauge(), new_strategy, {"from": gov})
    vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": strategist_ms})
    new_strategy.harvest({"from": dudesahn})

    assert new_strategy.estimatedTotalAssets() >= holdings    
    assert token.balanceOf(strategy) == 0
        
    # give rando his money back, then he sends back to whale
    vault.withdraw({"from": rando})    
    
    assert token.balanceOf(rando) >= startingRando
    endingRando = token.balanceOf(rando)
    token.transfer(whale, endingRando, {"from": rando})

    
    
