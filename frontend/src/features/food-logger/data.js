// Seed data + helpers for the Food Logger flow.
// Products/variants/BOMs come from ERPNext at runtime; this file holds presentation
// (images/icons keyed by template code) and pure helpers.
// Class-name literals are written in full so Tailwind's JIT scanner picks them up.

export const PRODUCT_PRESENTATION = {
  "Beef Burger": {
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/8de04f0132-a4d26b9fac68d3f1dc4c.png",
    icon: "fa-burger",
    headBg: "bg-red-50",
    headBorder: "border-red-100",
    iconBg: "bg-red-100",
    iconText: "text-red-500",
  },
  "Chicken Burger": {
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/03643144d9-907fefba5c1e40b19cf8.png",
    icon: "fa-drumstick-bite",
    headBg: "bg-amber-50",
    headBorder: "border-amber-100",
    iconBg: "bg-amber-100",
    iconText: "text-amber-500",
  },
  "Burger Buns": {
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/516077dbb6-fcb5658aad228244c8f3.png",
    icon: "fa-bread-slice",
    headBg: "bg-orange-50",
    headBorder: "border-orange-100",
    iconBg: "bg-orange-100",
    iconText: "text-orange-500",
  },
}

const FALLBACK_PRESENTATION = {
  img: null,
  icon: "fa-burger",
  headBg: "bg-slate-50",
  headBorder: "border-slate-100",
  iconBg: "bg-slate-100",
  iconText: "text-slate-500",
}

export function presentationFor(code) {
  return PRODUCT_PRESENTATION[code] || FALLBACK_PRESENTATION
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
  const rand = Math.floor(1000 + Math.random() * 9000)
  return `#B-${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${rand}`
}

export function createDraft() {
  return {
    batchRef: genBatchRef(),
    dateLabel: todayLabel(),
    shift: "morning",
    product: "", // template item_code, set after products load
    productName: "",
    variant: "", // variant item_code
    weight: 0, // grams per piece (from variant)
    producedQty: 480,
    notes: "",
    materials: [], // loaded from the variant BOM
    waste: [
      { reason: "برجر لحم محترق", qty: 12, unit: "قطعة", rate: 24 },
      { reason: "خبز منتهي الصلاحية", qty: 8, unit: "قطعة", rate: 24 },
    ],
    loss: [
      { reason: "فقد في التشكيل", qty: 2.5, unit: "كجم", rate: 45 },
      { reason: "فقد في الطهي", qty: 1.8, unit: "كجم", rate: 45 },
      { reason: "فقد في التعبئة", qty: 0.7, unit: "كجم", rate: 45 },
    ],
  }
}

export function calc(draft) {
  const materialTotal = draft.materials.reduce((s, m) => s + (Number(m.actual) || 0) * (Number(m.rate) || 0), 0)
  const wasteUnits = draft.waste.reduce((s, w) => s + (Number(w.qty) || 0), 0)
  const lossUnits = draft.loss.reduce((s, l) => s + (Number(l.qty) || 0), 0)
  const wasteTotal = draft.waste.reduce((s, w) => s + (Number(w.qty) || 0) * (Number(w.rate) || 0), 0)
  const lossTotal = draft.loss.reduce((s, l) => s + (Number(l.qty) || 0) * (Number(l.rate) || 0), 0)
  const totalCost = materialTotal + wasteTotal + lossTotal
  const qty = Number(draft.producedQty) || 0
  const unitCost = qty ? totalCost / qty : 0
  const totalWeight = (qty * (Number(draft.weight) || 0)) / 1000
  const pct = (v) => (totalCost ? (v / totalCost) * 100 : 0)
  return {
    materialTotal,
    wasteTotal,
    lossTotal,
    totalCost,
    unitCost,
    wasteUnits,
    lossUnits,
    totalWeight,
    matPct: pct(materialTotal),
    wastePct: pct(wasteTotal),
    lossPct: pct(lossTotal),
    wasteLossTotal: wasteTotal + lossTotal,
  }
}

export const fmt = (n) =>
  Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const fmt1 = (n) =>
  Number(n || 0).toLocaleString("en-US", { minimumFractionDigits: 0, maximumFractionDigits: 1 })

// Icon palette assigned to material rows by index (literal classes for Tailwind JIT).
export const palette = [
  { icon: "fa-drumstick-bite", wrap: "bg-red-50", color: "text-red-400" },
  { icon: "fa-egg", wrap: "bg-amber-50", color: "text-amber-400" },
  { icon: "fa-wheat-awn", wrap: "bg-yellow-50", color: "text-yellow-500" },
  { icon: "fa-droplet", wrap: "bg-blue-50", color: "text-blue-400" },
  { icon: "fa-bread-slice", wrap: "bg-orange-50", color: "text-orange-400" },
  { icon: "fa-carrot", wrap: "bg-green-50", color: "text-green-500" },
  { icon: "fa-box", wrap: "bg-slate-100", color: "text-slate-400" },
]

export const iconFor = (i) => palette[i % palette.length]

// Build a material row from a BOM material payload (planned per-piece × pieces).
export function materialFromBom(m, producedQty, index) {
  const perPiece = Number(m.per_piece) || 0
  const planned = perPiece * (Number(producedQty) || 0)
  return {
    item_code: m.item_code,
    name_ar: m.name_ar,
    name_en: m.name_en,
    unit: m.unit,
    rate: m.rate,
    available: m.available_qty ?? 0,
    perPiece,
    actual: planned,
    ...iconFor(index),
  }
}

// Build an ad-hoc material row (added via picker; not in the BOM).
export function materialFromItem(item, index) {
  return {
    item_code: item.item_code,
    name_ar: item.name_ar,
    name_en: item.name_en,
    unit: item.unit,
    rate: item.rate,
    available: item.available_qty ?? 0,
    perPiece: 0,
    actual: 0,
    ...iconFor(index),
  }
}
