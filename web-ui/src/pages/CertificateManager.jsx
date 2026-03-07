import React, { useState, useEffect } from 'react';
import { Shield, Download, RefreshCw, Key, FileWarning, AlertTriangle, Monitor, Smartphone, Server } from 'lucide-react';
import { api } from '../services/api';

const CertificateManager = () => {
    const [certInfo, setCertInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [generating, setGenerating] = useState(false);
    const [copied, setCopied] = useState(null);

    useEffect(() => {
        fetchCertInfo();
    }, []);

    const fetchCertInfo = async () => {
        try {
            setLoading(true);
            const data = await api.getCACertificateInfo();
            setCertInfo(data);
            setError(null);
        } catch (err) {
            setError(err.message || 'Failed to fetch certificate information');
            setCertInfo(null);
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = async (format) => {
        try {
            await api.downloadCACertificate(format);
        } catch (err) {
            alert('Failed to download certificate: ' + err.message);
        }
    };

    const handleGenerate = async () => {
        if (!window.confirm("WARNING: Generating a new Root CA will break SSL Inspection for all currently connected clients until they install the new certificate. Are you absolutely sure you want to rotate the CA?")) {
            return;
        }

        try {
            setGenerating(true);
            await api.generateNewCA();
            alert("New Root CA generated successfully! Please restart the firewall engine for changes to take effect.");
            await fetchCertInfo();
        } catch (err) {
            alert('Failed to generate new CA: ' + err.message);
        } finally {
            setGenerating(false);
        }
    };

    const copyToClipboard = (text, id) => {
        navigator.clipboard.writeText(text);
        setCopied(id);
        setTimeout(() => setCopied(null), 2000);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <RefreshCw className="animate-spin text-blue-500 w-8 h-8" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-2xl font-bold text-white">Certificate Management</h1>
                    <p className="text-slate-400">Manage the Enterprise NGFW Root CA for SSL Inspection</p>
                </div>
                <button
                    onClick={fetchCertInfo}
                    className="flex items-center space-x-2 px-4 py-2 bg-slate-800 text-white rounded-lg hover:bg-slate-700 transition"
                >
                    <RefreshCw className="w-4 h-4" />
                    <span>Refresh</span>
                </button>
            </div>

            {error && (
                <div className="p-4 bg-red-900/50 border border-red-500 rounded-lg flex items-center space-x-3 text-red-200">
                    <FileWarning className="w-6 h-6 shrink-0" />
                    <p>{error}</p>
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Left Column: CA Status & Actions */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-6 relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <Shield className="w-32 h-32" />
                        </div>

                        <h2 className="text-xl font-bold text-white mb-6 flex items-center">
                            <Key className="w-5 h-5 mr-3 text-blue-400" />
                            Root CA Status
                        </h2>

                        {certInfo && certInfo.status === 'active' ? (
                            <div className="space-y-4 relative z-10">
                                <div className="p-3 bg-green-900/30 border border-green-500/30 rounded-lg text-green-400 font-mono text-sm break-all">
                                    <span className="text-slate-400 text-xs uppercase block mb-1">Subject</span>
                                    {certInfo.subject}
                                </div>
                                <div className="p-3 bg-slate-900/50 rounded-lg text-slate-300 font-mono text-sm break-all">
                                    <span className="text-slate-400 text-xs uppercase block mb-1">Issuer</span>
                                    {certInfo.issuer}
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="p-3 bg-slate-900/50 rounded-lg">
                                        <span className="text-slate-400 text-xs uppercase block mb-1">Valid From</span>
                                        <div className="text-sm text-slate-200">{new Date(certInfo.valid_from).toLocaleDateString()}</div>
                                    </div>
                                    <div className="p-3 bg-slate-900/50 rounded-lg">
                                        <span className="text-slate-400 text-xs uppercase block mb-1">Valid To</span>
                                        <div className="text-sm text-slate-200">{new Date(certInfo.valid_to).toLocaleDateString()}</div>
                                    </div>
                                </div>
                                <div className="p-3 bg-slate-900/50 rounded-lg text-sky-300 font-mono text-xs break-all cursor-pointer hover:bg-slate-700 transition" onClick={() => copyToClipboard(certInfo.fingerprint, 'fingerprint')} title="Click to copy">
                                    <span className="text-slate-400 text-xs uppercase block mb-1">SHA-256 Fingerprint {copied === 'fingerprint' && <span className="text-green-400 ml-2">(Copied)</span>}</span>
                                    {certInfo.fingerprint}
                                </div>
                            </div>
                        ) : (
                            <div className="text-slate-400 p-6 text-center border border-dashed border-slate-600 rounded-lg">
                                No valid CA certificate found on disk.
                            </div>
                        )}

                        <div className="mt-8 pt-6 border-t border-slate-700">
                            <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-4 flex items-center">
                                <AlertTriangle className="w-4 h-4 mr-2" />
                                Danger Zone
                            </h3>
                            <button
                                onClick={handleGenerate}
                                disabled={generating}
                                className="w-full flex items-center justify-center space-x-2 px-4 py-3 bg-red-600/20 text-red-500 border border-red-500/50 rounded-lg hover:bg-red-600 hover:text-white transition disabled:opacity-50"
                            >
                                {generating ? <RefreshCw className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
                                <span>{generating ? 'Generating Keys...' : 'Rotate CA Certificate'}</span>
                            </button>
                            <p className="text-xs text-slate-500 mt-3 text-center">
                                Generates a new RSA 4096-bit Root CA. Instantly invalidates all previous client installations.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right Column: Downloads & Guides */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-6">
                        <h2 className="text-xl font-bold text-white mb-2">Download Client Packages</h2>
                        <p className="text-slate-400 mb-6 text-sm">Download the public certificate format required for your operating system.</p>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <button onClick={() => handleDownload('der')} disabled={!certInfo || certInfo.status !== 'active'} className="flex flex-col items-center justify-center p-6 bg-slate-900 border border-slate-700 rounded-xl hover:bg-blue-900/30 hover:border-blue-500 transition disabled:opacity-50">
                                <Monitor className="w-10 h-10 text-blue-400 mb-3" />
                                <span className="font-semibold text-white">Windows</span>
                                <span className="text-xs text-slate-400 mt-1">.der / .cer</span>
                            </button>

                            <button onClick={() => handleDownload('pem')} disabled={!certInfo || certInfo.status !== 'active'} className="flex flex-col items-center justify-center p-6 bg-slate-900 border border-slate-700 rounded-xl hover:bg-purple-900/30 hover:border-purple-500 transition disabled:opacity-50">
                                <Server className="w-10 h-10 text-purple-400 mb-3" />
                                <span className="font-semibold text-white">macOS / Linux</span>
                                <span className="text-xs text-slate-400 mt-1">.pem / .crt</span>
                            </button>

                            <button onClick={() => handleDownload('p12')} disabled={!certInfo || certInfo.status !== 'active'} className="flex flex-col items-center justify-center p-6 bg-slate-900 border border-slate-700 rounded-xl hover:bg-orange-900/30 hover:border-orange-500 transition disabled:opacity-50">
                                <Smartphone className="w-10 h-10 text-orange-400 mb-3" />
                                <span className="font-semibold text-white">Mobile / MDM</span>
                                <span className="text-xs text-slate-400 mt-1">.p12 (Pass: ngfw-ca-password)</span>
                            </button>
                        </div>
                    </div>

                    <div className="bg-slate-800 rounded-lg shadow-lg border border-slate-700 p-6">
                        <h2 className="text-xl font-bold text-white mb-6">Quick Installation Guides</h2>

                        <div className="space-y-4">
                            <div className="border border-slate-700 rounded-lg p-4">
                                <h3 className="text-lg font-semibold text-blue-400 flex items-center mb-3">
                                    <Monitor className="w-5 h-5 mr-2" /> Windows (PowerShell)
                                </h3>
                                <p className="text-sm text-slate-400 mb-3">Run the following command in PowerShell as Administrator after downloading the .der file:</p>
                                <div className="relative">
                                    <pre className="p-3 bg-slate-900 rounded border border-slate-800 text-green-400 text-sm overflow-x-auto">
                                        certutil -addstore -f "ROOT" .\ngfw-root-ca.der
                                    </pre>
                                </div>
                            </div>

                            <div className="border border-slate-700 rounded-lg p-4">
                                <h3 className="text-lg font-semibold text-purple-400 flex items-center mb-3">
                                    <Server className="w-5 h-5 mr-2" /> macOS (Terminal)
                                </h3>
                                <p className="text-sm text-slate-400 mb-3">Run the following command in your terminal after downloading the .pem file:</p>
                                <div className="relative">
                                    <pre className="p-3 bg-slate-900 rounded border border-slate-800 text-green-400 text-sm overflow-x-auto">
                                        sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ./ngfw-root-ca.pem
                                    </pre>
                                </div>
                            </div>

                            <div className="border border-slate-700 rounded-lg p-4">
                                <h3 className="text-lg font-semibold text-orange-400 flex items-center mb-3">
                                    <Smartphone className="w-5 h-5 mr-2" /> iOS / iPadOS
                                </h3>
                                <p className="text-sm text-slate-400">
                                    1. AirDrop or Email the .der file to your device.<br />
                                    2. Tap the file and select "Allow" to download the profile.<br />
                                    3. Go to <strong>Settings → General → VPN & Device Management</strong>.<br />
                                    4. Tap the profile and Install.<br />
                                    5. Go to <strong>Settings → General → About → Certificate Trust Settings</strong>.<br />
                                    6. Enable "Enterprise NGFW Root CA".
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default CertificateManager;
