// Runnable check for the cart money path. No framework — `node cartMath.test.js`.
import assert from "node:assert/strict"
import { lineTotal, unitPrice, isUniform, giftApplied, giftRemaining } from "./cartMath.js"

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

console.log("cartMath ok")
