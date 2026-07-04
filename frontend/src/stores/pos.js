import { reactive } from "vue"
import { checkOpeningShift, getPosConfig, getPosExtras } from "@/lib/api"

// POS session state: the open shift + POS Profile config + add-on catalog, loaded
// once per full-page load and reused by the router guard, opening screen, register,
// and customization sheet.
export const pos = reactive({
  config: null, // { pos_profile, company, currency, currency_symbol, price_list, payments, ... }
  shift: null, // open POS Opening Entry, or null
  extras: [], // add-on Items [{ id, item_code, name, price }] — empty if not set up
  ready: false,
})

export async function ensurePos() {
  if (pos.ready) return
  pos.config = await getPosConfig().catch(() => null)
  pos.shift = await checkOpeningShift().catch(() => null)
  pos.extras = (await getPosExtras().catch(() => [])) || []
  pos.ready = true
}

export function hasShift() {
  return !!pos.shift
}

export function setShift(shift) {
  pos.shift = shift
}
