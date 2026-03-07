import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws';

export const useWebSocket = (rooms = []) => {
    const [data, setData] = useState({
        stats: null,
        alerts: [],
        traffic: [],
        anomalies: []
    });
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef(null);
    const reconnectTimeoutRef = useRef(null);

    // Stringify rooms array to make sure it doesn't cause infinite re-renders in useCallback
    const roomsString = JSON.stringify(rooms);

    const connect = useCallback(() => {
        // Generate a simple random client ID for the session
        const clientId = Math.random().toString(36).substring(7);
        const token = localStorage.getItem('ngfw_token') || '';

        // Connect to WebSocket with token
        const ws = new WebSocket(`${WS_URL}/${clientId}?token=${token}`);

        ws.onopen = () => {
            setIsConnected(true);

            const parsedRooms = JSON.parse(roomsString);
            // Subscribe to requested rooms
            parsedRooms.forEach(room => {
                ws.send(JSON.stringify({
                    type: 'subscribe',
                    room: room
                }));
            });
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                const { room, data: payload } = message;

                setData(prev => {
                    if (room === 'stats') {
                        return { ...prev, stats: payload };
                    }
                    if (room === 'alerts') {
                        return { ...prev, alerts: [payload, ...prev.alerts].slice(0, 50) };
                    }
                    if (room === 'traffic') {
                        return { ...prev, traffic: [payload, ...prev.traffic].slice(0, 100) };
                    }
                    if (room === 'anomalies') {
                        return { ...prev, anomalies: [payload, ...prev.anomalies].slice(0, 50) };
                    }
                    return prev;
                });
            } catch (err) {
                console.error("WebSocket payload error:", err);
            }
        };

        ws.onclose = () => {
            setIsConnected(false);
            reconnectTimeoutRef.current = setTimeout(() => {
                connect();
            }, 3000);
        };

        ws.onerror = (err) => {
            console.error("WebSocket error:", err);
            ws.close();
        };

        wsRef.current = ws;
    }, [roomsString]);

    useEffect(() => {
        connect();

        return () => {
            if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [connect]);

    const sendMessage = (msg) => {
        if (wsRef.current && isConnected) {
            wsRef.current.send(JSON.stringify(msg));
        }
    };

    return { isConnected, data, sendMessage };
};
