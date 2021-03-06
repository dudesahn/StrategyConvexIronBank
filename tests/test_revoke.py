def test_revoke_strategy_from_vault(token, vault, strategy, amount, gov, strategist, whale, gaugeIB, strategyProxy, voter):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount
    
    old_assets_dai = vault.totalAssets()
    old_proxy_balanceOf_gauge = strategyProxy.balanceOf(gaugeIB)
    old_gauge_balanceOf_voter = gaugeIB.balanceOf(voter)
    old_strategy_balance = token.balanceOf(strategy)
    old_estimated_total_assets = strategy.estimatedTotalAssets()
    old_vault_balance = token.balanceOf(vault)

    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": strategist})
    
#     new_assets_dai = vault.totalAssets()
#     new_proxy_balanceOf_gauge = strategyProxy.balanceOf(gauge)
#     new_gauge_balanceOf_voter = gauge.balanceOf(voter)
#     new_strategy_balance = token.balanceOf(strategy)
#     new_estimated_total_assets = strategy.estimatedTotalAssets()
#     new_vault_balance = token.balanceOf(vault)
#     
#     # Check for any assets only in the vault, not in the strategy
#     print("\nOld Vault Holdings: ", old_vault_balance)
#     print("\nNew Vault Holdings: ", new_vault_balance)  
#     
#     # Check total assets in the strategy
#     print("\nOld Strategy totalAssets: ", old_estimated_total_assets)
#     print("\nNew Strategy totalAssets: ", new_estimated_total_assets)  
#     
#     # Check total assets in the vault + strategy
#     print("\nOld Vault totalAssets: ", old_assets_dai)
#     print("\nNew Vault totalAssets: ", new_assets_dai)
#     
#     # Want token should never be in the strategy    
#     print("\nOld Strategy balanceOf: ", old_strategy_balance)
#     print("\nNew Strategy balanceOf: ", new_strategy_balance)
#     
#     # These two calls should return the same value, and should update after every harvest call
#     print("\nOld Proxy balanceOf gauge: ", old_proxy_balanceOf_gauge)
#     print("\nNew Proxy balanceOf gauge: ", new_proxy_balanceOf_gauge)
#     print("\nOld gauge balanceOf voter: ", old_gauge_balanceOf_voter)
#     print("\nNew gauge balanceOf voter: ", new_gauge_balanceOf_voter)
    
    
    assert token.balanceOf(vault) >= amount


def test_revoke_strategy_from_strategy(token, vault, strategy, amount, strategist, whale, gov):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": strategist})
    assert token.balanceOf(vault) == amount
    
    
