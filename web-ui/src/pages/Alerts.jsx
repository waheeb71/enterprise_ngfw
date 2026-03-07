import React from 'react';
import { useTranslation } from 'react-i18next';
import { useWebSocket } from '../hooks/useWebSocket';
import { Shield } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const Alerts = () => {
    const { t } = useTranslation();
    const { data } = useWebSocket(['alerts']);

    const handleBlockIP = async (ip) => {
        if (!confirm(`Are you sure you want to block all traffic from ${ip}?`)) return;
        try {
            await api.createRule({
                src_ip: ip,
                action: 'BLOCK',
                protocol: 'ALL',
                priority: 10 // high priority block
            });
            alert(`IP ${ip} blocked successfully.`);
        } catch (err) {
            console.error(err);
            alert("Failed to block IP.");
        }
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header">
                <h1 className="page-title">{t('security_alerts') || 'Security Alerts'}</h1>
                <p className="page-subtitle text-muted">Full Event History and Threat Triage</p>
            </header>

            <div className="glass-panel" style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--text-muted)' }}>
                            <th style={{ padding: '1rem' }}>Timestamp</th>
                            <th>Severity</th>
                            <th>Type</th>
                            <th>Source IP</th>
                            <th>Destination IP</th>
                            <th>Description</th>
                            <th style={{ textAlign: 'center' }}>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.alerts.length === 0 ? (
                            <tr><td colSpan="7" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>No alerts recorded in this session.</td></tr>
                        ) : data.alerts.map((alert, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                <td style={{ padding: '1rem', whiteSpace: 'nowrap' }}>{new Date(alert.timestamp).toLocaleString()}</td>
                                <td>
                                    <span style={{
                                        padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold', textTransform: 'uppercase',
                                        background: alert.severity === 'high' ? 'rgba(239, 68, 68, 0.2)' : alert.severity === 'medium' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(6, 182, 212, 0.2)',
                                        color: alert.severity === 'high' ? 'var(--danger)' : alert.severity === 'medium' ? 'var(--warning)' : 'var(--info)'
                                    }}>
                                        {alert.severity}
                                    </span>
                                </td>
                                <td style={{ fontWeight: 600 }}>{alert.alert_type}</td>
                                <td style={{ fontFamily: 'monospace' }}>{alert.source_ip}</td>
                                <td style={{ fontFamily: 'monospace' }}>{alert.destination_ip}</td>
                                <td style={{ color: 'var(--text-muted)' }}>{alert.description}</td>
                                <td style={{ textAlign: 'center' }}>
                                    <button
                                        onClick={() => handleBlockIP(alert.source_ip)}
                                        style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--danger)', color: 'var(--danger)', padding: '4px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.85rem' }}
                                    >
                                        Block IP
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Alerts;
