import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_revoke_strategy_from_vault(gov, token, vault, whale, chain, strategy, strat_setup):
    vaultAssets_starting = token.balanceOf(vault)
    vault.revokeStrategy(strategy.address, {"from": gov})
    strategy.harvest({"from": gov})
    assert token.balanceOf(vault) >= vaultAssets_starting
    vaultAssets_after_revoke = token.balanceOf(vault)

    # This final harvest will collect funds
    # Unfortunately, there is no way to account for this balance, since you can't check claimable CRV via smart contract.
    strategy.harvest({"from": gov})
    assert strategy.estimatedTotalAssets() == 0
    
    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # So instead of ==, we set this to >= since we know it will have some small amount gained
    assert token.balanceOf(vault) >= vaultAssets_after_revoke