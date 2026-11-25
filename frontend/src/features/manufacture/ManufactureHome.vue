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
const drafts = ref([]) // saved runs waiting for a supervisor to review and post
const draftBusy = ref("")
const draftError = ref("")
const confirmDiscard = ref("") // draft name awaiting a second tap to delete

async function loadDrafts() {
  drafts.value = (await call("losand.api.manufacture.get_pending_drafts").catch(() => [])) || []
}
async function reviewDraft(d) {
  draftBusy.value = d.name
  draftError.value = ""
  try {
    const draft = await call("losand.api.manufacture.get_draft", { name: d.name })
    draft.dateLabel = createDraft().dateLabel
    sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
    router.push("/food-logger/summary")
  } catch (e) {
    draftError.value = e.message
  } finally {
    draftBusy.value = ""
  }
}
async function discardDraft(d) {
  if (confirmDiscard.value !== d.name) {
    confirmDiscard.value = d.name
    return
  }
  draftBusy.value = d.name
  draftError.value = ""
  try {
    await call("losand.api.manufacture.discard_draft", { name: d.name })
    confirmDiscard.value = ""
    await loadDrafts()
  } catch (e) {
    draftError.value = e.message
  } finally {
    draftBusy.value = ""
  }
}

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
    await loadDrafts()
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
          <img :src="'/assets/losand/images/losand-logo.jpg'" alt="Los Andalos" class="w-10 h-10 rounded-xl bg-white object-contain p-0.5" />
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

      <!-- Saved runs waiting for review (supervisors post them; operators see their own) -->
      <section v-if="drafts.length" data-testid="pending-drafts" class="mt-8">
        <h2 class="text-base font-bold text-text mb-3 flex items-center gap-2"><i class="fa-solid fa-hourglass-half text-primary"></i>{{ session.canPost ? "مسودات بانتظار المراجعة" : "دفعاتي بانتظار المراجعة" }}<span class="text-xs font-bold bg-primary-light text-primary rounded-full px-2 py-0.5">{{ drafts.length }}</span></h2>
        <p v-if="draftError" class="text-xs text-danger font-bold mb-2">{{ draftError }}</p>
        <div class="flex flex-col gap-2">
          <div v-for="d in drafts" :key="d.name" class="bg-white rounded-2xl border border-border p-4 flex items-center gap-3 flex-wrap">
            <div class="flex-1 min-w-[200px]">
              <p class="font-bold text-text">{{ d.workbench }} <span class="text-xs text-muted font-medium">· {{ d.shift || "—" }}</span></p>
              <p class="text-xs text-muted mt-0.5">{{ d.name }} · {{ d.operator_name }} · {{ String(d.creation).slice(0, 16) }} · {{ d.total_produced_qty || 0 }} قطعة<template v-if="session.canSeeCost && d.total_raw_cost"> · {{ Number(d.total_raw_cost).toFixed(2) }} {{ cur }}</template></p>
            </div>
            <button v-if="session.canProduce" @click="reviewDraft(d)" :disabled="draftBusy === d.name" class="rounded-xl bg-primary text-white text-sm font-bold px-4 py-2 min-h-[40px] hover:bg-primary-dark disabled:opacity-50"><i class="fa-solid fa-clipboard-check ml-1"></i> مراجعة وترحيل</button>
            <button @click="discardDraft(d)" :disabled="draftBusy === d.name" class="rounded-xl border text-sm font-bold px-4 py-2 min-h-[40px] disabled:opacity-50" :class="confirmDiscard === d.name ? 'border-danger text-danger bg-red-50' : 'border-border text-muted hover:border-danger hover:text-danger'">{{ confirmDiscard === d.name ? "اضغط للتأكيد" : "حذف" }}</button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
