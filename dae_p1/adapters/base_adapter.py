
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Tuple
from ..M00_common import MetricSample, ChangeEventCard, PreChangeSnapshot

class DomainAdapter(ABC):
    """
    Domain adapter contract.
    Adapters MUST ONLY collect observations and emit standardized artifacts.
    Adapters MUST NOT implement verdict logic, remediation guidance, or control actions.
    """
    @abstractmethod
    def collect_metric_sample(self) -> MetricSample:
        """Collect a metadata-only metric sample mapped to MetricSample."""
        raise NotImplementedError

    @abstractmethod
    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        """Collect recent change events and pre-change snapshot references (scoped, reference-only)."""
        raise NotImplementedError
