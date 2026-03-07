import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, Gauge, HardDrive, ShieldAlert, Zap, Save } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const QoSTraffic = () => {
    const { t } = useTranslation();
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    // Status object
    const [qosConfig, setQosConfig] = useState({
        enabled: false,
        default_user_rate_bytes: 5242880, // 5 MB/s
        default_user_burst_bytes: 10485760 // 10 MB
    });

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await api.getQoSConfig();
            setQosConfig({
                enabled: data.enabled !== undefined ? data.enabled : false,
                default_user_rate_bytes: data.default_user_rate_bytes || 5242880,
                default_user_burst_bytes: data.default_user_burst_bytes || 10485760
            });
        } catch (err) {
            setError(err.message || 'Failed to fetch QoS settings. Engine may be offline.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const handleSave = async (e) => {
        e.preventDefault();
        setSaving(true);
        setError('');
        setSuccess('');

        try {
            const response = await api.updateQoSConfig(qosConfig);
            setSuccess(response.message || 'Settings applied successfully.');
            // Re-fetch to normalize
            await fetchData();
            setTimeout(() => setSuccess(''), 5000);
        } catch (err) {
            setError(err.message || 'Failed to save QoS settings.');
        } finally {
            setSaving(false);
        }
    };

    // Helper conversions for UI
    const getMBytes = (bytes) => (bytes / (1024 * 1024)).toFixed(1);

    return (
        <div className="page-container fadeIn">
            <header className="page-header">
                <div>
                    <h1 className="page-title">{t('qos_traffic') || 'Quality of Service (QoS)'}</h1>
                    <p className="page-subtitle text-muted">Bandwidth Throttling, Traffic Shaping, and Token Buckets</p>
                </div>
            </header>

            {error && (
                <div className="alert alert-danger" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.3)' }}>
                    <ShieldAlert size={20} />
                    {error}
                </div>
            )}

            {success && (
                <div className="alert alert-success" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    <Zap size={20} />
                    {success}
                </div>
            )}

            <div className="dashboard-grid" style={{ gridTemplateColumns: '1fr 2fr', alignItems: 'start', gap: '2rem' }}>

                {/* Left Panel: Status & Toggle */}
                <div className="glass-panel" style={{ padding: '2rem', display: 'flex', flexDirection: 'column', height: '100%' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                        <div style={{
                            width: '48px', height: '48px', borderRadius: '50%',
                            background: qosConfig.enabled ? 'var(--primary-glow)' : 'rgba(255,255,255,0.05)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: qosConfig.enabled ? 'var(--primary-neon)' : 'var(--text-muted)',
                            transition: 'all 0.3s'
                        }}>
                            <Activity size={24} />
                        </div>
                        <div>
                            <h2 style={{ margin: '0 0 0.2rem 0', fontSize: '1.2rem' }}>Traffic Shaping</h2>
                            <span style={{ color: qosConfig.enabled ? 'var(--primary-neon)' : 'var(--text-muted)' }}>
                                {qosConfig.enabled ? 'Active/Enforcing' : 'Disabled (Passthrough)'}
                            </span>
                        </div>
                    </div>

                    <p className="text-muted" style={{ lineHeight: '1.6', flex: 1 }}>
                        When Quality of Service (QoS) is enabled, the Enterprise NGFW utilizes the highly efficient Token Bucket algorithm within the Policy Manager to throttle excessive bandwidth consumption per IP address automatically.
                    </p>

                    <div style={{ marginTop: 'auto', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                        <label className="toggle-switch" style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
                            <input
                                type="checkbox"
                                checked={qosConfig.enabled}
                                onChange={(e) => setQosConfig({ ...qosConfig, enabled: e.target.checked })}
                                style={{ display: 'none' }}
                            />
                            <div className="slider-bg" style={{
                                width: '50px', height: '26px', background: qosConfig.enabled ? 'var(--primary-color)' : 'rgba(255,255,255,0.2)',
                                borderRadius: '13px', position: 'relative', transition: '0.3s'
                            }}>
                                <div className="slider-knob" style={{
                                    width: '20px', height: '20px', background: 'white', borderRadius: '50%',
                                    position: 'absolute', top: '3px', left: qosConfig.enabled ? '27px' : '3px', transition: '0.3s'
                                }} />
                            </div>
                            <span style={{ fontWeight: '500' }}>Master QoS Power</span>
                        </label>
                    </div>
                </div>

                {/* Right Panel: Configuration Limits */}
                <div className="glass-panel" style={{ padding: '0' }}>
                    <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(0,0,0,0.2)' }}>
                        <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Gauge size={20} className="text-primary" /> Bandwidth Limits & Parameters
                        </h3>
                    </div>

                    <form onSubmit={handleSave} style={{ padding: '2rem' }}>

                        <div className="form-group" style={{ marginBottom: '2.5rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', fontWeight: '500' }}>
                                    <Activity size={18} className="text-muted" /> Default User Rate (Speed Limit)
                                </label>
                                <span style={{ color: 'var(--primary-neon)', fontWeight: 'bold' }}>{getMBytes(qosConfig.default_user_rate_bytes)} MB/s</span>
                            </div>
                            <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                                The maximum sustained download speed allowed per single active internal IP.
                            </p>

                            <input
                                type="range"
                                min="104857" // 100 KB/s
                                max="104857600" // 100 MB/s
                                step="104857" // 100 KB Steps
                                disabled={!qosConfig.enabled}
                                value={qosConfig.default_user_rate_bytes}
                                onChange={(e) => setQosConfig({ ...qosConfig, default_user_rate_bytes: parseInt(e.target.value) })}
                                style={{ width: '100%', accentColor: 'var(--primary-color)', opacity: qosConfig.enabled ? 1 : 0.5 }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                <span>100 KB/s</span>
                                <span>100 MB/s</span>
                            </div>
                        </div>

                        <div className="form-group" style={{ marginBottom: '3rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.1rem', fontWeight: '500' }}>
                                    <HardDrive size={18} className="text-muted" /> Burst Tolerance Bucket
                                </label>
                                <span style={{ color: 'var(--primary-neon)', fontWeight: 'bold' }}>{getMBytes(qosConfig.default_user_burst_bytes)} MB</span>
                            </div>
                            <p className="text-muted" style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>
                                How much data a user can instantly download (burst) before the continuous speed limit is rigorously applied.
                            </p>

                            <input
                                type="range"
                                min="1048576" // 1 MB
                                max="52428800" // 50 MB
                                step="1048576" // 1 MB steps
                                disabled={!qosConfig.enabled}
                                value={qosConfig.default_user_burst_bytes}
                                onChange={(e) => setQosConfig({ ...qosConfig, default_user_burst_bytes: parseInt(e.target.value) })}
                                style={{ width: '100%', accentColor: 'var(--primary-color)', opacity: qosConfig.enabled ? 1 : 0.5 }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                                <span>1 MB</span>
                                <span>50 MB</span>
                            </div>
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                            <button
                                type="submit"
                                className="btn btn-primary"
                                disabled={saving}
                                style={{
                                    background: 'var(--primary-color)', color: 'black', fontWeight: 'bold',
                                    padding: '0.8rem 2rem', border: 'none', borderRadius: '4px', cursor: 'pointer',
                                    boxShadow: '0 0 15px var(--primary-glow)', display: 'flex', gap: '0.5rem', alignItems: 'center'
                                }}
                            >
                                <Save size={18} />
                                {saving ? 'Applying...' : 'Apply Config'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default QoSTraffic;
