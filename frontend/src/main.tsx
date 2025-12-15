import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './index.css';
import Dashboard from './pages';
import LogPage from './pages/log';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/log" element={<LogPage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
