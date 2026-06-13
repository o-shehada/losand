import { createRouter, createWebHistory } from "vue-router"
import { isAuthenticated, refreshSession } from "@/stores/session"
import LoginView from "@/features/auth/LoginView.vue"
import ManufactureHome from "@/features/manufacture/ManufactureHome.vue"
import FoodLoggerEntry from "@/features/food-logger/FoodLoggerEntry.vue"
import FoodLoggerSummary from "@/features/food-logger/FoodLoggerSummary.vue"
import FoodLoggerSuccess from "@/features/food-logger/FoodLoggerSuccess.vue"

const routes = [
  { path: "/", redirect: "/home" },
  { path: "/login", name: "login", component: LoginView, meta: { public: true } },
  { path: "/home", name: "home", component: ManufactureHome },
  { path: "/food-logger/new", name: "food-logger-new", component: FoodLoggerEntry },
  { path: "/food-logger/summary", name: "food-logger-summary", component: FoodLoggerSummary },
  { path: "/food-logger/success", name: "food-logger-success", component: FoodLoggerSuccess },
]

const router = createRouter({
  history: createWebHistory("/los-andalus/manufacture"),
  routes,
})

router.beforeEach(async (to) => {
  if (!isAuthenticated()) {
    await refreshSession().catch(() => null)
  }
  if (to.meta.public && isAuthenticated()) {
    return "/home"
  }
  if (!to.meta.public && !isAuthenticated()) {
    return "/login"
  }
  return true
})

export default router
