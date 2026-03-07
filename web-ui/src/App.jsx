import { Routes, Route, Navigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useEffect } from 'react'
import Sidebar from './components/Sidebar'
import TopHeader from './components/TopHeader'
import SystemSettings from './pages/SystemSettings';
import Dashboard from './pages/Dashboard'
import AIPipeline from './pages/AIPipeline'
import VPNManager from './pages/VPNManager'
import QoSTraffic from './pages/QoSTraffic'
import SystemHA from './pages/SystemHA'
import Settings from './pages/Settings'
import FirewallRules from './pages/FirewallRules'
import LiveTraffic from './pages/LiveTraffic'
import Alerts from './pages/Alerts'
import InterfaceMap from './pages/InterfaceMap'
import CertificateManager from './pages/CertificateManager'
import SystemTerminal from './pages/SystemTerminal'

function App() {
  const { i18n } = useTranslation()

  // Update HTML direction for RTL/LTR support based on current language
  useEffect(() => {
    document.documentElement.dir = i18n.language === 'ar' ? 'rtl' : 'ltr';
    document.documentElement.lang = i18n.language;
  }, [i18n.language])

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content-wrapper">
        <TopHeader />
        <main className="main-content">
          <Routes>
            <Route path="/system" element={<SystemSettings />} />
            <Route path="/" element={<Dashboard />} />
            <Route path="/ai-pipeline" element={<AIPipeline />} />
            <Route path="/vpn" element={<VPNManager />} />
            <Route path="/qos" element={<QoSTraffic />} />
            <Route path="/system" element={<SystemHA />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/rules" element={<FirewallRules />} />
            <Route path="/traffic" element={<LiveTraffic />} />
            <Route path="/alerts" element={<Alerts />} />
            <Route path="/interfaces" element={<InterfaceMap />} />
            <Route path="/certificates" element={<CertificateManager />} />
            <Route path="/terminal" element={<SystemTerminal />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default App
