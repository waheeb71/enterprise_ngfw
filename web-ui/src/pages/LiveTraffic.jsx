import React from 'react';
import { useTranslation } from 'react-i18next';
import { useWebSocket } from '../hooks/useWebSocket';
import '../Pages.css';

const LiveTraffic = () => {
    const { t } = useTranslation();
    const { data } = useWebSocket(['traffic']);

    const formatBytes = (bytes) => {
        if (!bytes) return '0 B';
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / 1048576).toFixed(1) + ' MB';
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">{t('live_traffic') || 'Live Traffic Flows'}</h1>
                    <p className="page-subtitle text-muted">Real-time packet inspection queue</p>
                </div>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    <span className="status-dot active"></span> Tracking {data.traffic.length} recent flows
                </div>
            </header>

            <div className="glass-panel" style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                    <thead>
                        <tr style={{ background: 'rgba(59, 130, 246, 0.04)', borderBottom: '1px solid var(--glass-border)', color: 'var(--text-muted)' }}>
                            <th style={{ padding: '1rem' }}>Time</th>
                            <th>Source</th>
                            <th>Destination</th>
                            <th>Port</th>
                            <th>Protocol</th>
                            <th>Volume</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.traffic.length === 0 ? (
                            <tr><td colSpan="7" style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>Waiting for packet flows streams...</td></tr>
                        ) : data.traffic.map((flow, idx) => (
                            <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.02)', transition: 'background 0.2s', ':hover': { background: 'rgba(59, 130, 246, 0.04)' } }}>
                                <td style={{ padding: '1rem', whiteSpace: 'nowrap', color: 'var(--text-dim)' }}>{new Date(flow.timestamp || Date.now()).toLocaleTimeString()}</td>
                                <td style={{ fontFamily: 'monospace' }}>{flow.src_ip}</td>
                                <td style={{ fontFamily: 'monospace' }}>{flow.dst_ip}</td>
                                <td>{flow.dst_port}</td>
                                <td><span style={{ padding: '2px 6px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', fontSize: '0.8rem' }}>{flow.protocol || 'TCP'}</span></td>
                                <td>{formatBytes(flow.bytes)}</td>
                                <td>
                                    <span style={{
                                        padding: '4px 8px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold',
                                        background: flow.action === 'ALLOW' ? 'rgba(16, 185, 129, 0.15)' : flow.action === 'BLOCK' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                                        color: flow.action === 'ALLOW' ? 'var(--success)' : flow.action === 'BLOCK' ? 'var(--danger)' : 'var(--warning)'
                                    }}>
                                        {flow.action || 'ALLOW'}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default LiveTraffic;
