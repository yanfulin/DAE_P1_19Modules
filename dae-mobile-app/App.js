import React, { useEffect, useState } from 'react';
import { StyleSheet, SafeAreaView, Platform, StatusBar } from 'react-native';
import FleetView from './components/FleetView';
import DeviceDrilldown from './components/DeviceDrilldown';
import ProofCard from './components/ProofCard';

export default function App() {

  const [currentScreen, setCurrentScreen] = useState('FLEET'); // FLEET, DRILLDOWN, PROOF
  const [selectedDeviceId, setSelectedDeviceId] = useState(null);

  const navigateToDrilldown = (deviceId) => {
    setSelectedDeviceId(deviceId);
    setCurrentScreen('DRILLDOWN');
  };

  const navigateToProof = (deviceId) => {
    // deviceId is available in state, but passing it for clarity
    setCurrentScreen('PROOF');
  };

  const navigateBack = () => {
    if (currentScreen === 'PROOF') {
      setCurrentScreen('DRILLDOWN');
    } else if (currentScreen === 'DRILLDOWN') {
      setCurrentScreen('FLEET');
      setSelectedDeviceId(null);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      {currentScreen === 'FLEET' && (
        <FleetView onNavigate={navigateToDrilldown} />
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
