from util import genericStateOfStrat, genericStateOfVault
from brownie import Wei

def test_migration(
    token,
    strategy,
    chain,
    vault,
    whale,
    gov,
    strategist,
    StrategyCurveIBVoterProxy
):
    debt_ratio = 10_000
    vault.addStrategy(strategy, debt_ratio, 0, 2 ** 256 -1, 1000, {"from": gov})

    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(Wei("100 ether"), {"from": whale})
    strategy.harvest({"from": strategist})

    genericStateOfStrat(strategy, token, vault)
    genericStateOfVault(vault, token)

    chain.sleep(2592000)
    chain.mine(1)

    print(
        "\nEstimated APR: ",
        "{:.2%}".format(((vault.totalAssets() - 100 * 1e18) * 12) / (100 * 1e18)),
    )

    strategy2 = strategist.deploy(StrategyCurveIBVoterProxy, vault)
    vault.migrateStrategy(strategy, strategy2, {"from": gov})
    genericStateOfStrat(strategy, token, vault)
    genericStateOfStrat(strategy2, token, vault)
    genericStateOfVault(vault, token)
