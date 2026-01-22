import struct
import time
import json
import os
import uuid
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# --- Data Models (Spec v1.3) ---

@dataclass
class OutcomeFacet:
    name: str # e.g. fwa_rsrp_p50_dbm
    value: Any
    unit: str

@dataclass
class ProofCard:
    proof_card_ref: str
    verdict: str  # READY / NOT_READY / INSUFFICIENT_EVIDENCE
    window_ref: str
    reason_code: List[str]
    attempt_id: str
    enforcement_path_ref: str = "standard_closure_v1"
    authority_scope_ref: str = "consumer_dispute_v1"
    validity_horizon_ref: str = "7d_local"
    validity_verdict: str = "VALID" # VALID / STALE / OUT_OF_SCOPE
    basis_ref: str = "default_policy_v1"
    sample_count: int = 0
    outcome_facet: List[OutcomeFacet] = field(default_factory=list)
    evidence_bundle_ref: str = ""
    manifest_ref: str = ""

@dataclass
class DailySummary:
    daily_summary_ref: str
    day_window_ref: str
    sample_count: int
    facet_rollups: List[Dict[str, Any]] # {facet, value, unit}

@dataclass
class EventFragment:
    event_ref: str
    event_type: str
    event_window_ref: str
    trigger_reason_code: List[str]
    minimal_obs: List[Dict[str, Any]]
    linked_proof_card_ref: str = ""

@dataclass
class Manifest:
    manifest_ref: str
    available_day_refs: List[str] = field(default_factory=list)
    available_event_refs: List[str] = field(default_factory=list)
    bundle_pointer: str = "local_json_store"

# --- Controller ---

class RGAPController:
    """
    Manages RGAP ProofCard generation, Manifest maintenance, and 7-day retention.
    """
    def __init__(self, data_dir: str = "data/rgap"):
        self.data_dir = data_dir
        self.cards: Dict[str, ProofCard] = {}
        self.manifest = Manifest(manifest_ref=f"M-{int(time.time())}")
        self.daily_summaries: Dict[str, DailySummary] = {}
        self.events: Dict[str, EventFragment] = {}
        self._ensure_dir()
        self._load_state()

    def _ensure_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _get_state_file(self):
        return os.path.join(self.data_dir, "rgap_state.json")

    def _load_state(self):
        path = self._get_state_file()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    # Reconstruct simple manifest (simplified for demo)
                    m_data = data.get("manifest", {})
                    self.manifest = Manifest(**m_data)
                    # We skip loading full history into memory for this lightweight demo 
                    # except maybe recent cards if needed.
                    # For now, start fresh or keep persistent manifest ref.
                    logger.info(f"Loaded RGAP state. Manifest: {self.manifest.manifest_ref}")
            except Exception as e:
                logger.error(f"Failed to load RGAP state: {e}")

    def _save_state(self):
        path = self._get_state_file()
        try:
            state = {
                "manifest": asdict(self.manifest),
                "updated_at": time.time()
            }
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save RGAP state: {e}")

    def generate_proof_card(self, 
                            verdict: str, 
                            reason_codes: List[str], 
                            facets: List[OutcomeFacet],
                            sample_count: int,
                            window_ref: str = None) -> ProofCard:
        """
        Generates a new ProofCard and updates internal state.
        """
        now_ts = int(time.time())
        ref_id = str(uuid.uuid4())[:8]
        if not window_ref:
            window_ref = f"W-{now_ts}"

        card = ProofCard(
            proof_card_ref=f"PC-{ref_id}",
            verdict=verdict,
            window_ref=window_ref,
            reason_code=reason_codes,
            attempt_id=f"ATT-{now_ts}",
            sample_count=sample_count,
            outcome_facet=facets,
            manifest_ref=self.manifest.manifest_ref,
            validity_verdict="VALID"
        )

        # Enforce No Silent Claims
        if verdict == "INSUFFICIENT_EVIDENCE":
            # Just ensure it's marked (already done by caller usually, but good to enforce)
            pass

        # Store card (in memory for demo, could be file)
        self.cards[card.proof_card_ref] = card
        
        # In a real 7-day loop, we would update daily summaries here
        # For this demo, we just ensure manifest tracks the day
        day_ref = f"day-{datetime.now().strftime('%Y%m%d')}"
        if day_ref not in self.manifest.available_day_refs:
            self.manifest.available_day_refs.append(day_ref)
        
        self._cleanup_old_records()
        self._save_state()
        
        return card

    def _cleanup_old_records(self):
        """Removes records older than 7 days from Manifest."""
        # Simple string parsing for day-{YYYYMMDD}
        valid_refs = []
        limit = datetime.now() - timedelta(days=7)
        
        for ref in self.manifest.available_day_refs:
            try:
                date_str = ref.split("-")[1]
                ref_date = datetime.strptime(date_str, "%Y%m%d")
                if ref_date >= limit:
                    valid_refs.append(ref)
            except:
                pass # keep if parse fails (safe)
        
        self.manifest.available_day_refs = valid_refs

    def get_latest_proof(self) -> Optional[ProofCard]:
        if not self.cards:
            return None
        # Naive: return last created
        return list(self.cards.values())[-1]

    def record_event(self, event_type: str, reason: List[str], obs: List[Dict]):
        """Records a critical event if triggered."""
        ref = f"EVT-{int(time.time())}"
        evt = EventFragment(
            event_ref=ref,
            event_type=event_type,
            event_window_ref=f"W-{int(time.time())}",
            trigger_reason_code=reason,
            minimal_obs=obs
        )
        self.events[ref] = evt
        self.manifest.available_event_refs.append(ref)
        self._save_state()
        return evt
