import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { configureApiClient } from './lib/api'

// Configure API client with backend URL
const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://klaital.com:8081/api';
configureApiClient(backendUrl);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
