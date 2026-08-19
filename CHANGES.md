# GraMa Schema Corrections (August 2026)

## Summary
Fixed 6 critical files to match the **real CICIoV2024 dataset schema** (confirmed via direct inspection of UNB release). The original concept-note implementation was based on assumptions about column names, ECU mappings, and class labels that don't match what was actually released.

---

## Real CICIoV2024 Schema (vs. Original Assumptions)

| Aspect | Original Assumption | Real Schema |
|--------|-------|-------|
| **Columns** | `timestamp, can_id, dlc, d0-d7, label` | `ID, DATA_0-DATA_7, label, category, specific_class` |
| **Classes** | 5 (benign + DoS, RPM_SPOOFING, STEERING_ANGLE_SPOOFING, REPLAY) | 6 (benign + DoS, spoofing-GAS, spoofing-RPM, spoofing-SPEED, spoofing-STEERING_WHEEL) |
| **Timestamp** | Present (delta_t feature) | Absent — no inter-arrival time available |
| **DLC** | Present (payload-length field) | Absent |
| **ECU Labels** | Hardcoded name vocabulary (ENGINE, BRAKES, etc.) | Absent — CAN IDs only, no ECU mapping |
| **Download** | Gated behind request form | Publicly accessible, direct download |
| **Duplicates** | Unhandled | **Critical:** 99.7% exact duplicates; must dedup before train/test split |

---

## Files Modified

### 1. **`config/data.yaml`** ⚠️ CRITICAL
**Changes:**
- Column names: `d0-d7` → `DATA_0-DATA_7`, `can_id` → `ID`, removed `timestamp`, removed `dlc`
- Classes: 5 → 6 classes (added missing spoofing variants, removed non-existent "Replay")
- Added deduplication warning and config section
- Added `payload_columns` explicit list for normalization

**Why:** The schema is hardcoded in config; wrong column names cause immediate pipeline failure.

---

### 2. **`config/model.yaml`** ⚠️ CRITICAL
**Changes:**
- `num_classes: 5` → `num_classes: 6`
- `gat_encoder.in_features: 11` → `in_features: 10` (removed DLC, adjusted for real features)
- Removed hardcoded `ecu_nodes` ECU name vocabulary (no longer used)
- Added comment that nodes must be data-driven, not hardcoded

**Why:** Feature dimensionality mismatch and class count mismatch cause training crashes.

---

### 3. **`src/grama/data/preprocess.py`** ⚠️ HIGH
**Changes:**
- `PAYLOAD_COLS = [f"d{i}" for i in range(8)]` → `[f"DATA_{i}" for i in range(8)]`
- Removed `add_inter_arrival_time()` function (no timestamp in real data)
- Added `deduplicate()` function to drop exact duplicate rows
- Updated `sliding_windows()` docstring; removed timestamp assumptions
- Changed `can_id_col` default from `"can_id"` to `"ID"`

**Why:** Without deduplication, train/test split will leak duplicates, inflating accuracy. Without correct column names, preprocessing fails.

---

### 4. **`src/grama/data/graph_builder.py`** ⚠️ HIGH
**Changes:**
- Completely refactored from hardcoded ECU mapping to **data-driven** CAN ID vocabulary
- Renamed `ECUGraph` → `CANIDGraph` (nodes are CAN IDs, not named ECUs)
- Removed `DEFAULT_CAN_ID_TO_ECU` dict and all ECU name logic
- `GraphBuilder.__init__()` no longer takes `ecu_nodes` or `can_id_to_ecu` parameters
- `build()` now discovers unique CAN IDs dynamically from each window's frames
- Feature set: 8 DATA bytes + frame_count + burst_flag (10 features, not 11)
- `node_order` now contains sorted integer CAN IDs, not ECU names

**Why:** Real dataset has no ECU-to-CAN-ID mapping. Hardcoded mapping is meaningless. Nodes must be inferred from data itself.

---

### 5. **`src/grama/data/download.py`**
**Changes:**
- Updated docstring: removed "gated behind request form" statement
- Changed `REQUEST_FORM_URL` → `DOWNLOAD_URL` pointing to direct download page
- Updated `main()` messages to reflect that dataset is publicly downloadable
- No code logic change; purely documentation/messaging

**Why:** Original code correctly handled data validation but was pessimistic about availability. Turns out the dataset is public.

---

### 6. **`tests/test_graph_builder.py`** ⚠️ HIGH
**Changes:**
- Removed ECU node vocabulary fixture (`ECU_NODES`)
- Updated `make_window()` to use real schema: `ID` column instead of `can_id`, `DATA_0-7` instead of `d0-7`, removed `dlc`, removed `delta_t`
- Rewrote all test functions to expect data-driven vocabulary (variable number of nodes)
- Updated assertions: feature dimension 11 → 10, frame_count logic updated
- Added new test: `test_frame_count_feature()` to verify burst intensity signal
- Added new test: `test_data_driven_vocabulary()` to verify CAN IDs are discovered from data

**Why:** Tests must match new schema and data-driven architecture. Old ECU-based tests are no longer applicable.

---

### 7. **`README.md`**
**Changes:**
- **Dataset section:** Updated to reflect direct download (no request form), added schema notes
- Added dataset gotchas: no ECU labels, 99.7% duplicates, deduplication is automatic
- **Key implementation notes:** 
  - Removed note about placeholder CAN ID mapping (now resolved: data-driven)
  - Added note about automatic deduplication
  - Updated feature schema description
  - Noted that "Replay" class does not exist in real release

**Why:** Documentation should match implementation and warn about data gotchas.

---

## Impact on Other Files

These files are **unaffected** (no schema-specific hardcoding):
- `src/grama/models/gat_encoder.py` — Generic parameter-based design; works with any feature dimension
- `src/grama/models/mamba_block.py` — Generic temporal encoder
- `src/grama/models/classifier_head.py` — Parameterized by `num_classes`
- `src/grama/federated/*.py` — Operate on tensors, not raw schema
- Other test files — Use synthetic tensors, not real data

---

## Deployment Checklist

1. ✅ Correct column names in preprocessing (`DATA_0-7` not `d0-d7`)
2. ✅ Deduplication before windowing (prevents train/test leakage)
3. ✅ Graph builder is data-driven (learns CAN IDs from data)
4. ✅ Class count updated to 6
5. ✅ Feature dimension corrected to 10 (no DLC, no timestamp)
6. ✅ Tests updated to match new schema
7. ✅ README updated with real dataset gotchas

---

## Next Steps

1. **Download real data:**
   ```bash
   # https://www.unb.ca/cic/datasets/iov-dataset-2024.html
   # Place CSVs in data/raw/
   ```

2. **Validate:**
   ```bash
   python -m grama.data.download --check
   ```

3. **Preprocess (includes automatic dedup):**
   ```bash
   make preprocess
   ```

4. **Train on real data:**
   ```bash
   make train
   ```

---

## References

- Real dataset: https://www.unb.ca/cic/datasets/iov-dataset-2024.html
- Duplicate analysis: Stiawan et al., "Intrusion detection in CAN bus networks: A systematic review," *IJAIT* 2024
- Concept note: "Redesigning Federated Intrusion Detection for IoV: The GraMa Architecture"
