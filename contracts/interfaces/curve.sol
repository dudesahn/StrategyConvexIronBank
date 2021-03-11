// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface IGauge {
    function balanceOf(address) external view returns (uint256);

    function withdraw(uint256) external;
}

interface ICurveFi {
    function add_liquidity(
        // Iron bank pool
        uint256[3] calldata amounts,
        uint256 min_mint_amount,
        bool use_underlying
    ) external payable;
}

interface ICrvV3 is IERC20 {
    function minter() external view returns (address);
}
