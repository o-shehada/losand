// Runnable check for the cart money path. No framework — `node cartMath.test.js`.
import assert from "node:assert/strict"
import {
  lineTotal,
  unitPrice,
  isUniform,
  giftApplied,
  giftRemaining,
  tenderedTotal,
  tenderDiff,
  tenderFill,
  canGiveChange,
} from "./cartMath.js"

const e = (id, price) => ({ id, name: id, price })
const piece = (extras = [], notes = []) => ({ extras, notes })

// Mixed pieces: 4× base 21, piece#1 +pickle(1), piece#4 +sauce(1) → 84+1+1 = 86.
const mixed = { price: 21, pieces: [piece([e("pickle", 1)]), piece(), piece(), piece([e("sauce", 1)])] }
assert.equal(lineTotal(mixed), 86)
assert.equal(isUniform(mixed), false)
assert.equal(unitPrice(mixed), 21) // mixed → base only

// Uniform: 4× (base 22 + cheese 2) = 96, unit = 24.
const uniform = { price: 22, pieces: Array.from({ length: 4 }, () => piece([e("cheese", 2)])) }
assert.equal(lineTotal(uniform), 96)
assert.equal(isUniform(uniform), true)
assert.equal(unitPrice(uniform), 24)

// Gift card covers whole total → remaining 0.
assert.equal(giftApplied(10, 10), 10)
assert.equal(giftRemaining(10, 10), 0)
// Gift card covers part → remaining paid by another method.
assert.equal(giftApplied(20, 10), 10)
assert.equal(giftRemaining(20, 10), 10)
// Card worth more than total never goes negative.
assert.equal(giftRemaining(5, 10), 0)

// --- Payment tender ---
const typeOf = (mode) => ({ Cash: "Cash", "Credit Card": "Bank" })[mode]
const rows = (cash, card) => [
  { mode_of_payment: "Cash", amount: cash },
  { mode_of_payment: "Credit Card", amount: card },
]

// Exact single-method payment settles the balance.
assert.equal(tenderDiff(73, rows(73, 0)), 0)
// Short by 3 → positive diff; over by 27 → negative diff.
assert.equal(tenderDiff(73, rows(70, 0)), 3)
assert.equal(tenderDiff(73, rows(100, 0)), -27)
// Split across two methods sums, and float noise is rounded away.
assert.equal(tenderedTotal(rows(0.1, 0.2)), 0.3)
assert.equal(tenderDiff(100, rows(60, 40)), 0)

// Tapping a method fills only what the other rows leave unpaid.
const split = rows(40, 0)
assert.equal(tenderFill(100, split, split[1]), 60)
// Re-tapping an already-tendered row is idempotent, not additive.
const full = rows(100, 0)
assert.equal(tenderFill(100, full, full[0]), 100)
// Others already cover the balance → nothing left to fill (never negative).
const over = rows(120, 0)
assert.equal(tenderFill(100, over, over[1]), 0)

// Change is only real on a Cash-type mode — card-only overpay must not claim it.
assert.equal(canGiveChange(rows(100, 0), typeOf), true)
assert.equal(canGiveChange(rows(0, 100), typeOf), false)
// A zero-amount cash row is not tendered cash.
assert.equal(canGiveChange(rows(0, 73), typeOf), false)

console.log("cartMath ok")
