import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';

export default function HomeDashboard({ onNavigate }) {

    const menuItems = [
        {
            id: 'PROOF',
            title: 'View Proof Card',
            desc: 'Generate V1.3 Proof Card',
            color: '#9C27B0',
            icon: '📜'
        },
        {
            id: 'INSTALL',
            title: 'Installation Verifier',
            desc: 'Validate install quality & readiness',
            color: '#4CAF50',
            icon: '✓'
        },
        {
            id: 'OBH',
            title: 'One Button Helper',
            desc: 'Instant diagnose & capture',
            color: '#FF3B30',
            icon: '⛑'
        },
        {
            id: 'FLEET',
            title: 'Fleet View',
            desc: 'Monitor all devices (Legacy)',
            color: '#007AFF',
            icon: '📱'
        },
        {
            id: 'SIMULATE',
            title: 'Simulate Incident',
            desc: 'Inject faults to test detection',
            color: '#FF9500',
            icon: '⚠'
        }
    ];

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>DAE Field Tool</Text>
                <Text style={styles.headerSubtitle}>Technician Dashboard</Text>
            </View>

            <ScrollView contentContainerStyle={styles.menuContainer}>
                {menuItems.map((item) => (
                    <TouchableOpacity
                        key={item.id}
                        style={[styles.card, { borderLeftColor: item.color }]}
                        onPress={() => onNavigate(item.id)}
                    >
                        <View style={[styles.iconCircle, { backgroundColor: item.color }]}>
                            <Text style={styles.iconText}>{item.icon}</Text>
                        </View>
                        <View style={styles.textContainer}>
                            <Text style={styles.cardTitle}>{item.title}</Text>
                            <Text style={styles.cardDesc}>{item.desc}</Text>
                        </View>
                        <Text style={styles.arrow}>→</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>

            <Text style={styles.footer}>DAE P1 Modules v1.9</Text>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F2F2F7',
    },
    header: {
        paddingTop: 60,
        paddingBottom: 20,
        paddingHorizontal: 20,
        backgroundColor: '#FFF',
        borderBottomWidth: 1,
        borderBottomColor: '#E5E5EA',
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: '800',
        color: '#000',
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#8E8E93',
        fontWeight: '500',
    },
    menuContainer: {
        padding: 20,
    },
    card: {
        backgroundColor: '#FFF',
        borderRadius: 16,
        padding: 20,
        marginBottom: 16,
        flexDirection: 'row',
        alignItems: 'center',
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 2,
        },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
        borderLeftWidth: 6,
    },
    iconCircle: {
        width: 50,
        height: 50,
        borderRadius: 25,
        alignItems: 'center',
        justifyContent: 'center',
        marginRight: 15,
    },
    iconText: {
        fontSize: 24,
        color: '#FFF',
        fontWeight: 'bold',
    },
    textContainer: {
        flex: 1,
    },
    cardTitle: {
        fontSize: 18,
        fontWeight: '700',
        color: '#000',
        marginBottom: 4,
    },
    cardDesc: {
        fontSize: 14,
        color: '#666',
    },
    arrow: {
        fontSize: 24,
        color: '#C7C7CC',
        marginLeft: 10,
    },
    footer: {
        textAlign: 'center',
        padding: 20,
        color: '#999',
        fontSize: 12
    }
});
