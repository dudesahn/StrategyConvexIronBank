import brownie
from helpers import showBalances
from brownie import Contract

# **** TEST ALL CONTRACT FUNCTIONS 


def test_operation(accounts, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": accounts[0]})
    vault.deposit(amount, {"from": accounts[0]})
    assert token.balanceOf(vault.address) == amount

	# set optimal to decide which token to deposit into Curve pool for each harvest (DAI first)
	strategy.setOptimal(0)

    # harvest
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

	# set optimal to USDC
	strategy.setOptimal(1)

    # harvest
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

	# set optimal to USDT
	strategy.setOptimal(2)

    # harvest
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # tend()
    strategy.tend()

    # withdrawal
    vault.withdraw({"from": accounts[0]})
    assert token.balanceOf(accounts[0]) != 0
    
    
def test_emergency_exit(accounts, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": accounts[0]})
    vault.deposit(amount, {"from": accounts[0]})
	strategy.setOptimal(0)
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest()
    assert token.balanceOf(strategy.address) < amount
    

# def test_profitable_harvest(gov, vault, strategy, token, amount, chain):
#     # Deposit to the vault and harvest
#     # print(yveCrv.strategies(strategy)) # Strategy params (perf fee, activation, debtraatio, mindebtperharvest, maxdebtperharvest, lastreport, totaldebt)
#     token.approve(vault.address, amount, {"from": gov})
#     vault.deposit(amount, {"from": gov})
#     assert token.balanceOf(vault.address) == amount
#     
#     #showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
# 
# 	strategy.setOptimal(0)
#     strategy.harvest()
#     assert token.balanceOf(strategy.address) == amount
# 
#     #showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
#     
#     # Simulate a claim by sending some 3Crv to the strategy before harvest
#     crv3.transfer(strategy, 10e21, {"from":whale_3crv})
#     strategy.harvest()
#     print("\n\n~~After Harvest #2~~")
#     showBalances(token, vault, strategy, yveCrv, weth, usdc, crv3)
#     assert token.balanceOf(strategy.address) > amount
    
    
    
def test_change_debt(gov, token, vault, strategy, strategist, amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
	strategy.setOptimal(0)
    strategy.harvest()

    assert token.balanceOf(strategy.address) == amount / 2

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest()
    assert token.balanceOf(strategy.address) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    # vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    # assert token.balanceOf(strategy.address) == amount / 2


def test_sweep(gov, vault, strategy, token, amount, weth, weth_amount):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": gov})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})


def test_triggers(gov, vault, strategy, token, amount, weth, weth_amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
	strategy.setOptimal(0)
    strategy.harvest()
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)