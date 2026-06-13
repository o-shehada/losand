export const batchDraft = {
  batchRef: "#B-2024-0847",
  product: "Beef Burger",
  producedQty: 480,
  notes: "",
  materials: [
    { item: "Beef Mince 80/20", unit: "kg", planned: 50, actual: 48.5, rate: 45 },
    { item: "Fresh Eggs", unit: "pcs", planned: 120, actual: 120, rate: 0.75 },
    { item: "Spices & Seasoning", unit: "g", planned: 500, actual: 480, rate: 0.12 },
    { item: "Vegetable Oil", unit: "l", planned: 5, actual: 5, rate: 8.5 },
    { item: "Bread Crumbs", unit: "kg", planned: 3, actual: 2.8, rate: 12 },
  ],
  waste: [
    { reason: "Burnt beef burger", qty: 12, unit: "pcs", cost: 288 },
    { reason: "Expired buns", qty: 8, unit: "pcs", cost: 192 },
  ],
  loss: [
    { reason: "Shaping loss", qty: 2.5, unit: "kg", cost: 112.5 },
    { reason: "Cooking loss", qty: 1.8, unit: "kg", cost: 81 },
    { reason: "Packing loss", qty: 0.7, unit: "kg", cost: 31.5 },
  ],
}

export function calculateTotals(draft) {
  const materialTotal = draft.materials.reduce((sum, item) => sum + item.actual * item.rate, 0)
  const wasteTotal = draft.waste.reduce((sum, item) => sum + item.cost, 0)
  const lossTotal = draft.loss.reduce((sum, item) => sum + item.cost, 0)
  const totalCost = materialTotal + wasteTotal + lossTotal
  return {
    materialTotal,
    wasteTotal,
    lossTotal,
    totalCost,
    unitCost: totalCost / draft.producedQty,
    wastePercent: ((draft.waste.reduce((sum, item) => sum + item.qty, 0) / draft.producedQty) * 100).toFixed(1),
  }
}
