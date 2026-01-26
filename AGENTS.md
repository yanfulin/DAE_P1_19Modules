# AGENTS.md

## 1. Build, Lint, and Test Commands

### Python Backend (Root)
* **Setup:**
  ```bash
  python -m venv venv
  # Windows
  .\venv\Scripts\activate
  # Linux/Mac
  source venv/bin/activate
  ```

* **Install Dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

* **Run Server:**
  ```bash
  # Starts the FastAPI server with hot reload
  uvicorn server:app --reload
  ```

* **Run Tests (Self-Test):**
  ```bash
  # Validates EvidenceBundle.schema.json and fp_lite_output.schema.json
  # Generates TEST_REPORT_10RUNS.md
  python run_self_test.py --runs 10
  ```

* **Verification Scripts:**
  - `python update_capability_map.py`: Regenerates `CAPABILITY_MAP.md` from CSV.
  - `python install_verify_run.py <bundle.json>`: Verifies installation (default 3 mins).
  - `python verify_api.py`: Verification script for API endpoints.

### Mobile App (`dae-mobile-app/`)
* **Setup:**
  ```bash
  cd dae-mobile-app
  npm install
  ```

* **Run Development Server:**
  ```bash
  npx expo start
  ```

---

## 2. Code Style Guidelines

### Python (General)
* **Standard:** Adhere to PEP 8.
* **Formatting:** Use 4 spaces for indentation.
* **Type Hinting:** Strongly encouraged for function arguments and return types.
  ```python
  def get_metrics_history(limit: int = 20) -> list:
      ...
  ```
* **Async/Await:** This project heavily utilizes `asyncio` and `FastAPI`. Ensure non-blocking I/O operations are awaited.

### Imports
* **Ordering:**
  1. Standard Library (`asyncio`, `logging`, `contextlib`)
  2. Third-Party Libraries (`fastapi`, `uvicorn`)
  3. Local Application Modules (`dae_p1.core_service`, `dae_p1.adapters`)
* **Style:** Absolute imports preferred over relative imports for clarity.

### Naming Conventions
* **Variables/Functions:** `snake_case` (e.g., `run_core_loop`, `background_task`).
* **Classes:** `PascalCase` (e.g., `OBHCoreService`, `WindowsWifiAdapter`).
* **Constants:** `UPPER_CASE` (though not explicitly seen, standard convention applies).

### Error Handling & Logging
* **Logging:** Use the standard `logging` module. Do not use `print` for production logs.
  ```python
  import logging
  logger = logging.getLogger(__name__)
  logger.info("Starting Core Loop")
  logger.error(f"Error in tick: {e}")
  ```
* **Exceptions:** Handle specific exceptions where possible. In background loops, catch generic `Exception` to prevent the loop from crashing, but log the error.

### Project Architecture Patterns
* **Core vs. Adapters:**
  - **Core (`dae_p1/core_service.py`):** Contains business logic and semantics.
  - **Adapters (`dae_p1/adapters/`):** Provide raw observations only. Do not put business logic here.
* **Capabilities:**
  - Capability definitions are mapped in `capabilities/capability_dictionary.csv`.
  - Always run `python update_capability_map.py` if you modify capability mappings.

---

## 3. Directory Structure Key
* `dae_p1/`: Core module logic.
* `dae-mobile-app/`: React Native (Expo) mobile application.
* `capabilities/`: Documentation and CSVs for feature mapping.
* `schemas/`: JSON schemas for validation.
* `server.py`: Main entry point for the FastAPI backend.
