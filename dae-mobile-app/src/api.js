export const API_BASE_URL = 'http://localhost:8000'; 
// Note: If testing on a physical device, replace 'localhost' with your PC's IP address (e.g., 192.168.1.x)

export const fetchMetrics = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/metrics`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching metrics:", error);
        return null;
    }
};

export const fetchEvents = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/events`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching events:", error);
        return [];
    }
};

export const fetchSnapshots = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/snapshots`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching snapshots:", error);
        return [];
    }
};

export const triggerRecognition = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/recognition`);
        return await response.json();
    } catch (error) {
        console.error("Error triggering recognition:", error);
        return null;
    }
};
