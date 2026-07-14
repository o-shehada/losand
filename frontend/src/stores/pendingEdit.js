import { reactive } from "vue"

// One-shot handoff from the invoice-history "edit" action to the register: the
// history screen cancels the original invoice server-side and stashes its item
// lines here, then navigates to "/"; the register consumes and clears it on
// mount. Session-local only — no server round-trip needed for a same-tab handoff.
export const pendingEdit = reactive({ cart: null, table: null })

export function setPendingEdit(cart, table) {
  pendingEdit.cart = cart
  pendingEdit.table = table
}

export function consumePendingEdit() {
  if (!pendingEdit.cart) return null
  const result = { cart: pendingEdit.cart, table: pendingEdit.table }
  pendingEdit.cart = null
  pendingEdit.table = null
  return result
}
