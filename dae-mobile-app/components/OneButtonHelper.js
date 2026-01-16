import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Image, ScrollView } from 'react-native';
import { triggerOBH } from '../src/api';

export default function OneButtonHelper({ onBack }) {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handlePress = async () => {
        setLoading(true);
        setResult(null);
        const data = await triggerOBH();
        setResult(data);
        setLoading(false);
    };

    const renderEvidence = (bundle) => {
        if (!bundle || !bundle.evidence_refs) return null;

        // Filter out "no_flags"
        const failures = bundle.evidence_refs.filter(ref => !ref.includes('no_flags'));

        if (failures.length === 0) {
            return <Text style={styles.noFailuresText}>No flagged evidence refs found.</Text>;
        }

        return failures.map((ref, index) => (
            <Text key={index} style={styles.failureText}>• {ref}</Text>
        ));
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>One Button Helper</Text>
            </View>

            <View style={styles.content}>
                <Text style={styles.guide}>
                    Experiencing an issue? Tap the button below to capture diagnostics and generate a support bundle instantly.
                </Text>

                <TouchableOpacity
                    style={styles.bigButton}
                    onPress={handlePress}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator size="large" color="#FFF" />
                    ) : (
                        <Text style={styles.bigButtonText}>HELP</Text>
                    )}
                </TouchableOpacity>

                <Text style={styles.subtext}>
                    {loading ? "Capturing timeline & metrics..." : "Tap to capture 30 min history"}
                </Text>

                {result && (
                    <ScrollView style={styles.resultBox} contentContainerStyle={{ paddingBottom: 20 }}>
                        {result.error ? (
                            <Text style={styles.errorText}>Error: {result.error}</Text>
                        ) : (
                            <>
                                <Text style={styles.successTitle}>✓ Bundle Exported!</Text>
                                <Text style={styles.label}>Episode ID:</Text>
                                <Text style={styles.value}>{result.episode_id}</Text>
                                <Text style={styles.label}>Location:</Text>
                                <Text style={styles.value}>{result.path}</Text>

                                <Text style={[styles.label, { marginTop: 15 }]}>Failure Evidence:</Text>
                                <View style={styles.jsonBox}>
                                    {renderEvidence(result.bundle)}
                                </View>
                            </>
                        )}
                    </ScrollView>
                )}
            </View>
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
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        padding: 30,
    },
    guide: {
        fontSize: 16,
        textAlign: 'center',
        color: '#555',
        marginBottom: 40,
        lineHeight: 24,
    },
    bigButton: {
        width: 200,
        height: 200,
        borderRadius: 100,
        backgroundColor: '#FF3B30',
        alignItems: 'center',
        justifyContent: 'center',
        shadowColor: "#FF3B30",
        shadowOffset: {
            width: 0,
            height: 10,
        },
        shadowOpacity: 0.5,
        shadowRadius: 10,
        elevation: 20,
        marginBottom: 20,
        alignSelf: 'center'
    },
    bigButtonText: {
        color: '#FFF',
        fontSize: 32,
        fontWeight: '900',
        letterSpacing: 2,
    },
    subtext: {
        color: '#999',
        fontSize: 14,
        marginBottom: 40,
        textAlign: 'center'
    },
    resultBox: {
        flex: 1,
        width: '100%',
        backgroundColor: '#F0F9F0',
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#C8E6C9',
        padding: 15,
    },
    successTitle: {
        color: '#2E7D32',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 10,
        textAlign: 'center',
    },
    label: {
        fontSize: 12,
        color: '#666',
        marginTop: 5,
    },
    value: {
        fontSize: 14,
        color: '#333',
        fontWeight: 'bold',
    },
    errorText: {
        color: 'red',
        textAlign: 'center'
    },
    jsonBox: {
        marginTop: 5,
        backgroundColor: '#fff',
        padding: 10,
        borderRadius: 5,
        borderWidth: 1,
        borderColor: '#eee',
    },
    failureText: {
        fontSize: 12,
        fontFamily: 'monospace',
        color: '#D32F2F',
        marginBottom: 2,
        fontWeight: 'bold'
    },
    noFailuresText: {
        fontSize: 12,
        fontStyle: 'italic',
        color: '#888'
    }
});
