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

        .logout-btn {
          margin-top: 40px;
          background-color: #e74c3c;
          color: white;
          border: none;
          border-radius: 6px;
          padding: 12px 24px;
          font-size: 16px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }

        .logout-btn:hover {
          background-color: #c0392b;
        }
      `}</style>

      <div className="container">
        <div className="title">Wallet Dashboard</div>
        <div className="info"><strong>Address:</strong> {account}</div>
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

        <button className="logout-btn" onClick={logout}>Logout</button>
      </div>
    </>
  );
};

export default DashboardPage;
