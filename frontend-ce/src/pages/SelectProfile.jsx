import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const profiles = ['Risk Averse', 'Balanced Trader', 'Max Yield'];

const SelectProfile = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const selectProfile = async (profile) => {
    setLoading(true); // show loading spinner

    try {
      const response = await fetch('http://localhost:5050/save-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile }),
      });

      if (!response.ok) {
        throw new Error('Failed to save profile');
      }

      //  Profile was saved — navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error(error);
      alert('Failed to save profile');
    } finally {
      setLoading(false);
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

        .profile-container {
          margin-top: 15vh;
        }

        .profile-title {
          font-size: 28px;
          margin-bottom: 40px;
          color: #1abc9c;
        }

        .profile-buttons {
          display: flex;
          justify-content: center;
          gap: 20px;
          flex-wrap: wrap;
        }

        .profile-btn {
          background-color: #1abc9c;
          border: none;
          padding: 16px 24px;
          font-size: 16px;
          color: white;
          border-radius: 8px;
          cursor: pointer;
          transition: background-color 0.3s ease;
        }

        .profile-btn:hover {
          background-color: #17a589;
        }

        .loading {
          margin-top: 40px;
          font-size: 18px;
          color: #8b949e;
        }
      `}</style>

      <div className="profile-container">
        <h2 className="profile-title">Select Your Investment Profile</h2>
        <div className="profile-buttons">
          {profiles.map((p) => (
            <button key={p} className="profile-btn" onClick={() => selectProfile(p)} disabled={loading}>
              {p}
            </button>
          ))}
        </div>

        {loading && <div className="loading">Saving profile and preparing dashboard...</div>}
      </div>
    </>
  );
};

export default SelectProfile;
