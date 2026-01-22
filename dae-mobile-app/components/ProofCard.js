import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, Button, ActivityIndicator, Share, Platform, ScrollView, FlatList } from 'react-native';
import { fetchProofData } from '../src/api';

export default function ProofCard({ deviceId, onBack }) {
    const [proof, setProof] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await fetchProofData(deviceId);
                setProof(data);
            } catch (e) {
                console.error("Failed to load proof", e);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, [deviceId]);

    const handleShare = async () => {
        if (!proof) return;
        try {
            await Share.share({
                message: JSON.stringify(proof, null, 2),
                title: `RGAP Proof: ${proof.proof_card_ref || 'Incident'}`
            });
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <View style={styles.center}><ActivityIndicator size="large" color="#673ab7" /></View>;
    
    if (!proof) return (
        <View style={styles.center}>
            <Text style={styles.errorText}>Failed to generate proof.</Text>
            <Button title="Go Back" onPress={onBack} />
        </View>
    );

    // Helper for Verdict Color
    const getVerdictColor = (v) => {
        if (v === 'READY') return '#2e7d32'; // Green
        if (v === 'NOT_READY') return '#c62828'; // Red
        return '#f9a825'; // Yellow/Orange
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="Close" onPress={onBack} color="#333" />
                <Text style={styles.headerTitle}>RGAP ProofCard</Text>
                <Button title="Share" onPress={handleShare} />
            </View>

            <ScrollView contentContainerStyle={styles.scrollContent}>
                <View style={styles.card}>
                    {/* Header Section */}
                    <View style={styles.cardHeader}>
                        <Text style={styles.cardRef}>{proof.proof_card_ref || "UNKNOWN REF"}</Text>
                        <Text style={styles.cardDate}>{proof.window_ref || "No Window"}</Text>
                    </View>

                    {/* Verdict Banner */}
                    <View style={[styles.verdictBox, { backgroundColor: getVerdictColor(proof.verdict) + '20', borderColor: getVerdictColor(proof.verdict) }]}> 
                        <Text style={[styles.verdictLabel, { color: getVerdictColor(proof.verdict) }]}>
                            {proof.verdict}
                        </Text>
                        <Text style={styles.verdictSub}>Closure Readiness</Text>
                    </View>

                    <View style={styles.divider} />

                    {/* Meta Data Grid */}
                    <View style={styles.grid}>
                        <View style={styles.gridItem}>
                            <Text style={styles.label}>Attempt ID</Text>
                            <Text style={styles.value}>{proof.attempt_id || "-"}</Text>
                        </View>
                        <View style={styles.gridItem}>
                            <Text style={styles.label}>Samples</Text>
                            <Text style={styles.value}>{proof.sample_count}</Text>
                        </View>
                        <View style={styles.gridItem}>
                            <Text style={styles.label}>Validity</Text>
                            <Text style={styles.value}>{proof.validity_verdict}</Text>
                        </View>
                    </View>

                    <View style={styles.divider} />

                    {/* Reasons */}
                    {proof.reason_code && proof.reason_code.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Reason Codes</Text>
                            <View style={styles.tagContainer}>
                                {proof.reason_code.map((r, i) => (
                                    <View key={i} style={styles.tag}>
                                        <Text style={styles.tagText}>{r}</Text>
                                    </View>
                                ))}
                            </View>
                        </View>
                    )}

                    {/* Facets Table */}
                    {proof.outcome_facet && proof.outcome_facet.length > 0 && (
                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Outcome Facets</Text>
                            {proof.outcome_facet.map((facet, i) => (
                                <View key={i} style={styles.row}>
                                    <Text style={styles.rowLabel}>{facet.name}</Text>
                                    <Text style={styles.rowValue}>
                                        {typeof facet.value === 'number' ? facet.value.toFixed(1) : facet.value} 
                                        {facet.unit && <Text style={styles.unit}> {facet.unit}</Text>}
                                    </Text>
                                </View>
                            ))}
                        </View>
                    )}
                    
                    {/* Manifest / Footer */}
                    <View style={styles.footer}>
                         <Text style={styles.footerText}>Manifest Ref: {proof.manifest_ref || "N/A"}</Text>
                         <Text style={styles.footerText}>Generated via RGAP v1.3</Text>
                    </View>
                </View>

                <Text style={styles.helperText}>
                    This digital voucher acts as immutable evidence for vendor accountability and dispute resolution.
                </Text>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#121212' }, // Dark theme
    center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#121212' },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        paddingTop: 50,
        backgroundColor: '#1e1e1e',
        borderBottomWidth: 1,
        borderBottomColor: '#333'
    },
    headerTitle: { fontSize: 18, fontWeight: '700', color: '#fff' },
    
    scrollContent: { padding: 16 },
    
    card: {
        backgroundColor: '#1e1e1e',
        borderRadius: 16,
        padding: 20,
        borderWidth: 1,
        borderColor: '#333',
        ...Platform.select({
            web: { boxShadow: '0 4px 12px rgba(0,0,0,0.5)' },
            default: { elevation: 4 }
        })
    },
    cardHeader: { marginBottom: 16 },
    cardRef: { fontSize: 12, color: '#888', textTransform: 'uppercase', letterSpacing: 1 },
    cardDate: { fontSize: 16, fontWeight: 'bold', color: '#fff', marginTop: 4 },
    
    verdictBox: {
        alignItems: 'center',
        padding: 16,
        borderRadius: 8,
        borderWidth: 1,
        marginBottom: 16
    },
    verdictLabel: { fontSize: 24, fontWeight: '900', letterSpacing: 1 },
    verdictSub: { fontSize: 12, color: '#aaa', marginTop: 4, textTransform: 'uppercase' },
    
    divider: { height: 1, backgroundColor: '#333', marginVertical: 16 },
    
    grid: { flexDirection: 'row', justifyContent: 'space-between' },
    gridItem: { alignItems: 'center', flex: 1 },
    label: { fontSize: 11, color: '#666', marginBottom: 4, textTransform: 'uppercase' },
    value: { fontSize: 14, color: '#eee', fontWeight: '600' },
    
    section: { marginBottom: 16 },
    sectionTitle: { fontSize: 14, fontWeight: '700', color: '#888', marginBottom: 12, textTransform: 'uppercase' },
    
    tagContainer: { flexDirection: 'row', flexWrap: 'wrap' },
    tag: { backgroundColor: '#333', paddingVertical: 4, paddingHorizontal: 10, borderRadius: 4, marginRight: 8, marginBottom: 8 },
    tagText: { color: '#ddd', fontSize: 12, fontWeight: '500' },
    
    row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#2a2a2a' },
    rowLabel: { color: '#aaa', fontSize: 14 },
    rowValue: { color: '#fff', fontSize: 14, fontWeight: '600' },
    unit: { fontSize: 12, color: '#666' },
    
    footer: { marginTop: 8, alignItems: 'center' },
    footerText: { fontSize: 10, color: '#444' },
    
    helperText: { color: '#555', textAlign: 'center', marginTop: 24, fontSize: 12, paddingHorizontal: 20 },
    errorText: { color: '#f44336', fontSize: 16, marginBottom: 16 }
});
