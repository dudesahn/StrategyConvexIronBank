def gov_to_daddy():
    assert rpc.is_active()
    multisig = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    strategist_ms = accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)
    vault.setGovernance(multisig, {"from": strategist_ms})

    safe_tx = multisend_from_receipts(strategist_ms, history)
    estimate_safe_tx(safe_tx)
    broadcast_tx(safe_tx)


def migrate_ib():
    assert rpc.is_active()
    # here's our addresses
    live_strategy = Contract("0x5c0309fa022Bc1B73fE45A2D73EddeD58a820ff8")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    multisig = accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)
    new_strategy = Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")
    strategyProxy = Contract("0x9a165622a744C20E3B2CB443AeD98110a33a231b")
    gaugeIB = Contract("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F")
    registry = Contract("0xE15461B18EE31b7379019Dc523231C57d1Cbc18c")

    # accept governance as multisig from strategist ms
    vault.acceptGovernance({"from": multisig})

    # harvest and migrate our old strategy. this will set debt ratio to 0 on current strategy
    live_strategy.harvest({"from": multisig})
    vault.migrateStrategy(live_strategy, new_strategy, {"from": multisig})
    assert live_strategy.estimatedTotalAssets() == 0

    # Set our proxy address on old strategy to burn address to be safe, and transfer gov to daddy
    live_strategy.setProxy("0x0000000000000000000000000000000000000000", {"from": multisig})
    assert live_strategy.proxy() == "0x0000000000000000000000000000000000000000"

    # assert that our gauge is still empty
    old_gauge_balance = strategyProxy.balanceOf(gaugeIB)
    assert old_gauge_balance == 0
    total_old = vault.totalAssets()

    # assert that our new strategy is in the withdrawal queue and is the only one
    new_strategy_address = "0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7"
    current_strategy = vault.withdrawalQueue(0)
    assert current_strategy == new_strategy_address
    assert vault.withdrawalQueue(1) == "0x0000000000000000000000000000000000000000"

    # approve our new strategy on proxy and adjust debt ratio
    strategyProxy.approveStrategy(new_strategy.gauge(), new_strategy, {"from": multisig})
    vault.updateStrategyDebtRatio(new_strategy, 9800, {"from": multisig})
    assert new_strategy.estimatedTotalAssets() > 0

    # Update deposit limit to the vault to $10 million since it's currently maxed out
    vault.setDepositLimit(10000000000000000000000000, {"from": multisig})
    vault.setManagementFee(200, {"from": multisig})
    assert vault.managementFee() == 200
    registry.endorseVault("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7", {"from": multisig})

    # will still need to harvest myself manually once this is done

    safe_tx = multisend_from_receipts(multisig, history)
    estimate_safe_tx(safe_tx)
    broadcast_tx(safe_tx)
