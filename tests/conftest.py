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
def cvx():
    yield Contract("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")

@pytest.fixture
def cvxIBDeposit():
    yield Contract("0x912EC00eaEbf3820a9B0AC7a5E15F381A1C91f22")

@pytest.fixture
def dai():
    yield Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")

@pytest.fixture
def rewardsContract():
    yield Contract("0x3E03fFF82F77073cc590b656D42FceB12E4910A8")

@pytest.fixture
def voter():
    # this is yearn's veCRV voter, where we send all CRV to vote-lock
    yield Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

# Define any accounts in this section
@pytest.fixture
def gov(accounts):
    # yearn multis... I mean YFI governance. I swear!
    yield accounts.at("0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52", force=True)

@pytest.fixture
def dudesahn(accounts):
    yield accounts.at("0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09", force=True)

@pytest.fixture
def strategist_ms(accounts):
    # like governance, but better
    yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

@pytest.fixture
def new_address(accounts):
    # new account for voter and proxy tests
    yield accounts.at("0xb5DC07e23308ec663E743B1196F5a5569E4E0555", force=True)

@pytest.fixture
def keeper(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts[4]

@pytest.fixture
def strategist_ms(accounts):
    # like governance, but better
    yield accounts.at("0x16388463d60FFE0661Cf7F1f31a7D658aC790ff7", force=True)

@pytest.fixture
def whale(accounts):
    # Totally in it for the tech (largest EOA holder of ib-3crv, ~600k worth)
    whale = accounts.at('0xE594173Aaa1493665EC6A19a0D170C76EEa1124a', force=True)
    yield whale

@pytest.fixture
def convexWhale(accounts):
    # Totally in it for the tech (largest EOA holder of CVX, ~70k worth)
    convexWhale = accounts.at('0x48e91eA1b2ce7FE7F39b0f606412d63855bfD674', force=True)
    yield convexWhale

# this is the live strategy for ib3crv
@pytest.fixture
def curveVoterProxyStrategy():
    yield Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")

@pytest.fixture
def strategy(strategist, keeper, vault, StrategyConvexIronBank, gov, curveVoterProxyStrategy, guardian):
	# parameters for this are: strategy, vault, max deposit, minTimePerInvest, slippage protection (10000 = 100% slippage allowed), 
    strategy = guardian.deploy(StrategyConvexIronBank, vault)
    strategy.setKeeper(keeper, {"from": gov})
    # lower the debtRatio of genlender to make room for our new strategy
    vault.updateStrategyDebtRatio(curveVoterProxyStrategy, 9950, {"from": gov})
    vault.setManagementFee(0, {"from": gov})
    curveVoterProxyStrategy.harvest({"from": gov})
    vault.addStrategy(strategy, 50, 0, 2 ** 256 -1, 1000, {"from": gov})
    strategy.setStrategist('0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09', {"from": gov})
    strategy.harvest({"from": gov})
    yield strategy

@pytest.fixture
def vault(pm):
    Vault = pm(config["dependencies"][0]).Vault
    vault = Vault.at('0x27b7b1ad7288079A66d12350c828D3C00A6F07d7')
    yield vault
