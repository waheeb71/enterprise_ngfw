import React from 'react';
import { useTranslation } from 'react-i18next';
import { ServerCrash, Cpu, Activity, Database } from 'lucide-react';
import { useWebSocket } from '../hooks/useWebSocket';
import '../Pages.css';

const SystemHA = () => {
    const { t } = useTranslation();
    const { data } = useWebSocket(['stats']);

    const stats = data.stats || {
        cpu_usage: 0,
        memory_usage: 0,
        active_connections: 0,
        ha_state: 'UNKNOWN',
        ha_peer: 'Disconnected',
        ha_priority: 0
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header">
                <h1 className="page-title">{t('system_ha')}</h1>
                <p className="page-subtitle text-muted">Active-Passive Cluster Management</p>
            </header>

            <div className="metrics-grid">
                <div className="metric-card glass-panel" style={{ borderColor: stats.ha_state === 'MASTER' ? 'var(--primary-glow)' : '' }}>
                    <div className="metric-header">
                        <h3>{t('ha_master')} (Local Node)</h3>
                        <span className={`status-dot ${stats.ha_state === 'MASTER' ? 'active' : 'warning'}`}></span>
                    </div>
                    <div className={`metric-value ${stats.ha_state === 'MASTER' ? 'safe-text' : 'text-muted'}`} style={{ fontSize: '1.5rem' }}>
                        {stats.ha_state}
                    </div>
                    <p className="metric-sub text-muted">Priority: {stats.ha_priority}</p>
                </div>

                <div className="metric-card glass-panel">
                    <div className="metric-header">
                        <h3>{t('ha_backup')} (Peer Node)</h3>
                        <span className={`status-dot ${stats.ha_peer !== 'Disconnected' ? 'active' : 'error'}`} style={stats.ha_peer !== 'Disconnected' ? { backgroundColor: 'var(--info)', boxShadow: '0 0 10px var(--info)' } : {}}></span>
                    </div>
                    <div className="metric-value info-text" style={{ fontSize: '1.5rem' }}>{stats.ha_peer !== 'Disconnected' ? 'ONLINE' : 'OFFLINE'}</div>
                    <p className="metric-sub text-muted">IP: {stats.ha_peer}</p>
                </div>
            </div>

            <div className="dashboard-content" style={{ gridTemplateColumns: '1fr' }}>
                <div className="events-section glass-panel">
                    <h3>System Resources & State Sync</h3>
                    <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', marginTop: '1.5rem' }}>
                        <div style={{ flex: 1, minWidth: '200px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <Cpu size={32} color="var(--primary-neon)" />
                            <div>
                                <h4 style={{ margin: 0 }}>CPU Usage</h4>
                                <p className="text-muted" style={{ margin: 0 }}>{stats.cpu_usage || 0}% (System Load)</p>
                            </div>
                        </div>
                        <div style={{ flex: 1, minWidth: '200px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <Database size={32} color="var(--info)" />
                            <div>
                                <h4 style={{ margin: 0 }}>Memory Usage</h4>
                                <p className="text-muted" style={{ margin: 0 }}>{stats.memory_usage || 0}% (RAM)</p>
                            </div>
                        </div>
                        <div style={{ flex: 1, minWidth: '200px', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <Activity size={32} color="var(--primary-neon)" />
                            <div>
                                <h4 style={{ margin: 0 }}>Heartbeat</h4>
                                <p className="text-muted" style={{ margin: 0 }}>OK (Last: 0.5s ago)</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SystemHA;
