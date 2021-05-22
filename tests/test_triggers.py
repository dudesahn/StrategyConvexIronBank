import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_triggers(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract):
    # this is assuming tendCounter is set to 3
    ## deposit to the vault after approving
    strategy.setTendsPerHarvest(3, {"from": gov})
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    starting_assets = vault.totalAssets()

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # harvest should trigger false
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be False.", tx)
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # harvest should trigger true
    tx = strategy.harvestTrigger(0, {"from": gov})
    print("\nShould we harvest? Should be true.", tx)
    strategy.harvest({"from": gov})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend should trigger true,
    tx = strategy.tendTrigger(0, {"from": gov})
    print("\nShould we tend? Should be true", tx)
    print("\nShould be 0, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": gov})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend should trigger true,
    tx = strategy.tendTrigger(0, {"from": gov})
    print("\nShould we tend? Should be true", tx)
    print("\nShould be 1, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": gov})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend 
    tx = strategy.tendTrigger(0, {"from": gov})
    print("\nShould we tend? Should be true", tx)
    print("\nShould be 2, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": gov})
    print("\nShould be 3, tendCounter = ", strategy.tendCounter())
    tx = strategy.tendTrigger(0, {"from": gov})
    print("\nShould we tend? Should be false", tx)

    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 