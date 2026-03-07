import React from 'react';
import { NavLink } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    Activity,
    Network,
    Gauge,
    ServerCrash,
    Settings,
    Globe,
    Cpu,
    ShieldCheck,
    Terminal
} from 'lucide-react';
import './Sidebar.css';
import logoImage from '../assets/logo.png';

const Sidebar = () => {
    const { t } = useTranslation();

    const navItems = [
        { path: '/', label: 'dashboard', icon: <Gauge size={22} /> },
        { path: '/traffic', label: 'live_traffic', icon: <Globe size={22} /> },
        { path: '/rules', label: 'firewall_rules', icon: <ClipboardList size={22} /> },
        { path: '/alerts', label: 'security_alerts', icon: <Bell size={22} /> },
        { path: '/ai-pipeline', label: 'ai_inspection', icon: <BrainCircuit size={22} /> },
        { path: '/vpn', label: 'vpn_manager', icon: <Network size={22} /> },
        { path: '/qos', label: 'qos_traffic', icon: <Activity size={22} /> },
        { path: '/ha', label: 'system_ha', icon: <ServerCrash size={22} /> },
        { path: '/interfaces', label: 'hardware_map', icon: <Cpu size={22} /> },
        { path: '/certificates', label: 'certificate_manager', icon: <ShieldCheck size={22} /> },
        { path: '/terminal', label: 'system_terminal', icon: <Terminal size={22} /> },
        { path: '/system', label: 'system_management', icon: <Settings size={22} /> },
    ];

    return (
        <aside className="sidebar glass-panel">
            <div className="sidebar-brand">
                <div className="brand-logo" style={{ background: 'transparent', boxShadow: 'none' }}>
                    <img src={logoImage} alt="CyberNexus Logo" style={{ width: '40px', height: '40px', objectFit: 'contain' }} />
                </div>
                <h2 className="brand-title text-gradient" style={{ background: 'linear-gradient(90deg, #FFDF40, #D4AF37)', WebkitBackgroundClip: 'text' }}>CyberNexus</h2>
            </div>

            <nav className="sidebar-nav">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        <span className="nav-label">{t(item.label)}</span>
                        <div className="active-indicator"></div>
                    </NavLink>
                ))}
            </nav>

            <div className="sidebar-footer">
                <div className="status-container">
                    <span className="status-dot active"></span>
                    <span className="status-text">{t('system_healthy')}</span>
                </div>
            </div>
        </aside>
    );
};

export default Sidebar;
