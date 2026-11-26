# Los Andalus App (`losand`)

A Frappe / ERPNext v15 app for Los Andalus, a restaurant group with a central food factory and several branches. It adds two Arabic, RTL web portals on top of ERPNext:

| Portal | URL | For |
|---|---|---|
| **POS** (نقاط البيع) | `/los-andalus/pos` | Branch cashiers: sell, receive stock from the factory, count stock, waste, close the shift |
| **Manufacturing** (نظام إدارة الإنتاج) | `/los-andalus/manufacture` | Factory staff: log a production run per workbench |

ERPNext stays the source of truth. The portals are thin screens that call whitelisted Python methods, and every sale and stock movement is a normal ERPNext document (Sales Invoice, Stock Entry), so ERPNext's own stock, accounting and reports keep working.

Current version: see [`losand/__init__.py`](losand/__init__.py). Releases are tagged `vMAJOR.MINOR.PATCH` ([semantic versioning](https://semver.org)).

## Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Installation](#installation)
- [Setup for a new site](#setup-for-a-new-site)
- [Daily operations](#daily-operations)
- [Roles](#roles)
- [Development](#development)
- [Repository layout](#repository-layout)
- [Releasing](#releasing)
- [License](#license)

## How it works

```
Vue 3 SPA (one bundle, two route trees)
   │  /api/method/losand.api.pos.*          Frappe session + CSRF
   │  /api/method/losand.api.manufacture.*
   ▼
losand/api/*.py   whitelisted methods
   ▼
ERPNext: Sales Invoice, Stock Entry, POS Profile, Item, Batch, Warehouse, Cost Center
```

- One Vite build (`frontend/`) serves both portals. `losand/www/los-andalus/pos.html` and `manufacture.html` are the Frappe pages that mount it; the route tree is chosen from the URL prefix.
- **POS Profile is the single source of truth** for a branch: warehouse, price list, payment methods, item groups, cost center, branch.
- Sales are submitted **server-side** as `Sales Invoice` (`is_pos=1`), with server-side pricing, FEFO batch allocation and an idempotency key, so the browser cannot set prices and a double click cannot double-sell.
- The portal API answers in Arabic (`losand/utils.py`), whatever language the Desk user chose.

## Features

### POS

- **Register**: item grid by group, per-piece customization, gift cards, park and resume orders, split payments.
- **Add-ons and notes** (see [Add-ons and notes](#add-ons-and-notes)): priced add-ons are Items and can be limited to item groups; free kitchen notes are configurable records.
- **Receiving (استلام الطلبات)**: the factory or a manager creates a draft Material Transfer to the branch warehouse in the Desk; the branch sees it in the POS (with a count badge on the sidebar and an expandable item list), enters what actually arrived, and confirms. Confirming submits the transfer. A short delivery is recorded in the remarks.
- **Daily stock count (الجرد اليومي)**: counts the branch warehouse and posts the difference as a Stock Entry on the branch Cost Center. A `Los Andalus Stocktake` record is kept per count.
- **Waste (الهالك)**: write off ready items spoiled at the branch (opt-in list on the POS Profile).
- **Shift**: open with a cash float; **closing requires the day's stock count**, then reconciles expected against counted cash per payment mode and records the count shortage and waste value.
- **Invoice history** for the shift with return, edit and cancel (POS Manager only).

### Manufacturing

- Production run per **Workbench** (a line, with its raw-material, work-in-progress and finished-goods warehouses and its own Cost Center). No BOM is needed: the operator enters what was consumed and what was produced.
- On submit it posts three Stock Entries tied to a `Los Andalus Production Batch`:
  1. Material Transfer: raw-material warehouse → work-in-progress
  2. Material Issue: consume from work-in-progress (FEFO)
  3. Material Receipt: finished goods, costed by weight allocation
- **Raw-material loss (الفاقد)** is consumed with the materials and absorbed into product cost.
- **Finished-product waste (الهالك)** is a fourth Material Issue out of the finished-goods warehouse, limited to what the run produced.
- Costs and rates are shown only to Manufacturing Manager, Manufacture Supervisor and System Manager.
- **Worker Submission** (Los Andalus Manufacture Settings) decides what a worker does at the end of a run:
  - *Save for supervisor review* (default): the worker's run is saved as a draft with no stock movement. A supervisor sees it under "مسودات بانتظار المراجعة" on the portal's start screen, reviews it with its costs, and posts it, or deletes it. The batch records who entered it; the stock entries are owned by whoever posted.
  - *Post directly*: the worker posts the run themselves. They still never see costs.
  - Supervisors can always post.

### Workspaces and reports

The Desk has one common workspace with two children (Desk sidebar: **Los Andalus → Manufacture, POS**):

| Workspace | Holds |
|---|---|
| **Los Andalus** | Shared master data (Item, Warehouse, Branch, Cost Center…), stock documents, cross-cutting reports, today's POS sales, finished-goods stock value, sales by branch, links to both portals |
| **Manufacture** | Production Batch, Workbench, Product Category, Shift, Manufacture Settings, production cards and charts, Production Summary report |
| **POS** | POS Profile, shifts and closings, invoices, parked orders, gift cards, kitchen notes, stock count, POS cards and the sales-by-branch chart |

Custom reports (all Script Reports, Arabic column labels):

| Report | Shows |
|---|---|
| **Los Andalus Branch Performance** | Per day and branch: revenue by payment mode, cash reconciliation, stock opening, receipts, consumption and closing |
| **Los Andalus Cost Center Performance** | Income, expense, net and margin per Cost Center from the GL, so each branch and production line has its own profit and loss |
| **Los Andalus Production Summary** | Per production batch: pieces, weight, material cost, cost per piece, finished-product waste and its value |
| **Los Andalus Stock Count and Waste** | Per day and branch: counts done, items with variance, shortage and surplus value, waste value |

### Cost centers and branches

Every document the portals post is tagged so each branch and production line can be reported separately:

- the POS Profile's **Branch** accounting dimension (`losand_branch`),
- the POS Profile's **Cost Center**, pinned on every invoice and stock-entry row,
- the Workbench's **Cost Center** on every production entry.

If no Cost Center is set, ERPNext's default is used and posting still works.

## Installation

Requires a bench with **Frappe v15** and **ERPNext v15**.

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/o-shehada/losand.git --branch main
bench --site your.site install-app losand
bench --site your.site migrate
```

`bench migrate` also runs the app's setup steps (`after_migrate`): Arabic translation fixes, the extra POS Profile fields, the Branch dimension, the Add-on field on Item, the starter kitchen notes, print formats and the manufacturing wiki. The one-time patch `assign_cost_centers` creates a Cost Center for every POS Profile and Workbench that has none.

The built frontend is committed (`losand/public/frontend`), so installing needs no Node.js. Only developers changing the UI need it.

## Setup for a new site

1. **Company, warehouses, price list.** Create these in ERPNext as usual. The factory warehouses are `Stores`, `Work In Progress` and `Finished Goods`; defaults live in **Los Andalus Manufacture Settings**.
2. **A POS Profile per branch.** Set its warehouse, price list, payment methods, item groups and users (only listed users can open its POS). Fill the **Branch** (`losand_branch`) and **Cost Center** fields. Add the **POS Add-ons** item group to the profile's item groups if the branch sells add-ons. The optional waste list (`losand_waste_items`) decides what the branch may write off.
3. **Workbenches.** Create a Workbench per production line with its category, three warehouses, Cost Center and the users allowed on it.
4. **Items.** Mark factory output with *Is Final Product* and a Product Category; mark inputs with *Is Raw Material* and list them in the Raw Materials table of the final product.
5. **Users and roles.** See [Roles](#roles).
6. **Language.** Set the site and users to Arabic if you want the Desk in Arabic too; the portals are Arabic already.

## Daily operations

### Sending stock to a branch

1. In the Desk, create a **Stock Entry** of type **Material Transfer** from the factory warehouse to the branch's warehouse (the one on its POS Profile). **Save it as a draft; do not submit it.**
2. At the branch, the POS sidebar badge on **استلام الطلبات** shows the number of waiting transfers. Open one, enter the quantity that arrived, and confirm.
3. Confirming submits the Stock Entry, moves the stock and tags it with the branch and its Cost Center. It then leaves the inbox.

### Add-ons and notes

- **Priced add-ons** are Items in the Item Group `POS Add-ons` (Is Sales Item on, with an Item Price on the branch's price list). To allow an add-on only with certain items, fill **Add-on Allowed Item Groups** on that Item, one Item Group per line (sub-groups are included). Empty means any item. The restriction is applied in the register screen.
- **Free notes** (no price, no stock) are records of **Los Andalus Kitchen Note**; untick *Enabled* to hide one. Notes are printed on the kitchen ticket.
- The register loads both at page load, so reload it after a change.

### Closing a shift

Run the daily stock count first. The closing screen blocks confirmation until it is done and shows count shortage and waste value alongside the cash reconciliation.

## Roles

| Role | Can |
|---|---|
| Users listed in a POS Profile (`applicable_for_users`) | Sell, receive, count, waste, close their shift, on that profile only. No role is exempt, and a profile with no users admits nobody |
| **POS Manager** | Also return, edit and cancel submitted invoices of the profiles they are listed in; edit kitchen notes |
| **Manufacturing User / Manufacture Operator / Stock User** | Enter production data on their assigned workbenches (no cost shown); post it, or send it for review, per *Worker Submission* |
| **Manufacture Supervisor / Manufacturing Manager** | Post production runs and see rates and costs |
| **System Manager** | Everything |

## Development

```bash
cd apps/losand
pre-commit install          # ruff, eslint, prettier, pyupgrade

cd frontend
npm install
npm run dev                 # Vite dev server
npm run build               # writes ../losand/public/frontend and the www/*.html asset tags
```

Commit the rebuilt `losand/public/frontend` and `losand/www/los-andalus/manufacture.html` together; the POS page reads its asset names from `manufacture.html`.

After changing a doctype JSON or adding a patch, run `bench --site your.site migrate`. Don't force-import a Workspace file with `import_file_by_path(..., force=True)` in developer mode: Frappe deletes the workspace first, which also deletes its folder from the app. Cart arithmetic has a small unit test in `frontend/src/features/pos/cartMath.test.js`.

## Repository layout

```
frontend/                      Vue 3 + Tailwind SPA (POS and manufacturing)
  src/features/pos/            POS screens
  src/features/food-logger/    production entry, summary, success
  src/stores, src/lib          session, POS state, API client, i18n
losand/
  api/pos.py                   POS endpoints: register, receiving, count, waste, shift
  api/manufacture.py           production endpoints
  utils.py                     portal API language hook
  los_andalus_app/doctype/     Workbench, Production Batch, Stocktake, POS Closing, Gift Card, Kitchen Note, …
  los_andalus_app/report/      Branch Performance, Cost Center Performance, Production Summary, Stock Count and Waste
  los_andalus_app/workspace/   Los Andalus (common), Manufacture and POS workspaces
  setup/                       after_migrate setup: custom fields, dashboards, POS Profile fields, Branch dimension, print formats, wiki (the app ships no fixtures)
  patches/                     one-time data patches
  translations/ar.csv          Arabic strings, including portal error messages
  public/frontend/             built bundle (committed)
  www/los-andalus/             pos.html and manufacture.html pages
docs/wiki/manufacturing/       user manual, published into the Wiki app on migrate
docs/                          design notes (earlier BOM-based design in erpnext-integration.md is superseded by the no-BOM flow)
```

## Releasing

Versions follow semantic versioning while below 1.0.0: a minor bump for new features, a patch bump for fixes.

```bash
# update __version__ in losand/__init__.py, then
git commit -am "chore(release): vX.Y.Z"
git tag -a vX.Y.Z -m "vX.Y.Z"
```

## License

MIT. See [license.txt](license.txt).
