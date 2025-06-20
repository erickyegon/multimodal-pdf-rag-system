import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Environment Variable Validation
console.log('Environment Variables:');
console.log('REACT_APP_API_URL:', process.env.REACT_APP_API_URL);

if (!process.env.REACT_APP_API_URL) {
  console.error('⚠️ REACT_APP_API_URL is not defined in .env file');
  console.log('Using fallback: http://localhost:8000');
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
