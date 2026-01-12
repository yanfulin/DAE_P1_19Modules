import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, Button, ActivityIndicator, Share, Platform } from 'react-native';
import { fetchProofData } from '../src/api';

export default function ProofCard({ deviceId, onBack }) {
    const [proof, setProof] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            const data = await fetchProofData(deviceId);
            setProof(data);
            setLoading(false);
        };
        load();
    }, [deviceId]);

    const handleShare = async () => {
        if (!proof) return;
        try {
            await Share.share({
                message: JSON.stringify(proof, null, 2),
                title: proof.title
            });
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <ActivityIndicator size="large" color="#673ab7" style={{ marginTop: 50 }} />;
    if (!proof) return <Text style={{ marginTop: 50, textAlign: 'center' }}>Failed to generate proof.</Text>;

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="Close" onPress={onBack} color="#333" />
                <Text style={styles.headerTitle}>Proof Generated</Text>
                <Button title="Share" onPress={handleShare} />
            </View>

            <View style={styles.cardContainer}>
                <View style={styles.card}>
                    <Text style={styles.cardTitle}>{proof.title}</Text>
                    <Text style={styles.timestamp}>{proof.timestamp}</Text>

                    <View style={styles.divider} />

                    <View style={styles.row}>
                        <Text style={styles.label}>Trigger:</Text>
                        <Text style={styles.value}>{proof.trigger_summary}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Snapshots:</Text>
                        <Text style={styles.value}>{proof.snapshot_refs.join(", ")}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Ledger:</Text>
                        <Text style={styles.value}>{proof.feature_ledger_summary}</Text>
                    </View>

                    <View style={styles.divider} />

                    <View style={styles.resultBox}>
                        <Text style={styles.label}>Vendor Compliance Verdict</Text>
                        <Text style={[styles.verdict, { color: proof.vendor_compliance_verdict === 'PASS' ? '#2e7d32' : '#c62828' }]}>
                            {proof.vendor_compliance_verdict}
                        </Text>
                        <Text style={styles.subVerdict}>Closure: {proof.closure_readiness}</Text>
                    </View>
                </View>

                <Text style={styles.helperText}>
                    This card serves as immutable proof for incident closures and vendor accountability.
                </Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#333' }, // Dark background for contrast
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        paddingTop: 40,
        backgroundColor: '#fff'
    },
    headerTitle: { fontSize: 16, fontWeight: 'bold' },
    cardContainer: {
        flex: 1,
        padding: 20,
        justifyContent: 'center'
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 24,
        elevation: 8,
        ...Platform.select({
            web: {
                boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.3)',
            },
            default: {
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.3,
                shadowRadius: 10,
            },
        }),
    },
    cardTitle: { fontSize: 22, fontWeight: 'bold', color: '#333', textAlign: 'center' },
    timestamp: { fontSize: 12, color: '#999', textAlign: 'center', marginBottom: 20 },
    divider: { height: 1, backgroundColor: '#eee', marginVertical: 16 },
    row: { flexDirection: 'row', marginBottom: 12 },
    label: { width: 100, color: '#777', fontWeight: '600' },
    value: { flex: 1, color: '#222' },
    resultBox: { alignItems: 'center', backgroundColor: '#f9f9f9', padding: 16, borderRadius: 8 },
    verdict: { fontSize: 24, fontWeight: '900', marginVertical: 4 },
    subVerdict: { fontSize: 14, color: '#555' },
    helperText: { color: '#aaa', textAlign: 'center', marginTop: 24, fontSize: 12 }
});
