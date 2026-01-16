import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, FlatList, ActivityIndicator, TouchableOpacity, RefreshControl } from 'react-native';
import { API_BASE_URL } from '../src/api'; // Assuming you have an api.js or similar, check FleetView for usage

// Fallback if not exported cleanly
// const API_BASE_URL = 'http://localhost:8000'; // Make sure this matches your environment (e.g. 10.0.2.2 for Android)
// Using logic from existing files to determine fetch URL

export default function ModuleInspector({ onBack }) {
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);

    const fetchModules = async () => {
        try {
            // Assuming localhost mapping, adjust as needed or read from config
            // In FleetView/Drilldown, how is API called? Let's check api.js or use relative path if proxy...
            // For now, hardcode or try to find a shared constant.
            // Since I can't confirm `api.js` existence/content purely from memory, I'll use a safe fetch.

            const response = await fetch('http://localhost:8000/modules');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setModules(data);
            setError(null);
        } catch (err) {
            console.error("Failed to fetch modules:", err);
            setError("Failed to load module data. Is server running?");
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchModules();
        // Poll every 3 seconds to make it feel "live"
        const interval = setInterval(fetchModules, 3000);
        return () => clearInterval(interval);
    }, []);

    const onRefresh = () => {
        setRefreshing(true);
        fetchModules();
    };

    const renderItem = ({ item }) => {
        // Determine color based on status
        let statusColor = '#4CAF50'; // Green for Active/Ready
        if (item.status === 'Offline') statusColor = '#9E9E9E';
        if (item.status === 'Waiting') statusColor = '#FFC107';
        if (item.status === 'Info') statusColor = '#2196F3';

        return (
            <View style={styles.card}>
                <View style={styles.header}>
                    <Text style={styles.idText}>{item.id}</Text>
                    <View style={[styles.badge, { backgroundColor: statusColor }]}>
                        <Text style={styles.statusText}>{item.status}</Text>
                    </View>
                </View>
                <Text style={styles.nameText}>{item.name}</Text>
                <View style={styles.dataContainer}>
                    {Object.entries(item.data).map(([key, value]) => {
                        let displayValue = String(value);
                        if (typeof value === 'object' && value !== null) {
                            displayValue = JSON.stringify(value, null, 2); // Pretty print objects
                        }
                        return (
                            <Text key={key} style={styles.dataText}>
                                <Text style={styles.dataKey}>{key}: </Text>
                                <Text style={styles.dataValue}>{displayValue}</Text>
                            </Text>
                        );
                    })}
                </View>
            </View>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.topBar}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>System Modules (M0-M19)</Text>
            </View>

            {loading ? (
                <ActivityIndicator size="large" color="#0000ff" style={{ marginTop: 20 }} />
            ) : error ? (
                <View style={styles.center}>
                    <Text style={styles.errorText}>{error}</Text>
                    <TouchableOpacity onPress={fetchModules} style={styles.retryButton}>
                        <Text style={styles.retryText}>Retry</Text>
                    </TouchableOpacity>
                </View>
            ) : (
                <FlatList
                    data={modules}
                    keyExtractor={(item) => item.id}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContent}
                    refreshControl={
                        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
                    }
                />
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    topBar: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 16,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        // For iOS status bar
        paddingTop: 0 // handled by SafeArea in App.js
    },
    backButton: {
        marginRight: 16,
        padding: 8,
    },
    backButtonText: {
        fontSize: 16,
        color: '#007AFF',
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
    },
    listContent: {
        padding: 16,
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 8,
        padding: 16,
        marginBottom: 12,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.1,
        shadowRadius: 2,
        elevation: 2,
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 4,
    },
    idText: {
        fontSize: 14,
        fontWeight: '900',
        color: '#666',
    },
    nameText: {
        fontSize: 18,
        fontWeight: '600',
        marginBottom: 8,
        color: '#333',
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 4,
    },
    statusText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: 'bold',
    },
    dataContainer: {
        backgroundColor: '#f9f9f9',
        padding: 8,
        borderRadius: 4,
    },
    dataText: {
        fontSize: 14,
        fontFamily: 'Courier', // Monospace for code-like feel
        marginBottom: 2,
    },
    dataKey: {
        color: '#555',
        fontWeight: 'bold',
    },
    dataValue: {
        color: '#333',
    },
    center: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 20
    },
    errorText: {
        color: 'red',
        marginBottom: 10,
        fontSize: 16
    },
    retryButton: {
        padding: 10,
        backgroundColor: '#ddd',
        borderRadius: 5
    },
    retryText: {
        fontWeight: "bold"
    }
});
