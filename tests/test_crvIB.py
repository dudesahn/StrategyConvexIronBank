from util import genericStateOfStrat, genericStateOfVault
from brownie import Wei


def test_ops(token, strategy, chain, vault, whale, gov, strategist):
    print("\n----test ops----")

    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 -1, 1000, {"from": gov})

    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    initial_deposit = 100 * 1e18
    whalebefore = token.balanceOf(whale)
    vault.deposit(initial_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    print("\n-----harvest-----")

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    print("\n-----sleep for a month-----")

    chain.sleep(2592000)
    chain.mine(1)

    strategy.harvest({"from": strategist})
    print("\n-----harvest-----")
    print("crvIB = ", token.balanceOf(strategy) / 1e18)

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - initial_deposit) * 12) / initial_deposit),
    )

    vault.withdraw({"from": whale})
    print("\n-----withdraw-----")
    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    print(f"\nWhale profit: ",  (token.balanceOf(whale) - whalebefore) / 1e18)


def test_revoke_from_vault(token, strategy, vault, whale, gov, strategist):
    print("\n----test revoke----")

    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 -1, 1000, {"from": gov})

    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    initial_deposit = 100 * 1e18
    vault.deposit(initial_deposit, {"from": whale})

    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    vault.revokeStrategy(strategy, {"from": gov})
    print("\n-----revoked-----")

    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)


# def test_revoke_strategy_from_strategy(token, strategy, vault, whale, gov, strategist):
#     # Deposit to the vault and harvest
#     debt_ratio = 10_000
#     vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 -1, 1000, {"from": gov})
# 
#     token.approve(vault, 2 ** 256 - 1, {"from": whale})
#     initial_deposit = 100 * 1e18
#     vault.deposit(initial_deposit, {"from": whale})
# 
#     strategy.harvest({"from": strategist})
#     assert token.balanceOf(strategy.address) == amount
# 
#     strategy.setEmergencyExit()
#     strategy.harvest() - good
#     assert token.balanceOf(vault.address) == amount


def test_reduce_limit(token, strategy, vault, whale, gov, strategist):
    print(f"\n----test reduce limit ")

    debt_ratio = 10_000
    print(f"\n-----ratio {debt_ratio}-----")

    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 -1, 1000, {"from": gov})
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    initial_deposit = 100 * 1e18
    vault.deposit(initial_deposit, {"from": whale})
    strategy.harvest({"from": strategist})

    # round off dust
    dec = token.decimals()
    assert token.balanceOf(vault) // 10 ** dec == 0

    debt_ratio = 5_000
    vault.updateStrategyDebtRatio(strategy, debt_ratio, {"from": gov})
    print(f"\n-----ratio {debt_ratio}-----")
    strategy.harvest({"from": strategist})

    assert token.balanceOf(vault) // 10 ** dec > 0
