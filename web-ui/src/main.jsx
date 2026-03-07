import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.jsx'
import './index.css'
import './layout.css'
import './i18n' // Implemented i18n
import { Suspense } from 'react'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Suspense fallback={<div className="loading-screen">Loading Enterprise NGFW...</div>}>
        <App />
      </Suspense>
    </BrowserRouter>
  </React.StrictMode>,
)
