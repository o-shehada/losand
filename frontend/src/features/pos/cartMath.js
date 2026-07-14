// Pure cart pricing. Kept out of the SFC so the money path has one runnable
// check (cartMath.test.js) — it's headed for real Sales Invoices later.

export const extrasSum = (piece) => piece.extras.reduce((s, e) => s + e.price, 0)

// Line total = sum over pieces of (base price + that piece's add-ons).
export const lineTotal = (line) => line.pieces.reduce((s, p) => s + line.price + extrasSum(p), 0)

const pieceKey = (p) => JSON.stringify([p.extras.map((e) => e.id).sort(), [...p.notes].sort()])
// All pieces carry the same customization (single piece, or bulk-applied).
export const isUniform = (line) => line.pieces.every((p) => pieceKey(p) === pieceKey(line.pieces[0]))

// Uniform → real per-piece price (base + shared extras); mixed → base only.
export const unitPrice = (line) => line.price + (isUniform(line) ? extrasSum(line.pieces[0]) : 0)

// Gift card credits min(card, total); the rest is paid by another method.
export const giftApplied = (total, cardValue) => Math.min(cardValue, total)
export const giftRemaining = (total, cardValue) => Math.max(0, total - giftApplied(total, cardValue))

// --- Payment tender (the modal's {mode_of_payment, amount} rows) ---

export const round2 = (n) => Math.round((Number(n) || 0) * 100) / 100
export const tenderedTotal = (splits) => round2(splits.reduce((s, r) => s + Number(r.amount || 0), 0))
// Positive = still short of the balance; negative = paid in excess.
export const tenderDiff = (remaining, splits) => round2(remaining - tenderedTotal(splits))

// Amount a row should hold to cover whatever the other rows leave unpaid.
export const tenderFill = (remaining, splits, row) =>
  Math.max(0, round2(remaining - round2(tenderedTotal(splits) - Number(row.amount || 0))))

// ERPNext computes change_amount only when a Cash-type Mode of Payment is
// tendered (see calculate_change_amount). Overpaying on a card posts a negative
// outstanding — a customer credit — instead of giving change back.
export const canGiveChange = (splits, typeOf) =>
  splits.some((r) => Number(r.amount || 0) > 0 && typeOf(r.mode_of_payment) === "Cash")
