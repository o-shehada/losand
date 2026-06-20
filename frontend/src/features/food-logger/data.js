// Data helpers for the no-BOM manufacture flow.
// Products/categories/workbenches come from ERPNext at runtime; this holds presentation + pure helpers.

const IMG_BASE = "/assets/losand/images/products"

// Presentation keyed by Product Category name.
export const CATEGORY_PRESENTATION = {
  "Chicken Burger": { img: `${IMG_BASE}/chicken-burger.svg`, icon: "fa-drumstick-bite", iconBg: "bg-amber-100", iconText: "text-amber-600" },
  "Beef Burger": { img: `${IMG_BASE}/beef-burger.svg`, icon: "fa-burger", iconBg: "bg-red-100", iconText: "text-red-600" },
  "Bread": { img: `${IMG_BASE}/burger-buns.svg`, icon: "fa-bread-slice", iconBg: "bg-orange-100", iconText: "text-orange-600" },
  "Sauce": { img: `${IMG_BASE}/default.svg`, icon: "fa-bottle-droplet", iconBg: "bg-rose-100", iconText: "text-rose-600" },
}
const FALLBACK = { img: `${IMG_BASE}/default.svg`, icon: "fa-utensils", iconBg: "bg-slate-100", iconText: "text-slate-500" }
export function categoryPresentation(cat) {
  return CATEGORY_PRESENTATION[cat] || FALLBACK
}

function todayLabel() {
  try {
    return new Intl.DateTimeFormat("ar", { weekday: "long", year: "numeric", month: "long", day: "numeric" }).format(new Date())
  } catch (e) {
    return new Date().toLocaleDateString()
  }
}
function genBatchRef() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, "0")
  return `#B-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${Math.floor(1000 + Math.random() * 9000)}`
}

export function createDraft() {
  return {
    workbench: "",
    category: "",
    shift: "",
    raw_warehouse: "",
    mfg_warehouse: "",
    fg_warehouse: "",
    batchRef: genBatchRef(),
    dateLabel: todayLabel(),
    finished_products: [], // {item_code, name, weight, qty}
    raw_materials: [], // {item_code, name_ar, name_en, unit, rate, available, qty}
    losses: [], // same raw materials table: {item_code, name_ar, unit, rate, available, qty}
    notes: "",
  }
}

export function calc(draft) {
  const materialCost = draft.raw_materials.reduce((s, m) => s + (Number(m.qty) || 0) * (Number(m.rate) || 0), 0)
  const lossCost = (draft.losses || []).reduce((s, m) => s + (Number(m.qty) || 0) * (Number(m.rate) || 0), 0)
  const C = materialCost + lossCost
  const W = draft.finished_products.reduce((s, f) => s + (Number(f.qty) || 0) * (Number(f.weight) || 0), 0)
  const costPerG = W ? C / W : 0
  const totalPieces = draft.finished_products.reduce((s, f) => s + (Number(f.qty) || 0), 0)
  return { C, W, costPerG, totalPieces }
}

export const fmt = (n) =>
  Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
export const fmt1 = (n) =>
  Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 1 })
