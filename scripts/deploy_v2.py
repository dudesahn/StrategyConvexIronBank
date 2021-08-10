# Migration for yDaddy
# First, I need to deploy the strategy, set the rewards and the sharer addresses up (done)

# next, strategist ms needs to do this, test everything out on mainnet fork first
live_strategy = Contract("0x5c0309fa022Bc1B73fE45A2D73EddeD58a820ff8")
vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
strategist_ms = accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

# Set debt ratio to 0, pull all funds from strategy, and confirm that it's empty
vault.updateStrategyDebtRatio(live_strategy, 0, {"from": strategist_ms})
live_strategy.harvest({"from": strategist_ms})
live_strat_balance = live_strategy.estimatedTotalAssets({"from": strategist_ms})
assert live_strat_balance == 0

# Set our proxy address on old strategy to burn address to be safe, and transfer gov to daddy
live_strategy.setProxy("0x0000000000000000000000000000000000000000", {"from": strategist_ms})
assert live_strategy.proxy() == "0x0000000000000000000000000000000000000000"
vault.setGovernance("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", {"from": strategist_ms})

# Now, yDaddy does the rest
# deploy our new strategy

#### THIS IS A DIFFERENT TRANSACTION FOR YDADDY #######
# here's our addresses
live_strategy = Contract("0x5c0309fa022Bc1B73fE45A2D73EddeD58a820ff8")
multisig = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)
new_strategy = Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")
strategyProxy = Contract("0x9a165622a744C20E3B2CB443AeD98110a33a231b")
gaugeIB = Contract("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F")
# deploy my strategy, set up sharer, set up rewards


# prepare our live strategy to migrate

# assert that our gauge is still empty
vault.acceptGovernance({"from": multisig})
old_gauge_balance = strategyProxy.balanceOf(gaugeIB)
assert old_gauge_balance == 0
print("\nLive strategy balance: ", live_strat_balance)
total_old = vault.totalAssets()
print("\nTotal Balance to Migrate: ", total_old)
print("\nProxy gauge balance: ", old_gauge_balance)

# attach our new strategy to the vault
vault.addStrategy(new_strategy, 10000, 0, 2 ** 256 - 1, 1000, {"from": multisig})

# migrate our old strategy
vault.migrateStrategy(live_strategy, new_strategy, {"from": multisig})

# approve on new strategy with proxy
strategyProxy.approveStrategy(live_strategy.gauge(), new_strategy, {"from": multisig})
vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": multisig})

# Update deposit limit to the vault to $10 million since it's currently maxed out
vault.setDepositLimit(10000000000000000000000000, {"from": multisig})

# harvest to get funds back in strategy
new_strategy.harvest({"from": dudesahn})
new_gauge_balance = strategyProxy.balanceOf(gaugeIB)
assert new_gauge_balance == total_old
print("\nNew Proxy gauge balance: ", new_gauge_balance)
