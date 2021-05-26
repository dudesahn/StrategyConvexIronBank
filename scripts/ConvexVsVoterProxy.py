# run this in brownie console
# establish our prices for our various underlying tokens
sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
uniswapRouter = Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
eurs = Contract.from_explorer("0xdB25f211AB05b1c97D595516F45794528a807ad8")
weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
wbtc = Contract("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
link = Contract.from_explorer("0x514910771AF9Ca656af840dff83E8264EcF986CA")
crv = Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")
cvx = Contract("0x4e3FBD56CD56c3e72c1403e103b45Db9da5B9D2B")
oneCoin = 1e18
oneWbtc = 1e8
oneEurs = 1e2
wethPath = [weth, usdc]
wbtcPath = [wbtc, weth, usdc]
linkPath = [link, weth, usdc]
crvPath = [crv, weth, usdc]
cvxPath = [cvx, weth, usdc]
eursPath = [eurs, usdc]
stable = 1
eth = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1]/1e6
btc = (sushiswapRouter.getAmountsOut(oneWbtc, wbtcPath)[2])/1e6
link = sushiswapRouter.getAmountsOut(oneCoin, linkPath)[2]/1e6
eurs = uniswapRouter.getAmountsOut(oneEurs, eursPath)[1]/1e6
priceOfCrv = sushiswapRouter.getAmountsOut(oneCoin, crvPath)[2]/1e6
priceOfCvx = sushiswapRouter.getAmountsOut(oneCoin, cvxPath)[2]/1e6
prices = [stable, eth, btc, link, eurs]
booster = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")

## -----------------CHANGE THIS STUFF HERE!!!!!!!---------------- ##
# Fees and keepCrv. Adjust these as needed based on changes with either protocol. do 12% convexKeepCrv to account for 16% convex pulls out in fees
# however, they only do 5% keepCrv
keepCrv = 0.1
convexFee = 0.16
convexKeepCrv = 0.12

# ib, most recent check: send to convex 106,954,685.88 IB pool tokens, target debtRatios of 6560 (convex) and 3423
# at 0.15 keepCRV,
# lpToken = Contract.from_explorer("0x5282a4eF67D9C33135340fB3289cc1711c13638C")
# poolId = 29
# strategy = Contract("0x864F408B422B7d33416AC678b1a1A7E6fbcF5C8c")
# # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
# underlyingPrice = prices[0]

# sETH, most recent check: send to convex 21,404.45 ETH pool tokens, target debtRatios of 5432 (convex) and 4545
# lpToken = Contract.from_explorer("0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c")
# poolId = 23
# strategy = Contract("0xc2fC89E79D4Fd2570dD9B413b851F38076bCd930")
# # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
# underlyingPrice = prices[1]

# stETH, most recent send to convex 82,435.63 ETH pool tokens. target debtRatios of 6735 (convex) and 3249
# lpToken = Contract.from_explorer("0x06325440D014e39736583c165C2963BA99fAf14E")
# poolId = 25
# strategy = Contract("0x6C0496fC55Eb4089f1Cf91A4344a2D56fAcE51e3")
# # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
# underlyingPrice = prices[1]

## -----------------CHANGE THIS STUFF HERE!!!!!!!---------------- ##
# constants, curve addresses
MaxBoost = 2.5
InverseMaxBoost = (1 / MaxBoost)
SecondsInYear = 31536000
FeeDenominator = 1e4
EthConstant = 1e18
registry = Contract("0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c")
vecrv = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")

# convex
# holds their gauge tokens, also where they keep their veCRV
convex_voter = Contract("0x989AEb4d175e16225E39E87d0D97A3360524AD80")
gaugeController = Contract.from_explorer("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")

# yearn
# holds our gauge tokens, also where we keep our veCRV
yearn_voter = Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

# these will change based on what our curve pool is
poolAddress = registry.get_pool_from_lp_token(lpToken)
gauges = registry.get_gauges(poolAddress)
gaugeAddress = gauges[0][0]
gauge = Contract.from_explorer(gaugeAddress)
gaugeWorkingSupply = gauge.working_supply()
gaugeRelativeWeight = gaugeController.gauge_relative_weight(gaugeAddress)
gaugeInflationRate = gauge.inflation_rate()
poolVirtualPrice = registry.get_virtual_price_from_lp_token(lpToken)

# yearn-specific metrics
yearnWorkingBalance = gauge.working_balances(yearn_voter)
yearnGaugeBalance = gauge.balanceOf(yearn_voter)

# convex-specific metrics
convexWorkingBalance = gauge.working_balances(convex_voter)
convexGaugeBalance = gauge.balanceOf(convex_voter)

# This is the base Apr for the pool
baseApr = (gaugeInflationRate) * (gaugeRelativeWeight) * (SecondsInYear/(gaugeWorkingSupply)) * (InverseMaxBoost/(poolVirtualPrice)) * (priceOfCrv) / (underlyingPrice)

# calculate our boosted values
# yearn. if this divides by 0, then we don't have anything in that gauge and this will error.
currentYearnBoost = yearnWorkingBalance / ( InverseMaxBoost * yearnGaugeBalance ) * (yearnGaugeBalance / yearnGaugeBalance)

# convex. if this divides by 0, then we don't have anything in that gauge and this will error.
# Convex doesn't take fees out of reward tokens, so we can ignore these in our comparison, same for base pool APY
currentConvexBoost = convexWorkingBalance / (InverseMaxBoost * convexGaugeBalance) * (convexGaugeBalance/convexGaugeBalance)

# this is how convex calculates how much CVX they mint per CRV farmed in their CVX contract
# convex minted per CRV
totalCliffs = 1000
maxSupply = 100 * 1000000 * 1e18
reductionPerCliff = 100000000000000000000000
supply = cvx.totalSupply()
cliff = supply/(reductionPerCliff)

# pretend we are claiming 1 CRV
claimableCrv = 1

# as long as we're still below the cliff, we're minting
reduction = totalCliffs - (cliff)
cvxMintedPerCrv = claimableCrv * (reduction) / (totalCliffs)

# convert our CVX to CRV units
converted_cvx = priceOfCvx / priceOfCrv
cvx_printed_as_crv = cvxMintedPerCrv * converted_cvx

# Calculate our final yield on Convex
periods = 365
# first remove Convex's fees, then apply this APR to both our CRV amount (1 - convexKeepCrv) and our cvx displayed as CRV balance
finalConvexApr = (((1 - convexFee) * currentConvexBoost * baseApr) * ((1 - convexKeepCrv) + cvx_printed_as_crv))
finalConvexApy = ((1+ (finalConvexApr / periods)) ** periods) - 1

# calculate our final yield on Yearn
finalYearnApr =  currentYearnBoost * baseApr * (1 - keepCrv)
finalYearnApy = ((1+ (finalYearnApr / periods)) ** periods) - 1

# ratio of Yearn's veCRV to Convex's
veCRV_ratio = vecrv.balanceOf(convex_voter)/vecrv.balanceOf(yearn_voter)
veCRV_ratio_for_printing = veCRV_ratio
price_fee_cvx_printing_ratio = ((1 - convexFee)* (1 - convexKeepCrv) + cvx_printed_as_crv) / (1 - keepCrv)

# Ratio target based on extra CVX yield. Consider veCRV ratio, CVX extra yield, and 16% fees on Convex.
targetRatio = veCRV_ratio * price_fee_cvx_printing_ratio
targetRatio_for_printing = targetRatio

# amount needed to transfer from yearn to Convex. If positive, send funds to convex, if negative, send that much back to yearn.
sendToConvex = (( targetRatio_for_printing / (1 + targetRatio_for_printing ) )* (yearnGaugeBalance + convexGaugeBalance)/1e18 - convexGaugeBalance/1e18)

# target debt ratios for each strategy, assuming 99.5% deployed
targetRewards = booster.poolInfo(poolId)[3]
rewards = Contract(targetRewards)
depositedInConvex = rewards.balanceOf(strategy)

convexDebtRatio = (depositedInConvex + sendToConvex*1e18) / (yearnGaugeBalance + depositedInConvex) * 9950
curveDebtRatio = (1 - convexDebtRatio/10000) * 9950

# APY at optimal allocation
# calculate this later

print("Final Yearn CRV APY:", "{:.2%}".format(finalYearnApy), "\nFinal Convex CRV+CVX APY:", "{:.2%}".format(finalConvexApy), "\nRatio of Yearn to Convex veCRV, 1 :", "{:.2}".format(veCRV_ratio_for_printing), "\nTarget Ratio of Yearn to Convex funds, 1 :", "{:.2}".format(targetRatio_for_printing), "\nSend this much want to Convex:", "{:,.2f}".format(sendToConvex), "\nTarget Convex debtRatio: ", "{:.0f}".format(convexDebtRatio), "\nTarget Curve debtRatio: ", "{:.0f}".format(curveDebtRatio))
quit()
