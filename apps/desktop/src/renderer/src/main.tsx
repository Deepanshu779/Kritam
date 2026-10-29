import React from 'react';
import ReactDOM from 'react-dom/client';
import { App } from './App';
import './styles/theme.css';

const storedTheme = localStorage.getItem('kritam-theme') || 'dark';
document.documentElement.setAttribute('data-theme', storedTheme);
const colorScheme = document.querySelector('meta[name="color-scheme"]');
if (colorScheme) colorScheme.setAttribute('content', storedTheme === 'system' ? 'light dark' : storedTheme);

const rootEl = document.getElementById('root');
if (rootEl) {
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
