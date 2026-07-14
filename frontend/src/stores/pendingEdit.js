import { reactive } from "vue"

// One-shot handoff from the invoice-history "edit" action to the register: the
// history screen cancels the original invoice server-side and stashes its item
// lines here, then navigates to "/"; the register consumes and clears it on
// mount. Session-local only — no server round-trip needed for a same-tab handoff.
//
// `amendedFrom` is the cancelled invoice's name — the register hands it back at
// checkout so the corrected invoice is submitted as that invoice's amendment.
export const pendingEdit = reactive({ cart: null, table: null, amendedFrom: null })

export function setPendingEdit(cart, table, amendedFrom) {
  pendingEdit.cart = cart
  pendingEdit.table = table
  pendingEdit.amendedFrom = amendedFrom
}

export function consumePendingEdit() {
  if (!pendingEdit.cart) return null
  const result = { cart: pendingEdit.cart, table: pendingEdit.table, amendedFrom: pendingEdit.amendedFrom }
  pendingEdit.cart = null
  pendingEdit.table = null
  pendingEdit.amendedFrom = null
  return result
}
