<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { call } from "@/lib/api"
import { session, signOut } from "@/stores/session"
import { cur } from "@/lib/currency"
import { createDraft, calc, fmt, fmt1, presentationFor } from "./data"

const router = useRouter()

async function logout() {
  await signOut()
  router.replace("/login")
}

const stored = sessionStorage.getItem("foodLoggerDraft")
const draft = reactive(stored ? JSON.parse(stored) : createDraft())
const totals = computed(() => calc(draft))
const presentation = computed(() => presentationFor(draft.product))

const confirmed = ref(false)
const saving = ref(false)

const acc = reactive({ materials: true, waste: false, loss: false })
function toggle(key) {
  acc[key] = !acc[key]
}

async function save() {
  if (!confirmed.value || saving.value || !session.canProduce) return
  saving.value = true
  try {
    const result = await call("losand.api.manufacture.submit_batch", {
      draft,
      totals: totals.value,
    })
    sessionStorage.setItem("foodLoggerSuccess", JSON.stringify(result))
    sessionStorage.removeItem("foodLoggerDraft")
    router.push("/food-logger/success")
  } catch (e) {
    saving.value = false
    alert(e.message)
  }
}

// Live clock
const liveTime = ref("")
let timer = null
function tick() {
  const now = new Date()
  let h = now.getHours()
  const m = now.getMinutes().toString().padStart(2, "0")
  const period = h >= 12 ? "م" : "ص"
  if (h > 12) h -= 12
  if (h === 0) h = 12
  liveTime.value = `${h}:${m} ${period}`
}
onMounted(() => {
  tick()
  timer = setInterval(tick, 60000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="font-cairo bg-warm text-text min-h-screen" dir="rtl">
    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
      <div class="bg-primary px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
            <i class="fa-solid fa-industry text-white text-base"></i>
          </div>
          <div>
            <p class="text-white/70 text-xs font-medium">نظام إدارة الإنتاج</p>
            <p class="text-white font-bold text-sm">مصنع الغذاء الحديث</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 bg-white/15 rounded-xl px-3 py-1.5">
            <i class="fa-regular fa-clock text-white/80 text-sm"></i>
            <span class="text-white font-semibold text-sm">{{ liveTime }}</span>
          </div>
          <div class="w-9 h-9 rounded-full border-2 border-white/40 bg-white/20 flex items-center justify-center">
            <i class="fa-solid fa-user text-white text-sm"></i>
          </div>
          <button @click="logout" title="تسجيل الخروج" class="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 transition-colors rounded-xl px-3 py-1.5 text-white">
            <i class="fa-solid fa-right-from-bracket text-sm"></i>
            <span class="text-sm font-semibold hidden sm:inline">تسجيل الخروج</span>
          </button>
        </div>
      </div>

      <div class="px-6 py-4 bg-white flex items-center justify-between gap-4">
        <div class="flex items-center gap-4">
          <button @click="router.push('/food-logger/new')" class="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center border border-border hover:bg-slate-200 transition-colors">
            <i class="fa-solid fa-arrow-right text-text text-base"></i>
          </button>
          <div>
            <h1 class="text-xl font-bold text-text">ملخص الإنتاج</h1>
            <div class="flex items-center gap-3 flex-wrap mt-0.5">
              <div class="flex items-center gap-1.5">
                <span class="text-xs text-muted">رقم الدفعة:</span>
                <span class="text-sm font-bold text-primary bg-primary-light px-2.5 py-0.5 rounded-lg">{{ draft.batchRef }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <i class="fa-regular fa-calendar text-muted text-xs"></i>
                <span class="text-sm text-muted font-medium">{{ draft.dateLabel }}</span>
              </div>
            </div>
          </div>
        </div>
        <button class="flex items-center gap-2 px-4 py-2.5 bg-slate-100 text-muted rounded-xl border border-border hover:bg-slate-200 transition-colors min-h-[44px]">
          <i class="fa-solid fa-print text-base"></i>
          <span class="text-sm font-semibold hidden sm:inline">طباعة</span>
        </button>
      </div>
    </header>

    <main class="px-4 md:px-6 py-6 pb-40 max-w-4xl mx-auto">
      <!-- Hero Card -->
      <section class="mb-6">
        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div class="bg-gradient-to-l from-primary to-primary-dark px-5 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center">
                <i class="fa-solid text-white text-xl" :class="presentation.icon"></i>
              </div>
              <div>
                <p class="text-white/80 text-xs font-medium">المنتج المحدد</p>
                <p class="text-white font-bold text-lg">{{ draft.productName }}</p>
                <p class="text-white/70 text-xs">{{ draft.weight }} جم / قطعة</p>
              </div>
            </div>
            <div class="text-left">
              <div class="bg-white/20 rounded-xl px-3 py-1.5 mb-1.5">
                <p class="text-white/70 text-xs">رقم الدفعة</p>
                <p class="text-white font-bold text-sm">{{ draft.batchRef }}</p>
              </div>
              <div class="flex items-center gap-1.5 bg-green-500/30 rounded-lg px-2.5 py-1 border border-green-400/30">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span class="text-white text-xs font-semibold">مكتملة</span>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 md:grid-cols-4 divide-x divide-x-reverse divide-border border-t border-border">
            <div class="px-4 py-4 text-center">
              <p class="text-xs text-muted mb-1 font-medium">الكمية المنتجة</p>
              <p class="text-2xl font-black text-text">{{ draft.producedQty }}</p>
              <p class="text-xs text-muted mt-0.5">قطعة</p>
            </div>
            <div class="px-4 py-4 text-center">
              <p class="text-xs text-muted mb-1 font-medium">تكلفة الوحدة</p>
              <p class="text-2xl font-black text-primary">{{ fmt(totals.unitCost) }}</p>
              <p class="text-xs text-muted mt-0.5">{{ cur }} / قطعة</p>
            </div>
            <div class="px-4 py-4 text-center border-t md:border-t-0 border-border">
              <p class="text-xs text-muted mb-1 font-medium">التكلفة الإجمالية</p>
              <p class="text-2xl font-black text-text">{{ fmt(totals.totalCost) }}</p>
              <p class="text-xs text-muted mt-0.5">{{ cur }}</p>
            </div>
            <div class="px-4 py-4 text-center border-t md:border-t-0 border-border">
              <p class="text-xs text-muted mb-1 font-medium">نسبة الهالك</p>
              <p class="text-2xl font-black text-danger">{{ totals.wastePct.toFixed(1) }}%</p>
              <p class="text-xs text-muted mt-0.5">من الإجمالي</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Accordions -->
      <section class="mb-6 space-y-3">
        <!-- Materials -->
        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <button @click="toggle('materials')" class="w-full px-5 py-4 flex items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-boxes-stacked text-blue-500 text-base"></i>
              </div>
              <div class="text-right">
                <p class="font-bold text-text text-sm">تفصيل المواد الخام</p>
                <p class="text-xs text-muted">{{ draft.materials.length }} مواد خام مستخدمة</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm font-bold text-text bg-slate-100 px-3 py-1 rounded-lg">{{ fmt(totals.materialTotal) }} {{ cur }}</span>
              <i class="fa-solid fa-chevron-down text-muted transition-transform" :class="{ 'rotate-180': acc.materials }"></i>
            </div>
          </button>
          <div v-show="acc.materials" class="border-t border-border">
            <div class="grid grid-cols-12 bg-slate-50 px-5 py-2.5 border-b border-border">
              <div class="col-span-5 text-xs font-bold text-muted">المادة الخام</div>
              <div class="col-span-2 text-xs font-bold text-muted text-center">الكمية</div>
              <div class="col-span-2 text-xs font-bold text-muted text-center">السعر/وحدة</div>
              <div class="col-span-3 text-xs font-bold text-muted text-center">الإجمالي</div>
            </div>
            <div v-for="(m, i) in draft.materials" :key="i" class="grid grid-cols-12 px-5 py-3 border-b border-border items-center">
              <div class="col-span-5 flex items-center gap-2">
                <div class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" :class="m.wrap">
                  <i class="fa-solid text-xs" :class="[m.icon, m.color]"></i>
                </div>
                <div>
                  <p class="text-sm font-semibold text-text">{{ m.name_ar }}</p>
                  <p class="text-xs text-muted">{{ m.actual }} {{ m.unit }} فعلي</p>
                </div>
              </div>
              <div class="col-span-2 text-center text-sm font-semibold text-text">{{ m.actual }} {{ m.unit }}</div>
              <div class="col-span-2 text-center text-sm font-semibold text-muted">{{ fmt(m.rate) }}</div>
              <div class="col-span-3 text-center text-sm font-bold text-text">{{ fmt(m.actual * m.rate) }} {{ cur }}</div>
            </div>
            <div class="bg-slate-50 px-5 py-3 flex items-center justify-between">
              <span class="text-sm font-bold text-text">إجمالي تكلفة المواد</span>
              <span class="text-base font-black text-primary">{{ fmt(totals.materialTotal) }} {{ cur }}</span>
            </div>
          </div>
        </div>

        <!-- Waste -->
        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <button @click="toggle('waste')" class="w-full px-5 py-4 flex items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-trash-can text-danger text-base"></i>
              </div>
              <div class="text-right">
                <p class="font-bold text-text text-sm">تفصيل الهالك</p>
                <p class="text-xs text-danger font-medium">{{ totals.wasteUnits }} قطعة تالفة — {{ totals.wastePct.toFixed(1) }}%</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm font-bold text-danger bg-red-50 px-3 py-1 rounded-lg border border-red-100">{{ fmt(totals.wasteTotal) }} {{ cur }}</span>
              <i class="fa-solid fa-chevron-down text-muted transition-transform" :class="{ 'rotate-180': acc.waste }"></i>
            </div>
          </button>
          <div v-show="acc.waste" class="border-t border-border">
            <div class="grid grid-cols-12 bg-red-50 px-5 py-2.5 border-b border-red-100">
              <div class="col-span-6 text-xs font-bold text-muted">نوع الهالك</div>
              <div class="col-span-3 text-xs font-bold text-muted text-center">الكمية</div>
              <div class="col-span-3 text-xs font-bold text-muted text-center">التكلفة</div>
            </div>
            <div v-for="(w, i) in draft.waste" :key="i" class="grid grid-cols-12 px-5 py-3.5 border-b border-border items-center">
              <div class="col-span-6 flex items-center gap-2">
                <div class="w-2 h-2 bg-danger rounded-full flex-shrink-0"></div>
                <span class="text-sm font-semibold text-text">{{ w.reason }}</span>
              </div>
              <div class="col-span-3 text-center">
                <span class="bg-red-50 text-danger text-xs font-bold px-2 py-1 rounded-md">{{ w.qty }} {{ w.unit }}</span>
              </div>
              <div class="col-span-3 text-center text-sm font-bold text-danger">{{ fmt(w.qty * w.rate) }} {{ cur }}</div>
            </div>
            <div class="bg-red-50 px-5 py-3 flex items-center justify-between border-t border-red-100">
              <span class="text-sm font-bold text-danger">إجمالي الهالك</span>
              <span class="text-base font-black text-danger">{{ fmt(totals.wasteTotal) }} {{ cur }}</span>
            </div>
          </div>
        </div>

        <!-- Loss -->
        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <button @click="toggle('loss')" class="w-full px-5 py-4 flex items-center justify-between gap-3 hover:bg-slate-50 transition-colors">
            <div class="flex items-center gap-3">
              <div class="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-arrow-trend-down text-warning text-base"></i>
              </div>
              <div class="text-right">
                <p class="font-bold text-text text-sm">تفصيل الفاقد</p>
                <p class="text-xs text-warning font-medium">{{ fmt1(totals.lossUnits) }} كجم إجمالي — {{ totals.lossPct.toFixed(1) }}%</p>
              </div>
            </div>
            <div class="flex items-center gap-3">
              <span class="text-sm font-bold text-warning bg-amber-50 px-3 py-1 rounded-lg border border-amber-100">{{ fmt(totals.lossTotal) }} {{ cur }}</span>
              <i class="fa-solid fa-chevron-down text-muted transition-transform" :class="{ 'rotate-180': acc.loss }"></i>
            </div>
          </button>
          <div v-show="acc.loss" class="border-t border-border">
            <div class="grid grid-cols-12 bg-amber-50 px-5 py-2.5 border-b border-amber-100">
              <div class="col-span-6 text-xs font-bold text-muted">نوع الفاقد</div>
              <div class="col-span-3 text-xs font-bold text-muted text-center">الكمية</div>
              <div class="col-span-3 text-xs font-bold text-muted text-center">التكلفة</div>
            </div>
            <div v-for="(l, i) in draft.loss" :key="i" class="grid grid-cols-12 px-5 py-3.5 border-b border-border items-center">
              <div class="col-span-6 flex items-center gap-2">
                <div class="w-2 h-2 bg-warning rounded-full flex-shrink-0"></div>
                <span class="text-sm font-semibold text-text">{{ l.reason }}</span>
              </div>
              <div class="col-span-3 text-center">
                <span class="bg-amber-50 text-warning text-xs font-bold px-2 py-1 rounded-md">{{ l.qty }} {{ l.unit }}</span>
              </div>
              <div class="col-span-3 text-center text-sm font-bold text-warning">{{ fmt(l.qty * l.rate) }} {{ cur }}</div>
            </div>
            <div class="bg-amber-50 px-5 py-3 flex items-center justify-between border-t border-amber-100">
              <span class="text-sm font-bold text-warning">إجمالي الفاقد</span>
              <span class="text-base font-black text-warning">{{ fmt(totals.lossTotal) }} {{ cur }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Summary Table -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-table-list text-white text-sm"></i>
          </div>
          <h2 class="text-base font-bold text-text">جدول ملخص التكاليف</h2>
          <div class="flex-1 h-px bg-border"></div>
        </div>

        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div class="grid grid-cols-12 bg-slate-50 px-5 py-3 border-b border-border">
            <div class="col-span-5 text-xs font-bold text-muted">البند</div>
            <div class="col-span-3 text-xs font-bold text-muted text-center">القيمة</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">النسبة</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">الحالة</div>
          </div>

          <div class="grid grid-cols-12 px-5 py-4 border-b border-border items-center">
            <div class="col-span-5 flex items-center gap-2.5">
              <div class="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-boxes-stacked text-blue-500 text-sm"></i>
              </div>
              <div>
                <p class="text-sm font-semibold text-text">تكلفة المواد الخام</p>
                <p class="text-xs text-muted">{{ draft.materials.length }} مواد</p>
              </div>
            </div>
            <div class="col-span-3 text-center text-sm font-bold text-text">{{ fmt(totals.materialTotal) }} {{ cur }}</div>
            <div class="col-span-2 text-center"><span class="text-sm font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md">{{ totals.matPct.toFixed(1) }}%</span></div>
            <div class="col-span-2 flex justify-center">
              <span class="bg-green-50 text-success text-xs font-bold px-2 py-1 rounded-lg border border-green-100"><i class="fa-solid fa-check text-xs ml-1"></i>طبيعي</span>
            </div>
          </div>

          <div class="grid grid-cols-12 px-5 py-4 border-b border-border items-center bg-red-50/30">
            <div class="col-span-5 flex items-center gap-2.5">
              <div class="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-trash-can text-danger text-sm"></i>
              </div>
              <div>
                <p class="text-sm font-semibold text-text">تكلفة الهالك</p>
                <p class="text-xs text-danger">{{ totals.wasteUnits }} قطعة تالفة</p>
              </div>
            </div>
            <div class="col-span-3 text-center text-sm font-bold text-danger">{{ fmt(totals.wasteTotal) }} {{ cur }}</div>
            <div class="col-span-2 text-center"><span class="text-sm font-bold text-danger bg-red-50 px-2 py-0.5 rounded-md">{{ totals.wastePct.toFixed(1) }}%</span></div>
            <div class="col-span-2 flex justify-center">
              <span class="bg-red-50 text-danger text-xs font-bold px-2 py-1 rounded-lg border border-red-100"><i class="fa-solid fa-triangle-exclamation text-xs ml-1"></i>مرتفع</span>
            </div>
          </div>

          <div class="grid grid-cols-12 px-5 py-4 border-b border-border items-center bg-amber-50/20">
            <div class="col-span-5 flex items-center gap-2.5">
              <div class="w-8 h-8 bg-amber-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-arrow-trend-down text-warning text-sm"></i>
              </div>
              <div>
                <p class="text-sm font-semibold text-text">تكلفة الفاقد</p>
                <p class="text-xs text-warning">{{ fmt1(totals.lossUnits) }} كجم فاقد</p>
              </div>
            </div>
            <div class="col-span-3 text-center text-sm font-bold text-warning">{{ fmt(totals.lossTotal) }} {{ cur }}</div>
            <div class="col-span-2 text-center"><span class="text-sm font-bold text-warning bg-amber-50 px-2 py-0.5 rounded-md">{{ totals.lossPct.toFixed(1) }}%</span></div>
            <div class="col-span-2 flex justify-center">
              <span class="bg-amber-50 text-warning text-xs font-bold px-2 py-1 rounded-lg border border-amber-100"><i class="fa-solid fa-minus text-xs ml-1"></i>متوسط</span>
            </div>
          </div>

          <div class="grid grid-cols-12 px-5 py-4 items-center bg-primary-light border-t-2 border-primary/20">
            <div class="col-span-5 flex items-center gap-2.5">
              <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-equals text-white text-sm"></i>
              </div>
              <div>
                <p class="text-sm font-bold text-primary">التكلفة الإجمالية</p>
                <p class="text-xs text-primary/70">للدفعة كاملة</p>
              </div>
            </div>
            <div class="col-span-3 text-center text-base font-black text-primary">{{ fmt(totals.totalCost) }} {{ cur }}</div>
            <div class="col-span-2 text-center"><span class="text-sm font-bold text-primary">100%</span></div>
            <div class="col-span-2 flex justify-center">
              <div class="text-center">
                <p class="text-xs text-primary font-bold">{{ fmt(totals.unitCost) }} {{ cur }}</p>
                <p class="text-xs text-primary/70">/قطعة</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Cost Distribution Chart (CSS stacked bar) -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-chart-bar text-white text-sm"></i>
          </div>
          <h2 class="text-base font-bold text-text">توزيع التكاليف</h2>
          <div class="flex-1 h-px bg-border"></div>
        </div>

        <div class="bg-white rounded-2xl border border-border shadow-sm p-5">
          <div class="flex items-center justify-between mb-4 flex-wrap gap-2">
            <p class="text-sm text-muted">تحليل مكونات التكلفة الإجمالية للدفعة</p>
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-1.5"><div class="w-3 h-3 rounded-sm bg-blue-500"></div><span class="text-xs text-muted">مواد خام</span></div>
              <div class="flex items-center gap-1.5"><div class="w-3 h-3 rounded-sm bg-danger"></div><span class="text-xs text-muted">هالك</span></div>
              <div class="flex items-center gap-1.5"><div class="w-3 h-3 rounded-sm bg-warning"></div><span class="text-xs text-muted">فاقد</span></div>
            </div>
          </div>
          <div class="flex w-full h-10 rounded-xl overflow-hidden border border-border">
            <div class="bg-blue-500 h-full flex items-center justify-center" :style="{ width: totals.matPct + '%' }">
              <span class="text-white text-xs font-bold">{{ totals.matPct.toFixed(0) }}%</span>
            </div>
            <div class="bg-danger h-full flex items-center justify-center" :style="{ width: totals.wastePct + '%' }">
              <span v-if="totals.wastePct > 6" class="text-white text-xs font-bold">{{ totals.wastePct.toFixed(0) }}%</span>
            </div>
            <div class="bg-warning h-full flex items-center justify-center" :style="{ width: totals.lossPct + '%' }">
              <span v-if="totals.lossPct > 6" class="text-white text-xs font-bold">{{ totals.lossPct.toFixed(0) }}%</span>
            </div>
          </div>
          <div class="flex items-center justify-between mt-3">
            <span class="text-xs text-muted">الإجمالي</span>
            <span class="text-sm font-black text-primary">{{ fmt(totals.totalCost) }} {{ cur }}</span>
          </div>
        </div>
      </section>

      <!-- Notes -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-note-sticky text-white text-sm"></i>
          </div>
          <h2 class="text-base font-bold text-text">ملاحظات الوردية</h2>
          <div class="flex-1 h-px bg-border"></div>
          <span class="text-xs text-muted bg-slate-100 px-2 py-1 rounded-md">اختياري</span>
        </div>
        <div class="bg-white rounded-2xl border border-border shadow-sm p-5">
          <textarea v-model="draft.notes" rows="4" maxlength="500" placeholder="أضف أي ملاحظات إضافية أو ملاحظات المراجعة هنا..." class="w-full text-sm text-text border-2 border-border rounded-xl p-3 focus:outline-none focus:border-primary resize-none placeholder-slate-400 font-cairo bg-warm"></textarea>
          <div class="flex items-center justify-between mt-2">
            <p class="text-xs text-muted">سيتم حفظ الملاحظات مع سجل الدفعة</p>
            <p class="text-xs text-muted">{{ (draft.notes || '').length }} / 500</p>
          </div>
        </div>
      </section>

      <!-- Sign-off -->
      <section class="mb-6">
        <div class="bg-white rounded-2xl border border-border shadow-sm p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full border-2 border-border bg-slate-100 flex items-center justify-center">
              <i class="fa-solid fa-user text-muted"></i>
            </div>
            <div>
              <p class="text-sm font-bold text-text">{{ session.user }}</p>
              <p class="text-xs text-muted">عامل الإنتاج — وردية صباحية</p>
            </div>
            <div class="flex-1"></div>
            <div class="flex items-center gap-1.5 bg-amber-50 text-amber-700 px-3 py-1.5 rounded-xl border border-amber-200">
              <i class="fa-solid fa-sun text-xs"></i>
              <span class="text-xs font-bold">وردية صباحية</span>
            </div>
          </div>
          <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-border cursor-pointer">
            <input type="checkbox" v-model="confirmed" class="w-5 h-5 accent-primary rounded flex-shrink-0 cursor-pointer" />
            <span class="text-sm text-text font-medium leading-relaxed">أقر بأن جميع البيانات المدخلة صحيحة ودقيقة وتعكس الإنتاج الفعلي لهذه الوردية.</span>
          </label>
        </div>
      </section>
    </main>

    <!-- Sticky Footer -->
    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-4xl mx-auto px-4 md:px-6 py-3">
        <div class="flex items-center gap-3 mb-3">
          <div class="flex-1 grid grid-cols-3 gap-3">
            <div class="bg-slate-50 rounded-xl px-3 py-2 text-center border border-border">
              <p class="text-xs text-muted mb-0.5">تكلفة المواد</p>
              <p class="text-sm font-bold text-text">{{ fmt(totals.materialTotal) }} {{ cur }}</p>
            </div>
            <div class="bg-red-50 rounded-xl px-3 py-2 text-center border border-red-100">
              <p class="text-xs text-danger mb-0.5">الهالك والفاقد</p>
              <p class="text-sm font-bold text-danger">{{ fmt(totals.wasteLossTotal) }} {{ cur }}</p>
            </div>
            <div class="bg-primary-light rounded-xl px-3 py-2 text-center border border-primary/20">
              <p class="text-xs text-primary mb-0.5">التكلفة الإجمالية</p>
              <p class="text-sm font-bold text-primary">{{ fmt(totals.totalCost) }} {{ cur }}</p>
            </div>
          </div>
        </div>
        <div v-if="!session.canProduce" class="mb-2 flex items-center gap-2 text-xs font-bold text-danger bg-red-50 border border-red-100 rounded-lg px-3 py-2">
          <i class="fa-solid fa-lock"></i>
          <span>ليس لديك صلاحية تأكيد الإنتاج (مطلوب دور «مشرف التصنيع»).</span>
        </div>
        <div class="flex items-center gap-3">
          <button @click="router.push('/food-logger/new')" class="flex items-center gap-2 px-5 py-3 bg-slate-100 text-muted rounded-xl text-sm font-semibold border border-border hover:bg-slate-200 transition-colors min-h-[44px]">
            <i class="fa-solid fa-xmark text-sm"></i>
            إلغاء
          </button>
          <button @click="save" :disabled="!confirmed || saving || !session.canProduce" class="flex-1 flex items-center justify-center gap-3 py-3 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-colors min-h-[44px] shadow-md shadow-primary/30 disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa-solid" :class="saving ? 'fa-spinner fa-spin' : 'fa-circle-check'"></i>
            {{ saving ? "جارٍ الحفظ..." : "تأكيد وحفظ الدفعة" }}
            <i v-if="!saving" class="fa-solid fa-arrow-left text-sm"></i>
          </button>
        </div>
      </div>
    </footer>
  </div>
</template>
