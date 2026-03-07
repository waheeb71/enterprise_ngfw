import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useWebSocket } from '../hooks/useWebSocket';
import '../Pages.css';

const Dashboard = () => {
    const { t } = useTranslation();
    const { data, isConnected } = useWebSocket(['stats', 'alerts']);
    const [chartBars, setChartBars] = useState(Array(15).fill(10));

    // Format bytes to human readable
    const formatBytes = (bytes) => {
        if (!bytes) return '0 B/s';
        const k = 1024;
        const sizes = ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s'];
        const i = Math.floor(Math.log(Math.max(1, bytes)) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const stats = data.stats || {
        bytes_per_second: 0,
        blocked_count: 0,
        active_connections: 0,
        anomaly_count: 0
    };

    // Update mock chart based on real-time traffic volume
    useEffect(() => {
        if (stats.bytes_per_second > 0) {
            const volume = Math.min(100, Math.max(10, (stats.bytes_per_second / 1024 / 1024) * 100)); // normalized to MBs
            setChartBars(prev => {
                const newBars = [...prev.slice(1), volume];
                return newBars;
            });
        }
    }, [stats.bytes_per_second]);

    return (
        <div className="page-container fadeIn">
            <header className="page-header">
                <h1 className="page-title">{t('dashboard')}</h1>
                <p className="page-subtitle text-muted">{t('enterprise_ngfw')} - Overview</p>
            </header>

            <div className="metrics-grid">
                <div className="metric-card glass-panel">
                    <div className="metric-header">
                        <h3>{t('live_traffic')}</h3>
                        <span className={`status-dot ${isConnected ? 'active' : 'error'}`}></span>
                    </div>
                    <div className="metric-value text-gradient">{formatBytes(stats.bytes_per_second)}</div>
                    <p className="metric-sub text-muted">Total Throughput</p>
                </div>

                <div className="metric-card glass-panel">
                    <div className="metric-header">
                        <h3>{t('threats_blocked')}</h3>
                    </div>
                    <div className="metric-value danger-text">{stats.blocked_count.toLocaleString()}</div>
                    <p className="metric-sub text-muted">Session Blocks</p>
                </div>

                <div className="metric-card glass-panel">
                    <div className="metric-header">
                        <h3>{t('active_connections')}</h3>
                    </div>
                    <div className="metric-value info-text">{stats.active_connections.toLocaleString()}</div>
                    <p className="metric-sub text-muted">Live Flows</p>
                </div>

                <div className="metric-card glass-panel">
                    <div className="metric-header">
                        <h3>{t('ai_confidence')}</h3>
                    </div>
                    <div className="metric-value ai-text">{stats.anomaly_count.toLocaleString()}</div>
                    <p className="metric-sub text-muted">Session Anomalies Detected</p>
                </div>
            </div>

            <div className="dashboard-content">
                <div className="chart-section glass-panel">
                    <h3>Live Traffic Volume (Real-time Flow)</h3>
                    <div className="mock-chart">
                        {chartBars.map((height, i) => (
                            <div
                                key={i}
                                className={`chart-bar ${height > 80 ? 'danger' : height > 60 ? 'warning' : ''}`}
                                style={{ height: `${height}%`, width: `${(100 / chartBars.length) - 2}%` }}
                            ></div>
                        ))}
                    </div>
                </div>

                <div className="events-section glass-panel">
                    <h3>{t('recent_events')}</h3>
                    <ul className="event-list">
                        {data.alerts.length === 0 ? (
                            <p className="text-muted" style={{ padding: '1rem', textAlign: 'center' }}>Waiting for alerts stream...</p>
                        ) : (
                            data.alerts.slice(0, 5).map((alert, idx) => (
                                <li key={idx} className={`event-item ${alert.severity === 'high' ? 'block' : 'ai'}`}>
                                    <span className="event-time">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                                    <span className="event-ip">{alert.source_ip}</span>
                                    <span className={`event-action ${alert.severity === 'high' ? 'danger-text' : 'ai-text'}`}>
                                        {alert.alert_type}
                                    </span>
                                </li>
                            ))
                        )}
                    </ul>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
