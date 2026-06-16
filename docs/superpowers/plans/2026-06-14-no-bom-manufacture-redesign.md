# Los Andalus — No‑BOM Manufacture Redesign (Plan)

> Status: PLAN ONLY (no code yet). Supersedes the Template/Variant + BOM + Work Order approach.

## Locked model
- Final products = **independent items per weight** (e.g. `Chicken Burger 200g`), flagged `is_final_product`, each with `weight_per_unit` + `weight_uom`, linked to a **Product Category** and **batch‑tracked**.
- Raw materials flagged `is_raw_material` (+ native `include_in_manufacturing`), batch‑tracked, with a `classification` MultiSelect of the **Product Categories** they serve.
- **Workbench** = a station for one category, carrying its 3 warehouses + staff/shifts.
- No BOM / no Work Order. Production = plain Stock Entries: **Material Receipt (raw) → Transfer (raw→mfg) → Issue (consume) → Material Receipt (finished)**.
- Raw consumed at **Valuation Rate**; finished cost **allocated by weight**; **FEFO** auto‑picks raw batches.
- **Waste (الهالك) removed.** **Loss (الفاقد) kept** as a recorded figure only (reason + kg) for analysis — NOT posted as stock (already absorbed by the weight allocation).

## 1. Data model

### New DocTypes
- **Product Category**: `category_name`, `description`.
- **Shift**: `shift_name`, `start_time`, `end_time`.
- **Workbench**: `workbench_name`, `product_category` (Link), `raw_material_warehouse`, `manufacturing_warehouse`, `fg_warehouse`, child table **Workbench Staff** (`user` Link User + `shift` Link Shift), child table **Workbench Worker** (`worker_name` Data + `shift` Link Shift).
- **Los Andalus Production Batch** (repurpose existing): `workbench`, `product_category`, `shift`, the 3 warehouses (copied from workbench), `status`, links `transfer_entry` / `issue_entry` / `receipt_entry` (Stock Entry), `total_raw_cost` (C), `total_output_weight` (W); child tables:
  - **Production Material** (raw consumed): `item_code`, `qty`, `valuation_rate`, `amount`.
  - **Production Output** (finished): `item_code`, `qty`, `weight_per_unit`, `unit_cost`, `amount`, `batch_no`.
  - **Production Loss** (الفاقد, recorded only): `reason`, `qty_kg`, `cost` (= qty_kg × C/W, for reporting).

### Custom fields on `Item`
- `is_final_product` (Check)
- `is_raw_material` (Check)
- `product_category` (Link → Product Category; shown when `is_final_product`)
- `classification` (Table MultiSelect → Product Category; shown when `is_raw_material`)
- enable `has_batch_no` on final + raw items; `weight_per_unit` + `weight_uom` on final items (native)
- (remove the old `custom_is_default_variant`)

### Custom field on `Stock Entry`
- reuse `custom_production_batch` (Link → Production Batch) to tie the 3 entries back to the batch.

## 2. ERPNext configuration (for the ERPNext specialist)
- **Perpetual inventory:** create/choose a single **Production Clearing** account; both the **Issue** and the FG **Receipt** use it as their difference account, with `Σ(receipt value) = C` exactly → the account nets to **zero** (no phantom P&L).
- **Batch:** auto‑naming series; FG batch **expiry from `Shelf Life In Days`**.
- **FEFO:** raw consumption auto‑selects batches by earliest expiry (Stock Settings auto‑batch / API‑resolved).
- Warehouses now come from the **Workbench** (the global settings warehouses become fallback only).
- The old `Manufacturing Settings.backflush…` is irrelevant now (no Manufacture entry).

## 3. Production cycle & costing
1. **Material Transfer** raw → manufacturing warehouse (actual quantities, FEFO batches).
2. **Material Issue** from manufacturing warehouse → ERPNext values it at Valuation Rate; read posted total **C**.
3. Compute **W = Σ(qty × weight_per_unit)** over finished products; **unit_cost = weight × (C / W)**.
4. **Material Receipt** finished goods into FG warehouse: each row `basic_rate = unit_cost`, totals reconciled to **C** (rounding on last line); creates FG **batches** with expiry; same clearing account.
5. Create/Complete **Production Batch** linking the 3 entries + child tables + C/W + status.

Process **loss is absorbed automatically** (C spread over actual output weight). FEFO removes batch‑picking from the operator.

## 4. API surface (`losand/api/manufacture.py`)
Replace:
- `get_allowed_products` / `get_variant_bom` → **removed**.
- New reads: `get_workbenches()` (allowed workbenches + category + warehouses), `get_final_products(category)` (items: `is_final_product` & `product_category`=category, with weight), `get_category_raw_materials(category, workbench)` (items: `is_raw_material` & `classification` contains category, with valuation rate + available stock in the workbench warehouse).
- `submit_batch(payload)` rewritten: inputs = workbench, finished_products[{item, qty}], raw_materials[{item, actual_qty}], shift; does Transfer→Issue→Receipt (+FEFO, +weight cost, +batches) + Production Batch log; permission `can_produce`.
- `save_draft` kept (new child tables). `get_current_session` kept.

## 5. Frontend flow
- **Screen 1 — Workbench + Shift select:** cards of workbenches (each = a category: chicken/meat/bread/sauce); choosing one fixes category + warehouses, and the user **picks the shift** (dropdown of that workbench's shifts) to start.
- **Screen 2 — Entry:**
  - **Finished products table** — rows of the category's final products + qty (e.g. 44× Chicken 200g, 20× Chicken 120g).
  - **Raw materials table** — the category's raw materials; operator enters **actual consumed** qty (no planned column, no batch picker — FEFO); shows valuation rate + available stock (stock‑aware).
  - **Loss (الفاقد) section** — optional rows of reason + kg (recorded for analysis, not posted).
  - Live preview: C, total output weight, allocated cost/piece.
- **Summary:** finished products with allocated unit costs + totals; confirm.
- **Success:** created Stock Entries + batch numbers + per‑product cost.
- Remove variant cards / weight switcher (no variants).

## 6. Phasing
- **Phase 0 (Desk/scaffold):** new doctypes, Item custom fields, batch enable, clearing account, sample data (categories, final‑product items per weight w/ category + weight, raw materials w/ classification, workbenches, shifts).
- **Phase 1 (reads + UI):** workbench/category selection, final‑products + raw‑materials tables, stock‑aware.
- **Phase 2 (transactional):** Transfer → Issue → Receipt + FEFO + weight cost + batches + Production Batch log.
- **Phase 3 (polish):** workspace + reports (production by category, cost per product, batch traceability), permissions, success screen.

## 7. What gets removed/replaced
Item Variants/Templates, the placeholder BOMs, Work Order usage, `get_variant_bom`, the WO+Manufacture path in `submit_batch`, `custom_is_default_variant`, the variant scaffold. Production Batch + stock‑aware UI + workspace are kept (reworked).

## 8. Resolved decisions
- **Waste (الهالك):** removed. **Loss (الفاقد):** kept as recorded data only (reason + kg), not posted.
- **Shift:** chosen by the user on Screen 1 (dropdown of the workbench's shifts) when starting.
- **Item → category:** via `product_category` Link field on Item (confirmed).
- Assumption: roughly **one workbench per category** (screen 1 lists workbenches).
