import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { BrowserProvider, formatEther, parseEther, Contract } from 'ethers';

// Update the ZapVault ABI to include withdrawal function
const ZapVaultABI = [
  "function deposit() external payable",
  "function depositToken(address token, uint256 amount) external",
  "function getBalance() public view returns (uint256)",
  "function getTokenBalance(address token, address user) public view returns (uint256)",
  "function withdrawToProtocol(address token, address protocol, uint256 amount) external"
];

// Add deployed contract address
const CONTRACT_ADDRESS = "0xff4EdEA900F4da54EbA5e79c2e071e0029ac2570";

const DepositPage = () => {
  const [amount, setAmount] = useState('');
  const [balance, setBalance] = useState('0');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isDepositing, setIsDepositing] = useState(false);
  const [isToken, setIsToken] = useState(false);
  const [selectedToken, setSelectedToken] = useState('ETH');
  const [isWithdraw, setIsWithdraw] = useState(false);
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
      setError('Insufficient funds');
      return;
    }

    if (parseFloat(amount) <= 0) {
      setError('Amount must be greater than 0');
      return;
    }

    setIsDepositing(true);
    setError('');

    try {
      const provider = new BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const vault = new Contract(CONTRACT_ADDRESS, ZapVaultABI, signer);

      // ETH deposit
      const amountInWei = parseEther(amount);
      const tx = await vault.deposit({ value: amountInWei });
      
      await tx.wait();
      console.log('Deposit successful:', tx.hash);

      navigate('/select');
    } catch (err) {
      console.error('Deposit error:', err);
      setError(err.message || 'Failed to deposit. Please try again.');
    } finally {
      setIsDepositing(false);
    }
  };

  // Add withdrawal function
  const handleWithdraw = async () => {
    try {
      setIsWithdraw(true);
      
      const provider = new BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const vault = new Contract(CONTRACT_ADDRESS, ZapVaultABI, signer);
      
      // Get contract balance
      const contractBalance = await vault.getBalance();
      
      if (contractBalance <= 0) {
        throw new Error('No funds to withdraw');
      }

      // Withdraw all funds back to user's wallet
      const tx = await vault.withdrawToProtocol(
        "0x0000000000000000000000000000000000000000", // Use zero address for ETH
        await signer.getAddress(),
        contractBalance
      );

      await tx.wait();
      console.log('Withdrawal successful:', tx.hash);
      
      // Refresh balance
      await fetchBalance();
      
    } catch (err) {
      console.error('Withdrawal error:', err);
      setError(err.message || 'Failed to withdraw. Please try again.');
    } finally {
      setIssWithdraw(false);
    }
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

        .loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(13, 17, 23, 0.8);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .loading-spinner {
          color: #1abc9c;
          font-size: 18px;
        }

        .withdraw-btn {
          background-color: #e74c3c;
          margin-top: 10px;
        }
      `}</style>

      {isDepositing && (
        <div className="loading-overlay">
          <div className="loading-spinner">
            Processing deposit...
          </div>
        </div>
      )}

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
                  disabled={isDepositing}
                />
                <div className="error-message">
                  {error}
                </div>
              </div>
              <button 
                type="submit" 
                className="submit-btn"
                disabled={!amount || error || isDepositing}
              >
                {isDepositing ? 'Processing...' : 'Continue to Investment Selection'}
              </button>
              
              {/* Add withdraw button */}
              <button 
                type="button"
                className="submit-btn withdraw-btn"
                onClick={handleWithdraw}
                disabled={isWithdraw}
              >
                {isWithdraw ? 'Processing Withdrawal...' : 'Withdraw Funds'}
              </button>
            </form>
          </>
        )}
      </div>
    </>
  );
};

export default DepositPage; 