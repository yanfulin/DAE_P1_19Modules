import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, RefreshControl, Platform } from 'react-native';
import { fetchFleet } from '../src/api';

const FleetItem = ({ item, onPress }) => {
    const isReady = item.closure_readiness === 'READY';

    let statusColor = '#9e9e9e';
    switch (item.current_state) {
        case 'ok': statusColor = '#4caf50'; break;
        case 'unstable': statusColor = '#f44336'; break;
        case 'suspected': statusColor = '#ff9800'; break;
        case 'investigating': statusColor = '#2196f3'; break;
    }

    return (
        <TouchableOpacity style={styles.card} onPress={() => onPress(item.id)}>
            <View style={styles.headerRow}>
                <Text style={styles.deviceName}>{item.name}</Text>
                <View style={[styles.badge, { backgroundColor: statusColor }]}>
                    <Text style={styles.badgeText}>{item.current_state.toUpperCase()}</Text>
                </View>
            </View>

            <View style={styles.infoRow}>
                <Text style={styles.label}>Issue:</Text>
                <Text style={styles.value}>{item.primary_issue_class}</Text>
            </View>

            <View style={styles.infoRow}>
                <Text style={styles.label}>Closure:</Text>
                <Text style={[styles.value, { color: isReady ? '#2e7d32' : '#c62828', fontWeight: 'bold' }]}>
                    {item.closure_readiness}
                </Text>
            </View>

            <View style={styles.footerRow}>
                <Text style={styles.timeText}>Last Change: {item.last_change_ref}</Text>
                {item.feature_deltas.length > 0 && (
                    <Text style={styles.deltaText}>{item.feature_deltas.length} Deltas</Text>
                )}
            </View>
        </TouchableOpacity>
    );
};

export default function FleetView({ onNavigate }) {
    const [fleet, setFleet] = useState([]);
    const [refreshing, setRefreshing] = useState(false);

    const loadFleet = async () => {
        const data = await fetchFleet();
        if (data) setFleet(data);
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await loadFleet();
        setRefreshing(false);
    };

    useEffect(() => {
        loadFleet();
        // Refresh every 5s
        const interval = setInterval(loadFleet, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <View style={styles.container}>
            <Text style={styles.title}>Project Fleet Board</Text>
            <FlatList
                data={fleet}
                keyExtractor={(item) => item.id}
                renderItem={({ item }) => <FleetItem item={item} onPress={onNavigate} />}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
                contentContainerStyle={styles.listContent}
            />
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    title: {
        fontSize: 22,
        fontWeight: 'bold',
        padding: 16,
        color: '#333'
    },
    listContent: {
        paddingHorizontal: 16,
        paddingBottom: 20
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 12,
        elevation: 2,
        ...Platform.select({
            web: {
                boxShadow: '0px 2px 4px rgba(0, 0, 0, 0.05)',
            },
            default: {
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 2 },
                shadowOpacity: 0.05,
                shadowRadius: 4,
            },
        }),
    },
    headerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12
    },
    deviceName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#222'
    },
    badge: {
        paddingHorizontal: 8,
        paddingVertical: 4,
        borderRadius: 8
    },
    badgeText: {
        color: '#fff',
        fontSize: 10,
        fontWeight: 'bold'
    },
    infoRow: {
        flexDirection: 'row',
        marginBottom: 6
    },
    label: {
        width: 80,
        color: '#888',
        fontSize: 14
    },
    value: {
        flex: 1,
        fontSize: 14,
        color: '#333'
    },
    footerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginTop: 8,
        paddingTop: 8,
        borderTopWidth: 1,
        borderTopColor: '#f0f0f0'
    },
    timeText: {
        fontSize: 12,
        color: '#999'
    },
    deltaText: {
        fontSize: 12,
        color: '#ff9800',
        fontWeight: '600'
    }
});
