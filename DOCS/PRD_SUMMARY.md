# PRD Summary: DAE fp_proof (Free v1)

## 1. Product Overview
**Name**: DAE fp_proof (Internal: fp_recognition)
**Vision**: "We don’t decide what to do. We preserve proof of what happened."
**Core Value Proposition**:
The product provides **validatable proof artifacts** (metadata-only) to support incident handling, disputes, and acceptance testing without taking control of the network, modifying configurations, or assuming liability for detection/remediation.

## 2. Key Capabilities (The "20 Capabilities")
The system maps 19 software modules to 20 operator-facing capabilities (C01–C20), focused on:

### A. Data Capture & Observability
-   **Always-on Rolling Buffer**: Maintains a 60-minute buffer of metrics (10s intervals) and event cards.
-   **Event Capture**: Records command/change events with origin, trigger, and scope stubs.
-   **Snapshot References**: Captures pre-change snapshots (Scoped) and generates Window references (Ws/Wl).
-   **Version References**: Tracks firmware, driver, and agent versions.

### B. Incident Recognition & Analysis
-   **Opaque Risk Flagging**: Identifies when observed behavior lacks referenceable provenance (Attribution boundary).
-   **Minimal Verdict Classification**: Classifies states as WAN, WiFi, Mesh, DFS, Opaque, or Unknown.
-   **Bad-window Detection**: Multi-signal detection of anomalous time windows.
-   **fp-lite Computation**: Generates behavioral fingerprints (before/during/after) with BOSD (Behavior, Origin, Scope, Duration) labels.

### C. Proof Generation & Export
-   **Incident Proof**: "One-Button Help" (OBH) functionality to freeze data and bind it to an episode.
-   **Baseline Proof**: Install verification (default 3 minutes) to validate network state at delivery.
-   **Flattened Timeline**: Generates a timeline combining metrics, events, and snapshots.
-   **Evidence Bundle Export**: Exports all captured data as a JSON bundle for offline analysis.

## 3. System Architecture
### Backend
-   **Tech Stack**: Python, FastAPI.
-   **Core Logic**: Implemented in 19 modules (`dae_p1/M01` to `M19`).
-   **Adapters**: Uses an adapter pattern (`WindowsWifiAdapter` implemented) to abstract underlying hardware/OS metrics.
-   **API**: Exposes endpoints for metrics, events, snapshots, recognition, and fleet management.

### Frontend
-   **Mobile App**: `dae-mobile-app` (likely React Native/Expo) for operator interaction.
-   **Features**:
    -   **Fleet View**: List of devices with status.
    -   **Device Drilldown**: Detailed view of specific devices.
    -   **Proof Card**: Summary of readiness and compliance.
    -   **Install Verify**: Interactive tool for technicians.

## 4. Operational Boundaries (Free v1 Scope)
-   **Metadata-only**: No payload inspection.
-   **No Remediation**: No automatic fixes or suggestions.
-   **No Network Control**: No configuration changes allowed.
-   **No Liability Shielding**: Provides evidence, not legal immunity.

## 5. User Roles
-   **Technician/Operator**: Uses the mobile app/CLI to verify installs and caption incidents.
-   **Engineering/Support**: Uses exported bundles and checking tools to analyze incidents offline.
