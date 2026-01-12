import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, RefreshControl, TouchableOpacity, Dimensions } from 'react-native';
import { fetchMetrics, fetchStatus, checkInstallVerification } from '../src/api';
import Svg, { Polyline } from 'react-native-svg';

const MetricCard = ({ label, value, unit, chartData, color }) => {
    const chartWidth = Dimensions.get('window').width - 64;
    const chartHeight = 60;

    const renderChart = () => {
        if (!chartData || chartData.length < 2) return null;

        const max = Math.max(...chartData);
        const min = Math.min(...chartData);
        const range = max - min || 1;

        const points = chartData.map((val, idx) => {
            const x = (idx / (chartData.length - 1)) * chartWidth;
            const y = chartHeight - ((val - min) / range) * chartHeight;
            return `${x},${y}`;
        }).join(' ');

        return (
            <Svg width={chartWidth} height={chartHeight} style={styles.chart}>
                <Polyline
                    points={points}
                    fill="none"
                    stroke={color}
                    strokeWidth="2"
                />
            </Svg>
        );
    };

    return (
        <View style={styles.metricCard}>
            <Text style={styles.metricLabel}>{label}</Text>
            <View style={styles.metricValueRow}>
                <Text style={[styles.metricValue, { color }]}>{value}</Text>
                <Text style={styles.metricUnit}>{unit}</Text>
            </View>
            {renderChart()}
        </View>
    );
};

const StatusIndicator = ({ status }) => {
    let statusColor = '#9e9e9e';
    switch (status?.toLowerCase()) {
        case 'ok': statusColor = '#4caf50'; break;
        case 'unstable': statusColor = '#ff9800'; break;
        case 'suspected': statusColor = '#f44336'; break;
        case 'investigating': statusColor = '#2196f3'; break;
    }

    return (
        <View style={styles.statusBanner}>
            <View style={styles.statusItem}>
                <View style={[styles.statusIndicator, { backgroundColor: statusColor }]} />
                <View>
                    <Text style={styles.statusLabel}>System Status</Text>
                    <Text style={styles.statusValue}>{status?.toUpperCase() || 'LOADING...'}</Text>
                </View>
            </View>
            <View style={styles.statusItem}>
                <Text style={styles.statusLabel}>Auto-refresh</Text>
                <Text style={styles.statusValue}>Every 2s</Text>
            </View>
        </View>
    );
};

export default function MetricsView({ onBack }) {
    const [metrics, setMetrics] = useState(null);
    const [status, setStatus] = useState(null);
    const [verification, setVerification] = useState(null);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);

    // Chart data storage (last 20 points)
    const [chartData, setChartData] = useState({
        signal: [],
        tx: [],
        rx: [],
        cpu: [],
        memory: []
    });

    const MAX_POINTS = 20;

    const loadData = async () => {
        try {
            const [metricsData, statusData, verificationData] = await Promise.all([
                fetchMetrics(),
                fetchStatus(),
                checkInstallVerification()
            ]);

            if (metricsData) {
                setMetrics(metricsData);
                setError(null);

                // Update chart data
                setChartData(prev => {
                    const newData = {
                        signal: [...prev.signal, metricsData.signal_strength_pct || 0],
                        tx: [...prev.tx, metricsData.out_rate || 0],
                        rx: [...prev.rx, metricsData.in_rate || 0],
                        cpu: [...prev.cpu, metricsData.cpu_load || 0],
                        memory: [...prev.memory, metricsData.mem_load || 0]
                    };

                    // Keep only last MAX_POINTS
                    Object.keys(newData).forEach(key => {
                        if (newData[key].length > MAX_POINTS) {
                            newData[key] = newData[key].slice(-MAX_POINTS);
                        }
                    });

                    return newData;
                });
            } else {
                setError('No metrics available');
            }

            if (statusData) setStatus(statusData.status);
            if (verificationData) setVerification(verificationData);

        } catch (err) {
            setError(`Failed to fetch data: ${err.message}`);
        }
    };

    const onRefresh = async () => {
        setRefreshing(true);
        await loadData();
        setRefreshing(false);
    };

    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← BACK</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Metrics Dashboard</Text>
                <View style={styles.placeholder} />
            </View>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            >
                {error && (
                    <View style={styles.errorBanner}>
                        <Text style={styles.errorText}>{error}</Text>
                    </View>
                )}

                <StatusIndicator status={status} />

                <View style={styles.metricsGrid}>
                    <MetricCard
                        label="Signal Strength"
                        value={metrics?.signal_strength_pct ?? '--'}
                        unit="%"
                        chartData={chartData.signal}
                        color="#667eea"
                    />

                    <MetricCard
                        label="TX Rate"
                        value={metrics?.out_rate ? metrics.out_rate.toFixed(1) : '--'}
                        unit="Mbps"
                        chartData={chartData.tx}
                        color="#48bb78"
                    />

                    <MetricCard
                        label="RX Rate"
                        value={metrics?.in_rate ? metrics.in_rate.toFixed(1) : '--'}
                        unit="Mbps"
                        chartData={chartData.rx}
                        color="#4299e1"
                    />

                    <MetricCard
                        label="CPU Usage"
                        value={metrics?.cpu_load ? metrics.cpu_load.toFixed(1) : '--'}
                        unit="%"
                        chartData={chartData.cpu}
                        color="#ed8936"
                    />

                    <MetricCard
                        label="Memory Usage"
                        value={metrics?.mem_load ? metrics.mem_load.toFixed(1) : '--'}
                        unit="%"
                        chartData={chartData.memory}
                        color="#f56565"
                    />

                    <View style={styles.metricCard}>
                        <Text style={styles.metricLabel}>Timestamp</Text>
                        <Text style={[styles.metricValue, { fontSize: 16, color: '#667eea' }]}>
                            {metrics?.ts ? Math.floor(metrics.ts) : '--'}
                        </Text>
                        <Text style={styles.metricUnit}>Unix Time</Text>
                    </View>
                </View>

                {verification && (
                    <View style={styles.verificationCard}>
                        <Text style={styles.verificationTitle}>Installation Verification</Text>
                        <View style={styles.verificationGrid}>
                            <View style={styles.verificationItem}>
                                <Text style={styles.verificationLabel}>Closure Readiness</Text>
                                <Text style={[
                                    styles.verificationValue,
                                    { color: verification.closure_readiness === 'ready' ? '#48bb78' : '#f56565' }
                                ]}>
                                    {verification.closure_readiness?.toUpperCase() || '--'}
                                </Text>
                            </View>

                            <View style={styles.verificationItem}>
                                <Text style={styles.verificationLabel}>Readiness Verdict</Text>
                                <Text style={[
                                    styles.verificationValue,
                                    { color: verification.readiness_verdict === 'PASS' ? '#48bb78' : '#f56565' }
                                ]}>
                                    {verification.readiness_verdict || '--'}
                                </Text>
                            </View>

                            <View style={styles.verificationItem}>
                                <Text style={styles.verificationLabel}>Dominant Factor</Text>
                                <Text style={styles.verificationValue}>
                                    {verification.dominant_factor || '--'}
                                </Text>
                            </View>

                            <View style={styles.verificationItem}>
                                <Text style={styles.verificationLabel}>Confidence</Text>
                                <Text style={styles.verificationValue}>
                                    {verification.confidence ? verification.confidence.toFixed(2) : '--'}
                                </Text>
                            </View>
                        </View>
                    </View>
                )}

                <Text style={styles.lastUpdated}>
                    Last updated: {new Date().toLocaleTimeString()}
                </Text>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: 16,
        paddingVertical: 12,
        backgroundColor: '#fff',
        borderBottomWidth: 1,
        borderBottomColor: '#e0e0e0',
    },
    backButton: {
        padding: 8,
    },
    backButtonText: {
        color: '#2196f3',
        fontSize: 14,
        fontWeight: '600',
    },
    title: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
    },
    placeholder: {
        width: 60,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: 16,
    },
    errorBanner: {
        backgroundColor: '#ffebee',
        borderRadius: 8,
        padding: 12,
        marginBottom: 16,
        borderWidth: 1,
        borderColor: '#ef5350',
    },
    errorText: {
        color: '#c62828',
        fontSize: 14,
        textAlign: 'center',
    },
    statusBanner: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    statusItem: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 12,
    },
    statusIndicator: {
        width: 12,
        height: 12,
        borderRadius: 6,
    },
    statusLabel: {
        fontSize: 12,
        color: '#888',
    },
    statusValue: {
        fontSize: 14,
        fontWeight: '600',
        color: '#333',
    },
    metricsGrid: {
        gap: 12,
    },
    metricCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    metricLabel: {
        fontSize: 12,
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 8,
        fontWeight: '500',
    },
    metricValueRow: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginBottom: 12,
    },
    metricValue: {
        fontSize: 32,
        fontWeight: '700',
        marginRight: 8,
    },
    metricUnit: {
        fontSize: 14,
        color: '#666',
    },
    chart: {
        marginTop: 8,
    },
    verificationCard: {
        backgroundColor: '#fff',
        borderRadius: 12,
        padding: 16,
        marginTop: 16,
        elevation: 2,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
    },
    verificationTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
        marginBottom: 16,
    },
    verificationGrid: {
        gap: 12,
    },
    verificationItem: {
        backgroundColor: '#f9f9f9',
        padding: 12,
        borderRadius: 8,
    },
    verificationLabel: {
        fontSize: 11,
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: 1,
        marginBottom: 4,
    },
    verificationValue: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    lastUpdated: {
        textAlign: 'center',
        color: '#999',
        fontSize: 12,
        marginTop: 24,
        marginBottom: 16,
    },
});
