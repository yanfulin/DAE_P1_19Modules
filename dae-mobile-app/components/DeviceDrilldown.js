import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, Button, ActivityIndicator } from 'react-native';
import { fetchDeviceDetail, fetchMetrics } from '../src/api';
import Svg, { Polyline } from 'react-native-svg';

const Section = ({ title, children }) => (
    <View style={styles.section}>
        <Text style={styles.sectionTitle}>{title}</Text>
        {children}
    </View>
);

export default function DeviceDrilldown({ deviceId, onNavigateProof, onBack }) {
    const [detail, setDetail] = useState(null);
    const [loading, setLoading] = useState(true);
    const [metrics, setMetrics] = useState(null);
    const [chartData, setChartData] = useState({
        signal: [],
        tx: [],
        rx: [],
        cpu: [],
        memory: []
    });

    const MAX_POINTS = 15;

    useEffect(() => {
        const load = async () => {
            const data = await fetchDeviceDetail(deviceId);
            setDetail(data);
            setLoading(false);
        };
        load();
    }, [deviceId]);

    // Fetch metrics for local device
    useEffect(() => {
        if (deviceId !== 'local') return; // Only fetch metrics for local device

        const loadMetrics = async () => {
            const metricsData = await fetchMetrics();
            if (metricsData) {
                setMetrics(metricsData);

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
            }
        };

        loadMetrics();
        const interval = setInterval(loadMetrics, 2000);
        return () => clearInterval(interval);
    }, [deviceId]);

    if (loading) return <ActivityIndicator size="large" color="#2196f3" style={{ marginTop: 50 }} />;
    if (!detail) return <Text>Error loading details.</Text>;

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="< Back" onPress={onBack} />
                <Text style={styles.headerTitle}>Device: {detail.id}</Text>
                <View style={{ width: 50 }} />
            </View>

            <ScrollView contentContainerStyle={styles.content}>

                {/* OBH Snapshot Timeline */}
                <Section title="OBH Snapshot Timeline">
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.timelineScroll}>
                        {detail.obh_snapshot_timeline.map((snap, idx) => (
                            <View key={idx} style={styles.timelineItem}>
                                <Text style={styles.timelineRef}>{snap.ref}</Text>
                                <Text style={styles.timelineType}>{snap.type}</Text>
                                <Text style={styles.timelineTime}>T={snap.time}</Text>
                            </View>
                        ))}
                    </ScrollView>
                </Section>

                {/* Cohort Compare */}
                <Section title="Cohort Compare">
                    <View style={[styles.card, { borderLeftColor: detail.cohort_compare.status === 'normal' ? '#4caf50' : '#ff9800', borderLeftWidth: 4 }]}>
                        <Text style={styles.cardTitle}>{detail.cohort_compare.status.toUpperCase()}</Text>
                        <Text style={styles.cardBody}>{detail.cohort_compare.message}</Text>
                    </View>
                </Section>

                {/* Feature Ledger */}
                <Section title="Feature Ledger">
                    {detail.feature_ledger.length === 0 ? <Text style={styles.emptyText}>No active feature controls.</Text> :
                        detail.feature_ledger.map((f, i) => (
                            <View key={i} style={styles.ledgerRow}>
                                <View>
                                    <Text style={styles.ledgerName}>{f.feature}</Text>
                                    <Text style={styles.ledgerReason}>{f.reason}</Text>
                                </View>
                                <View style={{ alignItems: 'flex-end' }}>
                                    <View style={[styles.badge, { backgroundColor: f.state === 'ON' ? '#4caf50' : '#f44336' }]}>
                                        <Text style={styles.badgeText}>{f.state}</Text>
                                    </View>
                                    {f.ttl && <Text style={styles.ttlText}>{f.ttl}</Text>}
                                </View>
                            </View>
                        ))
                    }
                </Section>

                {/* Compliance Verdict */}
                <Section title="Compliance Verdict">
                    <View style={styles.verdictBox}>
                        <Text style={[styles.verdictTitle, { color: detail.compliance_verdict.result === 'PASS' ? '#2e7d32' : '#c62828' }]}>
                            {detail.compliance_verdict.result}
                        </Text>
                        {detail.compliance_verdict.evidence_missing.length > 0 && (
                            <View style={{ marginTop: 8 }}>
                                <Text style={{ fontWeight: 'bold' }}>Evidence Missing:</Text>
                                {detail.compliance_verdict.evidence_missing.map((e, k) => (
                                    <Text key={k} style={styles.missingItem}>• {e}</Text>
                                ))}
                            </View>
                        )}
                    </View>
                </Section>

                {/* Real-time Metrics - Only for local device */}
                {deviceId === 'local' && metrics && (
                    <Section title="Real-time Metrics">
                        <View style={styles.metricsGrid}>
                            {/* Signal Strength */}
                            <View style={styles.metricCard}>
                                <Text style={styles.metricLabel}>Signal Strength</Text>
                                <View style={styles.metricValueRow}>
                                    <Text style={[styles.metricValue, { color: '#667eea' }]}>
                                        {metrics.signal_strength_pct ?? '--'}
                                    </Text>
                                    <Text style={styles.metricUnit}>%</Text>
                                </View>
                                {chartData.signal.length > 1 && (
                                    <Svg width={280} height={40} style={styles.miniChart}>
                                        <Polyline
                                            points={chartData.signal.map((val, idx) => {
                                                const max = Math.max(...chartData.signal);
                                                const min = Math.min(...chartData.signal);
                                                const range = max - min || 1;
                                                const x = (idx / (chartData.signal.length - 1)) * 280;
                                                const y = 40 - ((val - min) / range) * 40;
                                                return `${x},${y}`;
                                            }).join(' ')}
                                            fill="none"
                                            stroke="#667eea"
                                            strokeWidth="2"
                                        />
                                    </Svg>
                                )}
                            </View>

                            {/* TX Rate */}
                            <View style={styles.metricCard}>
                                <Text style={styles.metricLabel}>TX Rate</Text>
                                <View style={styles.metricValueRow}>
                                    <Text style={[styles.metricValue, { color: '#48bb78' }]}>
                                        {metrics.out_rate ? metrics.out_rate.toFixed(1) : '--'}
                                    </Text>
                                    <Text style={styles.metricUnit}>Mbps</Text>
                                </View>
                                {chartData.tx.length > 1 && (
                                    <Svg width={280} height={40} style={styles.miniChart}>
                                        <Polyline
                                            points={chartData.tx.map((val, idx) => {
                                                const max = Math.max(...chartData.tx);
                                                const min = Math.min(...chartData.tx);
                                                const range = max - min || 1;
                                                const x = (idx / (chartData.tx.length - 1)) * 280;
                                                const y = 40 - ((val - min) / range) * 40;
                                                return `${x},${y}`;
                                            }).join(' ')}
                                            fill="none"
                                            stroke="#48bb78"
                                            strokeWidth="2"
                                        />
                                    </Svg>
                                )}
                            </View>

                            {/* RX Rate */}
                            <View style={styles.metricCard}>
                                <Text style={styles.metricLabel}>RX Rate</Text>
                                <View style={styles.metricValueRow}>
                                    <Text style={[styles.metricValue, { color: '#4299e1' }]}>
                                        {metrics.in_rate ? metrics.in_rate.toFixed(1) : '--'}
                                    </Text>
                                    <Text style={styles.metricUnit}>Mbps</Text>
                                </View>
                                {chartData.rx.length > 1 && (
                                    <Svg width={280} height={40} style={styles.miniChart}>
                                        <Polyline
                                            points={chartData.rx.map((val, idx) => {
                                                const max = Math.max(...chartData.rx);
                                                const min = Math.min(...chartData.rx);
                                                const range = max - min || 1;
                                                const x = (idx / (chartData.rx.length - 1)) * 280;
                                                const y = 40 - ((val - min) / range) * 40;
                                                return `${x},${y}`;
                                            }).join(' ')}
                                            fill="none"
                                            stroke="#4299e1"
                                            strokeWidth="2"
                                        />
                                    </Svg>
                                )}
                            </View>

                            {/* CPU Usage */}
                            <View style={styles.metricCard}>
                                <Text style={styles.metricLabel}>CPU Usage</Text>
                                <View style={styles.metricValueRow}>
                                    <Text style={[styles.metricValue, { color: '#ed8936' }]}>
                                        {metrics.cpu_load ? metrics.cpu_load.toFixed(1) : '--'}
                                    </Text>
                                    <Text style={styles.metricUnit}>%</Text>
                                </View>
                                {chartData.cpu.length > 1 && (
                                    <Svg width={280} height={40} style={styles.miniChart}>
                                        <Polyline
                                            points={chartData.cpu.map((val, idx) => {
                                                const max = Math.max(...chartData.cpu);
                                                const min = Math.min(...chartData.cpu);
                                                const range = max - min || 1;
                                                const x = (idx / (chartData.cpu.length - 1)) * 280;
                                                const y = 40 - ((val - min) / range) * 40;
                                                return `${x},${y}`;
                                            }).join(' ')}
                                            fill="none"
                                            stroke="#ed8936"
                                            strokeWidth="2"
                                        />
                                    </Svg>
                                )}
                            </View>

                            {/* Memory Usage */}
                            <View style={styles.metricCard}>
                                <Text style={styles.metricLabel}>Memory Usage</Text>
                                <View style={styles.metricValueRow}>
                                    <Text style={[styles.metricValue, { color: '#f56565' }]}>
                                        {metrics.mem_load ? metrics.mem_load.toFixed(1) : '--'}
                                    </Text>
                                    <Text style={styles.metricUnit}>%</Text>
                                </View>
                                {chartData.memory.length > 1 && (
                                    <Svg width={280} height={40} style={styles.miniChart}>
                                        <Polyline
                                            points={chartData.memory.map((val, idx) => {
                                                const max = Math.max(...chartData.memory);
                                                const min = Math.min(...chartData.memory);
                                                const range = max - min || 1;
                                                const x = (idx / (chartData.memory.length - 1)) * 280;
                                                const y = 40 - ((val - min) / range) * 40;
                                                return `${x},${y}`;
                                            }).join(' ')}
                                            fill="none"
                                            stroke="#f56565"
                                            strokeWidth="2"
                                        />
                                    </Svg>
                                )}
                            </View>
                        </View>
                        <Text style={styles.metricsNote}>Updates every 2 seconds</Text>
                    </Section>
                )}

                <View style={{ marginTop: 24, marginBottom: 40 }}>
                    <Button title="Generate Proof Card" onPress={() => onNavigateProof(deviceId)} color="#673ab7" />
                </View>

            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#f5f5f5' },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 12,
        backgroundColor: '#fff',
        justifyContent: 'space-between',
        borderBottomWidth: 1,
        borderBottomColor: '#eee'
    },
    headerTitle: { fontSize: 18, fontWeight: 'bold' },
    content: { padding: 16 },
    section: { marginBottom: 24 },
    sectionTitle: { fontSize: 16, fontWeight: '600', color: '#444', marginBottom: 8 },
    card: { backgroundColor: '#fff', padding: 12, borderRadius: 8 },
    cardTitle: { fontWeight: 'bold', fontSize: 14, marginBottom: 4 },
    cardBody: { fontSize: 14, color: '#555' },

    timelineScroll: { paddingVertical: 8 },
    timelineItem: {
        marginRight: 12,
        backgroundColor: '#e3f2fd',
        padding: 10,
        borderRadius: 8,
        minWidth: 100,
        alignItems: 'center'
    },
    timelineRef: { fontWeight: 'bold', fontSize: 14, color: '#1565c0' },
    timelineType: { fontSize: 12, color: '#1976d2' },
    timelineTime: { fontSize: 10, color: '#555', marginTop: 4 },

    ledgerRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        backgroundColor: '#fff',
        padding: 12,
        borderRadius: 8,
        marginBottom: 8
    },
    ledgerName: { fontSize: 15, fontWeight: 'bold', color: '#333' },
    ledgerReason: { fontSize: 12, color: '#888' },
    badge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
    badgeText: { color: '#fff', fontSize: 10, fontWeight: 'bold' },
    ttlText: { fontSize: 10, color: '#f57c00', marginTop: 2 },

    emptyText: { fontStyle: 'italic', color: '#999' },

    verdictBox: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center'
    },
    verdictTitle: { fontSize: 24, fontWeight: '900' },
    missingItem: { color: '#d32f2f', fontSize: 12, marginTop: 2 },

    // Metrics styles
    metricsGrid: {
        gap: 12,
    },
    metricCard: {
        backgroundColor: '#fff',
        borderRadius: 8,
        padding: 12,
        marginBottom: 8,
    },
    metricLabel: {
        fontSize: 11,
        color: '#888',
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        marginBottom: 4,
        fontWeight: '500',
    },
    metricValueRow: {
        flexDirection: 'row',
        alignItems: 'baseline',
        marginBottom: 8,
    },
    metricValue: {
        fontSize: 24,
        fontWeight: '700',
        marginRight: 6,
    },
    metricUnit: {
        fontSize: 12,
        color: '#666',
    },
    miniChart: {
        marginTop: 4,
    },
    metricsNote: {
        fontSize: 11,
        color: '#999',
        textAlign: 'center',
        marginTop: 8,
        fontStyle: 'italic',
    },
});
