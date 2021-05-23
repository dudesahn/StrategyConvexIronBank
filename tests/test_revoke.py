import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_revoke_strategy_from_vault(gov, token, vault, whale, chain, strategy, strat_setup):
    vaultAssets_starting = vault.totalAssets()
    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": gov})
    vaultAssets_after_revoke = vault.totalAssets()
    assert vaultAssets_after_revoke >= vaultAssets_starting
    assert strategy.estimatedTotalAssets() == 0
    
    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(86400)
    chain.mine(1)

    # So instead of ==, we set this to >= since we know it will have some small amount gained
    assert vault.totalAssets() >= vaultAssets_after_revoke