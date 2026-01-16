import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, ScrollView } from 'react-native';
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
        if (status === 'READY' || status === 'ready') return '#4CAF50';
        if (status === 'NOT_READY' || status === 'not_ready') return '#F44336';
        return '#757575';
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Installation Verifier</Text>
            </View>

            <ScrollView contentContainerStyle={styles.content}>
                <Text style={styles.description}>
                    Verify the installation quality against the acceptance criteria.
                </Text>

                <TouchableOpacity
                    style={styles.verifyButton}
                    onPress={handleVerify}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator color="#FFF" />
                    ) : (
                        <Text style={styles.verifyButtonText}>VERIFY NOW</Text>
                    )}
                </TouchableOpacity>

                {result && (
                    <View style={styles.resultContainer}>
                        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(result.closure_readiness) }]}>
                            <Text style={styles.statusText}>
                                {result.closure_readiness ? result.closure_readiness.toUpperCase() : 'UNKNOWN'}
                            </Text>
                        </View>

                        <View style={styles.detailRow}>
                            <Text style={styles.label}>Verdict:</Text>
                            <Text style={styles.value}>{result.readiness_verdict}</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.label}>Dominant Factor:</Text>
                            <Text style={styles.value}>{result.dominant_factor}</Text>
                        </View>
                        <View style={styles.detailRow}>
                            <Text style={styles.label}>Confidence:</Text>
                            <Text style={styles.value}>{result.confidence}</Text>
                        </View>

                        {result.metrics_summary && (
                            <View style={styles.metricsContainer}>
                                <Text style={styles.subHeader}>Metrics Summary</Text>
                                <Text style={styles.metricText}>Latency: {result.metrics_summary.avg_latency?.toFixed(1) ?? 'N/A'} ms</Text>
                                <Text style={styles.metricText}>Jitter: {result.metrics_summary.jitter?.toFixed(1) ?? 'N/A'} ms</Text>
                                <Text style={styles.metricText}>Retry: {result.metrics_summary.avg_retry_pct?.toFixed(1) ?? 'N/A'} %</Text>
                            </View>
                        )}
                    </View>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#fff',
    },
    header: {
        padding: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        flexDirection: 'row',
        alignItems: 'center',
    },
    backButton: {
        marginRight: 15,
    },
    backText: {
        fontSize: 16,
        color: '#007AFF',
    },
    title: {
        fontSize: 20,
        fontWeight: 'bold',
    },
    content: {
        padding: 20,
        alignItems: 'center',
    },
    description: {
        fontSize: 16,
        color: '#666',
        textAlign: 'center',
        marginBottom: 30,
    },
    verifyButton: {
        backgroundColor: '#007AFF',
        paddingVertical: 15,
        paddingHorizontal: 40,
        borderRadius: 30,
        width: '100%',
        alignItems: 'center',
        marginBottom: 30,
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
        elevation: 5,
    },
    verifyButtonText: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    resultContainer: {
        width: '100%',
        backgroundColor: '#f9f9f9',
        borderRadius: 15,
        padding: 20,
        alignItems: 'center',
    },
    statusBadge: {
        paddingVertical: 10,
        paddingHorizontal: 30,
        borderRadius: 20,
        marginBottom: 20,
    },
    statusText: {
        color: '#FFF',
        fontSize: 22,
        fontWeight: 'bold',
    },
    detailRow: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        width: '100%',
        marginBottom: 10,
        borderBottomWidth: 1,
        borderBottomColor: '#eee',
        paddingBottom: 5,
    },
    label: {
        fontSize: 16,
        color: '#555',
    },
    value: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    metricsContainer: {
        marginTop: 15,
        width: '100%',
        alignItems: 'flex-start',
    },
    subHeader: {
        fontSize: 16,
        fontWeight: 'bold',
        marginBottom: 5,
        color: '#333',
    },
    metricText: {
        fontSize: 14,
        color: '#666',
        marginBottom: 3,
    }
});
