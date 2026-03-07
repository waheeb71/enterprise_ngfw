import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Settings, Power, Play, Square, Activity, Shield, Info, RefreshCw, TerminalSquare, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

const SystemSettings = () => {
    const { t } = useTranslation();
    const [daemonStatus, setDaemonStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);
    const [logs, setLogs] = useState([]);

    const fetchStatus = async () => {
        try {
            const res = await api.getDaemonStatus();
            setDaemonStatus(res);
        } catch (error) {
            console.error("Failed to fetch daemon status", error);
            setDaemonStatus({ daemon: 'offline', engine_running: false });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const appendLog = (msg, type = 'info') => {
        setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg, type }]);
    };

    const handleStartEngine = async () => {
        setActionLoading(true);
        appendLog('Instructing System Daemon to START Firewall payload...', 'info');
        try {
            const res = await api.startEngine();
            appendLog(`Success: ${res.message}`, 'success');
            await fetchStatus();
        } catch (err) {
            appendLog(`Failed to start: ${err.message}`, 'error');
        } finally {
            setActionLoading(false);
        }
    };

    const handleStopEngine = async () => {
        if (!window.confirm("WARNING: Stopping the Core Engine will interrupt ALL network traffic and bridging. Proceed?")) return;

        setActionLoading(true);
        appendLog('Instructing System Daemon to STOP Firewall mapping...', 'warning');
        try {
            const res = await api.stopEngine();
            appendLog(`Success: ${res.message}`, 'success');
            await fetchStatus();
        } catch (err) {
            appendLog(`Failed to stop: ${err.message}`, 'error');
        } finally {
            setActionLoading(false);
        }
    };

    const handleSystemUpdate = async () => {
        setActionLoading(true);
        appendLog('Executing system update script...', 'info');
        try {
            const res = await api.runSystemScript('update.sh', ['--auto']);
            appendLog(`Update Script Output: ${res.message || 'Started'}`, 'success');
        } catch (err) {
            appendLog(`Update failed: ${err.message}`, 'error');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading && !daemonStatus) {
        return <div className="p-8 text-white">Connecting to Enterprise Orchestrator...</div>;
    }

    const isDaemonOnline = daemonStatus?.daemon === 'online';
    const isEngineRunning = daemonStatus?.engine_running === true;

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <header className="mb-8">
                <div className="flex items-center space-x-3 mb-2">
                    <Settings size={40} className="text-gray-400" />
                    <h1 className="text-3xl font-bold text-gray-800 dark:text-white">Global Orchestration</h1>
                </div>
                <p className="text-gray-600 dark:text-gray-400">
                    Master control plane. Manage the lifecycle of the underlying C/eBPF and Python inspection engines completely independently of this dashboard.
                </p>
            </header>

            {/* Status Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Dashboard Controller Status */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-bold text-gray-800 dark:text-white flex items-center">
                            <Activity size={20} className="mr-2 text-blue-500" />
                            Daemon Supervisor (Control Plane)
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">Responsible for Web UI & Lifecycle</p>
                    </div>
                    <div className="flex flex-col items-center">
                        <div className={`h-4 w-4 rounded-full ${isDaemonOnline ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                        <span className={`text-xs mt-2 font-bold ${isDaemonOnline ? 'text-green-500' : 'text-red-500'}`}>
                            {isDaemonOnline ? 'ONLINE' : 'UNREACHABLE'}
                        </span>
                    </div>
                </div>

                {/* Firewall Engine Status */}
                <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-bold text-gray-800 dark:text-white flex items-center">
                            <Shield size={20} className="mr-2 text-indigo-500" />
                            Firewall Core (Data Plane)
                        </h2>
                        <p className="text-sm text-gray-500 mt-1">Responsible for Traffic, eBPF & AI Models</p>
                    </div>
                    <div className="flex flex-col items-center">
                        <div className={`h-4 w-4 rounded-full ${isEngineRunning ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                        <span className={`text-xs mt-2 font-bold ${isEngineRunning ? 'text-green-500' : 'text-gray-500'}`}>
                            {isEngineRunning ? 'RUNNING' : 'STOPPED'}
                        </span>
                    </div>
                </div>
            </div>

            {/* Control Actions */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow border border-gray-200 dark:border-gray-700 p-6">
                <h2 className="text-xl font-bold text-gray-800 dark:text-white mb-6 border-b border-gray-200 dark:border-gray-700 pb-2">Lifecycle Management</h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button
                        onClick={handleStartEngine}
                        disabled={!isDaemonOnline || isEngineRunning || actionLoading}
                        className="flex flex-col items-center justify-center p-6 rounded-lg border-2 border-green-500/30 hover:border-green-500 hover:bg-green-50 dark:hover:bg-green-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                    >
                        <Play size={32} className="text-green-500 mb-2 group-hover:scale-110 transition-transform" />
                        <span className="font-bold text-gray-800 dark:text-white">Start Engine</span>
                        <span className="text-xs text-gray-500 mt-1 text-center">Boot the main inspection core</span>
                    </button>

                    <button
                        onClick={handleStopEngine}
                        disabled={!isDaemonOnline || !isEngineRunning || actionLoading}
                        className="flex flex-col items-center justify-center p-6 rounded-lg border-2 border-red-500/30 hover:border-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                    >
                        <Square size={32} className="text-red-500 mb-2 group-hover:scale-110 transition-transform" />
                        <span className="font-bold text-gray-800 dark:text-white">Stop Engine</span>
                        <span className="text-xs text-gray-500 mt-1 text-center">Gracefully terminate inspections</span>
                    </button>

                    <button
                        onClick={handleSystemUpdate}
                        disabled={!isDaemonOnline || actionLoading}
                        className="flex flex-col items-center justify-center p-6 rounded-lg border-2 border-blue-500/30 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
                    >
                        <RefreshCw size={32} className="text-blue-500 mb-2 group-hover:rotate-180 transition-transform duration-500" />
                        <span className="font-bold text-gray-800 dark:text-white">System Update</span>
                        <span className="text-xs text-gray-500 mt-1 text-center">Pull latest definitions & scripts</span>
                    </button>
                </div>
            </div>

            {/* Daemon Logs / Terminal Output */}
            <div className="bg-black rounded-xl shadow overflow-hidden border border-gray-700">
                <div className="bg-gray-900 px-4 py-2 flex items-center justify-between border-b border-gray-700">
                    <div className="flex items-center text-gray-300 text-sm font-mono">
                        <TerminalSquare size={16} className="mr-2" />
                        Daemon Supervisor Log
                    </div>
                    <button onClick={() => setLogs([])} className="text-xs text-gray-400 hover:text-white">Clear</button>
                </div>
                <div className="p-4 h-64 overflow-y-auto font-mono text-sm space-y-1">
                    {logs.length === 0 ? (
                        <div className="text-gray-500 italic">No output yet. Connect or execute commands to see logs.</div>
                    ) : (
                        logs.map((log, idx) => (
                            <div key={idx} className={`${log.type === 'error' ? 'text-red-400' :
                                    log.type === 'success' ? 'text-green-400' :
                                        log.type === 'warning' ? 'text-yellow-400' : 'text-gray-300'
                                }`}>
                                <span className="text-gray-500 mr-2">[{log.time}]</span>
                                {log.msg}
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Notice */}
            {!isEngineRunning && isDaemonOnline && (
                <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 flex items-start">
                    <AlertTriangle className="text-yellow-600 dark:text-yellow-500 mr-3 mt-0.5" size={20} />
                    <div>
                        <h3 className="text-sm font-bold text-yellow-800 dark:text-yellow-400">Engine is Offline</h3>
                        <p className="text-sm text-yellow-700 dark:text-yellow-500 mt-1">
                            The Firewall Data Plane is currently not running. The Web UI will function, but no network traffic is being inspected, proxies are down, and AI Analytics are paused. Please start the engine to resume protection.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SystemSettings;
