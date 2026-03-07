const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Internal helper for fetch requests
async function fetchWithAuth(endpoint, options = {}) {
    const token = localStorage.getItem('ngfw_token');

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        if (response.status === 401) {
            // Handle unauthorized (e.g., redirect to login or clear token)
            localStorage.removeItem('ngfw_token');
            // window.location.href = '/login'; 
        }
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
}

export const api = {
    // Authentication
    login: async (username, password) => {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) throw new Error('Login failed');
        return response.json();
    },

    // System
    getSystemStatus: () => fetchWithAuth('/status'),
    getSystemLogs: (limit = 1000) => fetchWithAuth(`/system/logs?limit=${limit}`),

    // Traffic
    getTrafficStats: (timeWindow = 300) => fetchWithAuth(`/traffic/stats?time_window=${timeWindow}`),
    getAnomalies: () => fetchWithAuth('/anomalies'),

    // Firewall Rules
    getRules: () => fetchWithAuth('/rules'),
    createRule: (rule) => fetchWithAuth('/rules', { method: 'POST', body: JSON.stringify(rule) }),
    deleteRule: (ruleId) => fetchWithAuth(`/rules/${ruleId}`, { method: 'DELETE' }),

    // Interfaces
    getInterfaces: () => fetchWithAuth('/interfaces'),
    assignInterfaceRole: (interface_name, role) => fetchWithAuth('/interfaces/assign', {
        method: 'POST',
        body: JSON.stringify({ interface_name, role })
    }),

    // VPN Manager 
    getVpnStatus: () => fetchWithAuth('/vpn/status'),
    getVpnPeers: () => fetchWithAuth('/vpn/peers'),
    addVpnPeer: (peerData) => fetchWithAuth('/vpn/peers', {
        method: 'POST',
        body: JSON.stringify(peerData)
    }),
    removeVpnPeer: (publicKey) => fetchWithAuth(`/vpn/peers/${encodeURIComponent(publicKey)}`, {
        method: 'DELETE'
    }),

    // QoS (Assumed endpoints)
    getQoSConfig: () => fetchWithAuth('/qos/config'),
    updateQoSConfig: (config) => fetchWithAuth('/qos/config', {
        method: 'PUT',
        body: JSON.stringify(config)
    }),

    // Config Management
    getConfig: () => fetchWithAuth('/config'),
    updateConfig: (category, key, value) => fetchWithAuth('/config', {
        method: 'PUT',
        body: JSON.stringify({ category, key, value })
    }),

    // Interfaces / Hardware 
    getInterfaces: () => fetchWithAuth('/system/interfaces'),
    assignInterface: (port, role) => fetchWithAuth('/system/interfaces/assign', {
        method: 'POST',
        body: JSON.stringify({ port, role })
    }),

    // AI Models
    getAiModels: () => fetchWithAuth('/ai/models'),
    uploadAiModel: async (modelId, file) => {
        const token = localStorage.getItem('ngfw_token');
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_URL}/ai/models/upload/${modelId}`, {
            method: 'POST',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {},
            body: formData // Don't set Content-Type, browser handles multipart boundaries automatically
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Upload Error: ${response.status}`);
        }

        return response.json();
    },

    // Global Daemon / Orchestrator Controls
    getDaemonStatus: () => fetchWithAuth('/system/daemon/status'),
    startEngine: () => fetchWithAuth('/system/engine/start', { method: 'POST' }),
    stopEngine: () => fetchWithAuth('/system/engine/stop', { method: 'POST' }),
    runSystemScript: (scriptName, args = []) => fetchWithAuth('/system/scripts', {
        method: 'POST',
        body: JSON.stringify({ script_name: scriptName, args })
    }),

    // Certificate Management
    getCACertificateInfo: () => fetchWithAuth('/certificates/ca/info'),
    generateNewCA: () => fetchWithAuth('/certificates/ca/generate', { method: 'POST' }),
    downloadCACertificate: async (format) => {
        const token = localStorage.getItem('ngfw_token');
        const url = `${API_URL}/certificates/ca/download?format=${format}`;

        // Fetch it as a blob instead of JSON
        const response = await fetch(url, {
            method: 'GET',
            headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || `Download Error: ${response.status}`);
        }

        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = downloadUrl;

        let ext = format;
        if (format === 'p12') ext = 'p12';
        else if (format === 'der') ext = 'der';
        else ext = 'pem';

        link.download = `ngfw-root-ca.${ext}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);
    }
};
