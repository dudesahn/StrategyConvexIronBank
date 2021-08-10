import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_revoke_strategy_from_vault(gov, token, vault, whale, chain, strategy):
    vaultAssets_starting = vault.totalAssets()
    vault_holdings_starting = token.balanceOf(vault)
    strategy_starting = strategy.estimatedTotalAssets()
    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": gov})
    vaultAssets_after_revoke = vault.totalAssets()
    assert vaultAssets_after_revoke >= vaultAssets_starting
    assert strategy.estimatedTotalAssets() == 0
    assert token.balanceOf(vault) >= vault_holdings_starting + strategy_starting

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)

    # So instead of ==, we set this to >= since we know it will have some small amount gained
    assert vault.totalAssets() >= vaultAssets_after_revoke
