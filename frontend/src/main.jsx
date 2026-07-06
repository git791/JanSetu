import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#111827',
            color: '#F9FAFB',
            border: '1px solid rgba(99, 102, 241, 0.3)',
            borderRadius: '12px',
            fontSize: '14px',
            fontFamily: 'Inter, sans-serif',
          },
          success: {
            iconTheme: { primary: '#10B981', secondary: '#111827' },
          },
          error: {
            iconTheme: { primary: '#EF4444', secondary: '#111827' },
          },
        }}
      />
    </BrowserRouter>
  </React.StrictMode>
)
