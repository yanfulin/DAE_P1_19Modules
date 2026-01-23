# DAE ProofCard Free on CPE — 工程規格書 V1.3（Wi‑Fi 7/8 + FWA + Cable Modem）

版本：V1.3（Normative / 規範性）
目的：定義免費版 CPE 在 7 天本地留存下，最小可採信的「結案/對帳收據」資料結構與計算規範。

## 0. 適用範圍

本規格定義 Free-tier CPE 在本地（7 天 ring buffer + SQLite）必須產生、保存、可匯出之最小資料，支援：
• 消費者申訴/退貨/保固/爭議時的最低憑證（不是漂亮報告）
• 運營商 CSR / 工單結案時的最低對帳收據（可選擇硬性綁定）
• 供應鏈究責（晶片/韌體/雲管/回程）時的最小可調取索引
本規格不要求免費版做重分析/重推論；只要求產生可引用的裁決收據與可調取索引。

## 1. 核心原則（必守）

P1｜收據性：任何會影響「可否結案/可否宣稱」的判定，必出且只出一張 ProofCard。
P2｜可否定：ProofCard 必須能被反駁與再計算；缺必要欄位即不得宣稱。
P3｜有效性：必包含權限/時效引用與有效性裁決（validity_verdict）。
P4｜可調取：平常只上報 ProofCard + manifest_ref；需爭議時才拉取 bundle 片段。
P5｜最小揭露：不要求 payload/內容；以 metadata 級統計與事件片段為主。

## 2. 產出物與本地保存

### 2.1 必要產出物（Local Artifacts）

A. ProofCard（每次判定必出）
B. Manifest（可調取索引）
C. 7 天每日摘要（Daily Summary）
D. 關鍵事件片段（Critical Event Fragment，觸發才需）

### 2.2 本地保存（7 天）

CPE SHALL 使用 ring buffer 方式保留 7 天資料（到期覆寫），並以 SQLite（或等價嵌入式 DB）保存：
• 索引鍵：proof_card_ref、window_ref、event_ref、day_window_ref
• 可選：以 CBOR/Protobuf 封裝匯出（可節省 3–5 倍流量）

## 3. ProofCard（每次判定必須產生）

規則：只要系統做出任何會影響「可否結案/可否宣稱」的結論，CPE SHALL 產生且只產生一張 ProofCard。

| 欄位 | 型別 | 是否必填 | 定義（白話） | 規範（MUST/SHALL） |
| :--- | :--- | :--- | :--- | :--- |
| proof_card_ref | string | MUST | 本卡唯一識別碼 | 全域唯一（建議 ULID/UUID）；不可重用。 |
| profile_ref | string | MUST | 領域/情境 Profile | 必須指向本規格附錄的某一 Profile（或運營商擴充）。 |
| verdict | enum | MUST | 裁決結果 | READY / NOT_READY / INSUFFICIENT_EVIDENCE 三選一。 |
| window_ref | string | MUST | 本次判定看的主窗 | 必可重算引用（例如 W2@120s/step10s 或 day_window）。 |
| reason_code[] | string[] | MUST(>=1) | 原因代碼 | open set；至少 1 個；應來自該 profile 的字典。 |
| enforcement_path_ref | string | MUST | 承認路徑/流程路徑 | 指向不可繞過的判定路徑；並在描述中聲明 non_bypassable=true 或等價。 |
| authority_scope_ref | string | MUST | 權限範圍 | 聲明此卡可被用於哪些目的/由誰採信（消費者/CSR/審計/供應鏈）。 |
| validity_horizon_ref | string | MUST | 時效政策引用 | 定義此卡在多久內可採信（例如 7 天留存/48 小時對帳）。 |
| validity_verdict | enum | MUST | 有效性裁決 | VALID / STALE / OUT_OF_SCOPE / COMPROMISED / UNKNOWN。 |
| basis_ref | string | MUST | 口徑/方法引用 | 指向計算口徑版本（window policy、分位數方法、facet 定義）。 |
| sample_count | int | MUST | 樣本數 | 本次計算實際樣本數；低於門檻必輸出 INSUFFICIENT。 |
| p50[] | kv[] | SHOULD | 中位數摘要 | 每個為 {name,value,unit}；用於常態水準（第 5 章）。 |
| p95[] | kv[] | SHOULD | 尾端摘要 | 每個為 {name,value,unit}；用於尾端風險（第 5 章）。 |
| outcome_facet[] | kv[] | MUST(>=1) | 本次判定關鍵結果 | 至少 1 個 {name,value,unit}；建議包含該 profile 的核心 facet。 |
| event_type[] | string[] | OPTIONAL | 本次涉及的事件類型 | 若本次判定由事件觸發，填入對應 event_type。 |
| evidence_bundle_ref | string | MUST | 證據包命名空間引用 | 指向本地可調取的片段集合（不必上報全量）。 |
| manifest_ref | string | MUST | 可調取索引引用 | 指向 Manifest，列出 7 天內可取回的摘要與事件片段。 |

硬性規則（No Silent Claims）：若 verdict = INSUFFICIENT_EVIDENCE，該 ProofCard SHALL 視為不可用來主張「修好了/合規/可接受/省電成功/不是我們的錯」。

## 4. Manifest（可調取索引，必須存在）

CPE SHALL 維護 Manifest，並由 manifest_ref 引用，列出 7 天內可取回的摘要與事件片段。

| 欄位 | 型別 | 是否必填 | 定義 | 規範 |
| :--- | :--- | :--- | :--- | :--- |
| manifest_ref | string | MUST | 索引識別碼 | 與 ProofCard 中 manifest_ref 一致。 |
| available_day_refs[] | string[] | MUST | 可取回的 day_window_ref 列表 | 至少包含最近 7 天（存在者）。 |
| available_event_refs[] | string[] | MUST | 可取回的 event_ref 列表 | 包含所有已觸發事件。 |
| bundle_pointer | string | MUST | 本地資料位置指標 | 實作自定（SQLite key / 檔案路徑 / object id）。 |

## 5. p50 / p95（分位數）計算規範（可重算）

p50（中位數）：代表「常態水準」；p95（95 分位）：代表「尾端風險」。用它們把『感覺』變成『可對帳』：常態是否好、尾端是否爆。

計算方法（Nearest-Rank）：

1) 將樣本值依大小排序。
2) rank(p)=ceil(p/100*N)。
3) pX=第 rank(X) 個樣本值。

指標方向：對「越大越壞」(RTT/loss/retry) 使用 p95；對「越小越壞」(RSSI/RSRP/SINR) 建議使用 p5（可用 outcome_facet 表達）。
樣本數門檻：各 profile SHALL 定義 min_sample_count；低於門檻 MUST 輸出 INSUFFICIENT_EVIDENCE。

## 6. Fingerprint Lite (fpl) 與 Fingerprint (fp) 差異（白話）

fpl（Lite）＝「最低可採信裁決」：用最少必要欄位，把一個窗口內的狀態裁決成 READY / NOT_READY / INSUFFICIENT，並給出可對帳的 p50/p95 與 reason_code。
fp（Full）＝「可究責的行為結構」：在 fpl 基礎上，再增加狀態形狀/轉移/接近邊界距離等更強歸因能力，用於供應鏈究責與深度分析。
免費版建議：只做 fpl（不加複雜度），把 ProofCard 當作結案/對帳收據；fp 留給付費版。

## 7. 各領域 Profile / Event Type / Reason Code（規範性附錄）

### 7.1 Wi‑Fi 7/8 Profiles

| profile_ref | 用途 | min_sample_count | 核心 outcome_facet 建議（>=1） |
| :--- | :--- | :--- | :--- |
| WIFI78_INSTALL_ACCEPT | 安裝驗收（7天/短窗） | 10 | rtt_ms_p95, loss_rate_p95, wifi_retry_p95, phy_rate_p50 |
| WIFI78_MESH_BACKHAUL_SPLIT | Mesh：Backhaul vs Wi‑Fi 端定界 | 10 | backhaul_rssi_p5, access_retry_p95, roam_count, mlo_link_switch_count |
| WIFI78_OSCILLATION_GUARD | 臨界震蕩/高頻嘗試風險 | 20 | retry_burst_p95, mlo_switch_burst_p95, queue_delay_p95 |

Wi‑Fi 7/8 event_type（non-exhaustive）：

| event_type | 觸發條件（例） | 必存 minimal_obs（2–5） |
| :--- | :--- | :--- |
| MLO_LINK_FLAP | mlo_link_switch_rate 超門檻 | mlo_link_switch_rate, per_link_loss, per_link_rtt |
| MESH_BACKHAUL_WEAK | backhaul_rssi 低於門檻 | backhaul_rssi, backhaul_mcs, backhaul_retry |
| OBSS_INTERFERENCE_SPIKE | OBSS busy 突升 | obss_busy, cca_busy, retry_rate |
| ROAM_STORM | roam 次數突增 | roam_count, rssi_p5, retry_rate |

Wi‑Fi 7/8 reason_code（non-exhaustive；open set）：

| reason_code | 說明（白話） |
| :--- | :--- |
| P95_RTT_TOO_HIGH | 尾端延遲過高（卡頓風險） |
| P95_LOSS_TOO_HIGH | 尾端丟包過高（斷流風險） |
| MESH_BACKHAUL_LIMITER | 瓶頸在 backhaul（不是 Wi‑Fi 端） |
| WIFI_SIDE_OSCILLATION | Wi‑Fi 端震蕩/重試爆發 |
| MLO_ASYMMETRIC_LINK | MLO 多鏈路不對稱（一條好一條爛） |
| INSUFFICIENT_SAMPLES | 樣本不足/分布不均 |

### 7.2 FWA Profiles

| profile_ref | 用途 | min_sample_count | 核心 outcome_facet 建議 |
| :--- | :--- | :--- | :--- |
| FWA_INSTALL_ACCEPT | 安裝驗收（7天/短窗） | 10 | rtt_ms_p95, loss_rate_p95, rsrp_p5, sinr_p5 |
| FWA_PLACEMENT_GUIDE | 擺位/方向建議（弱覆蓋） | 10 | rsrp_p5, sinr_p5, cell_reselect_count, rtt_ms_p95 |
| FWA_CONGESTION_SUSPECT | 晚高峰擁塞疑似 | 20 | rtt_ms_p95, throughput_mbps_p50, retrans_p95 |

FWA event_type（non-exhaustive）：

| event_type | 觸發條件（例） | 必存 minimal_obs（2–5） |
| :--- | :--- | :--- |
| RSRP_DROP_EDGE | RSRP 在 guard_window 內急跌 | rsrp, sinr, cell_id |
| CELL_RESELECT_STORM | cell reselect 次數突增 | cell_reselect_count, rsrp_p5, rtt_p95 |
| RTT_SPIKE_TAIL | RTT 尾端尖峰超門檻 | rtt_p95, loss_p95, retrans_p95 |

FWA reason_code（non-exhaustive；open set）：

| reason_code | 說明（白話） |
| :--- | :--- |
| WEAK_COVERAGE_RSRP_P5 | 覆蓋弱（RSRP 太低） |
| LOW_SINR_P5 | 干擾大/品質差（SINR 太低） |
| CELL_RESELECT_UNSTABLE | 頻繁換小區（不穩） |
| TAIL_RTT_TOO_HIGH | 尾端 RTT 太高（體感卡） |
| PEAK_CONGESTION_SUSPECT | 晚高峰擁塞疑似 |
| INSUFFICIENT_SAMPLES | 樣本不足/分布不均 |

### 7.3 Cable Modem Profiles

| profile_ref | 用途 | min_sample_count | 核心 outcome_facet 建議 |
| :--- | :--- | :--- | :--- |
| CABLE_INSTALL_ACCEPT | 安裝驗收（7天/短窗） | 10 | us_rtt_ms_p95, us_loss_p95, t3_t4_count, ofdm_mer_p5 |
| CABLE_UPSTREAM_INTERMITTENT | 上行間歇性（難抓） | 20 | us_rtt_ms_p95, us_loss_p95, burst_error_count_p95 |
| CABLE_PLANT_IMPAIRMENT_SUSPECT | Plant 側疑似衰退 | 20 | ofdm_mer_p5, fec_corrected_p95, t3_t4_count |

Cable event_type（non-exhaustive）：

| event_type | 觸發條件（例） | 必存 minimal_obs（2–5） |
| :--- | :--- | :--- |
| T3_T4_BURST | T3/T4 在短窗內爆發 | t3_count, t4_count, us_rtt_p95 |
| US_RTT_TAIL_SPIKE | 上行 RTT 尾端尖峰 | us_rtt_p95, us_loss_p95, queue_depth |
| MER_DROP_EDGE | MER 在 guard_window 內急跌 | ofdm_mer, fec_corrected, fec_uncorrected |

Cable reason_code（non-exhaustive；open set）：

| reason_code | 說明（白話） |
| :--- | :--- |
| T3T4_RETRY_BURST | T3/T4 重試爆發（上行不穩） |
| TAIL_US_RTT_TOO_HIGH | 上行尾端延遲過高 |
| TAIL_US_LOSS_TOO_HIGH | 上行尾端丟包過高 |
| PLANT_IMPAIRMENT_SUSPECT | 疑似 plant 側問題（MER/FEC 不佳） |
| INSUFFICIENT_SAMPLES | 樣本不足/分布不均 |

## 8. 三次模擬（手算可重現）

目的：用最小資料 + p50/p95，演示 fpl 如何產生可對帳的 ProofCard。以下數字僅示例；口徑由 basis_ref 固定。
*(略，參見原規格)*

## 9. 合規檢查表（Pass/Fail）

Free-tier CPE 僅在同時滿足以下條件時，才可宣稱符合本規格：

1) 每次判定必產生 ProofCard，且包含所有 MUST 欄位。
2) reason_code[] ≥ 1 且 outcome_facet[] ≥ 1。
3) validity_verdict 每張卡必有。
4) Manifest 可列出可調取 day/event refs。
5) 本地 7 天 ring buffer 規則生效。
6) p50/p95 計算口徑固定於 basis_ref，且可重算。
