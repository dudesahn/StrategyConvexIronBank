// SPDX-License-Identifier: AGPL-3.0
pragma solidity >=0.6.0 <0.7.0;
pragma experimental ABIEncoderV2;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

interface ICurveStrategyProxy {
    function approveStrategy(address _gauge, address _strategy) external;

    function lock() external;

    function revokeStrategy(address _gauge) external;

    function withdraw(
        address _gauge,
        address _token,
        uint256 _amount
    ) external returns (uint256);

    function balanceOf(address _gauge) external view returns (uint256);

    //        return IERC20(_gauge).balanceOf(address(proxy));

    function withdrawAll(address _gauge, address _token)
        external
        returns (uint256);

    function deposit(address _gauge, address _token) external;

    //        require(strategies[_gauge] == msg.sender, "!strategy");
    //        uint _balance = IERC20(_token).balanceOf(address(this));
    //        IERC20(_token).safeTransfer(address(proxy), _balance);
    //        _balance = IERC20(_token).balanceOf(address(proxy));
    //
    //        proxy.execute(_token, 0, abi.encodeWithSignature("approve(address,uint256)", _gauge, 0));
    //        proxy.execute(_token, 0, abi.encodeWithSignature("approve(address,uint256)", _gauge, _balance));
    //        (bool success, ) = proxy.execute(_gauge, 0, abi.encodeWithSignature("deposit(uint256)", _balance));
    //        if (!success) assert(false);

    function harvest(address _gauge) external;

    //        require(strategies[_gauge] == msg.sender, "!strategy");
    //        uint _balance = IERC20(crv).balanceOf(address(proxy));
    //        proxy.execute(mintr, 0, abi.encodeWithSignature("mint(address)", _gauge));
    //        _balance = (IERC20(crv).balanceOf(address(proxy))).sub(_balance);
    //        proxy.execute(crv, 0, abi.encodeWithSignature("transfer(address,uint256)", msg.sender, _balance));

    function claim(address recipient) external;
}

interface IVoter {
    function execute(
        address to,
        uint256 value,
        bytes calldata data
    ) external returns (bool, bytes memory);

    function increaseAmount(uint256) external;
}
