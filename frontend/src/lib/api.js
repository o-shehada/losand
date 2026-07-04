const headers = {
  "Content-Type": "application/json",
  "X-Frappe-CSRF-Token": window.csrf_token || "",
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
    const message = data._server_messages
      ? JSON.parse(data._server_messages).join("\n")
      : data.message || "Request failed"
    throw new Error(message)
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

export async function saveStocktake(counts) {
  return call("losand.api.pos.save_stocktake", { counts })
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

export async function login(username, password) {
  return call("login", { usr: username, pwd: password })
}

export async function logout() {
  return call("logout")
}
