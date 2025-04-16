// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function approve(address spender, uint256 amount) external returns (bool);
    function transfer(address recipient, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract ZapVault {
    address public owner;
    address public operator;
    
    mapping(address => uint256) public deposits;
    mapping(address => mapping(address => uint256)) public tokenDeposits; // user => token => amount

    event Deposited(address indexed user, uint256 amount);
    event TokenDeposited(address indexed user, address indexed token, uint256 amount);
    event WithdrawnToProtocol(address indexed token, address indexed protocol, uint256 amount);
    event OperatorUpdated(address indexed newOperator);

    constructor() {
        owner = msg.sender;
        operator = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    modifier onlyOperator() {
        require(msg.sender == operator, "Not authorized");
        _;
    }

    // Update operator address
    function setOperator(address _operator) external onlyOwner {
        operator = _operator;
        emit OperatorUpdated(_operator);
    }

    // For ETH deposits
    function deposit() external payable {
        require(msg.value > 0, "Zero ETH not allowed");
        deposits[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    // For ERC20 token deposits
    function depositToken(address token, uint256 amount) external {
        require(amount > 0, "Zero amount not allowed");
        require(token != address(0), "Invalid token address");
        
        IERC20(token).transferFrom(msg.sender, address(this), amount);
        tokenDeposits[msg.sender][token] += amount;
        emit TokenDeposited(msg.sender, token, amount);
    }

    // Operator function to move funds to lending protocols
    function withdrawToProtocol(
        address token,
        address protocol,
        uint256 amount
    ) external onlyOperator {
        require(address(this).balance >= amount, "Insufficient balance");
        
        if (token == address(0)) {
            // For ETH
            payable(protocol).transfer(amount);
        } else {
            // For ERC20 tokens
            IERC20(token).approve(protocol, amount);
            IERC20(token).transfer(protocol, amount);
        }
        
        emit WithdrawnToProtocol(token, protocol, amount);
    }

    // View functions
    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }

    function getTokenBalance(address token, address user) public view returns (uint256) {
        return tokenDeposits[user][token];
    }
}
