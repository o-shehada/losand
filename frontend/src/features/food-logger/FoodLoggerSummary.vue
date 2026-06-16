<script setup>
import { computed, reactive, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import { call } from "@/lib/api"
import { cur, factoryName } from "@/lib/currency"
import { createDraft, calc, fmt, fmt1 } from "./data"

const router = useRouter()
const stored = sessionStorage.getItem("foodLoggerDraft")
const draft = reactive(stored ? JSON.parse(stored) : createDraft())
if (!draft.workbench) router.replace("/home")

const totals = computed(() => calc(draft))
const producedProducts = computed(() => draft.finished_products.filter((f) => Number(f.qty) > 0))
const usedMaterials = computed(() => draft.raw_materials.filter((m) => Number(m.qty) > 0))
const confirmed = ref(false)
const saving = ref(false)

async function logout() {
  await signOut()
  router.replace("/login")
}

async function save() {
  if (!confirmed.value || saving.value) return
  saving.value = true
  try {
    const result = await call("losand.api.manufacture.save_draft", { payload: draft })
    sessionStorage.setItem("foodLoggerSuccess", JSON.stringify({ ...result, draft }))
    sessionStorage.removeItem("foodLoggerDraft")
    router.push("/food-logger/success")
  } catch (e) {
    saving.value = false
    alert(e.message)
  }
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
onMounted(() => { tick(); timer = setInterval(tick, 60000) })
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="font-cairo bg-warm text-text min-h-screen" dir="rtl">
    <header class="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
      <div class="bg-primary px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center"><i class="fa-solid fa-industry text-white text-base"></i></div>
          <div><p class="text-white/70 text-xs font-medium">نظام إدارة الإنتاج</p><p class="text-white font-bold text-sm">{{ factoryName }}</p></div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 bg-white/15 rounded-xl px-3 py-1.5"><i class="fa-regular fa-clock text-white/80 text-sm"></i><span class="text-white font-semibold text-sm">{{ liveTime }}</span></div>
          <button @click="logout" title="تسجيل الخروج" class="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 rounded-xl px-3 py-1.5 text-white"><i class="fa-solid fa-right-from-bracket text-sm"></i><span class="text-sm font-semibold hidden sm:inline">تسجيل الخروج</span></button>
        </div>
      </div>
      <div class="px-6 py-4 bg-white flex items-center gap-4">
        <button @click="router.push('/food-logger/new')" class="w-10 h-10 bg-slate-100 rounded-xl flex items-center justify-center border border-border hover:bg-slate-200"><i class="fa-solid fa-arrow-right text-text"></i></button>
        <div>
          <h1 class="text-xl font-bold">ملخص الإنتاج — {{ draft.category }}</h1>
          <p class="text-sm text-muted mt-0.5">{{ draft.workbench }} · {{ draft.shift }} · {{ draft.batchRef }}</p>
        </div>
      </div>
    </header>

    <main class="px-4 md:px-6 py-6 pb-40 max-w-4xl mx-auto">
      <!-- KPIs -->
      <section class="mb-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <div class="bg-white rounded-2xl border border-border p-4 text-center"><p class="text-xs text-muted mb-1">القطع المنتجة</p><p class="text-2xl font-black">{{ totals.totalPieces }}</p></div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center"><p class="text-xs text-muted mb-1">إجمالي الوزن</p><p class="text-2xl font-black">{{ fmt1(totals.W) }}<span class="text-sm"> جم</span></p></div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center"><p class="text-xs text-muted mb-1">تكلفة المواد (C)</p><p class="text-2xl font-black text-primary">{{ fmt(totals.C) }}</p></div>
        <div class="bg-white rounded-2xl border border-border p-4 text-center"><p class="text-xs text-muted mb-1">التكلفة/جرام</p><p class="text-2xl font-black">{{ fmt(totals.costPerG) }}</p></div>
      </section>

      <!-- Finished products w/ allocated cost -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4"><div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><i class="fa-solid fa-box text-white text-sm"></i></div><h2 class="text-base font-bold">المنتجات النهائية وتكلفتها</h2><div class="flex-1 h-px bg-border"></div></div>
        <div class="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
          <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3 text-xs font-bold text-muted">
            <div class="col-span-5">المنتج</div><div class="col-span-2 text-center">الكمية</div><div class="col-span-2 text-center">الوزن</div><div class="col-span-3 text-center">التكلفة/قطعة</div>
          </div>
          <div v-for="(f, i) in producedProducts" :key="f.item_code" class="grid grid-cols-12 px-4 py-3 items-center" :class="i < producedProducts.length - 1 ? 'border-b border-border' : ''">
            <div class="col-span-5 font-semibold text-sm">{{ f.name }}</div>
            <div class="col-span-2 text-center text-sm font-bold">{{ f.qty }}</div>
            <div class="col-span-2 text-center text-sm text-muted">{{ f.weight }} جم</div>
            <div class="col-span-3 text-center text-sm font-bold text-primary">{{ fmt(f.weight * totals.costPerG) }} {{ cur }}</div>
          </div>
        </div>
      </section>

      <!-- Raw materials -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4"><div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center"><i class="fa-solid fa-boxes-stacked text-white text-sm"></i></div><h2 class="text-base font-bold">المواد الخام المستهلكة</h2><div class="flex-1 h-px bg-border"></div></div>
        <div class="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
          <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3 text-xs font-bold text-muted"><div class="col-span-6">المادة</div><div class="col-span-2 text-center">الكمية</div><div class="col-span-2 text-center">السعر</div><div class="col-span-2 text-center">الإجمالي</div></div>
          <div v-for="(m, i) in usedMaterials" :key="m.item_code" class="grid grid-cols-12 px-4 py-3 items-center" :class="i < usedMaterials.length - 1 ? 'border-b border-border' : ''">
            <div class="col-span-6 font-semibold text-sm">{{ m.name_ar }}</div>
            <div class="col-span-2 text-center text-sm">{{ m.qty }} {{ m.unit }}</div>
            <div class="col-span-2 text-center text-sm text-muted">{{ fmt(m.rate) }}</div>
            <div class="col-span-2 text-center text-sm font-bold">{{ fmt(m.qty * m.rate) }}</div>
          </div>
          <div class="bg-primary-light px-4 py-3 flex items-center justify-between border-t-2 border-primary/20"><span class="text-sm font-bold text-primary">إجمالي تكلفة المواد</span><span class="text-base font-black text-primary">{{ fmt(totals.C) }} {{ cur }}</span></div>
        </div>
      </section>

      <!-- Loss -->
      <section v-if="draft.losses.length" class="mb-6">
        <div class="flex items-center gap-3 mb-4"><div class="w-8 h-8 bg-warning rounded-lg flex items-center justify-center"><i class="fa-solid fa-arrow-trend-down text-white text-sm"></i></div><h2 class="text-base font-bold">الفاقد</h2><div class="flex-1 h-px bg-border"></div></div>
        <div class="bg-white rounded-2xl border border-border shadow-sm p-4 space-y-2">
          <div v-for="(l, i) in draft.losses" :key="i" class="flex items-center justify-between text-sm border-b border-border last:border-0 py-1.5"><span>{{ l.reason || "—" }}</span><span class="font-bold text-warning">{{ l.qty }} كجم</span></div>
        </div>
      </section>

      <!-- Sign-off -->
      <section class="mb-6">
        <div class="bg-white rounded-2xl border border-border shadow-sm p-5">
          <label class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl border border-border cursor-pointer">
            <input type="checkbox" v-model="confirmed" class="w-5 h-5 accent-primary rounded" />
            <span class="text-sm font-medium">أقر بأن بيانات هذه الدفعة صحيحة ({{ session.user }}).</span>
          </label>
        </div>
      </section>
    </main>

    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-4xl mx-auto px-4 md:px-6 py-3">
        <div class="flex items-center gap-3">
          <button @click="router.push('/food-logger/new')" class="flex items-center gap-2 px-5 py-3 bg-slate-100 text-muted rounded-xl text-sm font-semibold border border-border hover:bg-slate-200"><i class="fa-solid fa-arrow-right text-sm"></i> رجوع</button>
          <button @click="save" :disabled="!confirmed || saving" class="flex-1 flex items-center justify-center gap-3 py-3 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            <i class="fa-solid" :class="saving ? 'fa-spinner fa-spin' : 'fa-floppy-disk'"></i>
            {{ saving ? "جارٍ الحفظ..." : "حفظ الدفعة" }}
          </button>
        </div>
      </div>
    </footer>
  </div>
</template>
