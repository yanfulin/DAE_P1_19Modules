# DAE P1 - 19 Modules 介面文檔

## 概述

DAE P1 系統包含 **19 個模組 (M01-M19)** 和 **20 個能力 (C01-C20)**，專注於檢測、識別、證據凍結/導出、不透明風險標記和 fp-lite 參考。

**核心理念**: 無修復、無網路控制、無優化 - 僅偵測和證據收集。

---

## 核心數據結構 (M00_common.py)

### 基礎類型

#### `VersionRefs`
```python
@dataclass
class VersionRefs:
    fw: str = "unknown"
    driver: str = "unknown"
    agent: str = "dae_p1/0.1.0"
```

#### `MetricSample`
```python
@dataclass
class MetricSample:
    ts: float
    window_ref: str
    latency_p95_ms: Optional[float] = None
    loss_pct: Optional[float] = None
    retry_pct: Optional[float] = None
    airtime_busy_pct: Optional[float] = None
    roam_count: Optional[int] = None
    mesh_flap_count: Optional[int] = None
    wan_sinr_db: Optional[float] = None
    wan_rsrp_dbm: Optional[float] = None
    wan_reattach_count: Optional[int] = None
    jitter_ms: Optional[float] = None
    in_rate: Optional[float] = None
    out_rate: Optional[float] = None
    cpu_load: Optional[float] = None
    mem_load: Optional[float] = None
    signal_strength_pct: Optional[int] = None
```

#### `ChangeEventCard`
```python
@dataclass
class ChangeEventCard:
    event_time: float
    event_type: str
    origin_hint: str = "unknown"
    trigger: str = "unknown"
    target_scope: str = "unknown"
    change_ref: Optional[str] = None
    version_refs: VersionRefs = field(default_factory=VersionRefs)
    window_ref: Optional[str] = None
```

#### `PreChangeSnapshot`
```python
@dataclass
class PreChangeSnapshot:
    snapshot_ref_id: str
    snapshot_scope: str
    capture_time: float
    snapshot_digest: str
    snapshot_type: str = "periodic"
    readable_fields: Dict[str, Any] = field(default_factory=dict)
```

#### `ObservabilityResult`
```python
@dataclass
class ObservabilityResult:
    observability_status: Literal["SUFFICIENT","INSUFFICIENT"]
    opaque_risk: bool
    missing_refs: List[str] = field(default_factory=list)
    origin_hint: str = "unknown"
```

#### `EpisodeRecognition`
```python
@dataclass
class EpisodeRecognition:
    episode_id: str
    episode_start: float
    worst_window_ref: str
    primary_verdict: Verdict
    confidence: float
    evidence_refs: List[str]
    observability: ObservabilityResult
```

#### `Verdict` 類型
```python
Verdict = Literal["WAN_UNSTABLE","WIFI_CONGESTION","MESH_FLAP","DFS_EVENT","OPAQUE_RISK","UNKNOWN"]
```

### 工具函數

- `now_ts() -> float` - 獲取當前時間戳
- `iso(ts: Optional[float]=None) -> str` - 轉換為 ISO 時間格式
- `sha256_str(s: str) -> str` - 計算 SHA256 雜湊
- `ensure_dir(p: str) -> None` - 確保目錄存在
- `to_json(obj: Any) -> str` - 轉換為 JSON 字串

---

## M01 - 視窗管理 (M01_windowing.py)

### `WindowPolicy`
```python
@dataclass
class WindowPolicy:
    ws_sec: int = 10  # 短視窗 10 秒
    wl_sec: int = 60  # 長視窗 60 秒
```

### `Windowing`
```python
class Windowing:
    def __init__(self, policy: WindowPolicy = WindowPolicy())
    
    def window_ref(self, ts: float, kind: str = "Ws") -> str:
        """生成視窗參考標識符 (Ws:timestamp 或 Wl:timestamp)"""
    
    def current_refs(self) -> Tuple[str, str]:
        """返回當前的 (Ws, Wl) 視窗參考"""
```

**用途**: 生成 10 秒 (Ws) 和 60 秒 (Wl) 視窗的參考標識符

---

## M02 - 環形緩衝區 (M02_ring_buffer.py)

### `RingBuffer[T]`
```python
class RingBuffer(Generic[T]):
    def __init__(self, maxlen: int)
    
    def append(self, item: T) -> None:
        """添加項目到緩衝區"""
    
    def snapshot(self) -> List[T]:
        """獲取當前緩衝區的快照"""
    
    def last(self) -> Optional[T]:
        """獲取最後一個項目"""
    
    def __len__(self) -> int:
        """獲取緩衝區大小"""
```

**用途**: 固定大小的環形緩衝區，儲存最新的 N 個項目

---

## M03 - 指標收集器 (M03_metrics_collector.py)

### `MetricsCollector`
```python
class MetricsCollector:
    def __init__(self, windowing: Windowing)
    
    def collect(self,
                latency_p95_ms: Optional[float]=None,
                loss_pct: Optional[float]=None,
                retry_pct: Optional[float]=None,
                airtime_busy_pct: Optional[float]=None,
                roam_count: Optional[int]=None,
                mesh_flap_count: Optional[int]=None,
                wan_sinr_db: Optional[float]=None,
                wan_rsrp_dbm: Optional[float]=None,
                wan_reattach_count: Optional[int]=None,
                jitter_ms: Optional[float]=None,
                in_rate: Optional[float]=None,
                out_rate: Optional[float]=None,
                cpu_load: Optional[float]=None,
                mem_load: Optional[float]=None,
                signal_strength_pct: Optional[int]=None) -> MetricSample:
        """收集指標樣本"""
```

**用途**: 收集僅元數據的指標，在生產環境中替換為平台適配器

---

## M04 - 變更事件記錄器 (M04_change_event_logger.py)

### `ChangeEventLogger`
```python
class ChangeEventLogger:
    def __init__(self, windowing: Windowing, version_refs: VersionRefs)
    
    def record(self, event_type: str, 
               origin_hint: str="unknown", 
               trigger: str="unknown",
               target_scope: str="unknown", 
               change_ref: Optional[str]=None) -> ChangeEventCard:
        """記錄命令/變更事件（僅元數據）"""
```

**用途**: 記錄命令/變更存根（僅元數據），不捕獲有效載荷，僅事件事實

---

## M05 - 快照管理器 (M05_snapshot_manager.py)

### `SnapshotManager`
```python
class SnapshotManager:
    def create_pre_change(self, 
                          snapshot_scope: str, 
                          readable_fields: Dict[str, Any], 
                          snapshot_type: str = "periodic") -> PreChangeSnapshot:
        """創建範圍化的變更前快照（僅參考）"""
```

**用途**: 創建範圍化的變更前快照（僅參考），snapshot_digest 作為穩定參考而不洩露完整配置內容

---

## M06 - 可觀察性檢查器 (M06_observability_checker.py)

### `ObservabilityChecker`
```python
class ObservabilityChecker:
    MIN_REFS = ["origin_hint", "change_ref", "version_refs"]
    
    def check_event(self, ev: ChangeEventCard) -> ObservabilityResult:
        """檢查事件是否有最小可參考的工件"""
    
    def check_no_change_event(self) -> ObservabilityResult:
        """當沒有變更事件時返回不足狀態"""
```

**用途**: 確定變更/事件是否存在最小可參考的工件

---

## M07 - 事件檢測器 (M07_incident_detector.py)

### `DetectorThresholds`
```python
@dataclass
class DetectorThresholds:
    airtime_busy_pct: float = 75.0
    retry_pct: float = 18.0
    latency_p95_ms: float = 60.0
    mesh_flap_per_min: int = 2
    wan_sinr_low_db: float = 5.0
```

### `IncidentDetector`
```python
class IncidentDetector:
    def __init__(self, th: DetectorThresholds = DetectorThresholds())
    
    def badness_flags(self, m: MetricSample) -> List[str]:
        """返回壞信號標記列表"""
    
    def is_bad_window(self, m: MetricSample) -> Tuple[bool, List[str]]:
        """檢測是否為壞視窗（需要 2+ 信號以減少誤報）"""
```

**用途**: 使用僅元數據信號檢測"壞視窗"

---

## M08 - 判決分類器 (M08_verdict_classifier.py)

### `VerdictClassifier`
```python
class VerdictClassifier:
    def classify(self, flags: List[str], opaque_risk: bool=False) -> Tuple[Verdict, float]:
        """從壞信號標記產生最小判決"""
```

**判決類型**:
- `WAN_UNSTABLE` - WAN 不穩定
- `WIFI_CONGESTION` - WiFi 擁塞
- `MESH_FLAP` - Mesh 抖動
- `DFS_EVENT` - DFS 事件
- `OPAQUE_RISK` - 不透明風險
- `UNKNOWN` - 未知

**用途**: 從壞信號標記產生最小判決

---

## M09 - 事件管理器 (M09_episode_manager.py)

### `Episode`
```python
@dataclass
class Episode:
    episode_id: str
    start_ts: float
    worst_window_ref: str
    evidence_refs: List[str]
```

### `EpisodeManager`
```python
class EpisodeManager:
    def __init__(self)
    
    def start_or_update(self, worst_window_ref: str, evidence_ref: str) -> Episode:
        """開始或更新當前事件"""
    
    def get(self) -> Optional[Episode]:
        """獲取當前事件"""
    
    def clear(self) -> None:
        """清除當前事件"""
```

**用途**: 基於壞視窗追蹤當前事件

---

## M10 - 時間軸建構器 (M10_timeline_builder.py)

### `TimelineBuilder`
```python
class TimelineBuilder:
    def build(self,
              metrics: List[MetricSample],
              events: List[ChangeEventCard],
              snapshots: List[PreChangeSnapshot]) -> Dict[str, Any]:
        """建構最後 60 分鐘的扁平化時間軸"""
```

**返回結構**:
```python
{
    "metrics_points": [...],
    "change_events": [...],
    "pre_change_snapshots": [...]
}
```

**用途**: 建構最後 60 分鐘的扁平化時間軸

---

## M11 - 證據包導出器 (M11_bundle_exporter.py)

### `BundleExporter`
```python
class BundleExporter:
    def export(self, out_dir: str, episode_id: str, bundle: Dict[str, Any]) -> str:
        """導出證據包（JSON），無有效載荷"""
```

**用途**: 導出證據包（JSON），無有效載荷

---

## M12 - OBH 控制器 (M12_obh_controller.py)

### `OBHResult`
```python
@dataclass
class OBHResult:
    episode_id: str
    exported_path: str
```

### `OBHController`
```python
class OBHController:
    def __init__(self, timeline_builder: TimelineBuilder, exporter: BundleExporter)
    
    def run(self, out_dir: str, 
            recognition: EpisodeRecognition,
            metrics, events, snapshots) -> OBHResult:
        """執行 OBH: FREEZE_BUFFER + GENERATE_TIMELINE + EXPORT_BUNDLE"""
```

**用途**: 一鍵幫助 (OBH): 凍結緩衝區 + 生成時間軸 + 導出證據包。永不改變網路設定。

---

## M13 - fp-lite 計算 (M13_fp_lite.py)

### 函數介面

```python
def fp_lite_from_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """從證據包計算 fp-lite（before/during/after + BOSD 標籤）"""
```

**返回結構**:
```python
{
    "fp_before": {...},
    "fp_during": {...},
    "fp_after": {...},
    "delta_during_minus_before": {...},
    "delta_after_minus_before": {...},
    "pattern_label": "drift|stability|boundary|oscillation",
    "confidence": 0.0-1.0
}
```

**模式標籤**:
- `drift` - 漂移
- `stability` - 穩定性
- `boundary` - 邊界
- `oscillation` - 振盪

**用途**: fp-lite 計算（before/during/after + BOSD 標籤，僅參考）

---

## M16 - 識別引擎 (M16_recognition_engine.py)

### `RecognitionEngine`
```python
class RecognitionEngine:
    def __init__(self)
    
    def recognize(self, 
                  latest_metric: MetricSample,
                  recent_change_events: List,
                  worst_window_ref: str) -> EpisodeRecognition:
        """產生事件識別：事件 ID、判決、信心度、證據參考和可觀察性狀態"""
```

**用途**: 產生事件識別：事件 ID、判決、信心度、證據參考和可觀察性狀態

---

## M20 - 安裝驗證 (M20_install_verify.py)

### `InstallVerificationResult`
```python
@dataclass
class InstallVerificationResult:
    verify_window_sec: int
    sample_count: int
    readiness_verdict: str  # PASS / MARGINAL / FAIL
    closure_readiness: str  # ready / not_ready
    dominant_factor: str    # WAN / WIFI / MESH / OPAQUE / UNKNOWN
    confidence: float       # 0..1
    fp_vector: Dict[str, float]
```

### `verify_install`
```python
def verify_install(samples: List[MetricSample],
                   verify_window_sec: int = 180) -> InstallVerificationResult:
    """安裝驗證（fp_recognition）：使用最後 verify_window_sec 的 MetricSample 項目"""
```

**判決類型**:
- `PASS` - 通過（loss ≤ 1.0, latency ≤ 60.0, retry ≤ 12.0, flap < 2）
- `MARGINAL` - 邊緣
- `FAIL` - 失敗（loss > 3.0 或 latency > 120.0 或 retry > 25.0 或 flap ≥ 3）

**主導因素**:
- `WAN` - WAN SINR < 5
- `MESH` - Mesh flap ≥ 2
- `WIFI` - Airtime ≥ 75 或 retry ≥ 18
- `UNKNOWN` - 未知

**用途**: 安裝驗證，輸出 PASS/MARGINAL/FAIL 而不規定修復措施

---

## 核心服務 (core_service.py)

### `CoreRuntimeConfig`
```python
@dataclass
class CoreRuntimeConfig:
    sample_interval_sec: int = 10
    buffer_minutes: int = 60
    accelerate: bool = False  # 用於演示/測試加速時間
```

### `OBHCoreService`
```python
class OBHCoreService:
    def __init__(self, adapter: DomainAdapter, config: CoreRuntimeConfig = CoreRuntimeConfig())
    
    def tick_once(self) -> None:
        """執行一次收集週期"""
    
    def run_for(self, seconds: int) -> None:
        """運行收集循環一段時間（最適合演示）"""
    
    def generate_recognition(self) -> EpisodeRecognition:
        """從最新緩衝數據生成識別"""
    
    def obh_export(self, out_dir: str) -> OBHResult:
        """使用當前緩衝區執行 OBH 導出"""
```

**屬性**:
- `metrics_buf: RingBuffer[MetricSample]` - 指標緩衝區
- `events_buf: RingBuffer[ChangeEventCard]` - 事件緩衝區
- `snaps_buf: RingBuffer[PreChangeSnapshot]` - 快照緩衝區

**用途**: OBH 核心運行器，消費 DomainAdapter

---

## API 端點 (server.py)

### 基礎端點

#### `GET /`
```json
{
  "status": "running",
  "service": "DAE_P1 Demo Core"
}
```

#### `GET /metrics`
獲取最新的指標樣本

#### `GET /metrics/history?limit=20`
獲取最近的指標歷史

#### `GET /events`
獲取最近的變更事件

#### `GET /snapshots`
獲取最近的快照

#### `GET /recognition`
觸發並返回識別結果

#### `GET /install_verify`
觸發安裝驗證（閉包準備度）

#### `GET /status`
獲取簡單狀態（ok/unstable/suspected/investigation）

### 艦隊管理端點

#### `GET /fleet`
獲取艦隊中所有設備的列表（1 個真實 + N 個模擬）

**返回結構**:
```json
[
  {
    "id": "local",
    "name": "Local CPE (Real)",
    "current_state": "ok|unstable|suspected|investigating",
    "primary_issue_class": "None|WAN Issue|WIFI Issue|...",
    "closure_readiness": "READY|NOT_READY",
    "last_change_ref": "T-1m",
    "feature_deltas": ["BandSteering: OFF"]
  }
]
```

#### `GET /device/{device_id}`
獲取設備的詳細下鑽信息

**返回結構**:
```json
{
  "id": "local",
  "obh_snapshot_timeline": [
    {"ref": "S-100", "type": "post-install", "time": 1000}
  ],
  "cohort_compare": {
    "status": "normal|outlier",
    "message": "Behaving as expected for Model X v2.1"
  },
  "feature_ledger": [
    {"feature": "BandSteering", "state": "ON", "reason": "Default", "ttl": null}
  ],
  "compliance_verdict": {
    "result": "PASS|FAIL",
    "evidence_missing": []
  }
}
```

#### `GET /device/{device_id}/proof`
獲取證明卡摘要

**返回結構**:
```json
{
  "title": "Proof Card - local",
  "timestamp": "Now",
  "trigger_summary": "...",
  "snapshot_refs": ["S-100", "S-105"],
  "feature_ledger_summary": "2 features tracked",
  "closure_readiness": "READY|NOT_READY",
  "vendor_compliance_verdict": "PASS|FAIL"
}
```

---

## 能力對應表

| 能力 | 描述 | 模組 |
|------|------|------|
| C01 | 始終在線的滾動緩衝區（60 分鐘）- 指標採樣（10 秒） | M02, M03, M01 |
| C02 | 始終在線的滾動緩衝區 - 事件卡（命令/變更存根） | M02, M04, M01 |
| C03 | 命令/變更事件捕獲（帶 origin/trigger/scope 存根） | M04, M01 |
| C04 | 範圍化的變更前快照參考（僅參考，無回滾） | M05 |
| C05 | 版本參考捕獲（fw/driver/agent） | M00, M04 |
| C06 | 視窗參考生成（Ws/Wl） | M01 |
| C07 | 壞視窗檢測（多信號） | M07 |
| C08 | 最小判決分類（WAN/WiFi/Mesh/DFS/Opaque/Unknown） | M08 |
| C09 | 事件追蹤（episode_id、最壞視窗、證據參考） | M09, M16 |
| C10 | 可觀察性檢查（最小參考存在？） | M06 |
| C11 | 不透明風險標記（可觀察性不足 → opaque_risk） | M06, M16 |
| C12 | 扁平化事件時間軸生成（指標 + 事件 + 快照） | M10 |
| C13 | OBH: 凍結數據（緩衝區快照）+ 事件綁定 | M12, M09, M16 |
| C14 | 證據包導出（JSON） | M11, M12 |
| C15 | fp-lite 計算（before/during/after + BOSD 標籤） | M13 |
| C16 | 證據包讀取器（加載） | M14 |
| C17 | 離線 fp-lite CLI 工具 | M15 |
| C18 | 演示模擬器 + 演示運行器（無硬體） | M17, demo_run.py |
| C19 | Schema 附錄 + JSON Schemas | SCHEMA_APPENDIX.md, schemas/*.schema.json |
| C20 | 應用集成指南（離線/應用執行模型） | M18 |

---

## 使用流程

### 1. 初始化核心服務
```python
from dae_p1.adapters.windows_wifi_adapter import WindowsWifiAdapter
from dae_p1.core_service import OBHCoreService, CoreRuntimeConfig

adapter = WindowsWifiAdapter()
cfg = CoreRuntimeConfig(sample_interval_sec=1, buffer_minutes=60, accelerate=True)
core = OBHCoreService(adapter, cfg)
```

### 2. 運行收集循環
```python
# 方式 1: 運行指定時間
core.run_for(seconds=300)

# 方式 2: 手動控制（用於異步環境）
while True:
    core.tick_once()
    await asyncio.sleep(1)
```

### 3. 生成識別
```python
recognition = core.generate_recognition()
print(f"Episode ID: {recognition.episode_id}")
print(f"Verdict: {recognition.primary_verdict}")
print(f"Confidence: {recognition.confidence}")
```

### 4. 執行 OBH 導出
```python
result = core.obh_export(out_dir="./out")
print(f"Exported to: {result.exported_path}")
```

### 5. 安裝驗證
```python
from dae_p1.M20_install_verify import verify_install

metrics_snapshot = core.metrics_buf.snapshot()
result = verify_install(metrics_snapshot)
print(f"Readiness: {result.readiness_verdict}")
print(f"Closure: {result.closure_readiness}")
print(f"Dominant Factor: {result.dominant_factor}")
```

---

## 適配器介面

### `DomainAdapter` (基礎類)
```python
class DomainAdapter:
    def collect_metric_sample(self) -> MetricSample:
        """收集當前指標樣本"""
    
    def collect_change_events_and_snapshots(self) -> Tuple[List[ChangeEventCard], List[PreChangeSnapshot]]:
        """收集變更事件和快照"""
```

### 實現示例
- `WindowsWifiAdapter` - Windows WiFi 適配器（使用 netsh wlan）
- `DemoAdapter` - 演示適配器（模擬數據）

---

## 狀態計算

### 簡單狀態 (status_helper.py)
```python
def calculate_simple_status(core: OBHCoreService) -> str:
    """計算簡單狀態: ok/unstable/suspected/investigation"""
```

**狀態定義**:
- `ok` - 正常
- `unstable` - 不穩定（檢測到壞視窗）
- `suspected` - 懷疑（持續問題）
- `investigation` - 調查中（嚴重問題）

---

## 注意事項

1. **無修復**: 系統僅檢測和記錄，不執行任何修復操作
2. **無網路控制**: 永不改變網路設定
3. **無優化**: 不提供優化建議
4. **僅元數據**: 所有收集的數據僅為元數據，不包含有效載荷
5. **參考導向**: 使用參考和摘要而非完整數據
6. **不透明風險**: 當可觀察性不足時標記為不透明風險

---

## 相關文檔

- [MODULE_MAP.md](file:///d:/OneDrive%20-%20ubeeinteractive.com/%E6%A1%8C%E9%9D%A2/vince/DAE_P1_19Modules/MODULE_MAP.md) - 模組對應表
- [CAPABILITY_MAP.md](file:///d:/OneDrive%20-%20ubeeinteractive.com/%E6%A1%8C%E9%9D%A2/vince/DAE_P1_19Modules/CAPABILITY_MAP.md) - 能力對應表
- [SCHEMA_APPENDIX.md](file:///d:/OneDrive%20-%20ubeeinteractive.com/%E6%A1%8C%E9%9D%A2/vince/DAE_P1_19Modules/SCHEMA_APPENDIX.md) - Schema 附錄
- [README.md](file:///d:/OneDrive%20-%20ubeeinteractive.com/%E6%A1%8C%E9%9D%A2/vince/DAE_P1_19Modules/README.md) - 專案 README
