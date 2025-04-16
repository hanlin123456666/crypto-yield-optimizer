// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "forge-std/Script.sol";
import "../src/ZapVault.sol";

contract DeployZapVault is Script {
    function run() external {
        // Retrieve private key from environment
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Start broadcasting transactions
        vm.startBroadcast(deployerPrivateKey);

        // Deploy the contract
        ZapVault vault = new ZapVault();

        // Stop broadcasting transactions
        vm.stopBroadcast();

        // Log the deployed address
        console.log("ZapVault deployed to:", address(vault));
    }
}