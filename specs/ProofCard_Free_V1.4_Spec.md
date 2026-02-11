# DAE ProofCard Free on CPE — 工程規格書 V1.4（Privacy / Admissibility Framework）

**Version**: V1.4  
**Status**: Normative  
**Date**: 2026-02-10  
**Extends**: ProofCard V1.3

---

## 0. 適用範圍 (Scope)

本規格書定義 **ProofCard V1.4** 的結構與流程，在 V1.3 基礎上新增 **Privacy Governance Framework**，提供：

- **隱私治理 (Privacy Governance)**：四個 privacy hooks 整合於 ProofCard 生命週期
- **PC-Min / PC-Priv 分層**：最小證明欄位 (PC-Min) 與完整隱私欄位 (PC-Priv)
- **Admissibility Framework**：evidence grading 與 admission verdict 決策
- **BYUSE Upgrade Trigger**：基於用途的升級機制

V1.4 完全向後兼容 V1.3，所有 V1.3 欄位保留。

---

## 1. V1.3 → V1.4 變更摘要 (Change Summary)

### 1.1 新增概念

| 概念 | 說明 |
|------|------|
| **PC-Min** | Minimal ProofCard：僅包含 admission 決策必要欄位 |
| **PC-Priv** | Full Privacy ProofCard：包含完整隱私治理欄位 |
| **Privacy Validity Check** | 四個 privacy hooks 的檢查點：policy, purpose, retention, disclosure |
| **Egress Gate** | 出口閘門：根據請求方身份與目的控制資料釋出 |
| **BYUSE Triggered Upgrade** | "But-You-Said-Earlier" 升級觸發：當用途變更時觸發升級路徑 |

### 1.2 新增欄位群組

- **Attempt Tracking**: `attempt_id`, `enforcement_path_id`
- **Admission Decision**: `admission_verdict`, `admission_effect`, `evidence_grade`
- **Privacy Checks**: `privacy_check_verdict`, `privacy_policy_ref`, `purpose_ref`, `retention_ref`, `disclosure_scope_ref`
- **Egress Control**: `gate_ref`, `egress_receipt_ref`, `redaction_profile_ref`
- **Upgrade Triggers**: `byuse_context_ref`, `upgrade_requirements_ref`, `missing_evidence_class`
- **Privacy Violations**: `privacy_violation_flag`, `privacy_violation_reason_code`

---

## 2. ProofCard V1.4 欄位定義 (Field Definitions)

### 2.1 完整欄位表

| 欄位名稱 | 類型 | 必填 | V1.3 | V1.4 | 說明 |
|----------|------|------|------|------|------|
| `card_id` | string | ✓ | ✓ | ✓ | ProofCard 唯一識別碼 |
| `version` | string | ✓ | ✓ | ✓ | 版本號 (e.g., "1.4") |
| `timestamp` | ISO8601 | ✓ | ✓ | ✓ | 建立時間戳 |
| `cpe_id` | string | ✓ | ✓ | ✓ | CPE 設備識別碼 |
| `account_id` | string | ✓ | ✓ | ✓ | 帳號識別碼 |
| `attempt_id` | string | ✓ | - | ✓ | 本次 ingest 嘗試 ID |
| `enforcement_path_id` | string | - | - | ✓ | 執行路徑追蹤 ID |
| **Evidence Fields** |
| `evidence_type` | string | ✓ | ✓ | ✓ | 證據類型 (e.g., "wifi_metrics") |
| `evidence_grade` | enum | ✓ | - | ✓ | 證據等級：`DELIVERY_GRADE`, `PARTIAL_RELIANCE`, `NOT_CLOSURE_GRADE` |
| `source_module` | string | ✓ | ✓ | ✓ | 來源模組 (e.g., "M19") |
| `collection_method` | string | ✓ | ✓ | ✓ | 收集方法 |
| `data_integrity_hash` | string | ✓ | ✓ | ✓ | 資料完整性雜湊 |
| `chain_of_custody` | array | ✓ | ✓ | ✓ | 保管鏈記錄 |
| **Admission Decision (PC-Min)** |
| `admission_verdict` | enum | ✓ | - | ✓ | `ADMIT`, `DEGRADE`, `DENY` |
| `admission_effect` | string | ✓ | - | ✓ | 決策效果描述 |
| `missing_evidence_class` | array | - | - | ✓ | 缺失證據類別 (for DEGRADE) |
| `upgrade_requirements_ref` | string | - | - | ✓ | 升級需求參考 |
| **Privacy Validity Check (PC-Priv)** |
| `privacy_check_verdict` | enum | ✓ | - | ✓ | `PASS`, `FAIL`, `INCONCLUSIVE` |
| `privacy_policy_ref` | string | - | - | ✓ | Hook 1: 隱私政策參考 |
| `purpose_ref` | string | - | - | ✓ | Hook 2: 用途聲明參考 |
| `retention_ref` | string | - | - | ✓ | Hook 3: 保留期限參考 |
| `disclosure_scope_ref` | string | - | - | ✓ | Hook 4: 揭露範圍參考 |
| `privacy_violation_flag` | boolean | - | - | ✓ | 隱私違規旗標 |
| `privacy_violation_reason_code` | string | - | - | ✓ | 違規原因代碼 |
| **Egress Gate** |
| `gate_ref` | string | - | - | ✓ | 出口閘門參考 |
| `egress_receipt_ref` | string | - | - | ✓ | 出口收據參考 |
| `redaction_profile_ref` | string | - | - | ✓ | 遮蔽配置參考 |
| **BYUSE Context** |
| `byuse_context_ref` | string | - | - | ✓ | BYUSE 升級觸發記錄 |
| **Backward Compatibility (V1.3)** |
| `tamper_seal` | string | ✓ | ✓ | ✓ | 防篡改封印 |
| `validation_status` | enum | ✓ | ✓ | ✓ | 驗證狀態 |
| `metadata` | object | - | ✓ | ✓ | 擴展元資料 |
| `version_refs` | object | - | - | ✓ | 版本間參考連結 |

### 2.2 PC-Min vs PC-Priv

**PC-Min (Minimal ProofCard)** 包含：
- 基本識別：`card_id`, `version`, `timestamp`, `cpe_id`, `account_id`, `attempt_id`
- 證據核心：`evidence_type`, `evidence_grade`, `data_integrity_hash`, `chain_of_custody`
- Admission 決策：`admission_verdict`, `admission_effect`
- 隱私檢查狀態：`privacy_check_verdict`

**PC-Priv (Full Privacy ProofCard)** 額外包含：
- 四個 privacy hooks 的完整參考
- Egress gate 控制欄位
- BYUSE 升級追蹤
- Privacy violation 詳細記錄

---

## 3. Pipeline 流程 (One Spine)

V1.4 定義 **One Spine** 單一主幹流程：

```
┌─────────────────┐
│ ingest_attempt  │ ← 證據進入點
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ load_profile    │ ← 載入 CPE/Account 配置
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ privacy_check   │ ← Privacy Validity Check (4 hooks)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ byuse_qualify   │ ← 檢查用途變更 (BYUSE trigger)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ admission_decide│ ← Admissibility 決策 (ADMIT/DEGRADE/DENY)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ build_proof_card│ ← 組裝 PC-Min 或 PC-Priv
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ egress_gate     │ ← 出口控制 (redaction, disclosure check)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ return          │ ← 返回 ProofCard
└─────────────────┘
```

### 3.1 各節點說明

| 節點 | 輸入 | 輸出 | 說明 |
|------|------|------|------|
| `ingest_attempt` | Raw evidence | `attempt_id` | 記錄嘗試，分配 ID |
| `load_profile` | `cpe_id`, `account_id` | Profile config | 載入隱私政策與用途聲明 |
| `privacy_check` | Evidence + Profile | `privacy_check_verdict` | 檢查四個 hooks：policy, purpose, retention, disclosure |
| `byuse_qualify` | Current purpose vs history | `byuse_context_ref` | 偵測用途變更，觸發升級 |
| `admission_decide` | Evidence readiness + Privacy | `admission_verdict`, `evidence_grade` | 決定 ADMIT/DEGRADE/DENY |
| `build_proof_card` | All checks | ProofCard (PC-Min/PC-Priv) | 組裝 ProofCard 結構 |
| `egress_gate` | ProofCard + Request context | Final ProofCard | 根據請求方套用遮蔽 |
| `return` | Final ProofCard | HTTP 200/403/451 | 返回結果 |

---

## 4. Verdict Mapping 表 (TABLE 0)

| 主 Verdict | Evidence Status | Privacy Check | BYUSE Trigger | → Evidence Grade | → Admission Verdict | 說明 |
|-----------|----------------|---------------|---------------|-----------------|--------------------|----|
| **Case A** | READY | PASS | No | `DELIVERY_GRADE` | `ADMIT` | 完整證據，通過隱私，無用途變更 |
| **Case B** | READY | PASS | Yes | `PARTIAL_RELIANCE` | `ADMIT` | 完整證據，但觸發 BYUSE 升級 |
| **Case C** | NOT_READY | PASS | - | `NOT_CLOSURE_GRADE` | `DEGRADE` | 證據未完整，但隱私合規 |
| **Case D** | INSUFFICIENT | PASS | - | `NOT_CLOSURE_GRADE` | `DEGRADE` | 證據不足，但隱私合規 |
| **Case E** | READY | FAIL | - | `NOT_CLOSURE_GRADE` | `DENY` | 證據完整，但隱私違規 |
| **Case F** | READY | INCONCLUSIVE | - | `NOT_CLOSURE_GRADE` | `DEGRADE` | 證據完整，但隱私狀態不明 |
| **Case G** | NOT_READY | FAIL | - | `NOT_CLOSURE_GRADE` | `DENY` | 證據與隱私雙重不合格 |
| **Case H** | INSUFFICIENT | FAIL | - | `NOT_CLOSURE_GRADE` | `DENY` | 證據不足且隱私違規 |

### 4.1 Evidence Grade 定義

| Grade | 定義 | 可用性 |
|-------|------|--------|
| `DELIVERY_GRADE` | 完整證據，通過所有檢查，無升級需求 | 可直接用於法律/保險場景 |
| `PARTIAL_RELIANCE` | 證據完整但有用途限制或 BYUSE 觸發 | 需額外授權或升級 |
| `NOT_CLOSURE_GRADE` | 證據不完整或隱私未通過 | 僅供內部參考，不可對外 |

---

## 5. 10 Case 測例表 (TABLE 1)

| Case ID | Privacy Refs | BYUSE Trigger | Egress Request | Evidence Status | 預期 Privacy Verdict | 預期 Admission Verdict | 預期 Evidence Grade |
|---------|-------------|---------------|----------------|-----------------|---------------------|----------------------|---------------------|
| **T1** | All 4 hooks valid | No | Internal diagnostics | READY | PASS | ADMIT | DELIVERY_GRADE |
| **T2** | All 4 hooks valid | Yes (purpose changed) | Insurance claim | READY | PASS | ADMIT | PARTIAL_RELIANCE |
| **T3** | Missing retention_ref | No | Support dashboard | NOT_READY | INCONCLUSIVE | DEGRADE | NOT_CLOSURE_GRADE |
| **T4** | Purpose mismatch | No | Legal request | READY | FAIL | DENY | NOT_CLOSURE_GRADE |
| **T5** | Disclosure scope violation | No | Third-party API | READY | FAIL | DENY | NOT_CLOSURE_GRADE |
| **T6** | All valid | No | External audit (redact PII) | READY | PASS | ADMIT | DELIVERY_GRADE |
| **T7** | Retention expired | No | Historical query | INSUFFICIENT | FAIL | DENY | NOT_CLOSURE_GRADE |
| **T8** | All valid | Yes (scope expanded) | Marketing analytics | READY | PASS | ADMIT | PARTIAL_RELIANCE |
| **T9** | Policy ref not found | No | Compliance check | NOT_READY | INCONCLUSIVE | DEGRADE | NOT_CLOSURE_GRADE |
| **T10** | All valid, but BYUSE conflict | Yes (contradictory purpose) | Research study | READY | FAIL | DENY | NOT_CLOSURE_GRADE |

### 5.1 測例說明

- **T1**: 黃金路徑，所有條件滿足
- **T2**: BYUSE 觸發升級，需額外同意
- **T3**: 缺少保留期限，降級但不拒絕
- **T4**: 用途不符，直接拒絕
- **T5**: 揭露範圍違規，拒絕
- **T6**: 通過但需遮蔽 PII
- **T7**: 保留期限過期，拒絕
- **T8**: 範圍擴大觸發 BYUSE
- **T9**: 政策參考遺失，不確定狀態
- **T10**: BYUSE 衝突（矛盾用途），拒絕

---

## 6. 設定檔格式 (Configuration Format)

### 6.1 Privacy Configuration (configs/privacy_v14.yaml)

```yaml
privacy_framework:
  version: "1.4"
  
  # Hook 1: Privacy Policy
  privacy_policy:
    policy_id: "DAE_PRIVACY_2026"
    effective_date: "2026-01-01"
    jurisdiction: "TW"
    consent_mechanism: "explicit_opt_in"
  
  # Hook 2: Purpose Declaration
  purpose_registry:
    - purpose_id: "QOS_MONITORING"
      description: "Network quality monitoring"
      data_classes: ["wifi_metrics", "latency", "packet_loss"]
      retention_days: 90
    - purpose_id: "LEGAL_COMPLIANCE"
      description: "Legal and regulatory compliance"
      data_classes: ["all"]
      retention_days: 2555  # 7 years
    - purpose_id: "INSURANCE_CLAIM"
      description: "Insurance claim evidence"
      data_classes: ["proof_cards", "chain_of_custody"]
      retention_days: 365
  
  # Hook 3: Retention Limits
  retention_policy:
    default_days: 90
    minimum_days: 30
    maximum_days: 2555
    auto_deletion: true
  
  # Hook 4: Disclosure Scope
  disclosure_scope:
    internal_only: ["diagnostics", "support"]
    customer_authorized: ["insurance_claim", "legal_request"]
    third_party_restricted: ["anonymized_research"]
    public_prohibited: ["all_pii"]

  # Egress Gate Rules
  egress_gates:
    - gate_id: "GATE_INTERNAL"
      allowed_purposes: ["QOS_MONITORING", "diagnostics"]
      redaction_profile: "none"
    - gate_id: "GATE_LEGAL"
      allowed_purposes: ["LEGAL_COMPLIANCE"]
      redaction_profile: "minimal"
    - gate_id: "GATE_THIRD_PARTY"
      allowed_purposes: ["INSURANCE_CLAIM"]
      redaction_profile: "high_pii"
  
  # BYUSE Upgrade Triggers
  byuse_triggers:
    - trigger_id: "PURPOSE_CHANGE"
      condition: "purpose_id != original_purpose_id"
      action: "request_reauthorization"
    - trigger_id: "SCOPE_EXPANSION"
      condition: "new_scope > declared_scope"
      action: "upgrade_to_full_consent"
    - trigger_id: "RETENTION_EXTENSION"
      condition: "new_retention_days > declared_retention_days"
      action: "notify_and_confirm"
```

### 6.2 Admission Decision Rules

```yaml
admission_rules:
  version: "1.4"
  
  evidence_grading:
    DELIVERY_GRADE:
      conditions:
        - evidence_status: "READY"
        - privacy_check: "PASS"
        - byuse_trigger: false
    
    PARTIAL_RELIANCE:
      conditions:
        - evidence_status: "READY"
        - privacy_check: "PASS"
        - byuse_trigger: true
    
    NOT_CLOSURE_GRADE:
      conditions:
        - evidence_status: ["NOT_READY", "INSUFFICIENT"]
        - OR:
          - privacy_check: ["FAIL", "INCONCLUSIVE"]
  
  admission_mapping:
    ADMIT:
      evidence_grades: ["DELIVERY_GRADE", "PARTIAL_RELIANCE"]
      http_status: 200
    
    DEGRADE:
      evidence_grades: ["NOT_CLOSURE_GRADE"]
      conditions:
        - privacy_check: ["PASS", "INCONCLUSIVE"]
      http_status: 206  # Partial Content
    
    DENY:
      evidence_grades: ["NOT_CLOSURE_GRADE"]
      conditions:
        - privacy_check: "FAIL"
      http_status: 451  # Unavailable For Legal Reasons
```

---

## 7. 與 V1.3 的差異 (Differences from V1.3)

### 7.1 完全向後兼容

- 所有 V1.3 欄位保留，沒有 breaking changes
- V1.3 ProofCard 可視為 PC-Min 的子集
- V1.4 系統可讀取 V1.3 ProofCard

### 7.2 新增功能

| 功能 | V1.3 | V1.4 | 說明 |
|------|------|------|------|
| Privacy Hooks | ✗ | ✓ | 四個隱私檢查點 |
| Admission Framework | ✗ | ✓ | Evidence grading 與 verdict |
| BYUSE Trigger | ✗ | ✓ | 用途變更偵測 |
| Egress Gate | ✗ | ✓ | 出口控制與遮蔽 |
| PC-Min/PC-Priv 分層 | ✗ | ✓ | 最小與完整兩種格式 |

### 7.3 遷移建議

1. **V1.3 → V1.4 升級**：
   - 新增 `privacy_v14.yaml` 配置檔
   - 在 pipeline 中插入 `privacy_check` 與 `admission_decide` 節點
   - 更新 ProofCard 結構定義，加入 V1.4 新欄位

2. **V1.3 ProofCard 處理**：
   - 系統自動補充預設值：`privacy_check_verdict = "PASS"`, `admission_verdict = "ADMIT"`
   - `evidence_grade` 預設為 `DELIVERY_GRADE`
   - 記錄 `version_refs` 指向 V1.3 來源

3. **API 版本協商**：
   - Request Header: `X-ProofCard-Version: 1.4` 要求 V1.4 格式
   - 預設返回 PC-Min；`X-ProofCard-Full: true` 返回 PC-Priv

---

## 8. 實作檢查清單 (Implementation Checklist)

- [ ] 實作 One Spine pipeline 的 8 個節點
- [ ] 建立 `privacy_v14.yaml` 配置檔
- [ ] 實作四個 privacy hooks 檢查邏輯
- [ ] 實作 BYUSE trigger 偵測引擎
- [ ] 實作 admission decision 規則引擎
- [ ] 建立 PC-Min 與 PC-Priv 序列化器
- [ ] 實作 egress gate 遮蔽邏輯
- [ ] 建立 TABLE 0 與 TABLE 1 的測試案例
- [ ] 實作 V1.3 向後兼容層
- [ ] 更新 API 文件與版本協商機制

---

## 9. 參考文件 (References)

- ProofCard V1.3 規格書
- DAE Privacy Policy 2026
- GDPR Article 5 (Data Minimization)
- ISO/IEC 29100:2011 Privacy Framework
- NIST Privacy Framework 1.0

---

**END OF SPECIFICATION V1.4**
