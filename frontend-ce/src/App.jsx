import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import SelectProfile from './pages/SelectProfile';
import DashboardPage from './pages/DashboardPage';

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/select" element={<SelectProfile />} />
      <Route path="/dashboard" element={<DashboardPage/>} />
    </Routes>
  </BrowserRouter>
);

export default App;
