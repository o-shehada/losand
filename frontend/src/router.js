import { createRouter, createWebHistory } from "vue-router"
import { session, isAuthenticated, refreshSession } from "@/stores/session"
import LoginView from "@/features/auth/LoginView.vue"
import ManufactureHome from "@/features/manufacture/ManufactureHome.vue"
import FoodLoggerEntry from "@/features/food-logger/FoodLoggerEntry.vue"
import FoodLoggerSummary from "@/features/food-logger/FoodLoggerSummary.vue"
import FoodLoggerSuccess from "@/features/food-logger/FoodLoggerSuccess.vue"
import PosShell from "@/features/pos/PosShell.vue"
import PosRegister from "@/features/pos/PosRegister.vue"
import PosOrders from "@/features/pos/PosOrders.vue"
import PosInventory from "@/features/pos/PosInventory.vue"
import PosReports from "@/features/pos/PosReports.vue"
import PosSettings from "@/features/pos/PosSettings.vue"

// One Vite bundle serves two portals (manufacture + POS). Each portal is a
// full-page load mounting the same #app, so we pick the route tree + history
// base from the URL prefix the server rendered us under.
const POS_BASE = "/los-andalus/pos"
const MFG_BASE = "/los-andalus/manufacture"
const isPos = window.location.pathname.startsWith(POS_BASE)

const manufactureRoutes = [
  { path: "/", redirect: "/home" },
  { path: "/login", name: "login", component: LoginView, meta: { public: true } },
  { path: "/home", name: "home", component: ManufactureHome },
  { path: "/food-logger/new", name: "food-logger-new", component: FoodLoggerEntry },
  { path: "/food-logger/summary", name: "food-logger-summary", component: FoodLoggerSummary },
  { path: "/food-logger/success", name: "food-logger-success", component: FoodLoggerSuccess },
]

const posRoutes = [
  { path: "/login", name: "login", component: LoginView, meta: { public: true } },
  {
    path: "/",
    component: PosShell,
    children: [
      { path: "", name: "pos-register", component: PosRegister },
      { path: "orders", name: "pos-orders", component: PosOrders },
      { path: "inventory", name: "pos-inventory", component: PosInventory },
      { path: "reports", name: "pos-reports", component: PosReports },
      { path: "settings", name: "pos-settings", component: PosSettings },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(isPos ? POS_BASE : MFG_BASE),
  routes: isPos ? posRoutes : manufactureRoutes,
})

router.beforeEach(async (to) => {
  // window.boot may contain the user, but it does not contain this app's
  // capability flags. Hydrate them once on every full-page load.
  if (!session.initialized) {
    await refreshSession().catch(() => null)
  }
  if (to.meta.public && isAuthenticated()) {
    return "/"
  }
  if (!to.meta.public && !isAuthenticated()) {
    return "/login"
  }
  return true
})

export default router
