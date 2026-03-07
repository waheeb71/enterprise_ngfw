import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Shield, Plus, Trash2, Clock, Box, FileText, Map } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const FirewallRules = () => {
    const { t } = useTranslation();
    const [rules, setRules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);

    // Form state
    const [newRule, setNewRule] = useState({
        src_ip: '',
        dst_port: '',
        protocol: 'TCP',
        zone_src: 'ANY',
        zone_dst: 'ANY',
        app_category: 'ANY',
        file_type: 'ANY',
        schedule: 'ALWAYS',
        action: 'BLOCK',
        priority: 50
    });

    useEffect(() => {
        loadRules();
    }, []);

    const loadRules = async () => {
        try {
            setLoading(true);
            const data = await api.getRules();
            setRules(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Failed to fetch rules", error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddRule = async (e) => {
        e.preventDefault();
        try {
            const rulePayload = {
                ...newRule,
                dst_port: newRule.dst_port ? parseInt(newRule.dst_port) : null,
                priority: parseInt(newRule.priority)
            };
            // Clean empty strings
            if (!rulePayload.src_ip) delete rulePayload.src_ip;
            if (!rulePayload.dst_port) delete rulePayload.dst_port;

            await api.createRule(rulePayload);
            setShowModal(false);
            setNewRule({
                src_ip: '', dst_port: '', protocol: 'TCP',
                zone_src: 'ANY', zone_dst: 'ANY', app_category: 'ANY',
                file_type: 'ANY', schedule: 'ALWAYS', action: 'BLOCK', priority: 50
            });
            loadRules(); // reload
        } catch (error) {
            console.error("Failed to add rule", error);
            alert("Error adding rule: " + error.message);
        }
    };

    const handleDelete = async (ruleId) => {
        if (!window.confirm("Are you sure you want to delete this rule?")) return;
        try {
            await api.deleteRule(ruleId);
            loadRules();
        } catch (error) {
            console.error("Failed to delete rule", error);
        }
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
                        <Shield size={28} className="text-primary" /> {t('firewall_rules') || 'Advanced Firewall Rules'}
                    </h1>
                    <p className="page-subtitle text-muted">Manage Zero-Trust Access Control Lists (Zones, DPI, Schedules)</p>
                </div>
                <button
                    onClick={() => setShowModal(true)}
                    style={{ background: 'var(--primary-neon)', color: 'black', border: 'none', padding: '0.6rem 1.2rem', borderRadius: '4px', display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 0 10px var(--primary-glow)' }}
                >
                    <Plus size={18} /> Add Policy
                </button>
            </header>

            <div className="glass-panel" style={{ overflowX: 'auto', padding: 0 }}>
                {loading ? (
                    <p className="text-muted" style={{ padding: '3rem', textAlign: 'center' }}>Loading policies from kernel...</p>
                ) : (
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead>
                            <tr style={{ backgroundColor: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                <th style={{ padding: '1rem 1.5rem' }}>Zone Direction</th>
                                <th style={{ padding: '1rem 1.5rem' }}>Source & Port</th>
                                <th style={{ padding: '1rem 1.5rem' }}>App / File Type</th>
                                <th style={{ padding: '1rem 1.5rem' }}>Schedule</th>
                                <th style={{ padding: '1rem 1.5rem' }}>Action</th>
                                <th style={{ textAlign: 'right', padding: '1rem 1.5rem' }}>Manage</th>
                            </tr>
                        </thead>
                        <tbody>
                            {rules.length === 0 ? (
                                <tr>
                                    <td colSpan="6" style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                        <Shield size={48} style={{ margin: '0 auto 1rem', opacity: 0.2 }} />
                                        <p>No custom policies configured. Implicit Deny is active.</p>
                                    </td>
                                </tr>
                            ) : rules.map((r, idx) => (
                                <tr key={r.rule_id || idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', transition: 'background 0.2s', ':hover': { backgroundColor: 'rgba(255,255,255,0.02)' } }}>
                                    <td style={{ padding: '1rem 1.5rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Map size={14} className="text-muted" />
                                            <span style={{ color: 'var(--primary-color)' }}>{r.zone_src || 'ANY'}</span>
                                            <span className="text-muted">→</span>
                                            <span style={{ color: 'var(--primary-color)' }}>{r.zone_dst || 'ANY'}</span>
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem 1.5rem' }}>
                                        <div>{r.src_ip || 'ANY IP'}</div>
                                        <div className="text-muted" style={{ fontSize: '0.85rem' }}>
                                            {r.protocol || 'ALL'} : {r.dst_port || 'ANY PORT'}
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem 1.5rem' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                                                <Box size={14} className="text-muted" /> {r.app_category || 'ANY APP'}
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem' }} className="text-muted">
                                                <FileText size={14} /> {r.file_type || 'ANY FILE'}
                                            </div>
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem 1.5rem' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                                            <Clock size={14} /> {r.schedule || 'ALWAYS'}
                                        </div>
                                    </td>
                                    <td style={{ padding: '1rem 1.5rem' }}>
                                        <span style={{
                                            padding: '4px 10px', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 'bold', textShadow: '0 0 5px rgba(0,0,0,0.5)',
                                            background: r.action === 'ALLOW' ? 'rgba(16, 185, 129, 0.2)' : r.action === 'BLOCK' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                                            color: r.action === 'ALLOW' ? 'var(--success)' : r.action === 'BLOCK' ? 'var(--danger)' : 'var(--warning)',
                                            border: `1px solid ${r.action === 'ALLOW' ? 'var(--success)' : r.action === 'BLOCK' ? 'var(--danger)' : 'var(--warning)'}`
                                        }}>
                                            {r.action}
                                        </span>
                                    </td>
                                    <td style={{ textAlign: 'right', padding: '1rem 1.5rem' }}>
                                        <button
                                            onClick={() => handleDelete(r.rule_id)}
                                            className="btn-icon"
                                            style={{ color: 'var(--danger)', background: 'rgba(239,68,68,0.1)' }}
                                            title="Delete Policy"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Advanced Modal */}
            {showModal && (
                <div className="modal-overlay" style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(5px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, overflowY: 'auto', padding: '2rem' }}>
                    <div className="glass-panel" style={{ width: '100%', maxWidth: '700px', padding: 0 }}>
                        <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h3 style={{ margin: 0, color: 'var(--primary-neon)' }}>Create Advanced Policy</h3>
                            <button className="btn-icon" onClick={() => setShowModal(false)}>×</button>
                        </div>

                        <form onSubmit={handleAddRule} style={{ padding: '2rem' }}>

                            <h4 style={{ color: 'var(--text-muted)', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>1. Network & Zones</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Source Zone</label>
                                    <select value={newRule.zone_src} onChange={e => setNewRule({ ...newRule, zone_src: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                        <option value="ANY">ANY</option>
                                        <option value="LAN">LAN</option>
                                        <option value="WAN">WAN</option>
                                        <option value="DMZ">DMZ</option>
                                        <option value="VPN">VPN</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Destination Zone</label>
                                    <select value={newRule.zone_dst} onChange={e => setNewRule({ ...newRule, zone_dst: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                        <option value="ANY">ANY</option>
                                        <option value="LAN">LAN</option>
                                        <option value="WAN">WAN</option>
                                        <option value="DMZ">DMZ</option>
                                        <option value="VPN">VPN</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Source IP / CIDR (Optional)</label>
                                    <input type="text" value={newRule.src_ip} onChange={e => setNewRule({ ...newRule, src_ip: e.target.value })} placeholder="e.g. 192.168.1.0/24" className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }} />
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Protocol</label>
                                        <select value={newRule.protocol} onChange={e => setNewRule({ ...newRule, protocol: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: '#111827', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                            <option value="ALL">ALL</option>
                                            <option value="TCP">TCP</option>
                                            <option value="UDP">UDP</option>
                                            <option value="ICMP">ICMP</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Dest Port</label>
                                        <input type="number" value={newRule.dst_port} onChange={e => setNewRule({ ...newRule, dst_port: e.target.value })} placeholder="e.g. 443" className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }} />
                                    </div>
                                </div>
                            </div>

                            <h4 style={{ color: 'var(--text-muted)', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '0.5rem' }}>2. Deep Packet Inspection (DPI) & Time</h4>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>App Category</label>
                                    <select value={newRule.app_category} onChange={e => setNewRule({ ...newRule, app_category: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                        <option value="ANY">ANY</option>
                                        <option value="Social Media">Social Media</option>
                                        <option value="Streaming">Streaming</option>
                                        <option value="File Sharing">File Sharing</option>
                                        <option value="Games">Games</option>
                                        <option value="Malware/Botnet">Malware/Botnet</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>File Type Control</label>
                                    <select value={newRule.file_type} onChange={e => setNewRule({ ...newRule, file_type: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                        <option value="ANY">ANY</option>
                                        <option value="EXECUTABLES (.exe, .dll)">EXECUTABLES (.exe, .dll)</option>
                                        <option value="DOCUMENTS (.pdf, .doc)">DOCUMENTS (.pdf, .doc)</option>
                                        <option value="ARCHIVES (.zip, .tar)">ARCHIVES (.zip, .tar)</option>
                                    </select>
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Active Schedule</label>
                                    <select value={newRule.schedule} onChange={e => setNewRule({ ...newRule, schedule: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}>
                                        <option value="ALWAYS">Always Active</option>
                                        <option value="Work Hours (9-5)">Work Hours (9-5)</option>
                                        <option value="Weekends Only">Weekends Only</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end', padding: '1.5rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                                <div style={{ flex: 1 }}>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>Policy Action</label>
                                    <select value={newRule.action} onChange={e => setNewRule({ ...newRule, action: e.target.value })} className="form-control" style={{ width: '100%', padding: '0.8rem', background: '#111827', border: `1px solid ${newRule.action === 'ALLOW' ? 'var(--success)' : newRule.action === 'BLOCK' ? 'var(--danger)' : 'var(--warning)'}`, color: '#fff', borderRadius: '4px', fontWeight: 'bold' }}>
                                        <option value="BLOCK">BLOCK (Drop Packet)</option>
                                        <option value="ALLOW">ALLOW (Permit Traffic)</option>
                                        <option value="THROTTLE">THROTTLE (Apply QoS)</option>
                                    </select>
                                </div>
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '2rem' }}>
                                <button type="button" onClick={() => setShowModal(false)} className="btn btn-secondary" style={{ background: 'rgba(255,255,255,0.1)', color: 'white', border: 'none', padding: '0.8rem 1.5rem', borderRadius: '4px', cursor: 'pointer' }}>Cancel</button>
                                <button type="submit" className="btn btn-primary" style={{ background: 'var(--primary-color)', color: 'black', border: 'none', padding: '0.8rem 1.5rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', boxShadow: '0 0 10px var(--primary-glow)' }}>Deploy Policy</button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FirewallRules;
