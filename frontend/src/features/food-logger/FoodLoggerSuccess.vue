<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { factoryName, cur } from "@/lib/currency"
import { calc, fmt, fmt1 } from "./data"

const router = useRouter()
const saved = computed(() => JSON.parse(sessionStorage.getItem("foodLoggerSuccess") || "{}"))
const draft = computed(() => saved.value.draft || { finished_products: [], raw_materials: [] })
const totals = computed(() => calc(draft.value))
const producedProducts = computed(() => (draft.value.finished_products || []).filter((f) => Number(f.qty) > 0))

const copied = ref(false)
function copyRef() {
  const r = saved.value.batchName || ""
  if (navigator.clipboard?.writeText) navigator.clipboard.writeText(r).catch(() => {})
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}
function startNew() {
  sessionStorage.removeItem("foodLoggerDraft")
  sessionStorage.removeItem("foodLoggerSuccess")
  router.push("/home")
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
        <div class="flex items-center gap-2 bg-white/15 rounded-xl px-3 py-1.5"><i class="fa-regular fa-clock text-white/80 text-sm"></i><span class="text-white font-semibold text-sm">{{ liveTime }}</span></div>
      </div>
    </header>

    <main class="px-4 md:px-6 py-8 pb-36 max-w-3xl mx-auto">
      <section class="mb-8 flex flex-col items-center text-center">
        <div class="relative flex items-center justify-center mb-2" style="width: 150px; height: 150px;">
          <div class="pulse-ring absolute inset-0 rounded-full border-4 border-success/30"></div>
          <div class="circle-anim relative w-28 h-28 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center shadow-2xl shadow-green-500/40 z-10">
            <svg width="56" height="56" viewBox="0 0 64 64" fill="none"><path class="check-path" d="M14 34 L27 47 L50 20" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" /></svg>
          </div>
        </div>
        <div class="fade-up-1">
          <h2 class="text-3xl font-black text-success mb-2">تم الحفظ</h2>
          <p class="text-muted">تم حفظ دُفعة الإنتاج بنجاح</p>
        </div>
      </section>

      <section class="mb-6 fade-up-2">
        <div class="bg-white rounded-2xl border-2 border-green-200 shadow-sm overflow-hidden">
          <div class="bg-gradient-to-l from-green-600 to-green-500 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center"><i class="fa-solid fa-hashtag text-white text-lg"></i></div>
              <div><p class="text-white/80 text-xs font-medium">رقم الدفعة</p><p class="text-white font-black text-2xl tracking-wide">{{ saved.batchName }}</p></div>
            </div>
            <button @click="copyRef" class="flex items-center gap-2 bg-white/20 hover:bg-white/30 text-white px-3 py-2 rounded-xl text-sm font-semibold"><i class="fa-regular" :class="copied ? 'fa-circle-check' : 'fa-copy'"></i><span class="hidden sm:inline">{{ copied ? "تم النسخ" : "نسخ" }}</span></button>
          </div>
          <div class="grid grid-cols-3 divide-x divide-x-reverse divide-border border-t border-border">
            <div class="px-4 py-4 text-center"><p class="text-xs text-muted mb-1">القطع المنتجة</p><p class="text-2xl font-black">{{ totals.totalPieces }}</p></div>
            <div class="px-4 py-4 text-center"><p class="text-xs text-muted mb-1">إجمالي الوزن</p><p class="text-2xl font-black">{{ fmt1(totals.W) }}<span class="text-sm"> جم</span></p></div>
            <div class="px-4 py-4 text-center"><p class="text-xs text-muted mb-1">تكلفة المواد</p><p class="text-2xl font-black text-primary">{{ fmt(totals.C) }}</p></div>
          </div>
        </div>
      </section>

      <section class="mb-6 fade-up-3">
        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
          <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3 text-xs font-bold text-muted"><div class="col-span-6">المنتج</div><div class="col-span-2 text-center">الكمية</div><div class="col-span-4 text-center">التكلفة/قطعة</div></div>
          <div v-for="(f, i) in producedProducts" :key="f.item_code" class="grid grid-cols-12 px-4 py-3 items-center" :class="i < producedProducts.length - 1 ? 'border-b border-border' : ''">
            <div class="col-span-6 font-semibold text-sm">{{ f.name }}</div>
            <div class="col-span-2 text-center text-sm font-bold">{{ f.qty }}</div>
            <div class="col-span-4 text-center text-sm font-bold text-primary">{{ fmt(f.weight * totals.costPerG) }} {{ cur }}</div>
          </div>
        </div>
      </section>

      <div class="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 fade-up-4">
        <i class="fa-solid fa-circle-info ml-1"></i> حُفظت كمسودة. ترحيل المخزون الفعلي (نقل/صرف/استلام) سيتم في المرحلة الثانية.
      </div>
    </main>

    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-3xl mx-auto px-4 md:px-6 py-4 fade-up-5">
        <button @click="startNew" class="w-full flex items-center justify-center gap-3 py-3.5 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-all min-h-[52px] shadow-lg shadow-primary/30 active:scale-95"><i class="fa-solid fa-plus text-lg"></i> دُفعة جديدة <i class="fa-solid fa-arrow-left text-sm"></i></button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@keyframes scaleIn { 0% { transform: scale(0); opacity: 0; } 60% { transform: scale(1.15); opacity: 1; } 100% { transform: scale(1); opacity: 1; } }
@keyframes checkDraw { 0% { stroke-dashoffset: 100; opacity: 0; } 30% { opacity: 1; } 100% { stroke-dashoffset: 0; opacity: 1; } }
@keyframes fadeSlideUp { 0% { opacity: 0; transform: translateY(24px); } 100% { opacity: 1; transform: translateY(0); } }
@keyframes pulseRing { 0% { transform: scale(0.9); opacity: 0.6; } 50% { transform: scale(1.12); opacity: 0.2; } 100% { transform: scale(0.9); opacity: 0.6; } }
.circle-anim { animation: scaleIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both; }
.check-path { stroke-dasharray: 100; stroke-dashoffset: 100; animation: checkDraw 0.5s ease 0.75s forwards; }
.pulse-ring { animation: pulseRing 2s ease-in-out 1.2s infinite; }
.fade-up-1 { animation: fadeSlideUp 0.5s ease 1s both; }
.fade-up-2 { animation: fadeSlideUp 0.5s ease 1.15s both; }
.fade-up-3 { animation: fadeSlideUp 0.5s ease 1.3s both; }
.fade-up-4 { animation: fadeSlideUp 0.5s ease 1.45s both; }
.fade-up-5 { animation: fadeSlideUp 0.5s ease 1.6s both; }
</style>
