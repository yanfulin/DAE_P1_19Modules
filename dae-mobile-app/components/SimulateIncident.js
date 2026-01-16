import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { simulateIncident } from '../src/api';

export default function SimulateIncident({ onBack }) {
    const [selectedType, setSelectedType] = useState('latency');
    const [duration, setDuration] = useState(30);
    const [simulating, setSimulating] = useState(false);
    const [timeLeft, setTimeLeft] = useState(0);

    const incidentTypes = [
        { id: 'latency', label: 'Latency Spike', desc: 'Adds 150ms delay' },
        { id: 'retry', label: 'High Packet Loss', desc: 'Sets retry to 25%' },
        { id: 'airtime', label: 'Airtime Congestion', desc: 'Sets busy to 85%' },
        { id: 'complex', label: 'Complex Incident', desc: 'Latency + Packet Loss' },
    ];

    const handleStartSimulation = async () => {
        setSimulating(true);
        setTimeLeft(duration);

        // Call API
        const res = await simulateIncident(selectedType, duration);
        if (!res) {
            Alert.alert("Error", "Failed to start simulation");
            setSimulating(false);
            return;
        }

        // Start countdown timer locally for UI feedback
        const timer = setInterval(() => {
            setTimeLeft((prev) => {
                if (prev <= 1) {
                    clearInterval(timer);
                    setSimulating(false);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={onBack} style={styles.backButton}>
                    <Text style={styles.backText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Simulate Incident</Text>
            </View>

            <ScrollView contentContainerStyle={styles.content}>
                <Text style={styles.instruction}>
                    Select an incident type to inject faults into the network for testing detection logic.
                </Text>

                <View style={styles.typeContainer}>
                    {incidentTypes.map((type) => (
                        <TouchableOpacity
                            key={type.id}
                            style={[
                                styles.typeButton,
                                selectedType === type.id && styles.typeButtonSelected
                            ]}
                            onPress={() => setSelectedType(type.id)}
                            disabled={simulating}
                        >
                            <Text style={[
                                styles.typeLabel,
                                selectedType === type.id && styles.typeLabelSelected
                            ]}>{type.label}</Text>
                            <Text style={[
                                styles.typeDesc,
                                selectedType === type.id && styles.typeDescSelected
                            ]}>{type.desc}</Text>
                        </TouchableOpacity>
                    ))}
                </View>

                <View style={styles.durationContainer}>
                    <Text style={styles.sectionLabel}>Duration: {duration} seconds</Text>
                    {/* Slider replacment with simple buttons since Slider package might not be installed */}
                    <View style={styles.durationButtons}>
                        <TouchableOpacity onPress={() => setDuration(10)} style={[styles.durBtn, duration === 10 && styles.durBtnActive]} disabled={simulating}><Text style={duration === 10 ? styles.durTxtActive : styles.durTxt}>10s</Text></TouchableOpacity>
                        <TouchableOpacity onPress={() => setDuration(30)} style={[styles.durBtn, duration === 30 && styles.durBtnActive]} disabled={simulating}><Text style={duration === 30 ? styles.durTxtActive : styles.durTxt}>30s</Text></TouchableOpacity>
                        <TouchableOpacity onPress={() => setDuration(60)} style={[styles.durBtn, duration === 60 && styles.durBtnActive]} disabled={simulating}><Text style={duration === 60 ? styles.durTxtActive : styles.durTxt}>60s</Text></TouchableOpacity>
                    </View>
                </View>

                <TouchableOpacity
                    style={[styles.startButton, simulating && styles.startButtonActive]}
                    onPress={handleStartSimulation}
                    disabled={simulating}
                >
                    <Text style={styles.startButtonText}>
                        {simulating ? `RUNNING (${timeLeft}s)` : 'START SIMULATION'}
                    </Text>
                </TouchableOpacity>

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
    },
    instruction: {
        marginBottom: 20,
        color: '#666',
        fontSize: 15,
    },
    typeContainer: {
        marginBottom: 30,
    },
    typeButton: {
        padding: 15,
        borderWidth: 1,
        borderColor: '#ddd',
        borderRadius: 10,
        marginBottom: 10,
        backgroundColor: '#f9f9f9'
    },
    typeButtonSelected: {
        borderColor: '#FF9500',
        backgroundColor: '#FFF8E1',
    },
    typeLabel: {
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
        color: '#333',
    },
    typeLabelSelected: {
        color: '#D87000',
    },
    typeDesc: {
        fontSize: 14,
        color: '#777',
    },
    typeDescSelected: {
        color: '#D87000',
    },
    durationContainer: {
        marginBottom: 30,
    },
    sectionLabel: {
        fontWeight: 'bold',
        fontSize: 16,
        marginBottom: 10,
    },
    durationButtons: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    durBtn: {
        flex: 1,
        padding: 10,
        borderWidth: 1,
        borderColor: '#ddd',
        alignItems: 'center',
        marginHorizontal: 5,
        borderRadius: 8,
    },
    durBtnActive: {
        backgroundColor: '#007AFF',
        borderColor: '#007AFF',
    },
    durTxt: { color: '#333' },
    durTxtActive: { color: '#FFF', fontWeight: 'bold' },
    startButton: {
        marginTop: 10,
        backgroundColor: '#333',
        paddingVertical: 18,
        borderRadius: 12,
        alignItems: 'center',
    },
    startButtonActive: {
        backgroundColor: '#FF3B30',
    },
    startButtonText: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
        letterSpacing: 1,
    },
});
