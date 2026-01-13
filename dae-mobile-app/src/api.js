// export const API_BASE_URL = 'http://localhost:8000';
export const API_BASE_URL = 'https://dae-p1-19-modules.vercel.app';
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

export const checkInstallVerification = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/install_verify`);
        return await response.json();
    } catch (error) {
        console.error("Error checking install verification:", error);
        return null;
    }
};

export const fetchStatus = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/status`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching status:", error);
        return null;
    }
};

export const fetchFleet = async () => {
    try {
        const response = await fetch(`${API_BASE_URL}/fleet`);
        return await response.json();
    } catch (error) {
        console.error("Error fetching fleet:", error);
        return [];
    }
};

export const fetchDeviceDetail = async (deviceId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/device/${deviceId}`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching device detail for ${deviceId}:`, error);
        return null;
    }
};

export const fetchProofData = async (deviceId) => {
    try {
        const response = await fetch(`${API_BASE_URL}/device/${deviceId}/proof`);
        return await response.json();
    } catch (error) {
        console.error(`Error fetching proof for ${deviceId}:`, error);
        return null;
    }
};
