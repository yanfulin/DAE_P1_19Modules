import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView, RefreshControl } from 'react-native';
import { checkInstallVerification } from '../src/api';

export default function InstallationVerifier({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleVerify = async () => {
        setLoading(true);
        const data = await checkInstallVerification();
        setResult(data);
        setLoading(false);
    };

    const getStatusColor = (status) => {
        if (status === 'PASS') return '#4CAF50'; // Green
        if (status === 'FAIL') return '#F44336'; // Red
        if (status === 'MARGINAL') return '#FF9800'; // Orange
        return '#757575'; // Grey
    };

    const MetricCard = ({ label, value, unit, limit, isGood }) => (
        <View style={styles.card}>
            <Text style={styles.cardLabel}>{label}</Text>
            <Text style={styles.cardValue}>
                {value !== null && value !== undefined ? value : 'N/A'} 
                <Text style={styles.cardUnit}> {unit}</Text>
            </Text>
            {limit && (
                <Text style={styles.cardLimit}>Limit: {limit}</Text>
            )}
            <View style={[styles.indicator, { backgroundColor: isGood ? '#4CAF50' : '#F44336' }]} />
        </View>
    );

    const InfoRow = ({ label, value, subValue, isGood }) => (
        <View style={styles.infoRow}>
            <View>
                <Text style={styles.infoLabel}>{label}</Text>
                {subValue && <Text style={styles.infoSub}>{subValue}</Text>}
            </View>
            <View style={styles.infoValueContainer}>
                <Text style={[styles.infoValue, { color: isGood ? '#333' : '#F44336' }]}>{value}</Text>
                <Text style={styles.statusIcon}>{isGood ? '✅' : '⚠️'}</Text>
            </View>
        </View>
    );

    // Helpers to parse result safely
    const th = result?.thresholds || {};
    const sys = result?.system_info || {};
    const perf = result?.fp_vector || {};
    const internal = result?.internal_health || {};

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Installation Verifier</Text>
            </View>

            <ScrollView 
                contentContainerStyle={styles.content}
                refreshControl={<RefreshControl refreshing={loading} onRefresh={handleVerify} />}
            >
                <Text style={styles.description}>
                    Verify the installation quality against the acceptance criteria.
                </Text>

                {!result && (
                    <TouchableOpacity
                        style={styles.verifyButton}
                        onPress={handleVerify}
                        disabled={loading}
                    >
                        {loading ? (
                            <ActivityIndicator color="#FFF" />
                        ) : (
                            <Text style={styles.verifyButtonText}>START VERIFICATION</Text>
                        )}
                    </TouchableOpacity>
                )}

                {result && (
                    <>
                        {/* 1. Verdict Banner */}
                        <View style={[styles.banner, { backgroundColor: getStatusColor(result.readiness_verdict) }]}>
                            <Text style={styles.bannerText}>{result.readiness_verdict}</Text>
                            <Text style={styles.bannerSub}>
                                {result.dominant_factor !== 'UNKNOWN' ? result.dominant_factor : 'Installation Status'}
                            </Text>
                        </View>

                        {/* Confidence Bar */}
                        <View style={styles.confidenceContainer}>
                            <Text style={styles.sectionTitle}>Confidence: {(result.confidence * 100).toFixed(0)}%</Text>
                            <View style={styles.progressBarBg}>
                                <View style={[styles.progressBarFill, { width: `${result.confidence * 100}%` }]} />
                            </View>
                        </View>

                        {/* 2. Key Installation Info (System) */}
                        <View style={styles.section}>
                            <Text style={styles.sectionHeader}>KEY INSTALLATION INFO</Text>
                            <View style={styles.cardGrid}>
                                <InfoRow 
                                    label="DNS Status" 
                                    value={sys.dns_status || "Unknown"}
                                    isGood={sys.dns_status === 'OK'} 
                                />
                                <InfoRow 
                                    label="WiFi Channel" 
                                    value={sys.channel ? `Ch ${sys.channel}` : "Scanning..."}
                                    subValue={sys.radio_type ? `Radio: ${sys.radio_type}` : null}
                                    isGood={true} // Info only
                                />
                                <InfoRow 
                                    label="Link Rate (Tx/Rx)" 
                                    value={`${sys.phy_rate_mbps || 0} / ${sys.phy_rx_rate_mbps || 0} Mbps`}
                                    isGood={(sys.phy_rate_mbps || 0) > (th.link_rate_min_mbps || 100)}
                                />
                                <InfoRow 
                                    label="Signal Strength" 
                                    value={`${perf.signal_strength_pct || 0}%`}
                                    isGood={(perf.signal_strength_pct || 0) >= (th.signal_min_pct || 80)}
                                />
                            </View>
                        </View>

                        {/* 3. Performance Metrics */}
                        <View style={styles.section}>
                            <Text style={styles.sectionHeader}>PERFORMANCE METRICS</Text>
                            <View style={styles.grid}>
                                <MetricCard 
                                    label="Latency (P95)" 
                                    value={perf.latency_p95_ms?.toFixed(1)} 
                                    unit="ms"
                                    limit={`< ${th.latency_max_ms || 60}`}
                                    isGood={(perf.latency_p95_ms || 0) <= (th.latency_max_ms || 60)}
                                />
                                <MetricCard 
                                    label="Packet Loss" 
                                    value={perf.loss_pct?.toFixed(1)} 
                                    unit="%"
                                    limit={`< ${th.loss_max_pct || 1.0}`}
                                    isGood={(perf.loss_pct || 0) <= (th.loss_max_pct || 1.0)}
                                />
                                <MetricCard 
                                    label="Retry Rate" 
                                    value={perf.retry_pct?.toFixed(1)} 
                                    unit="%"
                                    limit={`< ${th.retry_max_pct || 12}`}
                                    isGood={(perf.retry_pct || 0) <= (th.retry_max_pct || 12)}
                                />
                                <MetricCard 
                                    label="Mesh Flaps" 
                                    value={perf.mesh_flap_count?.toFixed(0)} 
                                    unit="ev"
                                    limit={`< ${th.mesh_flap_max || 2}`}
                                    isGood={(perf.mesh_flap_count || 0) < (th.mesh_flap_max || 2)}
                                />
                            </View>
                        </View>

                        {/* 4. Internal Diagnostics (Footer) */}
                        <View style={styles.footer}>
                            <Text style={styles.footerTitle}>INTERNAL DIAGNOSTICS</Text>
                            <Text style={styles.footerText}>
                                C01 Buffer: {internal.buffer_health?.count || 0} / {internal.buffer_health?.capacity || 0} samples
                            </Text>
                            <Text style={styles.footerText}>
                                C06 Window Ref (Ws): {internal.window_refs?.Ws || 'N/A'}
                            </Text>
                            <Text style={styles.footerText}>
                                C06 Window Ref (Wl): {internal.window_refs?.Wl || 'N/A'}
                            </Text>
                            <Text style={styles.footerText}>
                                Verify Window: {result.verify_window_sec} sec
                            </Text>
                            
                            <TouchableOpacity style={styles.reverifyButton} onPress={handleVerify}>
                                <Text style={styles.reverifyText}>RE-VERIFY</Text>
                            </TouchableOpacity>
                        </View>
                    </>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F5F5F5',
    },
    header: {
        paddingTop: 50,
        paddingBottom: 15,
        paddingHorizontal: 20,
        backgroundColor: '#FFF',
        borderBottomWidth: 1,
        borderBottomColor: '#E0E0E0',
        flexDirection: 'row',
        alignItems: 'center',
    },
    backButton: {
        marginRight: 15,
        padding: 5,
    },
    backText: {
        fontSize: 16,
        color: '#007AFF',
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#333',
    },
    content: {
        padding: 15,
    },
    description: {
        fontSize: 14,
        color: '#666',
        textAlign: 'center',
        marginBottom: 20,
    },
    verifyButton: {
        backgroundColor: '#007AFF',
        paddingVertical: 15,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 20,
    },
    verifyButtonText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    banner: {
        padding: 20,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 20,
        elevation: 4,
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
    },
    bannerText: {
        fontSize: 32,
        fontWeight: '900',
        color: '#FFF',
        letterSpacing: 1,
    },
    bannerSub: {
        fontSize: 16,
        color: 'rgba(255,255,255,0.9)',
        marginTop: 5,
        fontWeight: '600',
    },
    confidenceContainer: {
        marginBottom: 25,
        paddingHorizontal: 5,
    },
    progressBarBg: {
        height: 10,
        backgroundColor: '#E0E0E0',
        borderRadius: 5,
        overflow: 'hidden',
        marginTop: 8,
    },
    progressBarFill: {
        height: '100%',
        backgroundColor: '#4CAF50',
    },
    section: {
        backgroundColor: '#FFF',
        borderRadius: 12,
        padding: 15,
        marginBottom: 20,
        borderWidth: 1,
        borderColor: '#EEEEEE',
    },
    sectionHeader: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#999',
        marginBottom: 15,
        letterSpacing: 0.5,
    },
    sectionTitle: {
        fontSize: 14,
        fontWeight: 'bold',
        color: '#555',
    },
    cardGrid: {
        gap: 10,
    },
    infoRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingVertical: 12,
        borderBottomWidth: 1,
        borderBottomColor: '#F0F0F0',
    },
    infoLabel: {
        fontSize: 16,
        color: '#333',
        fontWeight: '500',
    },
    infoSub: {
        fontSize: 12,
        color: '#888',
        marginTop: 2,
    },
    infoValueContainer: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    infoValue: {
        fontSize: 16,
        fontWeight: 'bold',
        marginRight: 10,
    },
    statusIcon: {
        fontSize: 16,
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
    },
    card: {
        width: '48%',
        backgroundColor: '#FAFAFA',
        padding: 12,
        borderRadius: 8,
        marginBottom: 10,
        borderWidth: 1,
        borderColor: '#EEE',
    },
    cardLabel: {
        fontSize: 13,
        color: '#666',
        marginBottom: 5,
    },
    cardValue: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#333',
    },
    cardUnit: {
        fontSize: 12,
        fontWeight: 'normal',
        color: '#888',
    },
    cardLimit: {
        fontSize: 11,
        color: '#AAA',
        marginTop: 4,
    },
    indicator: {
        height: 3,
        width: 20,
        marginTop: 8,
        borderRadius: 2,
    },
    footer: {
        padding: 20,
        alignItems: 'center',
    },
    footerTitle: {
        fontSize: 12,
        fontWeight: 'bold',
        color: '#AAA',
        marginBottom: 10,
    },
    footerText: {
        fontSize: 11,
        color: '#BBB',
        marginBottom: 4,
        fontFamily: 'monospace',
    },
    reverifyButton: {
        marginTop: 20,
        padding: 10,
    },
    reverifyText: {
        color: '#007AFF',
        fontSize: 14,
        fontWeight: '600',
    }
});
