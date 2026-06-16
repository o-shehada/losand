<script setup>
import { ref, onMounted, onUnmounted, computed } from "vue"
import { useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import { call } from "@/lib/api"
import { cur, factoryName } from "@/lib/currency"
import { createDraft, categoryPresentation } from "@/features/food-logger/data"

const router = useRouter()
const workbenches = ref([])
const loading = ref(true)
const selected = ref(null)
const shift = ref("")

async function logout() {
  await signOut()
  router.replace("/login")
}

function pick(wb) {
  selected.value = wb
  shift.value = wb.shifts && wb.shifts.length ? wb.shifts[0] : ""
}

function start() {
  if (!selected.value) return
  const wb = selected.value
  const draft = createDraft()
  draft.workbench = wb.name
  draft.category = wb.category
  draft.shift = shift.value
  draft.raw_warehouse = wb.raw_warehouse
  draft.mfg_warehouse = wb.mfg_warehouse
  draft.fg_warehouse = wb.fg_warehouse
  sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
  router.push("/food-logger/new")
}

const canStart = computed(() => !!selected.value && !!shift.value)

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
    workbenches.value = (await call("losand.api.manufacture.get_workbenches")) || []
  } finally {
    loading.value = false
  }
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="font-cairo bg-warm text-text min-h-screen" dir="rtl">
    <header class="sticky top-0 z-50 bg-white border-b border-border shadow-sm">
      <div class="bg-primary px-6 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center">
            <i class="fa-solid fa-industry text-white text-base"></i>
          </div>
          <div>
            <p class="text-white/70 text-xs font-medium">نظام إدارة الإنتاج</p>
            <p class="text-white font-bold text-sm">{{ factoryName }}</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 bg-white/15 rounded-xl px-3 py-1.5">
            <i class="fa-regular fa-clock text-white/80 text-sm"></i>
            <span class="text-white font-semibold text-sm">{{ liveTime }}</span>
          </div>
          <span class="text-white/90 text-sm font-semibold hidden sm:inline">{{ session.user }}</span>
          <button @click="logout" title="تسجيل الخروج" class="flex items-center gap-1.5 bg-white/15 hover:bg-white/25 transition-colors rounded-xl px-3 py-1.5 text-white">
            <i class="fa-solid fa-right-from-bracket text-sm"></i>
            <span class="text-sm font-semibold hidden sm:inline">تسجيل الخروج</span>
          </button>
        </div>
      </div>
      <div class="px-6 py-4 bg-white">
        <h1 class="text-xl font-bold text-text">ابدأ الإنتاج</h1>
        <p class="text-sm text-muted mt-0.5">اختر محطة العمل والوردية للبدء</p>
      </div>
    </header>

    <main class="px-4 md:px-6 py-6 max-w-5xl mx-auto">
      <div v-if="loading" class="text-center text-muted py-12"><i class="fa-solid fa-spinner fa-spin ml-2"></i> جارٍ تحميل محطات العمل...</div>
      <div v-else-if="!workbenches.length" class="text-center text-muted py-12">لا توجد محطات عمل مُعرّفة.</div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <button v-for="wb in workbenches" :key="wb.name" @click="pick(wb)"
          class="text-start rounded-2xl border-2 p-5 bg-white transition-all flex items-center gap-4"
          :class="selected && selected.name === wb.name ? 'border-primary bg-primary-light' : 'border-border hover:border-primary/40'">
          <div class="w-16 h-16 rounded-xl overflow-hidden flex items-center justify-center flex-shrink-0" :class="categoryPresentation(wb.category).iconBg">
            <img class="w-full h-full object-cover" :src="categoryPresentation(wb.category).img" :alt="wb.category" />
          </div>
          <div class="flex-1">
            <p class="font-bold text-text">{{ wb.name }}</p>
            <p class="text-sm text-muted mt-0.5">{{ wb.category }}</p>
          </div>
          <i v-if="selected && selected.name === wb.name" class="fa-solid fa-circle-check text-primary text-xl"></i>
        </button>
      </div>

      <div v-if="selected" class="mt-6 bg-white rounded-2xl border border-border shadow-sm p-5 max-w-md">
        <h2 class="font-bold text-text mb-3">{{ selected.name }}</h2>
        <label class="block mb-4">
          <span class="block text-sm font-semibold text-muted mb-2">الوردية</span>
          <select v-model="shift" class="w-full rounded-xl border-2 border-border px-4 py-3 focus:outline-none focus:border-primary bg-white">
            <option v-for="s in selected.shifts" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <button @click="start" :disabled="!canStart" class="w-full flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 font-bold text-white hover:bg-primary-dark transition-colors disabled:opacity-50">
          <i class="fa-solid fa-play"></i>
          بدء الإنتاج
        </button>
      </div>
    </main>
  </div>
</template>
