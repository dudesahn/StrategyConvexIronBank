import pytest
from brownie import config, Wei, Contract

# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass

# Define relevant tokens and contracts in this section

@pytest.fixture
def token():
    # this should be the address of the ERC-20 used by the strategy/vault. In this case, Curve's Iron Bank Pool token
    token_address = "0x5282a4eF67D9C33135340fB3289cc1711c13638C"
    yield Contract(token_address)


@pytest.fixture
def crv():
    yield Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")


@pytest.fixture
def dai():
    yield Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")


@pytest.fixture
def voter():
    # this is yearn's veCRV voter, where all gauge tokens are held (for v2 curve gauges that are tokenized)
    yield Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")


@pytest.fixture
def gaugeIB():
    # this is the gauge contract for the Iron Bank Curve Pool, in Curve v2 these are tokenized.
    yield Contract("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F")


# Define any accounts in this section


@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)


@pytest.fixture
def dudesahn(accounts):
    yield accounts.at("0x677Ae1C4FDa1A986a23a055Bbd0A94f8e5b284De", force=True)

@pytest.fixture
def rewards(accounts):
    yield accounts[0]


@pytest.fixture
def guardian(accounts):
    yield accounts[1]


@pytest.fixture
def management(accounts):
    yield accounts[2]


@pytest.fixture
def strategist(accounts):
    yield accounts[3]


@pytest.fixture
def keeper(accounts):
    yield accounts[4]


@pytest.fixture
def rando(accounts):
    yield accounts[5]

@pytest.fixture
def strategist_ms(accounts):
    # like governance, but better
    yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)


@pytest.fixture
def reserve(accounts):
    # this is the gauge contract, holds >99% of pool tokens. use this to seed our whale, as well for calling functions above as gauge
    yield accounts.at("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F", force=True)


@pytest.fixture
def new_address(accounts):
    # new account for voter and proxy tests
    yield accounts.at("0xb5DC07e23308ec663E743B1196F5a5569E4E0555", force=True)


# Whale accounts


@pytest.fixture
def whale(accounts, token, reserve):
    # Totally in it for the tech
    # Has 10% of tokens (was in the ICO)
    a = accounts[6]
    bal = token.totalSupply() // 10
    token.transfer(a, bal, {"from": reserve})
    yield a


# Define the amount of tokens that our whale will be using

# @pytest.fixture
# def amount(token, whale):
#     # set the amount that our whale friend is going to throw around; pocket change, 5% of stack
#     amount = token.balanceOf(whale) * 0.05
#     yield amount

# Set definitions for vault and strategy


@pytest.fixture
def strategyProxy(interface):
    # This is Yearn's StrategyProxy contract, overlord of the Curve world
    yield interface.ICurveStrategyProxy("0x9a165622a744C20E3B2CB443AeD98110a33a231b")


@pytest.fixture
def old_vault(pm, gov, rewards, guardian, management, token):
    Vault = pm(config["dependencies"][0]).Vault
    old_vault = guardian.deploy(Vault)
    vault.initialize(token, gov, rewards, "", "", guardian)
    old_vault.setDepositLimit(2 ** 256 - 1, {"from": gov})
    old_vault.setManagement(management, {"from": gov})
    yield old_vault

@pytest.fixture
def vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0x27b7b1ad7288079A66d12350c828D3C00A6F07d7')
    yield vault


@pytest.fixture
def old_strategy(strategist, keeper, old_vault, StrategyCurveIBVoterProxy, gov, strategyProxy):
    old_strategy = strategist.deploy(StrategyCurveIBVoterProxy, old_vault)
    old_strategy.setKeeper(keeper)
    strategyProxy.approveStrategy(old_strategy.gauge(), old_strategy, {"from": gov})
    old_vault.addStrategy(old_strategy, 10000, 0, 2 ** 256 - 1, 1000, {"from": gov})
    yield old_strategy

@pytest.fixture
def strategy(StrategyCurveIBVoterProxy):
    strategy = StrategyCurveIBVoterProxy.at('0x5c0309fa022Bc1B73fE45A2D73EddeD58a820ff8')
    yield strategy


# @pytest.fixture
# def crv3():
#     yield Contract("0x6c3F90f043a72FA612cbac8115EE7e52BDe6E490")
#
# @pytest.fixture
# def usdc():
#     yield Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
#
# @pytest.fixture
# def weth():
#     yield Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
#
# @pytest.fixture
# def yveCrvContract(token):
#     yield Contract("0xc5bDdf9843308380375a611c18B50Fb9341f502A")
#
# @pytest.fixture
# def yveCrv(token):
#     yield token
#
# @pytest.fixture
# def whale_eth(accounts):
#     yield accounts.at("0x73BCEb1Cd57C711feaC4224D062b0F6ff338501e", force=True)
#
# @pytest.fixture
# def whale_3crv(accounts):
#     yield accounts.at("0x5c00977a2002a3C9925dFDfb6815765F578a804f", force=True)
#
# @pytest.fixture
# def sushiswap_crv(accounts):
#     yield accounts.at("0x5c00977a2002a3C9925dFDfb6815765F578a804f", force=True)
#
# @pytest.fixture
# def sushiswap(accounts):
#     yield Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
