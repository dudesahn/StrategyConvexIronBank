from brownie import Contract, accounts, web3, chain


def iron_bank():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    uniswapRouter = Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    eurs = Contract("0xdB25f211AB05b1c97D595516F45794528a807ad8")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    wbtc = Contract("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
    link = Contract("0x514910771AF9Ca656af840dff83E8264EcF986CA")
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
    eth = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6
    btc = (sushiswapRouter.getAmountsOut(oneWbtc, wbtcPath)[2]) / 1e6
    link = sushiswapRouter.getAmountsOut(oneCoin, linkPath)[2] / 1e6
    eurs = uniswapRouter.getAmountsOut(oneEurs, eursPath)[1] / 1e6
    priceOfCrv = sushiswapRouter.getAmountsOut(oneCoin, crvPath)[2] / 1e6
    priceOfCvx = sushiswapRouter.getAmountsOut(oneCoin, cvxPath)[2] / 1e6
    prices = [stable, eth, btc, link, eurs, priceOfCrv, priceOfCvx]
    booster = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    lockIncentive = booster.lockIncentive()
    stakerIncentive = booster.stakerIncentive()
    earmarkIncentive = booster.earmarkIncentive()
    convexFee = (lockIncentive + stakerIncentive + earmarkIncentive) / 10000

    ## -----------------CHANGE THIS STUFF BELOW HERE!!!!!!!---------------- ##
    # Iron Bank Pool
    poolId = 29
    # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
    underlyingPrice = prices[0]

    ## -----------------CHANGE THIS STUFF ABOVE HERE!!!!!!!---------------- ##
    ## -------------------------------------------------------------- ##
    # constants, curve addresses
    MaxBoost = 2.5
    InverseMaxBoost = 1 / MaxBoost
    SecondsInYear = 31536000
    FeeDenominator = 1e4
    EthConstant = 1e18
    registry = Contract("0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c")
    vecrv = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")

    # convex
    # holds their gauge tokens, also where they keep their veCRV
    convex_voter = Contract("0x989AEb4d175e16225E39E87d0D97A3360524AD80")
    gaugeController = Contract("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")

    # use the pool ID to pull the LP token from the booster contract
    _lpToken = booster.poolInfo(poolId)[0]
    lpToken = Contract(_lpToken)

    # use LP token to pull vault from Yearn's registry
    yearn_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")
    _vault = yearn_registry.latestVault(lpToken)
    vault = Contract(_vault)

    # yearn
    # holds our gauge tokens, also where we keep our veCRV
    yearn_voter = Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

    # these will change based on what our curve pool is
    _poolAddress = registry.get_pool_from_lp_token(lpToken)
    poolAddress = Contract(_poolAddress)
    gauges = registry.get_gauges(poolAddress)
    gaugeAddress = gauges[0][0]
    gauge = Contract(gaugeAddress)
    gaugeWorkingSupply = gauge.working_supply()
    gaugeRelativeWeight = gaugeController.gauge_relative_weight(gaugeAddress)
    gaugeInflationRate = gauge.inflation_rate()
    poolVirtualPrice = poolAddress.get_virtual_price()

    # calculate debtRatios for strategies, as we use this to determine overall vault APY
    _curveStrategy = vault.withdrawalQueue(0)
    _convexStrategy = vault.withdrawalQueue(1)
    curveStrategy = Contract(_curveStrategy)
    convexStrategy = Contract(_convexStrategy)
    curveDebtRatio = vault.strategies(_curveStrategy)[2]
    convexDebtRatio = vault.strategies(_convexStrategy)[2]

    # pull keepCRV data based on the vault
    keepCrv = curveStrategy.keepCRV() / 1e4
    convexKeepCrv = convexStrategy.keepCRV() / 1e4

    # yearn-specific metrics
    yearnWorkingBalance = gauge.working_balances(yearn_voter)
    yearnGaugeBalance = gauge.balanceOf(yearn_voter)

    # convex-specific metrics
    convexWorkingBalance = gauge.working_balances(convex_voter)
    convexGaugeBalance = gauge.balanceOf(convex_voter)

    # This is the base Apr for the pool
    baseApr = (
        (gaugeInflationRate)
        * (gaugeRelativeWeight)
        * (SecondsInYear / (gaugeWorkingSupply))
        * (InverseMaxBoost / (poolVirtualPrice))
        * (priceOfCrv)
        / (underlyingPrice)
    )

    ## -------------------------------------------------------------- ##
    # calculate our boosted values
    # yearn. if this divides by 0, then we don't have anything in that gauge and this will error.
    currentYearnBoost = yearnWorkingBalance / (InverseMaxBoost * yearnGaugeBalance) * (yearnGaugeBalance / yearnGaugeBalance)

    # convex. if this divides by 0, then we don't have anything in that gauge and this will error.
    # Convex doesn't take fees out of reward tokens, so we can ignore these in our comparison, same for base pool APY
    currentConvexBoost = convexWorkingBalance / (InverseMaxBoost * convexGaugeBalance) * (convexGaugeBalance / convexGaugeBalance)

    ## -------------------------------------------------------------- ##
    # this is how convex calculates how much CVX they mint per CRV farmed in their CVX contract
    # convex minted per CRV
    totalCliffs = 1000
    maxSupply = 100 * 1000000 * 1e18
    reductionPerCliff = 100000000000000000000000
    supply = cvx.totalSupply()
    cliff = supply / (reductionPerCliff)

    # pretend we are claiming 1 CRV
    claimableCrv = 1

    # as long as we're still below the cliff, we're minting
    reduction = totalCliffs - (cliff)
    cvxMintedPerCrv = claimableCrv * (reduction) / (totalCliffs)

    # convert our CVX to CRV units
    converted_cvx = prices[6] / prices[5]
    cvx_printed_as_crv = cvxMintedPerCrv * converted_cvx
    ## -------------------------------------------------------------- ##
    # Calculate our convex and curve raw variable APRs (without base or rewards APR, as those are the same between protocols)
    cvx_variable_apr = ((1 - convexFee) * currentConvexBoost * baseApr) * (1 + cvx_printed_as_crv)
    cvx_variable_apr_minus_keep_crv = ((1 - convexFee) * currentConvexBoost * baseApr) * ((1 - convexKeepCrv) + cvx_printed_as_crv)

    crv_variable_apr = baseApr * currentYearnBoost
    crv_variable_apr_minus_keep_crv = baseApr * currentYearnBoost * (1 - keepCrv)

    # ratio of Yearn's veCRV to Convex's
    veCRV_ratio = vecrv.balanceOf(convex_voter) / vecrv.balanceOf(yearn_voter)
    veCRV_ratio_for_printing = veCRV_ratio
    price_fee_cvx_printing_ratio = ((1 - convexFee) * (1 - convexKeepCrv) + cvx_printed_as_crv) / (1 - keepCrv)

    # Ratio target based on extra CVX yield. Consider veCRV ratio, CVX extra yield, and 16% fees on Convex.
    targetRatio = veCRV_ratio * price_fee_cvx_printing_ratio
    targetRatio_for_printing = targetRatio

    # amount needed to transfer from yearn to Convex. If positive, send funds to convex, if negative, send that much back to yearn.
    sendToConvex = (targetRatio_for_printing / (1 + targetRatio_for_printing)) * (
        yearnGaugeBalance + convexGaugeBalance
    ) / 1e18 - convexGaugeBalance / 1e18

    # target debt ratios for each strategy, assuming 100% deployed
    targetRewards = booster.poolInfo(poolId)[3]
    rewards = Contract(targetRewards)
    depositedInConvex = rewards.balanceOf(convexStrategy)

    convexTargetDebtRatio = (depositedInConvex + sendToConvex * 1e18) / (yearnGaugeBalance + depositedInConvex) * 10000
    curveTargetDebtRatio = (1 - convexTargetDebtRatio / 10000) * 10000
    tokenName = lpToken.name()

    # , "\n\nSend this much want to Convex:", "{:,.2f}".format(sendToConvex), "\nTarget Convex debtRatio: ", "{:.0f}".format(convexTargetDebtRatio), "\nTarget Curve debtRatio: ", "{:.0f}".format(curveTargetDebtRatio))

    print(
        "\n\nVault Token: ",
        tokenName,
        "\nCurve Future APR :",
        "{:.2%}".format(crv_variable_apr_minus_keep_crv),
        "\nConvex Future APR :",
        "{:.2%}".format(cvx_variable_apr_minus_keep_crv),
        "\n\n",
    )


def sETH():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    uniswapRouter = Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    eurs = Contract("0xdB25f211AB05b1c97D595516F45794528a807ad8")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    wbtc = Contract("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
    link = Contract("0x514910771AF9Ca656af840dff83E8264EcF986CA")
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
    eth = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6
    btc = (sushiswapRouter.getAmountsOut(oneWbtc, wbtcPath)[2]) / 1e6
    link = sushiswapRouter.getAmountsOut(oneCoin, linkPath)[2] / 1e6
    eurs = uniswapRouter.getAmountsOut(oneEurs, eursPath)[1] / 1e6
    priceOfCrv = sushiswapRouter.getAmountsOut(oneCoin, crvPath)[2] / 1e6
    priceOfCvx = sushiswapRouter.getAmountsOut(oneCoin, cvxPath)[2] / 1e6
    prices = [stable, eth, btc, link, eurs, priceOfCrv, priceOfCvx]
    booster = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    lockIncentive = booster.lockIncentive()
    stakerIncentive = booster.stakerIncentive()
    earmarkIncentive = booster.earmarkIncentive()
    convexFee = (lockIncentive + stakerIncentive + earmarkIncentive) / 10000

    ## -----------------CHANGE THIS STUFF BELOW HERE!!!!!!!---------------- ##
    # sETH Pool
    poolId = 23
    # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
    underlyingPrice = prices[1]

    ## -----------------CHANGE THIS STUFF ABOVE HERE!!!!!!!---------------- ##
    ## -------------------------------------------------------------- ##
    # constants, curve addresses
    MaxBoost = 2.5
    InverseMaxBoost = 1 / MaxBoost
    SecondsInYear = 31536000
    FeeDenominator = 1e4
    EthConstant = 1e18
    registry = Contract("0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c")
    vecrv = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")

    # convex
    # holds their gauge tokens, also where they keep their veCRV
    convex_voter = Contract("0x989AEb4d175e16225E39E87d0D97A3360524AD80")
    gaugeController = Contract("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")

    # use the pool ID to pull the LP token from the booster contract
    _lpToken = booster.poolInfo(poolId)[0]
    lpToken = Contract(_lpToken)

    # use LP token to pull vault from Yearn's registry
    yearn_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")
    _vault = yearn_registry.latestVault(lpToken)
    vault = Contract(_vault)

    # yearn
    # holds our gauge tokens, also where we keep our veCRV
    yearn_voter = Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

    # these will change based on what our curve pool is
    _poolAddress = registry.get_pool_from_lp_token(lpToken)
    poolAddress = Contract(_poolAddress)
    gauges = registry.get_gauges(poolAddress)
    gaugeAddress = gauges[0][0]
    gauge = Contract(gaugeAddress)
    gaugeWorkingSupply = gauge.working_supply()
    gaugeRelativeWeight = gaugeController.gauge_relative_weight(gaugeAddress)
    gaugeInflationRate = gauge.inflation_rate()
    poolVirtualPrice = poolAddress.get_virtual_price()

    # calculate debtRatios for strategies, as we use this to determine overall vault APY
    _curveStrategy = vault.withdrawalQueue(0)
    _convexStrategy = vault.withdrawalQueue(1)
    curveStrategy = Contract(_curveStrategy)
    convexStrategy = Contract(_convexStrategy)
    curveDebtRatio = vault.strategies(_curveStrategy)[2]
    convexDebtRatio = vault.strategies(_convexStrategy)[2]

    # pull keepCRV data based on the vault
    keepCrv = curveStrategy.keepCRV() / 1e4
    convexKeepCrv = convexStrategy.keepCRV() / 1e4

    # yearn-specific metrics
    yearnWorkingBalance = gauge.working_balances(yearn_voter)
    yearnGaugeBalance = gauge.balanceOf(yearn_voter)

    # convex-specific metrics
    convexWorkingBalance = gauge.working_balances(convex_voter)
    convexGaugeBalance = gauge.balanceOf(convex_voter)

    # This is the base Apr for the pool
    baseApr = (
        (gaugeInflationRate)
        * (gaugeRelativeWeight)
        * (SecondsInYear / (gaugeWorkingSupply))
        * (InverseMaxBoost / (poolVirtualPrice))
        * (priceOfCrv)
        / (underlyingPrice)
    )

    ## -------------------------------------------------------------- ##
    # calculate our boosted values
    # yearn. if this divides by 0, then we don't have anything in that gauge and this will error.
    currentYearnBoost = yearnWorkingBalance / (InverseMaxBoost * yearnGaugeBalance) * (yearnGaugeBalance / yearnGaugeBalance)

    # convex. if this divides by 0, then we don't have anything in that gauge and this will error.
    # Convex doesn't take fees out of reward tokens, so we can ignore these in our comparison, same for base pool APY
    currentConvexBoost = convexWorkingBalance / (InverseMaxBoost * convexGaugeBalance) * (convexGaugeBalance / convexGaugeBalance)

    ## -------------------------------------------------------------- ##
    # this is how convex calculates how much CVX they mint per CRV farmed in their CVX contract
    # convex minted per CRV
    totalCliffs = 1000
    maxSupply = 100 * 1000000 * 1e18
    reductionPerCliff = 100000000000000000000000
    supply = cvx.totalSupply()
    cliff = supply / (reductionPerCliff)

    # pretend we are claiming 1 CRV
    claimableCrv = 1

    # as long as we're still below the cliff, we're minting
    reduction = totalCliffs - (cliff)
    cvxMintedPerCrv = claimableCrv * (reduction) / (totalCliffs)

    # convert our CVX to CRV units
    converted_cvx = prices[6] / prices[5]
    cvx_printed_as_crv = cvxMintedPerCrv * converted_cvx
    ## -------------------------------------------------------------- ##
    # Calculate our convex and curve raw variable APRs (without base or rewards APR, as those are the same between protocols)
    cvx_variable_apr = ((1 - convexFee) * currentConvexBoost * baseApr) * (1 + cvx_printed_as_crv)
    cvx_variable_apr_minus_keep_crv = ((1 - convexFee) * currentConvexBoost * baseApr) * ((1 - convexKeepCrv) + cvx_printed_as_crv)

    crv_variable_apr = baseApr * currentYearnBoost
    crv_variable_apr_minus_keep_crv = baseApr * currentYearnBoost * (1 - keepCrv)

    # ratio of Yearn's veCRV to Convex's
    veCRV_ratio = vecrv.balanceOf(convex_voter) / vecrv.balanceOf(yearn_voter)
    veCRV_ratio_for_printing = veCRV_ratio
    price_fee_cvx_printing_ratio = ((1 - convexFee) * (1 - convexKeepCrv) + cvx_printed_as_crv) / (1 - keepCrv)

    # Ratio target based on extra CVX yield. Consider veCRV ratio, CVX extra yield, and 16% fees on Convex.
    targetRatio = veCRV_ratio * price_fee_cvx_printing_ratio
    targetRatio_for_printing = targetRatio

    # amount needed to transfer from yearn to Convex. If positive, send funds to convex, if negative, send that much back to yearn.
    sendToConvex = (targetRatio_for_printing / (1 + targetRatio_for_printing)) * (
        yearnGaugeBalance + convexGaugeBalance
    ) / 1e18 - convexGaugeBalance / 1e18

    # target debt ratios for each strategy, assuming 100% deployed
    targetRewards = booster.poolInfo(poolId)[3]
    rewards = Contract(targetRewards)
    depositedInConvex = rewards.balanceOf(convexStrategy)

    convexTargetDebtRatio = (depositedInConvex + sendToConvex * 1e18) / (yearnGaugeBalance + depositedInConvex) * 10000
    curveTargetDebtRatio = (1 - convexTargetDebtRatio / 10000) * 10000
    tokenName = lpToken.name()

    # , "\n\nSend this much want to Convex:", "{:,.2f}".format(sendToConvex), "\nTarget Convex debtRatio: ", "{:.0f}".format(convexTargetDebtRatio), "\nTarget Curve debtRatio: ", "{:.0f}".format(curveTargetDebtRatio))

    print(
        "\n\nVault Token: ",
        tokenName,
        "\nCurve Future APR :",
        "{:.2%}".format(crv_variable_apr_minus_keep_crv),
        "\nConvex Future APR :",
        "{:.2%}".format(cvx_variable_apr_minus_keep_crv),
        "\n\n",
    )


def stETH():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    uniswapRouter = Contract("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
    eurs = Contract("0xdB25f211AB05b1c97D595516F45794528a807ad8")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    wbtc = Contract("0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599")
    link = Contract("0x514910771AF9Ca656af840dff83E8264EcF986CA")
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
    eth = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6
    btc = (sushiswapRouter.getAmountsOut(oneWbtc, wbtcPath)[2]) / 1e6
    link = sushiswapRouter.getAmountsOut(oneCoin, linkPath)[2] / 1e6
    eurs = uniswapRouter.getAmountsOut(oneEurs, eursPath)[1] / 1e6
    priceOfCrv = sushiswapRouter.getAmountsOut(oneCoin, crvPath)[2] / 1e6
    priceOfCvx = sushiswapRouter.getAmountsOut(oneCoin, cvxPath)[2] / 1e6
    prices = [stable, eth, btc, link, eurs, priceOfCrv, priceOfCvx]
    booster = Contract("0xF403C135812408BFbE8713b5A23a04b3D48AAE31")
    lockIncentive = booster.lockIncentive()
    stakerIncentive = booster.stakerIncentive()
    earmarkIncentive = booster.earmarkIncentive()
    convexFee = (lockIncentive + stakerIncentive + earmarkIncentive) / 10000

    ## -----------------CHANGE THIS STUFF BELOW HERE!!!!!!!---------------- ##
    # stETH Pool
    poolId = 25
    # set this to 0 for stables, 1 for ETH, 2 for WBTC, 3 for LINK, 4 for EURS
    underlyingPrice = prices[1]
    hasRewards = True

    ## -----------------CHANGE THIS STUFF ABOVE HERE!!!!!!!---------------- ##
    ## -------------------------------------------------------------- ##
    # constants, curve addresses
    MaxBoost = 2.5
    InverseMaxBoost = 1 / MaxBoost
    SecondsInYear = 31536000
    FeeDenominator = 1e4
    EthConstant = 1e18
    registry = Contract("0x7D86446dDb609eD0F5f8684AcF30380a356b2B4c")
    vecrv = Contract("0x5f3b5DfEb7B28CDbD7FAba78963EE202a494e2A2")

    # convex
    # holds their gauge tokens, also where they keep their veCRV
    convex_voter = Contract("0x989AEb4d175e16225E39E87d0D97A3360524AD80")
    gaugeController = Contract("0x2F50D538606Fa9EDD2B11E2446BEb18C9D5846bB")

    # use the pool ID to pull the LP token from the booster contract
    _lpToken = booster.poolInfo(poolId)[0]
    lpToken = Contract(_lpToken)

    # use LP token to pull vault from Yearn's registry
    yearn_registry = Contract("0x50c1a2eA0a861A967D9d0FFE2AE4012c2E053804")
    _vault = yearn_registry.latestVault(lpToken)
    vault = Contract(_vault)

    # yearn
    # holds our gauge tokens, also where we keep our veCRV
    yearn_voter = Contract("0xF147b8125d2ef93FB6965Db97D6746952a133934")

    # these will change based on what our curve pool is
    _poolAddress = registry.get_pool_from_lp_token(lpToken)
    poolAddress = Contract(_poolAddress)
    gauges = registry.get_gauges(poolAddress)
    gaugeAddress = gauges[0][0]
    gauge = Contract(gaugeAddress)
    gaugeWorkingSupply = gauge.working_supply()
    gaugeRelativeWeight = gaugeController.gauge_relative_weight(gaugeAddress)
    gaugeInflationRate = gauge.inflation_rate()
    poolVirtualPrice = poolAddress.get_virtual_price()

    # calculate debtRatios for strategies, as we use this to determine overall vault APY
    _curveStrategy = vault.withdrawalQueue(0)
    _convexStrategy = vault.withdrawalQueue(1)
    curveStrategy = Contract(_curveStrategy)
    convexStrategy = Contract(_convexStrategy)
    curveDebtRatio = vault.strategies(_curveStrategy)[2]
    convexDebtRatio = vault.strategies(_convexStrategy)[2]

    # pull keepCRV data based on the vault
    keepCrv = curveStrategy.keepCrvPercent() / 1e4
    convexKeepCrv = convexStrategy.keepCRV() / 1e4

    # yearn-specific metrics
    yearnWorkingBalance = gauge.working_balances(yearn_voter)
    yearnGaugeBalance = gauge.balanceOf(yearn_voter)

    # convex-specific metrics
    convexWorkingBalance = gauge.working_balances(convex_voter)
    convexGaugeBalance = gauge.balanceOf(convex_voter)

    # This is the base Apr for the pool
    baseApr = (
        (gaugeInflationRate)
        * (gaugeRelativeWeight)
        * (SecondsInYear / (gaugeWorkingSupply))
        * (InverseMaxBoost / (poolVirtualPrice))
        * (priceOfCrv)
        / (underlyingPrice)
    )

    ## -------------------------------------------------------------- ##
    # calculate our boosted values
    # yearn. if this divides by 0, then we don't have anything in that gauge and this will error.
    currentYearnBoost = yearnWorkingBalance / (InverseMaxBoost * yearnGaugeBalance) * (yearnGaugeBalance / yearnGaugeBalance)

    # convex. if this divides by 0, then we don't have anything in that gauge and this will error.
    # Convex doesn't take fees out of reward tokens, so we can ignore these in our comparison, same for base pool APY
    currentConvexBoost = convexWorkingBalance / (InverseMaxBoost * convexGaugeBalance) * (convexGaugeBalance / convexGaugeBalance)

    ## -------------------------------------------------------------- ##
    # this is how convex calculates how much CVX they mint per CRV farmed in their CVX contract
    # convex minted per CRV
    totalCliffs = 1000
    maxSupply = 100 * 1000000 * 1e18
    reductionPerCliff = 100000000000000000000000
    supply = cvx.totalSupply()
    cliff = supply / (reductionPerCliff)

    # pretend we are claiming 1 CRV
    claimableCrv = 1

    # as long as we're still below the cliff, we're minting
    reduction = totalCliffs - (cliff)
    cvxMintedPerCrv = claimableCrv * (reduction) / (totalCliffs)

    # convert our CVX to CRV units
    converted_cvx = prices[6] / prices[5]
    cvx_printed_as_crv = cvxMintedPerCrv * converted_cvx
    ## -------------------------------------------------------------- ##
    # Add in rewards data for stETH since that's most of its yield
    if hasRewards == True:
        # extra curve rewards calcs
        _stakingRewards = gauge.reward_contract()
        stakingRewards = Contract(_stakingRewards)
        stakingRewardsRate = stakingRewards.rewardRate()
        stakingRewardsTotalSupply = stakingRewards.totalSupply()
        # price of reward asset
        rewardAsset = gauge.reward_tokens(0)
        rewardPath = [rewardAsset, weth, usdc]
        priceOfRewardAsset = sushiswapRouter.getAmountsOut(oneCoin, rewardPath)[2] / 1e6
        rewardsApr = (
            SecondsInYear
            * (stakingRewardsRate / 1e18)
            * (priceOfRewardAsset)
            / (((poolVirtualPrice / 1e18) * stakingRewardsTotalSupply / (1e18)) * (underlyingPrice))
        )
    else:
        rewardsApr = 0
        print("This pool has no extra rewards")

    # Calculate our convex and curve raw variable APRs (without base or rewards APR, as those are the same between protocols)
    cvx_variable_apr = ((1 - convexFee) * currentConvexBoost * baseApr) * (1 + cvx_printed_as_crv) + rewardsApr
    cvx_variable_apr_minus_keep_crv = ((1 - convexFee) * currentConvexBoost * baseApr) * ((1 - convexKeepCrv) + cvx_printed_as_crv) + rewardsApr

    crv_variable_apr = baseApr * currentYearnBoost + rewardsApr
    crv_variable_apr_minus_keep_crv = baseApr * currentYearnBoost * (1 - keepCrv) + rewardsApr

    # ratio of Yearn's veCRV to Convex's
    veCRV_ratio = vecrv.balanceOf(convex_voter) / vecrv.balanceOf(yearn_voter)
    veCRV_ratio_for_printing = veCRV_ratio
    price_fee_cvx_printing_ratio = ((1 - convexFee) * (1 - convexKeepCrv) + cvx_printed_as_crv) / (1 - keepCrv)

    # Ratio target based on extra CVX yield. Consider veCRV ratio, CVX extra yield, and 16% fees on Convex.
    targetRatio = veCRV_ratio * price_fee_cvx_printing_ratio
    targetRatio_for_printing = targetRatio

    # amount needed to transfer from yearn to Convex. If positive, send funds to convex, if negative, send that much back to yearn.
    sendToConvex = (targetRatio_for_printing / (1 + targetRatio_for_printing)) * (
        yearnGaugeBalance + convexGaugeBalance
    ) / 1e18 - convexGaugeBalance / 1e18

    # target debt ratios for each strategy, assuming 100% deployed
    targetRewards = booster.poolInfo(poolId)[3]
    rewards = Contract(targetRewards)
    depositedInConvex = rewards.balanceOf(convexStrategy)

    convexTargetDebtRatio = (depositedInConvex + sendToConvex * 1e18) / (yearnGaugeBalance + depositedInConvex) * 10000
    curveTargetDebtRatio = (1 - convexTargetDebtRatio / 10000) * 10000
    tokenName = lpToken.name()

    # , "\n\nSend this much want to Convex:", "{:,.2f}".format(sendToConvex), "\nTarget Convex debtRatio: ", "{:.0f}".format(convexTargetDebtRatio), "\nTarget Curve debtRatio: ", "{:.0f}".format(curveTargetDebtRatio))

    print(
        "\n\nVault Token: ",
        tokenName,
        "\nCurve Future APR:",
        "{:.2%}".format(crv_variable_apr_minus_keep_crv),
        "\nConvex Future APR:",
        "{:.2%}".format(cvx_variable_apr_minus_keep_crv),
        "\n\n",
    )
