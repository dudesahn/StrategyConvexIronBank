import pytest
from brownie import config, Contract


@pytest.fixture
def curve_proxy(interface):
    yield interface.ICurveStrategyProxy("0x9a165622a744C20E3B2CB443AeD98110a33a231b")


@pytest.fixture
def strategy(strategist, keeper, vault, StrategyCurveIBVoterProxy, curve_proxy, gov_live):
    strategy = strategist.deploy(StrategyCurveIBVoterProxy, vault)
    strategy.setKeeper(keeper)
    curve_proxy.approveStrategy(strategy.crvIBgauge(), strategy, {"from": gov_live})
    yield strategy


@pytest.fixture
def vault(pm, gov, rewards, guardian, token):
    Vault = pm(config["dependencies"][0]).Vault
    vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    yield vault


@pytest.fixture
def token(gov):
    # crvIB token
    yield Contract("0x5282a4eF67D9C33135340fB3289cc1711c13638C", owner=gov)


@pytest.fixture
def dai(gov):
    # dai
    yield Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F", owner=gov)

@pytest.fixture
def crv(gov):
    # crv token
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52", owner=gov)

@pytest.fixture
def andre(accounts, token):
    # Andre, giver of tokens, and maker of yield
    crvIB_gauge = accounts.at("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F", force=True)
    gauge_balance = token.balanceOf(crvIB_gauge)
    andre_accnt = accounts[0]
    token.transfer(andre_accnt, gauge_balance // 3, {"from": crvIB_gauge})
    yield andre_accnt


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts[1]


@pytest.fixture
def gov_live(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def rewards(gov):
    yield gov  # TODO: Add rewards contract


@pytest.fixture
def guardian(accounts):
    # YFI Whale, probably
    yield accounts[2]


@pytest.fixture
def strategist(accounts):
    # You! Our new Strategist!
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    # This is our trusty bot!
    yield accounts[4]


@pytest.fixture
def whale(accounts, andre, token, vault):
    # Totally in it for the tech
    a = accounts[9]
    # Has 10% of tokens (was in the ICO)
    bal = token.totalSupply() // 10
    token.transfer(a, bal, {"from": andre})
    yield a
