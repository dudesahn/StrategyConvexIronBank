from brownie import Contract, accounts, web3, chain


def iron_bank_checkup():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    oneCoin = 1e18
    wethPath = [weth, usdc]
    ethPrice = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6

    # Check current price of a single yvCurve-IronBank token in dollars
    # variables
    ibpool = Contract("0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    daddy = accounts.at(web3.ens.resolve("ychad.eth"), force=True)
    IBstrategy = Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")
    dudesahn = accounts.at("0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09", force=True)
    crvIB = Contract("0x5282a4eF67D9C33135340fB3289cc1711c13638C")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    dai = Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    IBconvexStrategy = Contract("0x864F408B422B7d33416AC678b1a1A7E6fbcF5C8c")
    deployer = accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    usdt = Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")

    # Call current debtRatios
    curveDebtRatio = vault.strategies(IBstrategy)[2] / 1e4
    convexDebtRatio = vault.strategies(IBconvexStrategy)[2] / 1e4

    # call vault price per share
    share_price = vault.pricePerShare()
    virtual_price = ibpool.get_virtual_price()
    curve_ib_price = share_price * virtual_price / (1e36)

    ## -------------------------------------------------------------- ##
    ## Use this to check how much crvIB tokens we have sitting in the vault waiting to be moved to strategy
    sittingInVault = crvIB.balanceOf(vault) / 1e18

    ## -------------------------------------------------------------- ##
    ## Use this to check how much unclaimed yvCurve-IronBank tokens I have in the strategies
    rewardsCurve = vault.balanceOf(IBstrategy)
    rewardsConvex = vault.balanceOf(IBconvexStrategy)

    myRewards = (rewardsCurve / 1e18 * 0.55) + (rewardsConvex / 1e18 * 0.9)

    ## -------------------------------------------------------------- ##
    # Time since last report
    hoursSinceLastReportVoterProxy = (chain.time() - vault.strategies(IBstrategy)[5]) / 3600
    hoursSinceLastReportConvex = (chain.time() - vault.strategies(IBconvexStrategy)[5]) / 3600

    # Our current max time between harvests
    currentMaxDelayVoter = IBstrategy.maxReportDelay() / 3600
    currentMaxDelayConvex = IBconvexStrategy.maxReportDelay() / 3600

    ## -------------------------------------------------------------- ##
    # Check my current real APR and check how much we would earn from harvesting either strategy
    # Harvest to clear what we have
    beforeCurveHarvest = vault.totalAssets()
    IBstrategy.harvest({"from": deployer})
    afterCurveHarvest = vault.totalAssets()
    curveProfits = (afterCurveHarvest - beforeCurveHarvest) * virtual_price
    IBconvexStrategy.harvest({"from": deployer})
    afterConvexHarvest = vault.totalAssets()
    convexProfits = (afterConvexHarvest - afterCurveHarvest) * virtual_price
    old_assets = vault.totalAssets()
    curveStarting = IBstrategy.estimatedTotalAssets()
    convexStarting = IBconvexStrategy.estimatedTotalAssets()

    # this is one month
    # chain.sleep(2592000)
    # chain.mine(1)

    # this is one day, sleep for it
    chain.sleep(86400)
    chain.mine(1)

    IBstrategy.harvest({"from": deployer})
    new_assets = vault.totalAssets()
    IBconvexStrategy.harvest({"from": deployer})
    new_convex_assets = vault.totalAssets() - new_assets

    # Display estimated APY based on the past week
    periods = 365
    curveApr = ((new_assets - old_assets) * periods) / (curveStarting)
    curveApy = ((1 + (curveApr / periods)) ** periods) - 1
    convexApr = (new_convex_assets * periods) / (convexStarting)
    convexApy = ((1 + (convexApr / periods)) ** periods) - 1

    ## -------------------------------------------------------------- ##
    ## yvBOOST
    # Check on any distributed or undistributed rewards from this strategy

    # Calculate yvBOOST outstanding and distributed shares
    boostStrategy = Contract("0x2923a58c1831205C854DBEa001809B194FDb3Fa5")
    boostVault = Contract("0x9d409a0A012CFbA9B15F6D4B36Ac57A46966Ab9a")

    boostRewards = boostVault.balanceOf(boostStrategy)
    myBoostRewards = boostRewards * (8.5 / 1e20) + boostVault.balanceOf(dudesahn) / 1e18

    ## -------------------------------------------------------------- ##
    # hours to $40k
    curveHoursTo40k = 40000 / (curveProfits / 1e36) * hoursSinceLastReportVoterProxy
    convexHoursTo40k = 40000 / (convexProfits / 1e36) * hoursSinceLastReportConvex

    # Should we update debtRatios?
    updateDebtRatio = curveApy / convexApy > 1.2 or curveApy / convexApy < 0.8

    print(
        "\nLive Iron Bank Curve APY: ",
        "{:.2%}".format(curveApy),
        "\nLive Iron Bank Convex APY: ",
        "{:.2%}".format(convexApy),
        "\nCurrent Iron Bank Curve Debt Ratio: ",
        "{:.2%}".format(curveDebtRatio),
        "\nCurrent Iron Bank Convex Debt Ratio: ",
        "{:.2%}".format(convexDebtRatio),
        "\n\nShould we update Debt Ratios?",
        updateDebtRatio,
        "\n\nPending Iron Bank Curve Strategy Harvest: $" + str(curveProfits / 1e36),
        "\nHours Since Last Iron Bank Curve Strategy Harvest: " + "{:.4}".format(hoursSinceLastReportVoterProxy),
        "\nCurrent Max Delay Between Curve Harvests: " + "{:.4}".format(currentMaxDelayVoter),
        "\nCurrent Hours To $40k for Curve: " + "{:.4}".format(curveHoursTo40k),
        "\n\nPending Iron Bank Convex Strategy Harvest: $" + str(convexProfits / 1e36),
        "\nHours Since Last Iron Bank Convex Strategy Harvest: " + "{:.4}".format(hoursSinceLastReportConvex),
        "\nCurrent Max Delay Between Convex Harvests: " + "{:.4}".format(currentMaxDelayConvex),
        "\nCurrent Hours To $40k for Convex: " + "{:.4}".format(convexHoursTo40k),
        "\n\ncrvIB sitting in vault: " + str(sittingInVault),
        "\nIron Bank Vault Share Price: $" + str(curve_ib_price),
        "\nClaimable yvCurve-IronBank Tokens: " + str(myRewards),
        "\nTotal yvBOOST Reward Tokens: " + str(myBoostRewards),
    )


def sETH_checkup():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    oneCoin = 1e18
    wethPath = [weth, usdc]
    ethPrice = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6

    # Check current price of a single yvCurve-IronBank token in dollars
    # variables
    ibpool = Contract("0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    daddy = accounts.at(web3.ens.resolve("ychad.eth"), force=True)
    IBstrategy = Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")
    dudesahn = accounts.at("0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09", force=True)
    crvIB = Contract("0x5282a4eF67D9C33135340fB3289cc1711c13638C")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    dai = Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    IBconvexStrategy = Contract("0x864F408B422B7d33416AC678b1a1A7E6fbcF5C8c")
    deployer = accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    usdt = Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")

    ## -------------------------------------------------------------- ##
    ## yvCurve-sETH

    # Check current price of a single yvCurve-sETH token in dollars
    # variables
    sethpool = Contract("0xc5424B857f758E906013F3555Dad202e4bdB4567")
    seth_vault = Contract("0x986b4AFF588a109c09B50A03f42E4110E29D353F")
    crvSETH = Contract("0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c")
    MatSETHstrategy = Contract("0xdD498eB680B0CE6Cac17F7dab0C35Beb6E481a6d")
    SETHconvexStrategy = Contract("0xc2fC89E79D4Fd2570dD9B413b851F38076bCd930")

    # Call current debtRatios
    curveDebtRatio = seth_vault.strategies(MatSETHstrategy)[2] / 1e4
    convexDebtRatio = seth_vault.strategies(SETHconvexStrategy)[2] / 1e4

    # call vault price per share
    seth_share_price = seth_vault.pricePerShare()
    seth_virtual_price = sethpool.get_virtual_price()
    curve_seth_price = seth_share_price * seth_virtual_price / (1e36)

    ## -------------------------------------------------------------- ##
    ## Use this to check how much crvSETH tokens we have sitting in the vault waiting to be moved to strategy

    sETHsittingInVault = crvSETH.balanceOf(seth_vault) / 1e18

    # Time since last report
    hoursSinceLastReport = (chain.time() - seth_vault.strategies(SETHconvexStrategy)[5]) / 3600
    currentMaxDelay = SETHconvexStrategy.maxReportDelay() / 3600

    ## -------------------------------------------------------------- ##
    ## Use this to check how much unclaimed yvCurve-sETH tokens I have in the strategies
    # variables

    SETHrewardsConvex = seth_vault.balanceOf(SETHconvexStrategy)
    SETHmyRewards = SETHrewardsConvex / 1e18 * 0.9
    ## -------------------------------------------------------------- ##
    # Check my current real APR and how much we would make from harvesting either strategy
    # Harvest to clear what we have
    beforeCurveHarvest = seth_vault.totalAssets()
    MatSETHstrategy.harvest({"from": daddy})
    afterCurveHarvest = seth_vault.totalAssets()
    SETHcurveProfits = (afterCurveHarvest - beforeCurveHarvest) * seth_virtual_price * ethPrice
    SETHconvexStrategy.harvest({"from": daddy})
    afterConvexHarvest = seth_vault.totalAssets()
    SETHconvexProfits = (afterConvexHarvest - afterCurveHarvest) * seth_virtual_price * ethPrice
    old_assets = seth_vault.totalAssets()
    curveStarting = MatSETHstrategy.estimatedTotalAssets()
    convexStarting = SETHconvexStrategy.estimatedTotalAssets()

    # this is one month
    # chain.sleep(2592000)
    # chain.mine(1)

    # this is one day, sleep for it
    chain.sleep(86400)
    chain.mine(1)

    MatSETHstrategy.harvest({"from": daddy})
    new_assets = seth_vault.totalAssets()
    SETHconvexStrategy.harvest({"from": daddy})
    new_convex_assets = seth_vault.totalAssets() - new_assets

    # Display estimated APY based on the past week
    periods = 365
    curveApr = ((new_assets - old_assets) * periods) / (curveStarting)
    SETHcurveApy = ((1 + (curveApr / periods)) ** periods) - 1
    convexApr = (new_convex_assets * periods) / (convexStarting)
    SETHconvexApy = ((1 + (convexApr / periods)) ** periods) - 1

    ## -------------------------------------------------------------- ##
    # hours to $40k
    convexHoursTo40k = 40000 / (SETHconvexProfits / 1e36) * hoursSinceLastReport

    # Should we update debtRatios?
    updateDebtRatio = SETHcurveApy / SETHconvexApy > 1.2 or SETHcurveApy / SETHconvexApy < 0.8

    print(
        "\nLive sETH Curve APY: ",
        "{:.2%}".format(SETHcurveApy),
        "\nLive sETH Convex APY: ",
        "{:.2%}".format(SETHconvexApy),
        "\nCurrent sETH Curve Debt Ratio: ",
        "{:.2%}".format(curveDebtRatio),
        "\nCurrent sETH Convex Debt Ratio: ",
        "{:.2%}".format(convexDebtRatio),
        "\n\nShould we update Debt Ratios?",
        updateDebtRatio,
        "\n\nPending sETH Curve Strategy Harvest: $" + str(SETHcurveProfits / 1e36),
        "\nPending sETH Convex Strategy Harvest: $" + str(SETHconvexProfits / 1e36),
        "\nHours Since Last sETH Convex Strategy Harvest: " + "{:.4}".format(hoursSinceLastReport),
        "\nCurrent Max Delay Between Convex Harvests: " + "{:.4}".format(currentMaxDelay),
        "\nCurrent Hours To $40k for Convex: " + "{:.4}".format(convexHoursTo40k),
        "\n\ncrvSETH sitting in vault: " + str(sETHsittingInVault),
        "\nsETH Vault Share Price: $" + str(curve_seth_price),
        "\nClaimable yvCurve-sETH Tokens: " + str(SETHmyRewards),
    )


def stETH_checkup():
    # establish our prices for our various underlying tokens
    sushiswapRouter = Contract("0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F")
    weth = Contract("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    ldo = Contract("0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32")
    crv = Contract("0xD533a949740bb3306d119CC777fa900bA034cd52")
    ldoPath = [ldo, weth]
    oneCoin = 1e18
    wethPath = [weth, usdc]
    ethPrice = sushiswapRouter.getAmountsOut(oneCoin, wethPath)[1] / 1e6

    # Check current price of a single yvCurve-IronBank token in dollars
    # variables
    ibpool = Contract("0x2dded6Da1BF5DBdF597C45fcFaa3194e53EcfeAF")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    daddy = accounts.at(web3.ens.resolve("ychad.eth"), force=True)
    IBstrategy = Contract("0x5148C3124B42e73CA4e15EEd1B304DB59E0F2AF7")
    dudesahn = accounts.at("0x8Ef63b525fceF7f8662D98F77f5C9A86ae7dFE09", force=True)
    crvIB = Contract("0x5282a4eF67D9C33135340fB3289cc1711c13638C")
    vault = Contract("0x27b7b1ad7288079A66d12350c828D3C00A6F07d7")
    dai = Contract("0x6B175474E89094C44Da98b954EedeAC495271d0F")
    IBconvexStrategy = Contract("0x864F408B422B7d33416AC678b1a1A7E6fbcF5C8c")
    deployer = accounts.at("0xBedf3Cf16ba1FcE6c3B751903Cf77E51d51E05b8", force=True)
    usdc = Contract("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    usdt = Contract("0xdAC17F958D2ee523a2206206994597C13D831ec7")

    ## -------------------------------------------------------------- ##
    ## yvCurve-stETH

    # Check current price of a single yvCurve-stETH token in dollars
    # variables
    stethpool = Contract("0xDC24316b9AE028F1497c275EB9192a3Ea0f67022")
    steth_vault = Contract("0xdCD90C7f6324cfa40d7169ef80b12031770B4325")
    crvSTETH = Contract("0x06325440D014e39736583c165C2963BA99fAf14E")
    SamSTETHstrategy = Contract("0x979843B8eEa56E0bEA971445200e0eC3398cdB87")
    STETHconvexStrategy = Contract("0x6C0496fC55Eb4089f1Cf91A4344a2D56fAcE51e3")

    # call vault price per share
    steth_share_price = steth_vault.pricePerShare()
    steth_virtual_price = stethpool.get_virtual_price()
    curve_steth_price = steth_share_price * steth_virtual_price / (1e36)

    # Call current debtRatios
    curveDebtRatio = steth_vault.strategies(SamSTETHstrategy)[2] / 1e4
    convexDebtRatio = steth_vault.strategies(STETHconvexStrategy)[2] / 1e4

    ## -------------------------------------------------------------- ##
    ## Use this to check how much crvSTETH tokens we have sitting in the vault waiting to be moved to strategy
    stETHsittingInVault = crvSTETH.balanceOf(steth_vault) / 1e18

    # Time since last report
    hoursSinceLastReport = (chain.time() - steth_vault.strategies(STETHconvexStrategy)[4]) / 3600
    currentMaxDelay = STETHconvexStrategy.maxReportDelay() / 3600

    ## -------------------------------------------------------------- ##
    ## Use this to check how much unclaimed yvCurve-stETH tokens I have in the strategy
    # variables

    STETHrewardsConvex = steth_vault.balanceOf(STETHconvexStrategy)
    STETHmyRewards = STETHrewardsConvex / 1e18 * 0.85

    ## -------------------------------------------------------------- ##
    # Check my current real APR and how much we would earn from harvesting either strategy
    # Harvest to clear what we have
    SamSTETHstrategy.setLDORouter(1, ldoPath, {"from": daddy})
    beforeCurveHarvest = steth_vault.totalAssets()
    SamSTETHstrategy.harvest({"from": daddy})
    afterCurveHarvest = steth_vault.totalAssets()
    STETHcurveProfits = (afterCurveHarvest - beforeCurveHarvest) * steth_virtual_price * ethPrice
    STETHconvexStrategy.harvest({"from": daddy})
    afterConvexHarvest = steth_vault.totalAssets()
    STETHconvexProfits = (afterConvexHarvest - afterCurveHarvest) * steth_virtual_price * ethPrice
    old_assets = steth_vault.totalAssets()
    curveStarting = SamSTETHstrategy.estimatedTotalAssets()
    convexStarting = STETHconvexStrategy.estimatedTotalAssets()

    # this is one month
    # chain.sleep(2592000)
    # chain.mine(1)

    # this is one day, sleep for it
    chain.sleep(86400)
    chain.mine(1)

    SamSTETHstrategy.harvest({"from": daddy})
    new_assets = steth_vault.totalAssets()
    STETHconvexStrategy.harvest({"from": daddy})
    new_convex_assets = steth_vault.totalAssets() - new_assets

    # Display estimated APY based on the past week
    periods = 365
    curveApr = ((new_assets - old_assets) * periods) / (curveStarting)
    STETHcurveApy = ((1 + (curveApr / periods)) ** periods) - 1
    convexApr = (new_convex_assets * periods) / (convexStarting)
    STETHconvexApy = ((1 + (convexApr / periods)) ** periods) - 1

    ## -------------------------------------------------------------- ##
    # hours to $40k
    convexHoursTo40k = 40000 / (STETHconvexProfits / 1e36) * hoursSinceLastReport

    # Should we update debtRatios?
    updateDebtRatio = STETHcurveApy / STETHconvexApy > 1.2 or STETHcurveApy / STETHconvexApy < 0.8

    print(
        "\nLive stETH Curve APY: ",
        "{:.2%}".format(STETHcurveApy),
        "\nLive stETH Convex APY: ",
        "{:.2%}".format(STETHconvexApy),
        "\nCurrent stETH Curve Debt Ratio: ",
        "{:.2%}".format(curveDebtRatio),
        "\nCurrent stETH Convex Debt Ratio: ",
        "{:.2%}".format(convexDebtRatio),
        "\n\nShould we update Debt Ratios?",
        updateDebtRatio,
        "\n\nPending stETH Curve Strategy Harvest: $" + str(STETHcurveProfits / 1e36),
        "\nPending stETH Convex Strategy Harvest: $" + str(STETHconvexProfits / 1e36),
        "\nHours Since Last stETH Convex Strategy Harvest: " + "{:.4}".format(hoursSinceLastReport),
        "\nCurrent Max Delay Between Convex Harvests: " + "{:.4}".format(currentMaxDelay),
        "\nCurrent Hours To $40k for Convex: " + "{:.4}".format(convexHoursTo40k),
        "\n\ncrvSTETH sitting in vault: " + str(stETHsittingInVault),
        "\nstETH Vault Share Price: $" + str(curve_steth_price),
        "\nClaimable yvCurve-stETH Tokens: " + str(STETHmyRewards),
    )
