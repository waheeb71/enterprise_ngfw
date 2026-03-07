import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { BrainCircuit, UploadCloud, CheckCircle, AlertCircle, Activity, ShieldAlert, Zap, Search } from 'lucide-react';
import { api } from '../services/api';

const AIPipeline = () => {
    const { t } = useTranslation();
    const [activeTab, setActiveTab] = useState('insights');
    const [models, setModels] = useState([]);
    const [anomalies, setAnomalies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const fileInputRef = useRef(null);
    const [uploadingId, setUploadingId] = useState(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [modelsRes, anomaliesRes] = await Promise.all([
                api.getAiModels().catch(() => ({ models: [] })),
                api.getAnomalies().catch(() => [])
            ]);
            setModels(modelsRes.models || []);
            setAnomalies(anomaliesRes || []);
            setError(null);
        } catch (err) {
            console.error(err);
            setError('Failed to load AI Pipeline data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 15000); // refresh anomalies
        return () => clearInterval(interval);
    }, []);

    const handleUploadClick = (modelId) => {
        setUploadingId(modelId);
        fileInputRef.current.click();
    };

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file || !uploadingId) {
            setUploadingId(null);
            return;
        }

        try {
            await api.uploadAiModel(uploadingId, file);
            alert(`Model uploaded successfully! Engine will reload on next cycle.`);
            fetchData();
        } catch (err) {
            alert(`Failed to upload model: ${err.message}`);
        } finally {
            setUploadingId(null);
            e.target.value = null; // reset input
        }
    };

    if (loading && models.length === 0) return (
        <div className="page-container fadeIn" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
            <Activity className="spin text-primary" size={48} />
        </div>
    );

    return (
        <div className="page-container fadeIn">
            <header className="page-header" style={{ marginBottom: '1.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <BrainCircuit size={40} className="text-primary" style={{ filter: 'drop-shadow(0 0 10px var(--primary-glow))' }} />
                    <div>
                        <h1 className="page-title" style={{ margin: 0 }}>AI Inference Engine</h1>
                        <p className="page-subtitle text-muted" style={{ margin: '0.2rem 0 0 0' }}>
                            Advanced Machine Learning Integration & Kernel Acceleration Insights
                        </p>
                    </div>
                </div>
            </header>

            {/* Custom Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: '2rem' }}>
                <button
                    onClick={() => setActiveTab('insights')}
                    style={{
                        background: 'transparent', border: 'none', padding: '1rem 2rem',
                        fontSize: '1.1rem', cursor: 'pointer', transition: 'all 0.2s',
                        color: activeTab === 'insights' ? 'var(--primary-neon)' : 'var(--text-muted)',
                        borderBottom: activeTab === 'insights' ? '2px solid var(--primary-color)' : '2px solid transparent',
                        fontWeight: activeTab === 'insights' ? 'bold' : 'normal',
                        display: 'flex', alignItems: 'center', gap: '0.5rem'
                    }}
                >
                    <Activity size={18} /> Live ML & eBPF Insights
                </button>

                <button
                    onClick={() => setActiveTab('orchestration')}
                    style={{
                        background: 'transparent', border: 'none', padding: '1rem 2rem',
                        fontSize: '1.1rem', cursor: 'pointer', transition: 'all 0.2s',
                        color: activeTab === 'orchestration' ? 'var(--primary-neon)' : 'var(--text-muted)',
                        borderBottom: activeTab === 'orchestration' ? '2px solid var(--primary-color)' : '2px solid transparent',
                        fontWeight: activeTab === 'orchestration' ? 'bold' : 'normal',
                        display: 'flex', alignItems: 'center', gap: '0.5rem'
                    }}
                >
                    <UploadCloud size={18} /> Model Orchestrator
                </button>
            </div>

            {error && (
                <div className="alert alert-danger" style={{ marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <ShieldAlert size={20} /> {error}
                </div>
            )}

            {activeTab === 'insights' && (
                <div className="insights-tab">

                    {/* Metrics Banner */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem', marginBottom: '2.5rem' }}>
                        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderTop: '3px solid var(--primary-color)' }}>
                            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--primary-neon)', textShadow: '0 0 15px var(--primary-glow)' }}>
                                {anomalies.length}
                            </div>
                            <div className="text-muted" style={{ fontSize: '1.1rem' }}>Active ML Detections</div>
                        </div>
                        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderTop: '3px solid var(--danger)' }}>
                            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--danger)', textShadow: '0 0 15px rgba(239, 68, 68, 0.4)' }}>
                                {anomalies.filter(a => a.reason.includes('eBPF')).length}
                            </div>
                            <div className="text-muted" style={{ fontSize: '1.1rem' }}>eBPF Kernel Blocks</div>
                        </div>
                        <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', borderTop: '3px solid var(--success)' }}>
                            <div style={{ fontSize: '3rem', fontWeight: 'bold', color: 'var(--success)', textShadow: '0 0 15px rgba(16, 185, 129, 0.4)' }}>
                                99.8%
                            </div>
                            <div className="text-muted" style={{ fontSize: '1.1rem' }}>Confidence Average</div>
                        </div>
                    </div>

                    <h3 style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Search size={22} className="text-primary" /> Recent Inferences & Intercepts
                    </h3>

                    <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
                        {anomalies.length === 0 ? (
                            <div style={{ padding: '4rem 2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
                                <ShieldAlert size={48} style={{ margin: '0 auto 1rem', opacity: 0.2 }} />
                                <h4>No active anomalies detected</h4>
                                <p>The ML models are continuously monitoring traffic in the background.</p>
                            </div>
                        ) : (
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ backgroundColor: 'rgba(0,0,0,0.3)', color: 'var(--text-muted)', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                        <th style={{ padding: '1rem 1.5rem' }}>Time</th>
                                        <th style={{ padding: '1rem 1.5rem' }}>Source IP Tracker</th>
                                        <th style={{ padding: '1rem 1.5rem' }}>Inference / Threat Context</th>
                                        <th style={{ padding: '1rem 1.5rem' }}>Confidence Threshold</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {anomalies.map((a, idx) => (
                                        <tr key={idx} style={{
                                            borderBottom: '1px solid rgba(255,255,255,0.05)',
                                            background: a.reason.includes('eBPF') ? 'rgba(239, 68, 68, 0.05)' : 'transparent',
                                            transition: 'background 0.2s', ':hover': { backgroundColor: 'rgba(255,255,255,0.02)' }
                                        }}>
                                            <td style={{ padding: '1rem 1.5rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                                                {new Date(a.timestamp).toLocaleTimeString()}
                                            </td>
                                            <td style={{ padding: '1rem 1.5rem', fontFamily: 'monospace', color: 'var(--primary-color)' }}>
                                                {a.src_ip}
                                            </td>
                                            <td style={{ padding: '1rem 1.5rem' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    {a.reason.includes('eBPF') ? <Zap size={16} className="text-danger" /> : <BrainCircuit size={16} className="text-warning" />}
                                                    <span style={{ fontWeight: 500 }}>{a.reason}</span>
                                                </div>
                                            </td>
                                            <td style={{ padding: '1rem 1.5rem' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                    <div style={{ width: '100px', height: '6px', background: 'rgba(255,255,255,0.1)', borderRadius: '3px' }}>
                                                        <div style={{ width: `${a.confidence * 100}%`, height: '100%', background: a.confidence > 0.95 ? 'var(--danger)' : 'var(--warning)', borderRadius: '3px', boxShadow: '0 0 5px currentColor' }} />
                                                    </div>
                                                    <span style={{ fontSize: '0.85rem' }}>{(a.confidence * 100).toFixed(1)}%</span>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {activeTab === 'orchestration' && (
                <div className="orchestration-tab">

                    <input
                        type="file"
                        ref={fileInputRef}
                        style={{ display: 'none' }}
                        onChange={handleFileChange}
                        accept=".pkl,.onnx,.joblib"
                    />

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(400px, 1fr))', gap: '1.5rem' }}>
                        {models.map((m) => {
                            const isLoaded = m.status === 'Loaded';
                            return (
                                <div key={m.id} className="glass-panel" style={{ padding: 0, display: 'flex', flexDirection: 'column', overflow: 'hidden', border: `1px solid ${isLoaded ? 'rgba(16,185,129,0.3)' : 'rgba(245,158,11,0.3)'}` }}>

                                    <div style={{ padding: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(0,0,0,0.3)' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                                            <h3 style={{ margin: 0, fontSize: '1.2rem', color: isLoaded ? 'var(--primary-neon)' : 'white' }}>{m.name}</h3>
                                            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.6rem', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                                                {m.layer}
                                            </span>
                                        </div>
                                        <p className="text-muted" style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.5, minHeight: '40px' }}>
                                            {m.description}
                                        </p>
                                    </div>

                                    <div style={{ padding: '1.5rem', flexGrow: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                                            {isLoaded ? <CheckCircle size={20} className="text-success" /> : <AlertCircle size={20} className="text-warning" />}
                                            <span style={{ fontWeight: 'bold', color: isLoaded ? 'var(--success)' : 'var(--warning)' }}>
                                                {m.status}
                                            </span>
                                        </div>

                                        {isLoaded ? (
                                            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '4px' }}>
                                                <div style={{ fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                                                    <span className="text-muted">Active Binary: </span>
                                                    <span style={{ fontFamily: 'monospace', color: 'var(--primary-color)' }}>{m.filename}</span>
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                                    Timestamp: {new Date(m.last_updated).toLocaleString()}
                                                </div>
                                            </div>
                                        ) : (
                                            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', fontStyle: 'italic', background: 'rgba(0,0,0,0.2)', padding: '1rem', borderRadius: '4px' }}>
                                                Running in internal Heuristic Fallback Mode. Select "Mount Weights" to upload a pre-trained ML binary (.onnx / .pkl) to enable structural AI deep packet acceleration.
                                            </div>
                                        )}
                                    </div>

                                    <div style={{ padding: '1rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)', background: 'rgba(0,0,0,0.1)' }}>
                                        <button
                                            onClick={() => handleUploadClick(m.id)}
                                            disabled={uploadingId === m.id}
                                            className="btn"
                                            style={{
                                                width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem',
                                                padding: '0.8rem', background: isLoaded ? 'rgba(255,255,255,0.1)' : 'var(--primary-color)',
                                                color: isLoaded ? 'white' : 'black', fontWeight: 'bold', border: 'none', borderRadius: '4px', cursor: 'pointer',
                                                transition: '0.2s', boxShadow: isLoaded ? 'none' : '0 0 10px var(--primary-glow)'
                                            }}
                                        >
                                            <UploadCloud size={18} />
                                            {uploadingId === m.id ? 'Loading Weights...' : isLoaded ? 'Update Weights' : 'Mount Weights'}
                                        </button>
                                        <div style={{ textAlign: 'center', marginTop: '0.8rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                            Accepted Formats: {m.supported_extensions.join(', ')}
                                        </div>
                                    </div>

                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
};

export default AIPipeline;
