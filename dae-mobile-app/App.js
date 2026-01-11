import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, ScrollView, RefreshControl, Button, SafeAreaView, Platform, StatusBar } from 'react-native';
import { fetchMetrics, fetchEvents, fetchSnapshots, triggerRecognition } from './src/api';

const MetricCard = ({ label, value, unit = '' }) => (
  <View style={styles.card}>
    <Text style={styles.cardLabel}>{label}</Text>
    <Text style={styles.cardValue}>{value !== undefined ? value : '--'} <Text style={styles.unit}>{unit}</Text></Text>
  </View>
);

const EventItem = ({ event }) => (
  <View style={styles.listItem}>
    <Text style={styles.itemTime}>T={event.change_t}</Text>
    <Text style={styles.itemTitle}>{event.change_type}</Text>
    <Text style={styles.itemSubtitle}>{event.description}</Text>
  </View>
);

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [events, setEvents] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  const loadData = async () => {
    try {
      const m = await fetchMetrics();
      const e = await fetchEvents();

      if (m && !m.error && !m.message) {
        setMetrics(m);
        setConnectionStatus('Connected');
      } else {
        if (m && m.message) {
          setConnectionStatus(`Connected: ${m.message}`);
        } else {
          setConnectionStatus('Backend Unreachable');
        }
      }

      if (e) {
        // Sort by time descending
        setEvents(e.reverse().slice(0, 10));
      }
    } catch (err) {
      setConnectionStatus('Error');
    }
  };

  const onRefresh = React.useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, []);

  // Auto-refresh every 1 second
  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleRecognize = async () => {
    const res = await triggerRecognition();
    alert(JSON.stringify(res, null, 2));
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <View style={styles.header}>
        <Text style={styles.headerTitle}>DAE P1 Dashboard</Text>
        <View style={[styles.badge, { backgroundColor: connectionStatus.startsWith('Connected') ? '#4caf50' : '#f44336' }]}>
          <Text style={styles.badgeText}>{connectionStatus}</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.container}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >

        <Text style={styles.sectionTitle}>Current Metrics (T={metrics?.ts ?? '--'})</Text>
        <View style={styles.grid}>
          <MetricCard label="Down Rate" value={metrics?.in_rate?.toFixed(2)} unit="Mbps" />
          <MetricCard label="Up Rate" value={metrics?.out_rate?.toFixed(2)} unit="Mbps" />
          <MetricCard label="Latency" value={metrics?.latency?.toFixed(1)} unit="ms" />
          <MetricCard label="Jitter" value={metrics?.jitter?.toFixed(1)} unit="ms" />
          <MetricCard label="CPU" value={metrics?.cpu_load?.toFixed(1)} unit="%" />
          <MetricCard label="Memory" value={metrics?.mem_load?.toFixed(1)} unit="%" />
        </View>

        <View style={styles.actions}>
          <Button title="Analyze Episode / Check Verdict" onPress={handleRecognize} />
        </View>

        <Text style={styles.sectionTitle}>Recent Events</Text>
        {events.length === 0 ? (
          <Text style={styles.emptyText}>No recent events</Text>
        ) : (
          events.map((ev, idx) => <EventItem key={idx} event={ev} />)
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
  container: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 24,
    marginBottom: 12,
    color: '#444',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  card: {
    width: '48%',
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardLabel: {
    fontSize: 14,
    color: '#888',
    marginBottom: 8,
  },
  cardValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#222',
  },
  unit: {
    fontSize: 14,
    color: '#666',
    fontWeight: 'normal',
  },
  listItem: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#2196f3',
  },
  itemTime: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  itemTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
  },
  itemSubtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    marginTop: 20,
  },
  actions: {
    marginTop: 20
  }
});
