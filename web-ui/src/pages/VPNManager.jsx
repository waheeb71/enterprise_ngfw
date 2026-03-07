import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Network, Activity, Plus, ShieldAlert, Trash2, Key, Globe, Wifi, WifiOff } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const VPNManager = () => {
    const { t } = useTranslation();
    const [status, setStatus] = useState(null);
    const [peers, setPeers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [isAddModalOpen, setIsAddModalOpen] = useState(false);

    // Form State
    const [newPeer, setNewPeer] = useState({
        public_key: '',
        allowed_ips: '',
        endpoint: '',
        preshared_key: '',
        persistent_keepalive: 25
    });

    const fetchData = async () => {
        setLoading(true);
        setError('');
        try {
            const [statusRes, peersRes] = await Promise.all([
                api.getVpnStatus(),
                api.getVpnPeers()
            ]);
            setStatus(statusRes);
            setPeers(peersRes.peers || []);
        } catch (err) {
            setError(err.message || 'Failed to fetch VPN data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        // Poll every 30 seconds for status updates
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleAddPeer = async (e) => {
        e.preventDefault();
        setError('');
        try {
            // Need to convert comma separated string to array for allowed_ips
            const formattedPeer = {
                ...newPeer,
                allowed_ips: newPeer.allowed_ips.split(',').map(ip => ip.trim()).filter(ip => ip),
                endpoint: newPeer.endpoint || null,
                preshared_key: newPeer.preshared_key || null
            };

            await api.addVpnPeer(formattedPeer);
            setIsAddModalOpen(false);
            setNewPeer({
                public_key: '', allowed_ips: '', endpoint: '', preshared_key: '', persistent_keepalive: 25
            });
            await fetchData(); // Refresh list
        } catch (err) {
            setError(err.message || 'Failed to add peer.');
        }
    };

    const handleRemovePeer = async (publicKey) => {
        if (!window.confirm(`Are you sure you want to remove peer ${publicKey}?`)) return;

        setError('');
        try {
            await api.removeVpnPeer(publicKey);
            await fetchData(); // Refresh list
        } catch (err) {
            setError(err.message || 'Failed to remove peer.');
        }
    };

    const isOnline = status?.status === 'running' || status?.status?.toLowerCase().includes('up');

    return (
        <div className="page-container fadeIn">
            <header className="page-header">
                <div>
                    <h1 className="page-title">{t('vpn_manager') || 'WireGuard VPN'}</h1>
                    <p className="page-subtitle text-muted">Manage secure site-to-site and remote access tunnels</p>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => setIsAddModalOpen(true)}
                >
                    <Plus size={18} /> Add New Peer
                </button>
            </header>

            {error && (
                <div className="alert alert-danger" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.3)' }}>
                    <ShieldAlert size={20} />
                    {error}
                </div>
            )}

            {/* Status Banner */}
            <div className="glass-panel" style={{ padding: '2rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <div style={{
                        width: '64px', height: '64px', borderRadius: '50%',
                        background: isOnline ? 'var(--primary-glow)' : 'rgba(239,68,68,0.2)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: isOnline ? 'var(--primary-neon)' : '#ef4444'
                    }}>
                        {isOnline ? <Wifi size={32} /> : <WifiOff size={32} />}
                    </div>
                    <div>
                        <h2 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            Gateway Status:
                            <span style={{ color: isOnline ? 'var(--primary-neon)' : '#ef4444' }}>
                                {isOnline ? 'Online' : 'Offline'}
                            </span>
                        </h2>
                        <p className="text-muted" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <Network size={16} />
                            Interface: <strong style={{ color: 'white' }}>{status?.interface || 'wg0'}</strong>
                        </p>
                    </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--primary-neon)', textShadow: '0 0 10px var(--primary-glow)' }}>
                        {peers.length}
                    </div>
                    <div className="text-muted">Connected Peers</div>
                </div>
            </div>

            {/* Peers Table */}
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(0,0,0,0.2)' }}>
                    <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Globe size={20} className="text-primary" /> Active Connections
                    </h3>
                </div>

                {loading ? (
                    <div style={{ padding: '3rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                        <Activity className="spin" size={32} style={{ margin: '0 auto 1rem', color: 'var(--primary-neon)' }} />
                        Loading network topological data...
                    </div>
                ) : peers.length === 0 ? (
                    <div style={{ padding: '4rem 2rem', textAlign: 'center' }}>
                        <Network size={48} style={{ margin: '0 auto 1rem', color: 'rgba(255,255,255,0.1)' }} />
                        <h4 style={{ color: 'var(--text-muted)' }}>No peers configured</h4>
                        <p className="text-muted" style={{ fontSize: '0.9rem' }}>Click "Add New Peer" to establish a secure tunnel.</p>
                    </div>
                ) : (
                    <div className="table-responsive">
                        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                            <thead>
                                <tr style={{ backgroundColor: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                    <th style={{ padding: '1rem 1.5rem' }}>Public Key</th>
                                    <th style={{ padding: '1rem 1.5rem' }}>Endpoint</th>
                                    <th style={{ padding: '1rem 1.5rem' }}>Allowed IPs</th>
                                    <th style={{ padding: '1rem 1.5rem' }}>Keepalive</th>
                                    <th style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {peers.map((peer, idx) => (
                                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s', ':hover': { backgroundColor: 'rgba(255,255,255,0.02)' } }}>
                                        <td style={{ padding: '1rem 1.5rem', fontFamily: 'monospace', color: 'var(--primary-neon)' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <Key size={14} className="text-muted" />
                                                {peer.public_key.substring(0, 16)}...
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem 1.5rem' }}>
                                            {peer.endpoint ? (
                                                <span style={{ background: 'rgba(255,255,255,0.1)', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.9rem' }}>
                                                    {peer.endpoint}
                                                </span>
                                            ) : (
                                                <span className="text-muted" style={{ fontStyle: 'italic' }}>Dynamic</span>
                                            )}
                                        </td>
                                        <td style={{ padding: '1rem 1.5rem' }}>
                                            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                                                {peer.allowed_ips.map(ip => (
                                                    <span key={ip} style={{ background: 'var(--primary-glow)', color: 'white', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.85rem', border: '1px solid var(--primary-color)' }}>
                                                        {ip}
                                                    </span>
                                                ))}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem 1.5rem', color: 'var(--text-muted)' }}>
                                            {peer.persistent_keepalive}s
                                        </td>
                                        <td style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>
                                            <button
                                                className="btn-icon"
                                                style={{ color: '#ef4444', background: 'rgba(239,68,68,0.1)' }}
                                                onClick={() => handleRemovePeer(peer.public_key)}
                                                title="Revoke Peer"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Add Peer Modal */}
            {isAddModalOpen && (
                <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="glass-panel" style={{ width: '100%', maxWidth: '500px', padding: 0, transform: 'scale(1)', transition: 'all 0.3s' }}>
                        <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: 0, color: 'var(--primary-neon)' }}>Add WireGuard Peer</h3>
                            <button className="btn-icon" onClick={() => setIsAddModalOpen(false)}>×</button>
                        </div>
                        <form onSubmit={handleAddPeer} style={{ padding: '1.5rem' }}>
                            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Public Key (Required)</label>
                                <input
                                    type="text"
                                    required
                                    className="form-control"
                                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'white', fontFamily: 'monospace' }}
                                    placeholder="e.g., xTIBA5rboUvnH4htodjb6e697QjLERt1NAB4mZqp8Ro="
                                    value={newPeer.public_key}
                                    onChange={e => setNewPeer({ ...newPeer, public_key: e.target.value })}
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Allowed IPs (Comma separated)</label>
                                <input
                                    type="text"
                                    required
                                    className="form-control"
                                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'white' }}
                                    placeholder="e.g., 10.0.0.2/32, 192.168.2.0/24"
                                    value={newPeer.allowed_ips}
                                    onChange={e => setNewPeer({ ...newPeer, allowed_ips: e.target.value })}
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Endpoint (Optional)</label>
                                <input
                                    type="text"
                                    className="form-control"
                                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'white' }}
                                    placeholder="e.g., 203.0.113.5:51820"
                                    value={newPeer.endpoint}
                                    onChange={e => setNewPeer({ ...newPeer, endpoint: e.target.value })}
                                />
                            </div>
                            <div className="form-group" style={{ marginBottom: '2rem' }}>
                                <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-muted)' }}>Persistent Keepalive (Seconds)</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '4px', color: 'white' }}
                                    value={newPeer.persistent_keepalive}
                                    onChange={e => setNewPeer({ ...newPeer, persistent_keepalive: parseInt(e.target.value) })}
                                />
                            </div>

                            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                                <button type="button" className="btn btn-secondary" style={{ background: 'rgba(255,255,255,0.1)', color: 'white', padding: '0.8rem 1.5rem', border: 'none', borderRadius: '4px', cursor: 'pointer' }} onClick={() => setIsAddModalOpen(false)}>
                                    Cancel
                                </button>
                                <button type="submit" className="btn btn-primary" style={{ background: 'var(--primary-color)', color: 'white', padding: '0.8rem 1.5rem', border: 'none', borderRadius: '4px', cursor: 'pointer', boxShadow: '0 0 10px var(--primary-glow)' }}>
                                    Confirm & Activate
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

        </div>
    );
};

export default VPNManager;
