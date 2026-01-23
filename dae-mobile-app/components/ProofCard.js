
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, Button, ActivityIndicator, Share, Platform, ScrollView } from 'react-native';
import { fetchProofData, fetchManifest } from '../src/api';

export default function ProofCard({ deviceId, onBack }) {
    const [proof, setProof] = useState(null);
    const [manifest, setManifest] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const load = async () => {
            try {
                // Fetch both Proof and Manifest in parallel
                const [proofData, manifestData] = await Promise.all([
                    fetchProofData(deviceId),
                    fetchManifest(deviceId)
                ]);

                if (!proofData) throw new Error("Failed to fetch proof data");
                setProof(proofData);

                // Manifest is optional but good to have
                if (manifestData) setManifest(manifestData);

            } catch (err) {
                setError(err.message);
            }
            setLoading(false);
        };
        load();
    }, [deviceId]);

    const handleShare = async () => {
        if (!proof) return;
        const msg = {
            proof: proof,
            manifest: manifest
        };
        try {
            await Share.share({
                message: JSON.stringify(msg, null, 2),
                title: proof.proof_card_ref || "DAE Proof Card"
            });
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <ActivityIndicator size="large" color="#673ab7" style={{ marginTop: 50 }} />;
    if (error) return <Text style={{ marginTop: 50, textAlign: 'center', color: 'red' }}>Error: {error}</Text>;
    if (!proof) return <Text style={{ marginTop: 50, textAlign: 'center' }}>Failed to generate proof.</Text>;

    const isReady = proof.verdict === 'READY';
    const verdictColor = isReady ? '#2e7d32' : (proof.verdict === 'INSUFFICIENT_EVIDENCE' ? '#f57f17' : '#c62828');

    // Helper to render stats
    const renderStat = (stats) => {
        if (!stats || stats.length === 0) return <Text style={styles.value}>N/A</Text>;
        return stats.map((s, idx) => (
            <Text key={idx} style={styles.value}>
                {s.name}: {s.value} {s.unit === 'auto' ? '' : s.unit}
            </Text>
        ));
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="Close" onPress={onBack} color="#333" />
                <Text style={styles.headerTitle}>DAE Proof Card V1.3</Text>
                <Button title="Share" onPress={handleShare} />
            </View>

            <ScrollView contentContainerStyle={styles.cardContainer}>
                <View style={styles.card}>
                    <Text style={styles.cardRef}>{proof.proof_card_ref}</Text>
                    <Text style={styles.profileRef}>Profile: {proof.profile_ref}</Text>

                    <View style={styles.divider} />

                    <View style={styles.row}>
                        <Text style={styles.label}>Window:</Text>
                        <Text style={styles.value}>{proof.window_ref}</Text>
                    </View>
                    <View style={styles.row}>
                        <Text style={styles.label}>Samples:</Text>
                        <Text style={styles.value}>{proof.sample_count}</Text>
                    </View>

                    <View style={styles.divider} />

                    <Text style={styles.sectionHeader}>Key Outcome (Facet)</Text>
                    <View style={styles.statBox}>
                        {renderStat(proof.outcome_facet)}
                    </View>

                    {/* Expandable stats could go here, for now show p95 if NOT_READY to explain why */}
                    {!isReady && proof.p95 && (
                        <>
                            <Text style={styles.sectionHeader}>Critical Stats (p95)</Text>
                            <View style={styles.statBox}>
                                {renderStat(proof.p95)}
                            </View>
                        </>
                    )}

                    <View style={styles.divider} />

                    <View style={styles.resultBox}>
                        <Text style={styles.label}>Compliance Verdict</Text>
                        <Text style={[styles.verdict, { color: verdictColor }]}>
                            {proof.verdict}
                        </Text>
                        <Text style={styles.subVerdict}>
                            Reasons: {proof.reason_code ? proof.reason_code.join(", ") : "None"}
                        </Text>
                    </View>

                    <View style={styles.manifestBox}>
                        <Text style={styles.manifestLabel}>Manifest Ref:</Text>
                        <Text style={styles.manifestValue}>{proof.manifest_ref}</Text>

                        {manifest && (
                            <>
                                <View style={{ marginTop: 8 }} />
                                <Text style={styles.manifestLabel}>Bundle Pointer:</Text>
                                <Text style={styles.manifestValue}>{manifest.bundle_pointer}</Text>

                                <View style={{ marginTop: 8 }} />
                                <Text style={styles.manifestLabel}>Available Days:</Text>
                                <Text style={styles.manifestValue}>
                                    {manifest.available_day_refs ? manifest.available_day_refs.join(", ") : "None"}
                                </Text>
                            </>
                        )}
                    </View>

                </View>

                <Text style={styles.helperText}>
                    Authorized by {proof.authority_scope_ref || "Unknown Scope"}
                </Text>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#333' },
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
        padding: 20,
        justifyContent: 'center'
    },
    card: {
        backgroundColor: '#fff',
        borderRadius: 16,
        padding: 24,
        elevation: 8,
        ...Platform.select({
            web: { boxShadow: '0px 4px 10px rgba(0, 0, 0, 0.3)' },
            default: {
                shadowColor: '#000',
                shadowOffset: { width: 0, height: 4 },
                shadowOpacity: 0.3,
                shadowRadius: 10,
            },
        }),
    },
    cardRef: { fontSize: 12, color: '#999', textAlign: 'center', fontFamily: 'monospace' },
    profileRef: { fontSize: 18, fontWeight: 'bold', color: '#333', textAlign: 'center', marginBottom: 10 },
    divider: { height: 1, backgroundColor: '#eee', marginVertical: 12 },
    row: { flexDirection: 'row', marginBottom: 8 },
    label: { width: 100, color: '#777', fontWeight: '600' },
    value: { flex: 1, color: '#222' },
    sectionHeader: { fontSize: 14, fontWeight: 'bold', color: '#555', marginTop: 8, marginBottom: 4 },
    statBox: { backgroundColor: '#f0f4f8', padding: 8, borderRadius: 4, marginBottom: 8 },
    resultBox: { alignItems: 'center', backgroundColor: '#f9f9f9', padding: 16, borderRadius: 8 },
    verdict: { fontSize: 24, fontWeight: '900', marginVertical: 4, textAlign: 'center' },
    subVerdict: { fontSize: 14, color: '#555', textAlign: 'center' },
    manifestBox: { marginTop: 12, borderTopWidth: 1, borderTopColor: '#eee', paddingTop: 8 },
    manifestLabel: { fontSize: 10, color: '#aaa' },
    manifestValue: { fontSize: 10, color: '#aaa', fontFamily: 'monospace' },
    helperText: { color: '#aaa', textAlign: 'center', marginTop: 24, fontSize: 12 },
    infoGrid: { marginTop: 15, padding: 10, backgroundColor: '#f9f9f9', borderRadius: 8 },
    infoItem: { flexDirection: 'row', marginBottom: 4 },
    infoLabel: { width: 80, fontSize: 11, color: '#666', fontWeight: 'bold' },
    infoValue: { flex: 1, fontSize: 11, color: '#444' }
});
