import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings as SettingsIcon, Save, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const Settings = () => {
    const { t } = useTranslation();
    const [config, setConfig] = useState(null);
    const [loading, setLoading] = useState(true);
    const [savingStatus, setSavingStatus] = useState(null); // { status: 'success' | 'error', message: '' }

    useEffect(() => {
        loadConfig();
    }, []);

    const loadConfig = async () => {
        try {
            setLoading(true);
            const data = await api.getConfig();
            setConfig(data);
        } catch (error) {
            console.error("Failed to load config", error);
        } finally {
            setLoading(false);
        }
    };

    const handleUpdate = async (category, key, value, type) => {
        // Parse type if needed (e.g. number, boolean)
        let parsedValue = value;
        if (type === 'number') parsedValue = Number(value);
        if (type === 'boolean') parsedValue = value === 'true' || value === true;

        // Optimistic UI Update
        setConfig(prev => ({
            ...prev,
            [category]: {
                ...prev[category],
                [key]: parsedValue
            }
        }));

        try {
            setSavingStatus({ status: 'saving', message: 'Saving...' });
            await api.updateConfig(category, key, parsedValue);
            setSavingStatus({ status: 'success', message: 'Saved successfully. Reloading might be required.' });
            setTimeout(() => setSavingStatus(null), 3000);
        } catch (err) {
            setSavingStatus({ status: 'error', message: 'Failed to save configuration.' });
        }
    };

    if (loading) {
        return <div className="page-container fadeIn"><h3 className="text-muted">Loading System Configuration...</h3></div>;
    }

    if (!config) {
        return <div className="page-container fadeIn"><h3 className="danger-text">Failed to load configuration.</h3></div>;
    }

    // Helper to render sections
    const renderConfigSection = (categoryTitle, categoryKey, icon) => {
        const sectionConfig = config[categoryKey];
        if (!sectionConfig) return null;

        return (
            <div className="glass-panel" style={{ marginBottom: '2rem' }}>
                <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', color: 'var(--primary-neon)' }}>
                    {icon} {categoryTitle}
                </h3>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
                    {Object.entries(sectionConfig).map(([key, value]) => {
                        const isBoolean = typeof value === 'boolean';
                        const isNumber = typeof value === 'number';

                        return (
                            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                                    {key.replace(/_/g, ' ')}
                                </label>
                                {isBoolean ? (
                                    <select
                                        value={value}
                                        onChange={(e) => handleUpdate(categoryKey, key, e.target.value, 'boolean')}
                                        style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}
                                    >
                                        <option value="true">Enabled</option>
                                        <option value="false">Disabled</option>
                                    </select>
                                ) : (
                                    <input
                                        type={isNumber ? 'number' : 'text'}
                                        value={value}
                                        onChange={(e) => {
                                            // Provide optimistic local state update for text inputs, but only fire API on blur to avoid spamming
                                            setConfig(prev => ({
                                                ...prev,
                                                [categoryKey]: { ...prev[categoryKey], [key]: e.target.value }
                                            }));
                                        }}
                                        onBlur={(e) => handleUpdate(categoryKey, key, e.target.value, isNumber ? 'number' : 'string')}
                                        style={{ padding: '0.5rem', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: '#fff', borderRadius: '4px' }}
                                    />
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    };

    return (
        <div className="page-container fadeIn">
            <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1 className="page-title">{t('settings') || 'System Configuration'}</h1>
                    <p className="page-subtitle text-muted">Manage config.yaml properties directly</p>
                </div>
                {savingStatus && (
                    <div style={{
                        padding: '0.5rem 1rem',
                        borderRadius: '4px',
                        background: savingStatus.status === 'success' ? 'rgba(0, 229, 255, 0.1)' : savingStatus.status === 'error' ? 'rgba(255,0,0,0.1)' : 'rgba(255,255,255,0.1)',
                        border: `1px solid ${savingStatus.status === 'success' ? 'var(--primary-neon)' : savingStatus.status === 'error' ? 'var(--danger)' : '#fff'}`,
                        color: savingStatus.status === 'success' ? 'var(--primary-neon)' : savingStatus.status === 'error' ? 'var(--danger)' : '#fff'
                    }}>
                        {savingStatus.message}
                    </div>
                )}
            </header>

            <div className="dashboard-content" style={{ gridTemplateColumns: '1fr' }}>
                {renderConfigSection('System Core', 'system', <SettingsIcon size={20} />)}
                {renderConfigSection('Network Interfaces', 'network', <AlertTriangle size={20} />)}
                {renderConfigSection('AI & Analytics', 'ai', <SettingsIcon size={20} />)}
                {renderConfigSection('Security Defaults', 'security', <AlertTriangle size={20} />)}
            </div>
        </div>
    );
};

export default Settings;
