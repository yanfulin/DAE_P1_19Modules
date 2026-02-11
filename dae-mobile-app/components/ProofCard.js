
import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, Button, ActivityIndicator, Share, Platform, ScrollView, TouchableOpacity } from 'react-native';
import { fetchProofData, fetchProofDataV14, fetchManifest } from '../src/api';

export default function ProofCard({ deviceId, onBack }) {
    const [proof, setProof] = useState(null);
    const [egress, setEgress] = useState(null);
    const [manifest, setManifest] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('min'); // 'min' | 'priv'

    // Auto-detect V1.4 by presence of attempt_id
    const isV14 = proof && proof.attempt_id !== undefined;

    useEffect(() => {
        const load = async () => {
            try {
                // Try V1.4 first, fall back to V1.3
                const [v14Resp, manifestData] = await Promise.all([
                    fetchProofDataV14(deviceId),
                    fetchManifest(deviceId)
                ]);

                if (v14Resp && v14Resp.proof_card) {
                    setProof(v14Resp.proof_card);
                    setEgress(v14Resp.egress || null);
                } else {
                    // Fallback to V1.3
                    const proofData = await fetchProofData(deviceId);
                    if (!proofData) throw new Error("Failed to fetch proof data");
                    setProof(proofData);
                }

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

    // V1.4 evidence grade colors
    const gradeColors = {
        DELIVERY_GRADE: '#2e7d32',
        PARTIAL_RELIANCE: '#f57f17',
        NOT_CLOSURE_GRADE: '#c62828',
    };
    const gradeColor = isV14 ? (gradeColors[proof.evidence_grade] || '#999') : null;

    // Helper to render stats
    const renderStat = (stats) => {
        if (!stats || stats.length === 0) return <Text style={styles.value}>N/A</Text>;
        return stats.map((s, idx) => (
            <Text key={idx} style={styles.value}>
                {s.name}: {s.value} {s.unit === 'auto' ? '' : s.unit}
            </Text>
        ));
    };

    // V1.4 PC-Min section renderer
    const renderMinSection = () => {
        const min = proof.min;
        if (!min) return null;
        const admColor = min.admission_verdict === 'ADMIT' ? '#2e7d32'
            : min.admission_verdict === 'DEGRADE' ? '#f57f17' : '#c62828';
        return (
            <View style={styles.statBox}>
                <View style={styles.row}>
                    <Text style={styles.label}>Admission:</Text>
                    <Text style={[styles.value, { color: admColor, fontWeight: 'bold' }]}>{min.admission_verdict}</Text>
                </View>
                {min.admission_effect && min.admission_effect !== 'NONE' && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Effect:</Text>
                        <Text style={styles.value}>{min.admission_effect}</Text>
                    </View>
                )}
                <View style={styles.row}>
                    <Text style={styles.label}>Privacy:</Text>
                    <Text style={styles.value}>{min.privacy_check_verdict}</Text>
                </View>
                {min.egress_receipt_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Egress Ref:</Text>
                        <Text style={[styles.value, { fontSize: 10, fontFamily: 'monospace' }]}>{min.egress_receipt_ref}</Text>
                    </View>
                )}
                {min.byuse_context_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>BYUSE:</Text>
                        <Text style={styles.value}>{min.byuse_context_ref}</Text>
                    </View>
                )}
            </View>
        );
    };

    // V1.4 PC-Priv section renderer
    const renderPrivSection = () => {
        const priv = proof.priv;
        if (!priv) return (
            <View style={styles.statBox}>
                <Text style={styles.value}>Priv section not available (egress: MIN_ONLY)</Text>
            </View>
        );
        return (
            <View style={styles.statBox}>
                {priv.privacy_policy_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Policy:</Text>
                        <Text style={[styles.value, { fontSize: 10, fontFamily: 'monospace' }]}>{priv.privacy_policy_ref}</Text>
                    </View>
                )}
                {priv.purpose_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Purpose:</Text>
                        <Text style={styles.value}>{priv.purpose_ref}</Text>
                    </View>
                )}
                {priv.retention_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Retention:</Text>
                        <Text style={styles.value}>{priv.retention_ref}</Text>
                    </View>
                )}
                {priv.disclosure_scope_ref && (
                    <View style={styles.row}>
                        <Text style={styles.label}>Disclosure:</Text>
                        <Text style={styles.value}>{priv.disclosure_scope_ref}</Text>
                    </View>
                )}
                <View style={styles.row}>
                    <Text style={styles.label}>Violation:</Text>
                    <Text style={[styles.value, { color: priv.privacy_violation_flag ? '#c62828' : '#2e7d32' }]}>
                        {priv.privacy_violation_flag ? 'YES' : 'NO'}
                    </Text>
                </View>
            </View>
        );
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Button title="Close" onPress={onBack} color="#333" />
                <Text style={styles.headerTitle}>DAE Proof Card {isV14 ? 'V1.4' : 'V1.3'}</Text>
                <Button title="Share" onPress={handleShare} />
            </View>

            <ScrollView contentContainerStyle={styles.cardContainer}>
                <View style={styles.card}>
                    <Text style={styles.cardRef}>{proof.proof_card_ref}</Text>
                    <Text style={styles.profileRef}>Profile: {proof.profile_ref}</Text>

                    {/* V1.4 Evidence Grade Badge */}
                    {isV14 && (
                        <View style={[styles.gradeBadge, { backgroundColor: gradeColor }]}>
                            <Text style={styles.gradeBadgeText}>{proof.evidence_grade}</Text>
                        </View>
                    )}

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

                    {/* V1.4: PC-Min / PC-Priv Tabs */}
                    {isV14 && (
                        <>
                            <View style={styles.divider} />
                            <View style={styles.tabRow}>
                                <TouchableOpacity
                                    style={[styles.tab, activeTab === 'min' && styles.tabActive]}
                                    onPress={() => setActiveTab('min')}
                                >
                                    <Text style={[styles.tabText, activeTab === 'min' && styles.tabTextActive]}>PC-Min</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={[styles.tab, activeTab === 'priv' && styles.tabActive]}
                                    onPress={() => setActiveTab('priv')}
                                >
                                    <Text style={[styles.tabText, activeTab === 'priv' && styles.tabTextActive]}>PC-Priv</Text>
                                </TouchableOpacity>
                            </View>
                            {activeTab === 'min' ? renderMinSection() : renderPrivSection()}

                            {/* BYUSE upgrade info */}
                            {proof.upgrade_requirements_ref && (
                                <View style={[styles.statBox, { backgroundColor: '#fff3e0' }]}>
                                    <Text style={[styles.sectionHeader, { color: '#e65100' }]}>BYUSE Upgrade Required</Text>
                                    <Text style={styles.value}>Ref: {proof.upgrade_requirements_ref}</Text>
                                    {proof.missing_evidence_class && proof.missing_evidence_class.length > 0 && (
                                        <Text style={styles.value}>Missing: {proof.missing_evidence_class.join(', ')}</Text>
                                    )}
                                </View>
                            )}
                        </>
                    )}

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
    infoValue: { flex: 1, fontSize: 11, color: '#444' },
    gradeBadge: { alignSelf: 'center', paddingHorizontal: 12, paddingVertical: 4, borderRadius: 12, marginTop: 6 },
    gradeBadgeText: { color: '#fff', fontSize: 11, fontWeight: 'bold' },
    tabRow: { flexDirection: 'row', marginBottom: 8 },
    tab: { flex: 1, paddingVertical: 8, alignItems: 'center', backgroundColor: '#f0f0f0', borderRadius: 4, marginHorizontal: 2 },
    tabActive: { backgroundColor: '#673ab7' },
    tabText: { fontSize: 13, color: '#555', fontWeight: '600' },
    tabTextActive: { color: '#fff' },
});
