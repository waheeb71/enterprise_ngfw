import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Cpu, Activity, Globe, HardDrive, Shield, Server, PlugZap } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const ROLE_COLORS = {
    WAN: 'var(--primary-color)',
    LAN: 'var(--success)',
    DMZ: 'var(--warning)',
    MGMT: 'var(--info)',
    HA: 'var(--accent)',
    UNASSIGNED: 'rgba(255,255,255,0.2)'
};

const InterfaceMap = () => {
    const { t } = useTranslation();
    const [interfaces, setInterfaces] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const data = await api.getInterfaces();
            setInterfaces(data || []);
        } catch (err) {
            setError(err.message || 'Failed to map hardware interfaces.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000); // refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const handleRoleChange = async (interfaceName, newRole) => {
        setSaving(true);
        try {
            await api.assignInterfaceRole(interfaceName, newRole);

            // Immediate local update for UI snappy feel
            setInterfaces(prev => prev.map(iface =>
                iface.name === interfaceName ? { ...iface, role: newRole } : iface
            ));

        } catch (err) {
            alert(`Failed to assign role: ${err.message}`);
            // Revert on fail
            fetchData();
        } finally {
            setSaving(false);
        }
    };

    const getIconForRole = (role) => {
        switch (role) {
            case 'WAN': return <Globe size={24} style={{ color: ROLE_COLORS.WAN }} />;
            case 'LAN': return <HardDrive size={24} style={{ color: ROLE_COLORS.LAN }} />;
            case 'DMZ': return <Shield size={24} style={{ color: ROLE_COLORS.DMZ }} />;
            case 'MGMT': return <Server size={24} style={{ color: ROLE_COLORS.MGMT }} />;
            case 'HA': return <Activity size={24} style={{ color: ROLE_COLORS.HA }} />;
            default: return <PlugZap size={24} style={{ color: 'var(--text-muted)' }} />;
        }
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header" style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Cpu size={40} className="text-primary" style={{ filter: 'drop-shadow(0 0 10px var(--primary-glow))' }} />
                    <div>
                        <h1 className="page-title" style={{ margin: 0 }}>{t('hardware_map') || 'Network Interfaces'}</h1>
                        <p className="page-subtitle text-muted" style={{ margin: '0.2rem 0 0 0' }}>
                            Physical Port Discovery and Security Zone Assignment
                        </p>
                    </div>
                </div>
            </header>

            {error && (
                <div className="alert alert-danger" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.3)' }}>
                    <Activity size={20} />
                    {error}
                </div>
            )}

            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(0,0,0,0.3)' }}>
                    <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)' }}>
                        System Adapters & Zones
                    </h3>
                </div>

                {loading && interfaces.length === 0 ? (
                    <div style={{ padding: '4rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <Activity className="spin" size={32} style={{ margin: '0 auto 1rem', color: 'var(--primary-neon)' }} />
                        Scanning kernel network stack...
                    </div>
                ) : interfaces.length === 0 ? (
                    <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                        <PlugZap size={48} style={{ margin: '0 auto 1rem', color: 'rgba(255,255,255,0.1)' }} />
                        <h4 style={{ color: 'var(--text-muted)' }}>No network interfaces discovered</h4>
                    </div>
                ) : (
                    <div style={{ padding: '2rem' }}>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '1.5rem' }}>
                            {interfaces.map((iface, idx) => (
                                <div key={idx} className="glass-panel" style={{
                                    padding: '1.5rem',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: '1rem',
                                    borderTop: `4px solid ${ROLE_COLORS[iface.role] || ROLE_COLORS.UNASSIGNED}`,
                                    background: 'rgba(0,0,0,0.2)',
                                    position: 'relative',
                                    overflow: 'hidden'
                                }}>

                                    {/* Link Status Light */}
                                    <div style={{ position: 'absolute', top: '10px', right: '10px', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 'bold' }}>
                                            {iface.is_up ? 'LINK UP' : 'LINK DOWN'}
                                        </span>
                                        <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: iface.is_up ? 'var(--success)' : 'var(--danger)', boxShadow: `0 0 8px ${iface.is_up ? 'var(--success)' : 'var(--danger)'}` }} />
                                    </div>

                                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                        <div style={{
                                            padding: '1rem',
                                            background: 'rgba(255,255,255,0.05)',
                                            borderRadius: '12px'
                                        }}>
                                            {getIconForRole(iface.role)}
                                        </div>
                                        <div>
                                            <h2 style={{ margin: 0, fontSize: '1.5rem', fontFamily: 'monospace', color: 'white', letterSpacing: '1px' }}>
                                                {iface.name}
                                            </h2>
                                            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                                                MAC: <span style={{ fontFamily: 'monospace' }}>{iface.mac_address}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem', padding: '1rem', background: 'rgba(0,0,0,0.3)', borderRadius: '8px' }}>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>IPv4 Address</div>
                                            <div style={{ fontFamily: 'monospace', fontWeight: 'bold', color: iface.ip_address ? 'var(--primary-neon)' : 'rgba(255,255,255,0.2)' }}>
                                                {iface.ip_address || 'Unassigned'}
                                            </div>
                                        </div>
                                        <div>
                                            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Speed / MTU</div>
                                            <div style={{ fontFamily: 'monospace', fontWeight: 'bold', color: 'white' }}>
                                                {iface.speed > 0 ? `${iface.speed} Mbps` : 'Auto'} / {iface.mtu}
                                            </div>
                                        </div>
                                    </div>

                                    <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                                        <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>
                                            Zone / Role Assignment
                                        </label>
                                        <select
                                            className="form-control"
                                            value={iface.role}
                                            onChange={(e) => handleRoleChange(iface.name, e.target.value)}
                                            disabled={saving}
                                            style={{
                                                width: '100%', padding: '0.6rem', background: '#111827',
                                                border: `1px solid ${ROLE_COLORS[iface.role] || 'rgba(255,255,255,0.1)'}`,
                                                color: '#fff', borderRadius: '4px', fontWeight: 'bold'
                                            }}
                                        >
                                            <option value="UNASSIGNED">Unassigned (Passthrough)</option>
                                            <option value="WAN">WAN (External Internet)</option>
                                            <option value="LAN">LAN (Internal Transport)</option>
                                            <option value="DMZ">DMZ (Demilitarized Zone)</option>
                                            <option value="MGMT">MGMT (Management Interface)</option>
                                            <option value="HA">HA (High Availability Sync)</option>
                                        </select>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default InterfaceMap;
