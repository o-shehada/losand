<script setup>
import { reactive, computed, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import { call } from "@/lib/api"
import { cur, factoryName } from "@/lib/currency"
import { createDraft, calc, fmt, fmt1 } from "./data"

const router = useRouter()
const saved = sessionStorage.getItem("foodLoggerDraft")
const draft = reactive(saved ? JSON.parse(saved) : createDraft())

if (!draft.workbench) router.replace("/home")

const loading = ref(true)
const totals = computed(() => calc(draft))

async function logout() {
  await signOut()
  router.replace("/login")
}

function addLoss() {
  draft.losses.push({ reason: "", qty: 0, unit: "كجم" })
}

const producedAny = computed(() => draft.finished_products.some((f) => Number(f.qty) > 0))
const rawAny = computed(() => draft.raw_materials.some((m) => Number(m.qty) > 0))
const stockIssues = computed(() => draft.raw_materials.filter((m) => Number(m.qty) > Number(m.available || 0)))
const canContinue = computed(() => producedAny.value && rawAny.value && stockIssues.value.length === 0)

function continueToSummary() {
  if (!canContinue.value) return
  sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
  router.push("/food-logger/summary")
}

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

onMounted(async () => {
  tick()
  timer = setInterval(tick, 60000)
  try {
    const [finals, raws] = await Promise.all([
      call("losand.api.manufacture.get_final_products", { category: draft.category }),
      call("losand.api.manufacture.get_category_raw_materials", { category: draft.category, warehouse: draft.raw_warehouse }),
    ])
    if (!draft.finished_products.length) {
      draft.finished_products = (finals || []).map((f) => ({ item_code: f.item_code, name: f.name, weight: f.weight, qty: 0 }))
    }
    if (!draft.raw_materials.length) {
      draft.raw_materials = (raws || []).map((r) => ({ ...r, qty: 0 }))
    }
  } finally {
    loading.value = false
  }
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="font-cairo bg-warm text-text min-h-screen" dir="rtl">
    <!-- Header -->
    <header class="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
      <div class="bg-primary px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center"><i class="fa-solid fa-industry text-white text-base"></i></div>
          <div>
            <p class="text-white/70 text-xs font-medium">نظام إدارة الإنتاج</p>
            <p class="text-white font-bold text-sm">{{ factoryName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 bg-white/15 rounded-xl px-3 py-1.5"><i class="fa-regular fa-clock text-white/80 text-sm"></i><span class="text-white font-semibold text-sm">{{ liveTime }}</span></div>
          <button @click="logout" title="تسجيل الخروج" class="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 transition-colors rounded-xl px-3 py-1.5 text-white">
            <i class="fa-solid fa-right-from-bracket text-sm"></i><span class="text-sm font-semibold hidden sm:inline">تسجيل الخروج</span>
          </button>
        </div>
      </div>
      <div class="px-6 py-4 bg-white flex items-start justify-between gap-4">
        <div>
          <h1 class="text-xl font-bold text-text mb-1">تسجيل دُفعة إنتاج — {{ draft.category }}</h1>
          <div class="flex items-center gap-4 flex-wrap text-sm">
            <span><span class="text-muted">المحطة:</span> <span class="font-bold">{{ draft.workbench }}</span></span>
            <span><span class="text-muted">الوردية:</span> <span class="font-bold">{{ draft.shift }}</span></span>
            <span class="text-primary font-bold bg-primary-light px-2.5 py-0.5 rounded-lg">{{ draft.batchRef }}</span>
            <span class="text-muted">{{ draft.dateLabel }}</span>
          </div>
        </div>
        <button @click="router.push('/home')" class="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center border border-border hover:bg-slate-200"><i class="fa-solid fa-arrow-right text-text"></i></button>
      </div>
    </header>

    <main class="px-4 md:px-6 py-6 pb-40 max-w-4xl mx-auto">
      <div v-if="loading" class="text-center text-muted py-12"><i class="fa-solid fa-spinner fa-spin ml-2"></i> جارٍ التحميل...</div>

      <template v-else>
        <!-- Finished products -->
        <section class="mb-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><span class="text-white font-bold text-sm">1</span></div>
            <h2 class="text-base font-bold">المنتجات النهائية</h2>
            <div class="flex-1 h-px bg-border"></div>
            <span class="text-xs text-muted">أدخل الكميات المنتجة</span>
          </div>
          <div class="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
            <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3 text-xs font-bold text-muted">
              <div class="col-span-6">المنتج</div>
              <div class="col-span-3 text-center">الوزن (جم)</div>
              <div class="col-span-3 text-center">الكمية المنتجة</div>
            </div>
            <div v-for="(f, i) in draft.finished_products" :key="f.item_code" class="grid grid-cols-12 px-4 py-3 items-center" :class="i < draft.finished_products.length - 1 ? 'border-b border-border' : ''">
              <div class="col-span-6 font-semibold text-sm">{{ f.name }}</div>
              <div class="col-span-3 text-center text-sm text-muted">{{ f.weight }}</div>
              <div class="col-span-3 flex justify-center">
                <input type="number" min="0" v-model.number="f.qty" class="w-24 text-center text-sm font-semibold border-2 rounded-lg py-1.5 px-2 focus:outline-none" :class="Number(f.qty) > 0 ? 'border-primary/40 bg-primary-light text-primary focus:border-primary' : 'border-border'" />
              </div>
            </div>
          </div>
        </section>

        <!-- Raw materials -->
        <section class="mb-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><span class="text-white font-bold text-sm">2</span></div>
            <h2 class="text-base font-bold">المواد الخام المستهلكة</h2>
            <div class="flex-1 h-px bg-border"></div>
          </div>
          <div class="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
            <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3 text-xs font-bold text-muted">
              <div class="col-span-5">المادة الخام</div>
              <div class="col-span-2 text-center">الوحدة</div>
              <div class="col-span-3 text-center">الكمية المستهلكة</div>
              <div class="col-span-2 text-center">التكلفة/وحدة</div>
            </div>
            <div v-for="(m, i) in draft.raw_materials" :key="m.item_code" class="grid grid-cols-12 px-4 py-3 items-center" :class="i < draft.raw_materials.length - 1 ? 'border-b border-border' : ''">
              <div class="col-span-5">
                <p class="font-semibold text-sm">{{ m.name_ar }}</p>
                <p class="text-[11px] font-bold mt-0.5" :class="Number(m.qty) > Number(m.available || 0) || Number(m.available || 0) <= 0 ? 'text-danger' : 'text-success'"><i class="fa-solid fa-warehouse text-[10px] ml-1"></i>المتاح: {{ fmt1(m.available || 0) }} {{ m.unit }}</p>
              </div>
              <div class="col-span-2 text-center"><span class="bg-slate-100 text-slate-600 text-xs font-medium px-2 py-1 rounded-md">{{ m.unit }}</span></div>
              <div class="col-span-3 flex justify-center">
                <input type="number" min="0" v-model.number="m.qty" class="w-24 text-center text-sm font-semibold border-2 rounded-lg py-1.5 px-2 focus:outline-none" :class="Number(m.qty) > Number(m.available || 0) ? 'border-danger/60 bg-red-50 text-danger focus:border-danger' : 'border-border focus:border-primary'" />
              </div>
              <div class="col-span-2 text-center text-sm font-semibold">{{ fmt(m.rate) }} {{ cur }}</div>
            </div>
            <div class="bg-slate-50 border-t-2 border-border px-4 py-3 flex items-center justify-between">
              <span class="text-xs text-muted">إجمالي تكلفة المواد (C)</span>
              <span class="text-sm font-bold text-primary">{{ fmt(totals.C) }} {{ cur }}</span>
            </div>
          </div>
        </section>

        <!-- Loss -->
        <section class="mb-6">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><span class="text-white font-bold text-sm">3</span></div>
            <h2 class="text-base font-bold">الفاقد <span class="text-xs text-muted font-normal">(اختياري)</span></h2>
            <div class="flex-1 h-px bg-border"></div>
          </div>
          <div class="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-2">
            <div v-for="(l, i) in draft.losses" :key="i" class="flex items-center gap-3 p-2.5 bg-amber-50/50 rounded-xl border border-amber-100">
              <input v-model="l.reason" placeholder="السبب" class="text-sm flex-1 bg-transparent focus:outline-none" />
              <input type="number" step="0.1" v-model.number="l.qty" class="w-20 text-center text-sm font-semibold border-2 border-amber-200 bg-white rounded-lg py-1 focus:outline-none focus:border-warning" />
              <span class="text-xs text-muted w-8">كجم</span>
              <button @click="draft.losses.splice(i, 1)" class="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center"><i class="fa-solid fa-xmark text-warning text-xs"></i></button>
            </div>
            <button @click="addLoss" class="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-amber-200 rounded-xl text-warning text-sm font-semibold hover:bg-amber-50"><i class="fa-solid fa-plus text-xs"></i> إضافة فاقد</button>
          </div>
        </section>

        <!-- Notes -->
        <section class="mb-6">
          <div class="bg-white rounded-2xl border border-border shadow-sm p-4">
            <label class="text-sm font-semibold mb-2 block">ملاحظات</label>
            <textarea v-model="draft.notes" rows="2" class="w-full text-sm border-2 border-border rounded-xl p-3 focus:outline-none focus:border-primary resize-none font-cairo"></textarea>
          </div>
        </section>
      </template>
    </main>

    <!-- Footer -->
    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-4xl mx-auto px-4 md:px-6 py-3">
        <div class="flex items-center gap-3 mb-3">
          <div class="flex-1 grid grid-cols-3 gap-3">
            <div class="bg-slate-50 rounded-xl px-3 py-2 text-center border border-border"><p class="text-xs text-muted mb-0.5">تكلفة المواد (C)</p><p class="text-sm font-bold">{{ fmt(totals.C) }} {{ cur }}</p></div>
            <div class="bg-slate-50 rounded-xl px-3 py-2 text-center border border-border"><p class="text-xs text-muted mb-0.5">إجمالي الوزن</p><p class="text-sm font-bold">{{ fmt1(totals.W) }} جم</p></div>
            <div class="bg-primary-light rounded-xl px-3 py-2 text-center border border-primary/20"><p class="text-xs text-primary mb-0.5">القطع المنتجة</p><p class="text-sm font-bold text-primary">{{ totals.totalPieces }}</p></div>
          </div>
        </div>
        <div v-if="!canContinue" class="mb-2 flex items-center gap-2 text-xs font-bold text-danger bg-red-50 border border-red-100 rounded-lg px-3 py-2">
          <i class="fa-solid fa-triangle-exclamation"></i>
          <span v-if="stockIssues.length">كمية تتجاوز المتاح: {{ stockIssues.map((m) => m.name_ar).join("، ") }}</span>
          <span v-else-if="!producedAny">أدخل كمية منتج نهائي واحد على الأقل</span>
          <span v-else>أدخل كمية مادة خام مستهلكة واحدة على الأقل</span>
        </div>
        <button @click="continueToSummary" :disabled="!canContinue" class="w-full flex items-center justify-center gap-3 py-3 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
          <i class="fa-solid fa-calculator"></i> احسب التكلفة وراجع الملخص <i class="fa-solid fa-arrow-left text-sm"></i>
        </button>
      </div>
    </footer>
  </div>
</template>
