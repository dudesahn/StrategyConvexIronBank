import brownie
from brownie import Contract
from brownie import config


def test_setters(gov, token, vault, new_address, chain, strategy):

    strategy.setKeepCRV(2000, {"from": gov})
    assert strategy.keepCRV() > 1000

    strategy.setCrvRouter(0, {"from": gov})
    assert strategy.crvRouter != 1

    strategy.setVoter(new_address, {"from": gov})
    assert strategy.voter() == new_address

    strategy.setTendsPerHarvest(5, {"from": gov})
    assert strategy.tendsPerHarvest() == 5
        
    strategy.setOptimal(1, {"from": gov})
    assert strategy.optimal() == 1
    
    strategy.setKeep3rHarvest(1, {"from": gov})
    assert strategy.manualKeep3rHarvest == 1
    
    strategy.setCvxRouter(0, {"from": gov})
    assert strategy.cvxRouter != 1
    
    strategy.setHarvestExtras(True, {"from": gov})
    assert strategy.harvestExtras == True
    
    strategy.setClaimRewards(True, {"from": gov})
    assert strategy.claimRewards == True
    
    strategy.setConvexMintRatio(5000, {"from": gov})
    assert strategy.tendsPerHarvest() == 5000

    strategy.setHarvestProfitFactor(4000, {"from": gov})
    assert strategy.tendsPerHarvest() == 4000
