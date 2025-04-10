import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BrowserProvider, formatEther } from 'ethers';

const DepositPage = () => {
  const [amount, setAmount] = useState('');
  const [balance, setBalance] = useState('0');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    fetchBalance();
  }, []);

  useEffect(() => {
    // Validate amount whenever it changes
    if (amount && parseFloat(amount) > parseFloat(balance)) {
      setError('Insufficient funds');
    } else if (amount && parseFloat(amount) <= 0) {
      setError('Amount must be greater than 0');
    } else {
      setError('');
    }
  }, [amount, balance]);

  const fetchBalance = async () => {
    try {
      if (window.ethereum) {
        const provider = new BrowserProvider(window.ethereum);
        const accounts = await provider.listAccounts();
        if (accounts.length > 0) {
          const balance = await provider.getBalance(accounts[0]);
          setBalance(formatEther(balance));
        }
      }
      setLoading(false);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (parseFloat(amount) > parseFloat(balance)) {
      alert('Insufficient funds! You cannot deposit more than your balance.');
      return;
    }

    if (parseFloat(amount) <= 0) {
      alert('Please enter a valid amount greater than 0.');
      return;
    }

    // Here you would add the actual deposit logic
    console.log('Deposit amount:', amount);
    navigate('/select');
  };

  return (
    <>
      <style>{`
        body {
          margin: 0;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background-color: #0d1117;
          color: #f0f6fc;
          text-align: center;
        }

        .deposit-container {
          max-width: 400px;
          margin: 20vh auto 0;
          padding: 20px;
        }

        .deposit-form {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .input-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
          text-align: left;
        }

        .input-group label {
          color: #f0f6fc;
          font-size: 16px;
        }

        .input-group input {
          padding: 12px;
          border: 1px solid #30363d;
          border-radius: 6px;
          background-color: #161b22;
          color: #f0f6fc;
          font-size: 16px;
          transition: border-color 0.3s ease;
        }

        .input-group input.error {
          border-color: #e74c3c;
        }

        .error-message {
          color: #e74c3c;
          font-size: 14px;
          margin-top: 4px;
          text-align: left;
          min-height: 20px;
        }

        .balance-display {
          text-align: left;
          color: #1abc9c;
          margin-bottom: 20px;
        }

        .submit-btn {
          padding: 12px 24px;
          font-size: 16px;
          background-color: #1abc9c;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }

        .submit-btn:hover {
          background-color: #17a589;
        }

        .submit-btn:disabled {
          background-color: #597068;
          cursor: not-allowed;
        }
      `}</style>

      <div className="deposit-container">
        <h1>Deposit Funds</h1>
        {loading ? (
          <p>Loading your balance...</p>
        ) : (
          <>
            <div className="balance-display">
              <p>Your Balance: {parseFloat(balance).toFixed(4)} ETH</p>
            </div>
            <form className="deposit-form" onSubmit={handleSubmit}>
              <div className="input-group">
                <label htmlFor="amount">Amount to Deposit (ETH)</label>
                <input
                  type="number"
                  id="amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.0"
                  step="0.0001"
                  min="0"
                  max={balance}
                  required
                  className={error ? 'error' : ''}
                />
                <div className="error-message">
                  {error}
                </div>
              </div>
              <button 
                type="submit" 
                className="submit-btn"
                disabled={!amount || error}
              >
                Continue to Investment Selection
              </button>
            </form>
          </>
        )}
      </div>
    </>
  );
};

export default DepositPage; 