const headers = {
  "Content-Type": "application/json",
  "X-Frappe-CSRF-Token": window.csrf_token || "",
}

export async function call(method, payload = {}) {
  const response = await fetch(`/api/method/${method}`, {
    method: "POST",
    headers,
    credentials: "same-origin",
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

export async function login(username, password) {
  return call("login", { usr: username, pwd: password })
}

export async function logout() {
  return call("logout")
}
