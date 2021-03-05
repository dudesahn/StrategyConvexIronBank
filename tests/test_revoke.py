def test_revoke_strategy_from_vault(token, vault, strategy, amount, gov):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": strategist})
    assert token.balanceOf(vault.address) == amount


def test_revoke_strategy_from_strategy(token, vault, strategy, amount, gov):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert token.balanceOf(vault.address) == amount