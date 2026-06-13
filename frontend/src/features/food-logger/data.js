// Seed data + helpers for the Food Logger flow.
// Class-name literals (bg-red-50, text-red-400, …) are written out in full so
// Tailwind's JIT scanner picks them up from this file.

export const products = [
  {
    key: "beef",
    name_ar: "برجر لحم",
    name_en: "Beef Burger",
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/8de04f0132-a4d26b9fac68d3f1dc4c.png",
    icon: "fa-burger",
    headBg: "bg-red-50",
    headBorder: "border-red-100",
    iconBg: "bg-red-100",
    iconText: "text-red-500",
  },
  {
    key: "chicken",
    name_ar: "برجر دجاج",
    name_en: "Chicken Burger",
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/03643144d9-907fefba5c1e40b19cf8.png",
    icon: "fa-drumstick-bite",
    headBg: "bg-amber-50",
    headBorder: "border-amber-100",
    iconBg: "bg-amber-100",
    iconText: "text-amber-500",
  },
  {
    key: "buns",
    name_ar: "خبز البرجر",
    name_en: "Burger Buns",
    img: "https://storage.googleapis.com/uxpilot-auth.appspot.com/516077dbb6-fcb5658aad228244c8f3.png",
    icon: "fa-bread-slice",
    headBg: "bg-orange-50",
    headBorder: "border-orange-100",
    iconBg: "bg-orange-100",
    iconText: "text-orange-500",
  },
]

export function createDraft() {
  return {
    batchRef: "#B-2024-0847",
    dateLabel: "الجمعة، 6 يونيو 2025",
    shift: "morning",
    product: "beef",
    producedQty: 480,
    weightPerPiece: 120,
    notes: "",
    materials: [
      { name_ar: "لحم بقري مفروم", name_en: "Beef Mince 80/20", unit: "كجم", planned: 50, actual: 48.5, rate: 45, icon: "fa-drumstick-bite", wrap: "bg-red-50", color: "text-red-400" },
      { name_ar: "بيض طازج", name_en: "Fresh Eggs", unit: "حبة", planned: 120, actual: 120, rate: 0.75, icon: "fa-egg", wrap: "bg-amber-50", color: "text-amber-400" },
      { name_ar: "بهارات وتوابل", name_en: "Spices & Seasoning", unit: "جم", planned: 500, actual: 480, rate: 0.12, icon: "fa-wheat-awn", wrap: "bg-yellow-50", color: "text-yellow-500" },
      { name_ar: "زيت نباتي", name_en: "Vegetable Oil", unit: "لتر", planned: 5, actual: 5, rate: 8.5, icon: "fa-droplet", wrap: "bg-blue-50", color: "text-blue-400" },
      { name_ar: "فتات الخبز", name_en: "Bread Crumbs", unit: "كجم", planned: 3, actual: 2.8, rate: 12, icon: "fa-bread-slice", wrap: "bg-orange-50", color: "text-orange-400" },
    ],
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
  const totalWeight = (qty * (Number(draft.weightPerPiece) || 0)) / 1000
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

export function productByKey(key) {
  return products.find((p) => p.key === key) || products[0]
}
