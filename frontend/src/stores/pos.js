import { reactive } from "vue"
import { checkOpeningShift, getPosConfig, getPosExtras, getPosNotes } from "@/lib/api"

// POS session state: the open shift + POS Profile config + add-on catalog, loaded
// once per full-page load and reused by the router guard, opening screen, register,
// and customization sheet.
export const pos = reactive({
  config: null, // { pos_profile, company, currency, currency_symbol, price_list, payments, ... }
  shift: null, // open POS Opening Entry, or null
  extras: [], // add-on Items [{ id, item_code, name, price }] — empty if not set up
  notes: [], // free kitchen notes from the Los Andalus Kitchen Note doctype
  incoming: 0, // transfers waiting to be received — drives the sidebar badge
  ready: false,
  error: "", // why the POS config could not load (e.g. no assigned POS Profile)
})

export async function ensurePos() {
  if (pos.ready) return
  pos.error = ""
  pos.config = await getPosConfig().catch((e) => {
    pos.error = e.message
    return null
  })
  pos.shift = await checkOpeningShift().catch(() => null)
  pos.extras = (await getPosExtras().catch(() => [])) || []
  pos.notes = (await getPosNotes().catch(() => [])) || []
  pos.ready = !!pos.config // not cached on failure: another user may sign in next
}

export function hasShift() {
  return !!pos.shift
}

export function setShift(shift) {
  pos.shift = shift
}
