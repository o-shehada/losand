# Los Andalus Manufacture — Frontend ↔ ERPNext Integration

## 1. Architecture in one line
A **Vue 3 SPA** (production-floor UI) is served by Frappe at **`/los-andalus/manufacture`** and talks to ERPNext **only** through a handful of **whitelisted Python methods** in `losand/api/manufacture.py`. **ERPNext is the source of truth** for stock and cost; the SPA is a thin data-entry layer + a bridge DocType for audit/orchestration.

```
Vue SPA  ──/api/method/losand.api.manufacture.*──>  Python API  ──>  ERPNext docs
 (browser)        (Frappe session + CSRF)          (whitelisted)     (Item/BOM/WO/Stock Entry)
```

- **Serving:** built by Vite into `losand/public/frontend`, served via the Frappe web page `losand/www/los-andalus/manufacture.html` (+ `manufacture.py` `get_context`).
- **Auth:** standard **Frappe session** (sid cookie). The SPA has a custom login screen that calls Frappe `login`; all API calls send the **CSRF token** + cookie. Route guards check the session.
- **Boot context** (`get_context`) injects into `window.boot`: `user`, `lang`, `currency`, `currency_symbol`, `factory_name`.

## 2. ERPNext → Frontend (reads)
| API method | Reads from ERPNext | Purpose |
|---|---|---|
| `get_current_session` | session user + roles | who is logged in, `can_produce` / `can_enter` flags |
| `get_allowed_products` | **Item** (templates `has_variants=1`) + their **variants** (`variant_of`), `weight_per_unit`, `custom_is_default_variant`, `image` | product cards + weight variants + default |
| `get_variant_bom(variant)` | **Item.default_bom → BOM** items, **Item.valuation_rate**, **Bin.actual_qty** (source wh) | planned per-piece materials, unit cost, live stock, `loss_rate` |
| `get_raw_materials` | **Item** in the **Raw Material** item group (+ descendants), **Bin** | the “add material” picker + available stock |

So the **Item master, Item Attribute (Weight), BOM, and Bin (stock)** drive the whole UI. Currency comes from **Global Defaults / Currency**.

## 3. Frontend → ERPNext (writes)
Two write endpoints:

- **`save_draft(draft)`** → upserts a **Los Andalus Production Batch** with `status = Draft` (no stock movement).
- **`submit_batch(draft, totals)`** → runs the **real ERPNext production cycle** in one transaction:

```
1. Work Order                      (production_item = variant, bom_no, qty, source/WIP/FG warehouses)
2. Stock Entry  "Material Transfer for Manufacture"   Stores → WIP, qty = ACTUAL consumption
3. Stock Entry  "Manufacture"      consume WIP, receive FG  → ERPNext computes per-piece cost
4. Stock Entry  "Material Issue"   (waste) damaged finished pieces written off from FG
5. Los Andalus Production Batch     links all of the above, stores cost + child tables
```

Stock entries are built with ERPNext’s own helper `erpnext.manufacturing.doctype.work_order.work_order.make_stock_entry(work_order, purpose, qty)` and then submitted — we do **not** hand-roll Stock Entry rows.

**Important ERPNext setting:** `Manufacturing Settings.backflush_raw_materials_based_on = "Material Transferred for Manufacture"` — so the Manufacture entry consumes the **actual** transferred quantities (what the operator entered), not the BOM-planned amounts. **Per-piece cost = ERPNext’s finished-good valuation**, surfaced back to the UI; the UI’s own total is only a pre-submit preview.

## 4. Custom objects added by this app
**DocTypes**
- `Los Andalus Production Batch` — bridge/audit doc (LAB-#####). Links: `work_order`, `material_transfer_entry`, `manufacture_entry`, `waste_entry`; `status` (Draft → WO Created → Materials Transferred → Completed / Failed); ERPNext-computed `unit_cost` / `total_cost`; **child tables** `materials` / `waste_items` / `loss_items`; **Connections tab** to WO + Stock Entries.
- `Los Andalus Production Material/Waste/Loss` — child tables of the batch.
- `Los Andalus Manufacture Settings` — **Single**: `company`, `source_warehouse`, `wip_warehouse`, `fg_warehouse`, `raw_material_group`, `factory_name` (all config is read from here, with fallbacks — nothing hardcoded).

**Custom fields**
- `Item.custom_is_default_variant` (Check) — marks each template’s standard weight.
- `Work Order.custom_production_batch` + `Stock Entry.custom_production_batch` (Link) — reverse links for the batch’s Connections tab.

**Roles:** `Manufacture Operator` (enter/draft) and `Manufacture Supervisor` (produce/post). `submit_batch` requires a produce role; also honors System Manager / Manufacturing Manager.

## 5. Product / costing model
- 3 product **templates** (Beef Burger, Chicken Burger, Burger Buns) with an **Item Attribute “Weight”** → weight **variants** (e.g. `Chicken Burger-200G`), each a `Nos` stock item with **its own BOM** and its own moving-average cost.
- Production counted in **pieces (Nos)**; `weight_per_unit` is the per-piece spec.
- Per-piece cost is whatever ERPNext computes on the Manufacture entry (actual materials valued + overhead ÷ pieces).

## 6. Prerequisites / notes for the ERPNext specialist
- **Raw materials need opening stock** (Material Receipt into `Stores - LA`) before producing; **Allow Negative Stock stays OFF**.
- **BOMs must be active/default** per variant; the seeded recipes are **placeholders** — correct quantities in Desk.
- **Process loss (kg)** is intentionally **not** posted as a separate stock movement (it’s already inside actual consumption) — only recorded on the batch for analysis. **Waste** (damaged finished pieces) **is** posted (Material Issue from FG).
- Warehouses/company/RM-group are all configurable in **Los Andalus Manufacture Settings** (currently: company `Los Andalus`; `Stores - LA` / `Work In Progress - LA` / `Finished Goods - LA`).
- A **Workspace “Los Andalus”** groups the batch + manufacturing/stock doctypes, reports, number cards and charts.
- Everything is in the `losand` app on the `develop` branch (GitHub: o-shehada/losand).
