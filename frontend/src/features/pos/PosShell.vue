<script setup>
import { useRoute, useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import "./pos.css"

const route = useRoute()
const router = useRouter()

const navItems = [
  { name: "pos-register", to: "/", icon: "fa-cash-register", label: "نقاط البيع" },
  { name: "pos-orders", to: "/orders", icon: "fa-receipt", label: "الطلبات" },
  { name: "pos-inventory", to: "/inventory", icon: "fa-boxes-stacked", label: "المخزون" },
  { name: "pos-stocktake", to: "/stocktake", icon: "fa-clipboard-check", label: "الجرد اليومي" },
  { name: "pos-receiving", to: "/receiving", icon: "fa-truck-ramp-box", label: "استلام الطلبات" },
  { name: "pos-reports", to: "/reports", icon: "fa-chart-bar", label: "التقارير" },
  { name: "pos-settings", to: "/settings", icon: "fa-gear", label: "الإعدادات" },
]

async function logout() {
  await signOut()
  router.replace("/login")
}
</script>

<template>
  <div class="pos-root flex flex-row-reverse w-full bg-pos-canvas" dir="rtl" style="height: 100dvh; overflow: hidden">
    <!-- Sidebar nav (RTL → sits on the right) -->
    <aside class="flex flex-col items-center bg-pos-sidebar w-16 md:w-20 py-4 gap-2 border-l border-pos-border flex-shrink-0 relative z-20">
      <div class="w-10 h-10 md:w-12 md:h-12 bg-pos-brand rounded-xl2 flex items-center justify-center mb-3 shadow-md">
        <i class="fa-solid fa-utensils text-white text-base md:text-lg"></i>
      </div>
      <div class="flex flex-col gap-2 w-full px-2 mt-2">
        <RouterLink
          v-for="item in navItems"
          :key="item.name"
          :to="item.to"
          class="pos-nav-item flex flex-col items-center justify-center gap-1 rounded-xl2 py-3 px-1 min-h-[56px] hover:bg-pos-brand-light"
          :class="route.name === item.name ? 'active' : 'text-pos-muted'"
        >
          <i class="fa-solid text-lg" :class="item.icon"></i>
          <span class="text-[9px] font-bold leading-tight">{{ item.label }}</span>
        </RouterLink>
      </div>
      <div class="mt-auto flex flex-col items-center gap-3">
        <div class="flex flex-col items-center gap-1">
          <div class="w-2.5 h-2.5 bg-pos-green rounded-full pos-sync-dot"></div>
          <span class="text-[8px] text-pos-muted font-semibold">متزامن</span>
        </div>
        <button
          @click="logout"
          :title="`${session.user} — تسجيل الخروج`"
          class="w-9 h-9 rounded-full border-2 border-pos-brand bg-pos-brand-light flex items-center justify-center text-pos-brand-dark hover:bg-pos-brand hover:text-white transition-colors"
        >
          <i class="fa-solid fa-right-from-bracket text-sm"></i>
        </button>
      </div>
    </aside>

    <!-- Active screen -->
    <main class="flex-1 flex flex-col overflow-hidden min-w-0">
      <RouterView />
    </main>
  </div>
</template>
