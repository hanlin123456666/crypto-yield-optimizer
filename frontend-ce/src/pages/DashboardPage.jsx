import React, { useEffect, useState } from 'react';
import {
  PieChart, Pie, Cell, Legend, ResponsiveContainer,
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts';
import { JsonRpcProvider, formatEther } from 'ethers';
import { useNavigate } from 'react-router-dom';

const INFURA_URL = "https://sepolia.infura.io/v3/eadc5f28a76f499b96c0dbbf9ab11121"; //  Replace this with your real one

const COLORS = ['#1abc9c', '#3498db', '#9b59b6', '#f39c12', '#e74c3c'];

const DashboardPage = () => {
  const [account, setAccount] = useState('');
  const [ethBalance, setEthBalance] = useState(0);
  const [chartData, setChartData] = useState([]);
  const [priceData, setPriceData] = useState([]);
  const navigate = useNavigate();

  const logout = () => {
    setAccount('');
    setEthBalance(0);
    setChartData([]);
    setPriceData([]);
    navigate('/', { replace: true });
  };

  useEffect(() => {
    const loadData = async () => {
      if (!window.ethereum) return alert("MetaMask not detected");

      try {
        const [addr] = await window.ethereum.request({ method: 'eth_requestAccounts' });
        setAccount(addr);

        const provider = new JsonRpcProvider(INFURA_URL);
        const balance = await provider.getBalance(addr);
        const eth = parseFloat(formatEther(balance));
        setEthBalance(eth);

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
        <div className="info"><strong>ETH Balance:</strong> {ethBalance} ETH</div>

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
