# Migration for yDaddy

there's another last step to set the proxy of the old strategy with zero address. to make it safer.

	# I do this step first
	new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)
	# Set up sharer on new strategy as well

	# Now, yDaddy does the rest
    # deploy our new strategy
    new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)  
      
    # here's our addresses
    multisig = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)  
    
    # deploy my strategy, set up sharer, set up rewards
    
      
    # prepare our live strategy to migrate
    vault.updateStrategyDebtRatio(live_strategy, 0, {"from": strategist_ms})
    live_strategy.harvest({"from": dudesahn})
    live_strategy.setProxy(0x0000000000000000000000000000000000000000)

    # assert that our old strategy is empty
    live_strat_balance = live_strategy.estimatedTotalAssets()
    assert live_strat_balance == 0
    old_gauge_balance = strategyProxy.balanceOf(gaugeIB)
    assert old_gauge_balance == 0
    print("\nLive strategy balance: ", live_strat_balance)
    total_old = vault.totalAssets()
    print("\nTotal Balance to Migrate: ", total_old)
    print("\nProxy gauge balance: ", old_gauge_balance)

    # migrate our old strategy
    vault.migrateStrategy(live_strategy, new_strategy, {"from": strategist_ms})

    # approve on new strategy with proxy
    strategyProxy.approveStrategy(live_strategy.gauge(), new_strategy, {"from": gov})
    vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": strategist_ms})
 
    # Update deposit limit to the vault to $10 million since it's currently maxed out
    vault.setDepositLimit(10000000000000000000000000, {"from": strategist_ms})
    
    # harvest to get funds back in strategy
    new_strategy.harvest({"from": dudesahn})
    new_gauge_balance = strategyProxy.balanceOf(gaugeIB)
    assert new_gauge_balance == total_old
    print("\nNew Proxy gauge balance: ", new_gauge_balance)