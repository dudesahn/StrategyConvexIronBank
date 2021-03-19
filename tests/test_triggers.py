import brownie
from brownie import Contract
from brownie import config


def test_triggers(token, vault, strategy, dudesahn, voter, gov, whale, StrategyCurveIBVoterProxy, strategyProxy, strategist_ms, rando, chain, gaugeIB):
    ###### All of this is to migrate to the new strategy with better triggers ##########
    
    # Update deposit limit to the vault since it's currently maxed out
    vault.setDepositLimit(1000000000000000000000000000, {"from": strategist_ms})
    
    # deploy our new strategy
    new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)
    
    # prepare our old strategy to migrate
    vault.updateStrategyDebtRatio(strategy, 0, {"from": strategist_ms})
    vault.revokeStrategy(strategy.address, {"from": strategist_ms})
    strategy.harvest({"from": dudesahn})
    # assert that our old strategy is empty
    assert strategy.estimatedTotalAssets() == 0
    # assert token.balanceOf(vault) >= holdings

    # migrate our old strategy
    vault.migrateStrategy(strategy, new_strategy, {"from": strategist_ms})

    # approve on new strategy with proxy
    strategyProxy.approveStrategy(strategy.gauge(), new_strategy, {"from": gov})
    vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": strategist_ms})
    
    # harvest to start the timer
    new_strategy.harvest({"from": dudesahn})
    
	# get a lot of money in the vault
    amount = 1000000 * (10 ** 18)
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    new_strategy.harvest({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # harvest should trigger false
    tx = new_strategy.harvestTrigger(0, {"from": dudesahn})
    print("\nShould we harvest?", tx)
    
    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)
    
    # harvest should trigger true or false?
    tx = new_strategy.harvestTrigger(0, {"from": dudesahn})
    print("\nShould we harvest?", tx)
    new_strategy.harvest({"from": dudesahn})
    
    # simulate three days of earnings
    chain.sleep(259200)
    chain.mine(1)
    
    # harvest should trigger true
    tx = new_strategy.harvestTrigger(0, {"from": dudesahn})
    print("\nShould we harvest?", tx)
    new_strategy.harvest({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend should trigger true, should be good profit factor
    tx = new_strategy.tendTrigger(0, {"from": dudesahn})
    print("\nShould we tend?", tx)
    new_strategy.tend({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0
