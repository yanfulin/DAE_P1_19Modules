import React, { useState } from 'react';
import { StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import HomeDashboard from './components/HomeDashboard';
import InstallationVerifier from './components/InstallationVerifier';
import SimulateIncident from './components/SimulateIncident';
import OneButtonHelper from './components/OneButtonHelper';
import FleetView from './components/FleetView';
import DeviceDrilldown from './components/DeviceDrilldown';
import ProofCard from './components/ProofCard';
import MetricsView from './components/MetricsView';
import ModuleInspector from './components/ModuleInspector';

export default function App() {

  const [currentScreen, setCurrentScreen] = useState('HOME');
  // Screens: HOME, INSTALL, SIMULATE, OBH, FLEET, DRILLDOWN, PROOF, METRICS, MODULES
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  const handleNavigate = (screenId) => {
    if (screenId === 'PROOF') {
      setSelectedDeviceId('local');
    }
    setCurrentScreen(screenId);
  };

  const navigateToDrilldown = (deviceId) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('DRILLDOWN');
  };

  const navigateToProof = (deviceId) => {
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
    } else if (['METRICS', 'MODULES'].includes(currentScreen)) {
      // Return to wherever we came from, but for now FLEET is the main legacy parent
      setCurrentScreen('FLEET');
    } else {
      // Default back to Home
      setCurrentScreen('HOME');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />

      {currentScreen === 'HOME' && (
        <HomeDashboard onNavigate={handleNavigate} />
      )}

      {currentScreen === 'INSTALL' && (
        <InstallationVerifier onBack={() => setCurrentScreen('HOME')} />
      )}

      {currentScreen === 'SIMULATE' && (
        <SimulateIncident onBack={() => setCurrentScreen('HOME')} />
      )}

      {currentScreen === 'OBH' && (
        <OneButtonHelper onBack={() => setCurrentScreen('HOME')} />
      )}

      {currentScreen === 'FLEET' && (
        <FleetView
          onNavigate={navigateToDrilldown}
          onNavigateMetrics={navigateToMetrics}
          onNavigateModules={navigateToModules}
          onBack={() => setCurrentScreen('HOME')} // Pass back prop if FleetView supports it, or add button
        />
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
    backgroundColor: '#fff', // Changed to match HomeDashboard
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  }
});
