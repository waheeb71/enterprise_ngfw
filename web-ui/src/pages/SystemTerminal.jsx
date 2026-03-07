import React, { useState, useEffect, useRef } from 'react';
import { Terminal as TerminalIcon, Pause, Play, Download, Trash2, Cpu } from 'lucide-react';
import { api } from '../services/api';
import '../Pages.css';

const SystemTerminal = () => {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [autoScroll, setAutoScroll] = useState(true);
    const [filterLevel, setFilterLevel] = useState('ALL');
    const [searchQuery, setSearchQuery] = useState('');
    const bottomRef = useRef(null);

    const fetchLogs = async () => {
        try {
            const data = await api.getSystemLogs(2000);
            if (data.status === 'success') {
                setLogs(data.logs);
            }
        } catch (err) {
            console.error("Failed to fetch logs:", err);
        } finally {
            setLoading(false);
        }
    };

    // Poll every 2 seconds
    useEffect(() => {
        fetchLogs();
        const interval = setInterval(fetchLogs, 2000);
        return () => clearInterval(interval);
    }, []);

    // Auto scroll logic
    useEffect(() => {
        if (autoScroll && bottomRef.current) {
            bottomRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, autoScroll]);

    const handleClear = () => {
        setLogs([]);
    };

    const handleDownload = () => {
        const text = logs.map(l => l.formatted).join('\n');
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ngfw_logs_${new Date().getTime()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const _getLogColor = (level) => {
        switch (level) {
            case 'ERROR': case 'CRITICAL': return 'text-red-400';
            case 'WARNING': return 'text-yellow-400';
            case 'INFO': return 'text-green-400';
            case 'DEBUG': return 'text-blue-400';
            default: return 'text-slate-300';
        }
    };

    const filteredLogs = logs.filter(log => {
        if (filterLevel !== 'ALL' && log.level !== filterLevel) return false;
        if (searchQuery && !log.formatted.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
    });

    return (
        <div className="page-container fadeIn" style={{ height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
            <header className="page-header" style={{ marginBottom: '1rem', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <TerminalIcon size={40} className="text-primary" style={{ filter: 'drop-shadow(0 0 10px var(--primary-glow))' }} />
                        <div>
                            <h1 className="page-title" style={{ margin: 0 }}>System Terminal</h1>
                            <p className="page-subtitle text-muted" style={{ margin: '0.2rem 0 0 0' }}>
                                Real-time Deep Inspection & Engine Logs
                            </p>
                        </div>
                    </div>
                </div>
            </header>

            <div className="glass-panel" style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid rgba(255,255,255,0.05)', backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
                    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                        <select
                            className="form-control"
                            style={{ background: '#111827', width: '120px' }}
                            value={filterLevel}
                            onChange={e => setFilterLevel(e.target.value)}
                        >
                            <option value="ALL">ALL LEVELS</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                            <option value="DEBUG">DEBUG</option>
                        </select>
                        <input
                            type="text"
                            placeholder="Grep / Filter..."
                            className="form-control"
                            style={{ background: '#111827', width: '200px' }}
                            value={searchQuery}
                            onChange={e => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button className="btn btn-secondary" onClick={() => setAutoScroll(!autoScroll)} style={{ padding: '0.5rem 1rem', display: 'flex', gap: '0.5rem' }}>
                            {autoScroll ? <Pause size={18} /> : <Play size={18} />}
                            {autoScroll ? 'Auto-Scroll ON' : 'Auto-Scroll OFF'}
                        </button>
                        <button className="btn btn-secondary" onClick={handleClear} style={{ padding: '0.5rem 1rem' }} aria-label="Clear">
                            <Trash2 size={18} />
                        </button>
                        <button className="btn btn-secondary" onClick={handleDownload} style={{ padding: '0.5rem 1rem' }} aria-label="Download">
                            <Download size={18} />
                        </button>
                    </div>
                </div>

                <div
                    style={{
                        flexGrow: 1,
                        backgroundColor: '#050a14',
                        overflowY: 'auto',
                        padding: '1rem',
                        fontFamily: 'monospace',
                        fontSize: '0.85rem',
                        lineHeight: '1.5',
                        boxShadow: 'inset 0 0 20px rgba(0,0,0,0.8)'
                    }}
                >
                    {loading && logs.length === 0 ? (
                        <div style={{ color: 'var(--text-muted)' }}>Connecting to local engine stdout socket...</div>
                    ) : filteredLogs.length === 0 ? (
                        <div style={{ color: 'var(--text-muted)' }}>No logs matching the criteria.</div>
                    ) : (
                        filteredLogs.map((log, idx) => (
                            <div key={idx} style={{
                                wordBreak: 'break-all',
                                borderBottom: '1px solid rgba(255,255,255,0.02)',
                                paddingBottom: '0.2rem',
                                marginBottom: '0.2rem'
                            }}>
                                <span style={{ color: '#64748b' }}>[{log.timestamp}]</span>{' '}
                                <span className={`font-bold ${_getLogColor(log.level)}`}>[{log.level}]</span>{' '}
                                <span style={{ color: '#bae6fd' }}>{log.name}:</span>{' '}
                                <span style={{ color: '#e2e8f0' }}>{log.message}</span>
                            </div>
                        ))
                    )}
                    <div ref={bottomRef} />
                </div>
            </div>
        </div>
    );
};

export default SystemTerminal;
