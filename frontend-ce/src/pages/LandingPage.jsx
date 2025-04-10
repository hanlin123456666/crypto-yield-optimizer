import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage = () => {
  const navigate = useNavigate();

  const connectWallet = async () => {
    if (typeof window.ethereum !== 'undefined') {
      try {
        const accounts = await window.ethereum.request({
          method: 'eth_requestAccounts',
        });

        console.log("Connected account:", accounts[0]);
        navigate('/deposit');
      } catch (error) {
        console.error("User rejected wallet connection:", error);
        alert("Please allow wallet connection to continue.");
      }
    } else {
      alert("MetaMask not detected. Please install MetaMask and try again.");
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

        .landing-container {
          margin-top: 20vh;
        }

        .highlight {
          color: #1abc9c;
        }

        .connect-btn {
          padding: 12px 24px;
          font-size: 16px;
          background-color: #1abc9c;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          margin-top: 20px;
          transition: background-color 0.3s ease;
        }

        .connect-btn:hover {
          background-color: #17a589;
        }
      `}</style>

      <div className="landing-container">
        <h1>Welcome to <span className="highlight">CryptoApp</span></h1>
        <button className="connect-btn" onClick={connectWallet}>
          Connect Wallet
        </button>
      </div>
    </>
  );
};

export default LandingPage;
