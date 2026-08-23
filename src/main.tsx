import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App.tsx'
import { AuditSessionProvider } from './context/AuditSessionContext.tsx'
import { ThemeProvider } from './context/ThemeContext.tsx'
import { ToastProvider } from './components/ui/Toast.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuditSessionProvider>
          <ToastProvider>
            <App />
          </ToastProvider>
        </AuditSessionProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>,
)
