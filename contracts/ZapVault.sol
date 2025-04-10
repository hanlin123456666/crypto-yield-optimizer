// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ZapVault {
    address public owner;

    mapping(address => uint256) public deposits;

    event Deposited(address indexed user, uint256 amount);
    event WithdrawnToBackend(uint256 amount);

    constructor() {
        owner = msg.sender;
    }

    // Frontend calls this
    function deposit() external payable {
        require(msg.value > 0, "Zero ETH not allowed");
        deposits[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    // Backend calls this to take ETH from vault
    function withdrawToBackend(address target, uint256 amount) external {
        require(msg.sender == owner, "Not authorized");
        require(address(this).balance >= amount, "Insufficient balance");
        payable(target).transfer(amount);
        emit WithdrawnToBackend(amount);
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
