import React, { useEffect, useState } from 'react';
import { StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import FleetView from './components/FleetView';
import DeviceDrilldown from './components/DeviceDrilldown';
import ProofCard from './components/ProofCard';
import MetricsView from './components/MetricsView';
import ModuleInspector from './components/ModuleInspector';

export default function App() {

  const [currentScreen, setCurrentScreen] = useState('FLEET'); // FLEET, DRILLDOWN, PROOF, METRICS
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  const navigateToDrilldown = (deviceId) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('DRILLDOWN');
  };

  const navigateToProof = (deviceId) => {
    // deviceId is available in state, but passing it for clarity
    setCurrentScreen('PROOF');
  };

  const navigateToMetrics = () => {
    setCurrentScreen('METRICS');
  };

  const navigateToModules = () => {
    setCurrentScreen('MODULES');
  };

  const navigateBack = () => {
    if (currentScreen === 'PROOF') {
      setCurrentScreen('DRILLDOWN');
    } else if (currentScreen === 'DRILLDOWN') {
      setCurrentScreen('FLEET');
      setSelectedDeviceId(null);
    } else if (currentScreen === 'METRICS') {
      setCurrentScreen('FLEET');
    } else if (currentScreen === 'MODULES') {
      setCurrentScreen('FLEET');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      {currentScreen === 'FLEET' && (
        <FleetView onNavigate={navigateToDrilldown} onNavigateMetrics={navigateToMetrics} onNavigateModules={navigateToModules} />
      )}
      {currentScreen === 'DRILLDOWN' && selectedDeviceId && (
        <DeviceDrilldown
          deviceId={selectedDeviceId}
          onNavigateProof={navigateToProof}
          onBack={navigateBack}
        />
      )}
      {currentScreen === 'PROOF' && selectedDeviceId && (
        <ProofCard
          deviceId={selectedDeviceId}
          onBack={navigateBack}
        />
      )}
      {currentScreen === 'METRICS' && (
        <MetricsView onBack={navigateBack} />
      )}
      {currentScreen === 'MODULES' && (
        <ModuleInspector onBack={navigateBack} />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  }
});
