<script setup>
import { computed } from "vue"
import { ORDER_COLUMNS, ORDERS, orderType, orderTotal, BRANCH, money, ar } from "./data"
import { pos } from "@/stores/pos"

const colOrders = (key) => ORDERS.filter((o) => o.col === key)
const counts = computed(() => Object.fromEntries(ORDER_COLUMNS.map((c) => [c.key, colOrders(c.key).length])))
const activeTotal = computed(() => ORDERS.filter((o) => o.col !== "done").length)

const advance = {
  new: { label: "إرسال للمطبخ", icon: "fa-fire-burner", cls: "bg-pos-brand hover:bg-pos-brand-dark text-white" },
  prep: { label: "جاهز للتسليم", icon: "fa-bell-concierge", cls: "bg-pos-green hover:opacity-90 text-white" },
  ready: { label: "تسليم الطلب", icon: "fa-motorcycle", cls: "bg-pos-brand-dark hover:bg-pos-brand text-white" },
  done: { label: "فاتورة", icon: "fa-print", cls: "bg-pos-canvas border border-pos-border text-pos-muted hover:border-pos-brand hover:text-pos-brand" },
}
const timeIcon = (t) => (t === "late" ? "fa-triangle-exclamation" : "fa-clock")
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-list-check text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">إدارة الطلبات</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }}</span>
          <span class="text-xs text-pos-muted">·</span>
          <span class="text-xs text-pos-muted">الأربعاء، 22 يناير 2025</span>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-2 flex-wrap justify-end">
      <div class="relative">
        <input type="text" placeholder="بحث برقم الطلب..." class="bg-pos-canvas border border-pos-border rounded-xl pr-4 pl-9 py-2 text-sm focus:outline-none focus:border-pos-brand text-gray-700 w-40 md:w-52 min-h-[44px]" />
        <i class="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-pos-muted text-sm"></i>
      </div>
      <div class="pos-shift-pill text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
        <i class="fa-solid fa-sun text-yellow-200 text-xs"></i><span>{{ pos.config?.pos_profile || "…" }}</span>
      </div>
      <div class="flex items-center gap-1.5 bg-pos-brand-light border border-pos-brand/30 rounded-xl px-2.5 py-2 min-h-[44px]">
        <i class="fa-solid fa-rotate text-pos-brand text-xs pos-sync-dot"></i>
        <span class="text-xs text-pos-brand font-bold hidden md:inline">تحديث تلقائي</span>
      </div>
    </div>
  </header>

  <!-- STATS BAR -->
  <div class="bg-pos-surface border-b border-pos-border px-4 py-2 flex items-center gap-4 flex-shrink-0 overflow-x-auto">
    <div class="flex items-center gap-2">
      <span class="text-xs text-pos-muted font-semibold whitespace-nowrap">إجمالي الطلبات النشطة:</span>
      <span class="bg-pos-brand text-white text-xs font-extrabold px-2.5 py-0.5 rounded-full">{{ ar(activeTotal) }} طلب</span>
    </div>
    <div class="h-4 w-px bg-pos-border"></div>
    <div v-for="c in ORDER_COLUMNS" :key="c.key" class="flex items-center gap-1.5 whitespace-nowrap">
      <div class="w-2 h-2 rounded-full" :class="c.dot"></div>
      <span class="text-xs text-pos-muted font-semibold">{{ c.label }}: <span class="text-gray-700 font-bold">{{ ar(counts[c.key]) }}</span></span>
    </div>
  </div>

  <!-- BOARD -->
  <div class="flex-1 overflow-hidden p-3 md:p-4">
    <div class="flex gap-3 h-full">
      <div
        v-for="c in ORDER_COLUMNS"
        :key="c.key"
        class="flex-1 flex flex-col bg-pos-surface rounded-xl2 border border-pos-border overflow-hidden shadow-sm min-w-0"
        :class="c.accent"
      >
        <!-- column header -->
        <div class="px-3 py-3 border-b border-pos-border bg-pos-brand-light/40 flex items-center justify-between flex-shrink-0">
          <div class="flex items-center gap-2">
            <div class="w-3 h-3 rounded-full" :class="c.dot"></div>
            <span class="font-extrabold text-gray-800 text-sm">{{ c.label }}</span>
          </div>
          <span class="text-xs font-extrabold px-2.5 py-1 rounded-full" :class="c.badge">{{ ar(counts[c.key]) }} طلبات</span>
        </div>

        <!-- cards -->
        <div class="flex-1 overflow-y-auto p-2 space-y-2.5">
          <div
            v-for="o in colOrders(c.key)"
            :key="o.id"
            class="pos-order-card bg-pos-canvas rounded-xl border border-pos-border overflow-hidden cursor-pointer"
            :class="o.col === 'done' ? 'opacity-80' : ''"
          >
            <!-- card header -->
            <div class="px-3 py-2 bg-pos-surface border-b border-pos-border flex items-center justify-between gap-1">
              <div class="flex items-center gap-2">
                <span class="font-extrabold text-gray-800 text-sm">#{{ ar(o.id) }}</span>
                <span class="text-[10px] font-bold px-2 py-0.5 rounded-full" :class="orderType(o.type).chip">{{ orderType(o.type).label }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <span class="bg-pos-canvas border border-pos-border text-gray-600 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                  <i class="fa-solid text-[9px]" :class="orderType(o.type).icon"></i> {{ o.where }}
                </span>
                <span class="text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1" :class="`pos-time-${o.time || 'fresh'}`" v-if="o.col !== 'done'">
                  <i class="fa-solid text-[9px]" :class="timeIcon(o.time)"></i> {{ ar(o.mins) }} دقيقة
                </span>
                <span v-else class="bg-pos-muted/10 text-pos-muted text-[10px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1">
                  <i class="fa-solid fa-check text-[9px]"></i> {{ ar(o.mins) }} دقيقة
                </span>
              </div>
            </div>

            <!-- progress (prep) -->
            <div v-if="o.progress != null" class="px-3 pt-2">
              <div class="flex items-center justify-between mb-1">
                <span class="text-[10px] text-pos-muted font-semibold">التقدم</span>
                <span class="text-[10px] font-bold" :class="o.late ? 'text-pos-danger' : 'text-pos-amber'">{{ ar(o.progress) }}٪</span>
              </div>
              <div class="w-full bg-pos-border rounded-full h-1.5">
                <div class="h-1.5 rounded-full" :class="o.late ? 'bg-pos-danger' : 'bg-pos-amber'" :style="{ width: o.progress + '%' }"></div>
              </div>
            </div>

            <!-- ready hint -->
            <div v-if="o.hint" class="px-3 pt-2.5 pb-1">
              <div class="flex items-center gap-1.5 bg-pos-green/10 rounded-lg px-2 py-1 border border-pos-green/25">
                <div class="w-2 h-2 rounded-full bg-pos-green pos-sync-dot flex-shrink-0"></div>
                <span class="text-xs text-pos-green font-bold">{{ o.hint }}</span>
              </div>
            </div>

            <!-- items -->
            <div class="px-3 py-2 space-y-1">
              <div v-for="(it, i) in o.items" :key="i" class="flex items-center justify-between text-sm">
                <span class="font-semibold text-xs" :class="it.done ? 'text-gray-400 line-through' : 'text-gray-700'">{{ ar(it.q) }}× {{ it.name }}</span>
                <span class="font-bold text-xs" :class="it.done ? 'text-pos-muted' : 'text-pos-brand-dark'">{{ money(it.price) }}</span>
              </div>
              <div v-if="o.note" class="mt-1.5 bg-pos-amber/10 border border-pos-amber/30 rounded-lg px-2 py-1 flex items-center gap-1.5">
                <i class="fa-solid fa-note-sticky text-pos-amber text-xs"></i>
                <span class="text-xs text-pos-amber font-semibold">{{ o.note }}</span>
              </div>
            </div>

            <!-- footer -->
            <div class="px-3 py-2 border-t border-pos-border flex items-center justify-between bg-pos-surface gap-1">
              <div class="flex items-center gap-1.5">
                <span class="text-xs text-pos-muted font-semibold">{{ money(orderTotal(o)) }}</span>
                <span v-if="o.late" class="bg-pos-danger/10 text-pos-danger text-[9px] font-bold px-1.5 py-0.5 rounded-full">متأخر</span>
                <span v-if="o.paid" class="bg-pos-brand/10 text-pos-brand-dark text-[10px] font-bold px-2 py-0.5 rounded-full border border-pos-brand/20 flex items-center gap-1">
                  <i class="fa-solid fa-circle-check text-[9px]"></i> مدفوع
                </span>
              </div>
              <button class="pos-btn text-xs font-bold px-3 py-2 rounded-xl min-h-[36px] flex items-center gap-1.5 transition-colors shadow-sm" :class="advance[o.col].cls">
                <i class="fa-solid text-xs" :class="advance[o.col].icon"></i> {{ advance[o.col].label }}
              </button>
            </div>
          </div>

          <div v-if="!colOrders(c.key).length" class="border-2 border-dashed border-pos-border rounded-xl p-4 flex flex-col items-center justify-center text-center gap-2 opacity-60">
            <div class="w-10 h-10 bg-pos-canvas rounded-full flex items-center justify-center">
              <i class="fa-solid fa-check-double text-pos-muted text-base"></i>
            </div>
            <p class="text-xs text-pos-muted font-semibold">لا توجد طلبات هنا</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
