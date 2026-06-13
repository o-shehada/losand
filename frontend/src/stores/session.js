import { reactive } from "vue"
import { getCurrentSession, login, logout } from "@/lib/api"

export const session = reactive({
  user: window.boot?.user || "Guest",
  loading: false,
  error: "",
})

export function isAuthenticated() {
  return session.user && session.user !== "Guest"
}

export async function refreshSession() {
  session.loading = true
  session.error = ""
  try {
    const current = await getCurrentSession()
    session.user = current.user
    return current
  } finally {
    session.loading = false
  }
}

export async function signIn(username, password) {
  session.loading = true
  session.error = ""
  try {
    await login(username, password)
    await refreshSession()
  } catch (error) {
    session.error = error.message
    throw error
  } finally {
    session.loading = false
  }
}

export async function signOut() {
  await logout()
  session.user = "Guest"
}
