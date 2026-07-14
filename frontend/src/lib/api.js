const headers = {
  "Content-Type": "application/json",
  "X-Frappe-CSRF-Token": window.csrf_token || "",
}

function messageText(value) {
  if (typeof value !== "string") return value?.message
  try {
    return JSON.parse(value)?.message || value
  } catch {
    return value
  }
}

function serverMessage(data) {
  const fallback = messageText(data.message) || "Request failed"
  if (!data._server_messages) return fallback

  try {
    const parsed = JSON.parse(data._server_messages)
    const entries = Array.isArray(parsed) ? parsed : [parsed]
    return entries
      .map(messageText)
      .filter(Boolean)
      .join("\n") || fallback
  } catch {
    return fallback
  }
}

export async function call(method, payload = {}) {
  const response = await fetch(`/api/method/${method}`, {
    method: "POST",
    headers,
    credentials: "same-origin",
    cache: "no-store",
    body: JSON.stringify(payload),
  })
  const data = await response.json().catch(() => ({}))
  if (!response.ok || data.exc) {
    throw new Error(serverMessage(data))
  }
  return data.message
}

export async function getCurrentSession() {
  return call("losand.api.manufacture.get_current_session")
}

export async function getPosConfig(posProfile) {
  return call("losand.api.pos.get_pos_config", posProfile ? { pos_profile: posProfile } : {})
}

export async function getPosProducts(params = {}) {
  return call("losand.api.pos.get_products", params)
}

export async function getPosExtras() {
  return call("losand.api.pos.get_extras")
}

export async function previewOrder(payload) {
  return call("losand.api.pos.preview_order", payload)
}

export async function checkOpeningShift() {
  return call("losand.api.pos.check_opening_shift")
}

export async function createOpeningShift(posProfile, company, balances) {
  return call("losand.api.pos.create_opening_shift", { pos_profile: posProfile, company, balances })
}

export async function getShiftSummary() {
  return call("losand.api.pos.get_shift_summary")
}

export async function closeShift(counted) {
  return call("losand.api.pos.close_shift", { counted })
}

export async function checkGiftCard(code) {
  return call("losand.api.pos.check_gift_card", { code })
}

export async function getInventory() {
  return call("losand.api.pos.get_inventory")
}

export async function getStocktakeItems() {
  return call("losand.api.pos.get_stocktake_items")
}

export async function getWasteItems() {
  return call("losand.api.pos.get_waste_items")
}

export async function getReceivingItems() {
  return call("losand.api.pos.get_receiving_items")
}

export async function saveStocktake(counts) {
  return call("losand.api.pos.save_stocktake", { counts })
}

export async function saveWaste(items) {
  return call("losand.api.pos.save_waste", { items })
}

export async function receiveGoods(payload) {
  return call("losand.api.pos.receive_goods", payload)
}

export async function submitOrder(payload) {
  return call("losand.api.pos.submit_order", payload)
}

export async function parkOrder(payload) {
  return call("losand.api.pos.park_order", payload)
}

export async function listParked() {
  return call("losand.api.pos.list_parked")
}

export async function resumeParked(name) {
  return call("losand.api.pos.resume_order", { name })
}

export async function discardParked(name) {
  return call("losand.api.pos.discard_parked", { name })
}

export async function getShiftInvoices() {
  return call("losand.api.pos.get_shift_invoices")
}

export async function returnInvoice(invoice) {
  return call("losand.api.pos.return_invoice", { invoice })
}

export async function editInvoice(invoice) {
  return call("losand.api.pos.edit_invoice", { invoice })
}

export async function cancelInvoice(invoice) {
  return call("losand.api.pos.cancel_invoice", { invoice })
}

export async function login(username, password) {
  return call("login", { usr: username, pwd: password })
}

export async function logout() {
  return call("logout")
}
