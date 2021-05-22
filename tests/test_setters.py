import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_setters(gov, token, vault, new_address, chain, strategy, rewardsContract):

    strategy.setTendsPerHarvest(5, {"from": gov})
    assert strategy.tendsPerHarvest() == 5

    strategy.setKeep3rHarvest(1, {"from": gov})
    assert strategy.manualKeep3rHarvest() != 0
    
    strategy.setKeepCRV(2000, {"from": gov})
    assert strategy.keepCRV() > 1000

    strategy.setCrvRouter(0, {"from": gov})
    assert strategy.crvRouter() == '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'  

    strategy.setCvxRouter(0, {"from": gov})
    assert strategy.cvxRouter() == '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D'
    
    strategy.setHarvestExtras(True, {"from": gov})
    assert strategy.harvestExtras() == True
    
    strategy.setClaimRewards(True, {"from": gov})
    assert strategy.claimRewards() == True

    strategy.setHarvestProfitFactor(4000, {"from": gov})
    assert strategy.harvestProfitFactor() == 4000

    strategy.setOptimal(1, {"from": gov})
    assert strategy.optimal() == 1