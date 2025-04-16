import React, { useEffect, useState } from 'react';
import {
  PieChart, Pie, Cell, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import { JsonRpcProvider, formatEther, BrowserProvider, Contract, parseEther } from 'ethers';
import { useNavigate } from 'react-router-dom';

const INFURA_URL = "https://sepolia.infura.io/v3/eadc5f28a76f499b96c0dbbf9ab11121"; //  Replace this with your real one

const COLORS = ['#1abc9c', '#3498db', '#9b59b6', '#f39c12', '#e74c3c'];

// Add the ZapVault ABI
const ZapVaultABI = [
  "function deposit() external payable",
  "function depositToken(address token, uint256 amount) external",
  "function getBalance() public view returns (uint256)",
  "function getTokenBalance(address token, address user) public view returns (uint256)",
  "function withdrawToProtocol(address token, address protocol, uint256 amount) external"
];

// Add your deployed contract address
const CONTRACT_ADDRESS = "0xff4EdEA900F4da54EbA5e79c2e071e0029ac2570";

const DashboardPage = () => {
  const [account, setAccount] = useState('');
  const [ethBalance, setEthBalance] = useState(0);
  const [chartData, setChartData] = useState([]);
  const [priceData, setPriceData] = useState([]);
  const [isWithdrawing, setIsWithdrawing] = useState(false);
  const [contractBalance, setContractBalance] = useState('0');
  const navigate = useNavigate();

  const logout = () => {
    setAccount('');
    setEthBalance(0);
    setChartData([]);
    setPriceData([]);
    setIsWithdrawing(false);
    setContractBalance('0');
    navigate('/', { replace: true });
  };

  useEffect(() => {
    const loadData = async () => {
      if (!window.ethereum) return alert("MetaMask not detected");

      try {
        const [addr] = await window.ethereum.request({ method: 'eth_requestAccounts' });
        setAccount(addr);

        const provider = new BrowserProvider(window.ethereum);
        const balance = await provider.getBalance(addr);
        const eth = parseFloat(formatEther(balance));
        setEthBalance(eth);

        // Get contract balance
        const vault = new Contract(CONTRACT_ADDRESS, ZapVaultABI, provider);
        const vaultBalance = await vault.getBalance();
        setContractBalance(formatEther(vaultBalance));

        //  Add more tokens here later
        const tokens = [
          { name: 'ETH', value: eth },
          // { name: 'USDC', value: 23 },
          // { name: 'DAI', value: 45 }
        ];

        const total = tokens.reduce((sum, t) => sum + t.value, 0);
        const withPercent = tokens.map(t => ({
          ...t,
          percent: ((t.value / total) * 100).toFixed(1) + '%'
        }));

        setChartData(withPercent);

        //  Placeholder price data (7-day trend)
        setPriceData([
          { day: 'Mon', price: 1824 },
          { day: 'Tue', price: 1862 },
          { day: 'Wed', price: 1830 },
          { day: 'Thu', price: 1887 },
          { day: 'Fri', price: 1912 },
          { day: 'Sat', price: 1890 },
          { day: 'Sun', price: 1924 },
        ]);

      } catch (err) {
        console.error(err);
        alert("Failed to load wallet data");
      }
    };

    loadData();
  }, []);

  const handleWithdraw = async () => {
    if (!contractBalance || parseFloat(contractBalance) <= 0) {
      alert('No funds available to withdraw');
      return;
    }

    setIsWithdrawing(true);

    try {
      const provider = new BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const vault = new Contract(CONTRACT_ADDRESS, ZapVaultABI, signer);
      
      // Withdraw all funds back to user's wallet
      const tx = await vault.withdrawToProtocol(
        "0x0000000000000000000000000000000000000000", // Use zero address for ETH
        await signer.getAddress(),
        parseEther(contractBalance)
      );

      await tx.wait();
      console.log('Withdrawal successful:', tx.hash);
      
      // Refresh balances
      const newBalance = await provider.getBalance(account);
      setEthBalance(parseFloat(formatEther(newBalance)));
      
      const newVaultBalance = await vault.getBalance();
      setContractBalance(formatEther(newVaultBalance));

    } catch (err) {
      console.error('Withdrawal error:', err);
      alert('Failed to withdraw. Please try again.');
    } finally {
      setIsWithdrawing(false);
    }
  };

  const shortenAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <>
      <style>{`
        body {
          margin: 0;
          background-color: #0d1117;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          color: #f0f6fc;
        }

        .container {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 20px;
          min-height: 100vh;
          position: relative;
        }

        .address-btn {
          position: absolute;
          top: 20px;
          right: 20px;
          background-color: #21262d;
          color: #f0f6fc;
          border: 1px solid #30363d;
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.3s ease;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .address-btn:hover {
          background-color: #e74c3c;
          border-color: #e74c3c;
        }

        .address-btn:hover .address-text {
          display: none;
        }

        .address-btn:hover .logout-text {
          display: block;
        }

        .logout-text {
          display: none;
        }

        .wallet-icon {
          width: 16px;
          height: 16px;
          fill: currentColor;
        }

        .title {
          font-size: 32px;
          margin-bottom: 20px;
          color: #1abc9c;
        }

        .info {
          margin: 10px 0;
        }

        .chart-wrapper {
          width: 100%;
          max-width: 600px;
          margin-top: 30px;
        }

        .withdraw-btn {
          background-color: #1abc9c;
          color: white;
          border: none;
          border-radius: 6px;
          padding: 12px 24px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.3s ease;
          margin-top: 20px;
        }

        .withdraw-btn:hover {
          background-color: #17a589;
        }

        .withdraw-btn:disabled {
          background-color: #597068;
          cursor: not-allowed;
        }

        .balance-info {
          display: flex;
          flex-direction: column;
          gap: 10px;
          margin: 20px 0;
          padding: 20px;
          background-color: #21262d;
          border-radius: 8px;
          text-align: center;
        }
      `}</style>

      <div className="container">
        <button className="address-btn" onClick={logout}>
          <svg className="wallet-icon" viewBox="0 0 24 24">
            <path d="M21 18v1c0 1.1-.9 2-2 2H5c-1.11 0-2-.9-2-2V5c0-1.1.89-2 2-2h14c1.1 0 2 .9 2 2v1h-9c-1.11 0-2 .9-2 2v8c0 1.1.89 2 2 2h9zm-9-2h10V8H12v8zm4-2.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
          </svg>
          <span className="address-text">{account ? shortenAddress(account) : '...'}</span>
          <span className="logout-text">Logout</span>
        </button>

        <div className="title">Wallet Dashboard</div>
        <div className="balance-info">
          <div className="info"><strong>Wallet Balance:</strong> {ethBalance} ETH</div>
          <div className="info"><strong>Invested Balance:</strong> {parseFloat(contractBalance).toFixed(4)} ETH</div>
          <button 
            className="withdraw-btn"
            onClick={handleWithdraw}
            disabled={isWithdrawing || parseFloat(contractBalance) <= 0}
          >
            {isWithdrawing ? 'Processing...' : 'Withdraw Funds'}
          </button>
        </div>

        {/* Pie Chart - Portfolio Breakdown */}
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
                label={({ name, percent }) => `${name}: ${percent}`}
              >
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Line Chart - Price Trend */}
        <div className="chart-wrapper">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={priceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="price" stroke="#1abc9c" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  );
};

export default DashboardPage;