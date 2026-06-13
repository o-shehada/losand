<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import { fmt, productByKey } from "./data"

const router = useRouter()

async function logout() {
  await signOut()
  router.replace("/login")
}
const saved = computed(() => JSON.parse(sessionStorage.getItem("foodLoggerSuccess") || "{}"))
const product = computed(() => productByKey(saved.value.product || "beef"))

const copied = ref(false)
function copyRef() {
  const ref = saved.value.batchRef || ""
  if (navigator.clipboard?.writeText) navigator.clipboard.writeText(ref).catch(() => {})
  copied.value = true
  setTimeout(() => (copied.value = false), 2200)
}

function startNewBatch() {
  sessionStorage.removeItem("foodLoggerDraft")
  sessionStorage.removeItem("foodLoggerSuccess")
  router.push("/food-logger/new")
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
onMounted(() => {
  tick()
  timer = setInterval(tick, 60000)
})
onUnmounted(() => clearInterval(timer))
</script>

<template>
  <div class="font-cairo bg-warm text-text min-h-screen" dir="rtl">
    <!-- Header -->
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
          <div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center border border-green-200">
            <i class="fa-solid fa-circle-check text-success text-base"></i>
          </div>
          <div>
            <h1 class="text-xl font-bold text-text">حالة النجاح</h1>
            <div class="flex items-center gap-3 flex-wrap mt-0.5">
              <span class="text-xs text-muted">رقم الدفعة:</span>
              <span class="text-sm font-bold text-primary bg-primary-light px-2.5 py-0.5 rounded-lg">{{ saved.batchRef }}</span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-1.5 bg-green-50 text-success px-3 py-1.5 rounded-xl border border-green-200">
          <div class="w-2 h-2 bg-success rounded-full animate-pulse"></div>
          <span class="text-xs font-bold">تم الحفظ</span>
        </div>
      </div>
    </header>

    <main class="px-4 md:px-6 py-8 pb-36 max-w-3xl mx-auto">
      <!-- Success Hero -->
      <section class="mb-8 flex flex-col items-center text-center">
        <div class="relative flex items-center justify-center mb-2" style="width: 160px; height: 160px;">
          <div class="pulse-ring absolute inset-0 rounded-full border-4 border-success/30"></div>
          <div class="circle-anim relative w-32 h-32 bg-gradient-to-br from-green-400 to-green-600 rounded-full flex items-center justify-center shadow-2xl shadow-green-500/40 z-10">
            <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
              <path class="check-path" d="M14 34 L27 47 L50 20" stroke="white" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" />
            </svg>
          </div>
        </div>
        <div class="fade-up-1">
          <h2 class="text-4xl font-black text-success mb-2">تم الحفظ</h2>
          <p class="text-lg text-muted font-medium">تم حفظ دُفعة الإنتاج بنجاح</p>
        </div>
      </section>

      <!-- Batch Reference Card -->
      <section class="mb-6 fade-up-2">
        <div class="bg-white rounded-2xl border-2 border-green-200 shadow-sm overflow-hidden">
          <div class="bg-gradient-to-l from-green-600 to-green-500 px-6 py-4 flex items-center justify-between">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-white/20 rounded-xl flex items-center justify-center">
                <i class="fa-solid fa-hashtag text-white text-lg"></i>
              </div>
              <div>
                <p class="text-white/80 text-xs font-medium">رقم مرجع الدفعة</p>
                <p class="text-white font-black text-2xl tracking-wide">{{ saved.batchRef }}</p>
              </div>
            </div>
            <button @click="copyRef" class="flex items-center gap-2 bg-white/20 hover:bg-white/30 transition-colors text-white px-3 py-2 rounded-xl text-sm font-semibold min-h-[44px]">
              <i class="fa-regular" :class="copied ? 'fa-circle-check' : 'fa-copy'"></i>
              <span class="hidden sm:inline">{{ copied ? "تم النسخ" : "نسخ" }}</span>
            </button>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 divide-x divide-x-reverse divide-border border-t border-border">
            <div class="px-4 py-4 text-center">
              <p class="text-xs text-muted mb-1 font-medium">المنتج</p>
              <i class="fa-solid text-primary text-lg mb-1" :class="product.icon"></i>
              <p class="text-xs font-bold text-text">{{ product.name_ar }}</p>
            </div>
            <div class="px-4 py-4 text-center">
              <p class="text-xs text-muted mb-1 font-medium">الكمية</p>
              <p class="text-2xl font-black text-text">{{ saved.producedQty }}</p>
              <p class="text-xs text-muted mt-0.5">قطعة</p>
            </div>
            <div class="px-4 py-4 text-center border-t md:border-t-0 border-border">
              <p class="text-xs text-muted mb-1 font-medium">التكلفة الإجمالية</p>
              <p class="text-xl font-black text-primary">{{ fmt(saved.totalCost) }}</p>
              <p class="text-xs text-muted mt-0.5">ر.س</p>
            </div>
            <div class="px-4 py-4 text-center border-t md:border-t-0 border-border">
              <p class="text-xs text-muted mb-1 font-medium">تكلفة الوحدة</p>
              <p class="text-xl font-black text-text">{{ fmt(saved.unitCost) }}</p>
              <p class="text-xs text-muted mt-0.5">ر.س / قطعة</p>
            </div>
          </div>
        </div>
      </section>

      <!-- Save Details -->
      <section class="mb-6 fade-up-3">
        <div class="bg-white rounded-2xl border border-border shadow-sm p-5">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-8 h-8 bg-success/10 rounded-lg flex items-center justify-center flex-shrink-0">
              <i class="fa-solid fa-shield-halved text-success text-sm"></i>
            </div>
            <h3 class="text-base font-bold text-text">تفاصيل الحفظ</h3>
            <div class="flex-1 h-px bg-border"></div>
          </div>
          <div class="space-y-3">
            <div class="flex items-center justify-between py-2.5 border-b border-border">
              <div class="flex items-center gap-2.5">
                <i class="fa-regular fa-clock text-muted text-sm w-4 text-center"></i>
                <span class="text-sm text-muted font-medium">وقت الحفظ</span>
              </div>
              <span class="text-sm font-bold text-text">{{ liveTime }} — اليوم</span>
            </div>
            <div class="flex items-center justify-between py-2.5 border-b border-border">
              <div class="flex items-center gap-2.5">
                <i class="fa-solid fa-user text-muted text-sm w-4 text-center"></i>
                <span class="text-sm text-muted font-medium">العامل المسؤول</span>
              </div>
              <span class="text-sm font-bold text-text">{{ saved.savedBy || session.user }}</span>
            </div>
            <div class="flex items-center justify-between py-2.5 border-b border-border">
              <div class="flex items-center gap-2.5">
                <i class="fa-solid fa-sun text-muted text-sm w-4 text-center"></i>
                <span class="text-sm text-muted font-medium">الوردية</span>
              </div>
              <span class="text-sm font-bold text-text bg-amber-50 text-amber-700 px-2.5 py-0.5 rounded-lg border border-amber-200">وردية صباحية</span>
            </div>
            <div class="flex items-center justify-between py-2.5">
              <div class="flex items-center gap-2.5">
                <i class="fa-solid fa-cloud-arrow-up text-muted text-sm w-4 text-center"></i>
                <span class="text-sm text-muted font-medium">حالة المزامنة</span>
              </div>
              <div class="flex items-center gap-1.5 bg-green-50 text-success px-2.5 py-0.5 rounded-lg border border-green-200">
                <div class="w-2 h-2 bg-success rounded-full animate-pulse"></div>
                <span class="text-xs font-bold">تمت المزامنة</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick Actions -->
      <section class="mb-6 fade-up-4">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <i class="fa-solid fa-bolt text-white text-sm"></i>
          </div>
          <h2 class="text-base font-bold text-text">إجراءات سريعة</h2>
          <div class="flex-1 h-px bg-border"></div>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
          <button class="bg-white rounded-2xl border border-border shadow-sm p-4 flex flex-col items-center gap-3 hover:border-primary/30 hover:bg-primary-light/30 transition-all group">
            <div class="w-11 h-11 bg-slate-100 group-hover:bg-primary-light rounded-xl flex items-center justify-center transition-colors">
              <i class="fa-solid fa-print text-muted group-hover:text-primary text-lg transition-colors"></i>
            </div>
            <span class="text-sm font-semibold text-text group-hover:text-primary transition-colors">طباعة التقرير</span>
          </button>
          <button class="bg-white rounded-2xl border border-border shadow-sm p-4 flex flex-col items-center gap-3 hover:border-primary/30 hover:bg-primary-light/30 transition-all group">
            <div class="w-11 h-11 bg-slate-100 group-hover:bg-primary-light rounded-xl flex items-center justify-center transition-colors">
              <i class="fa-solid fa-share-nodes text-muted group-hover:text-primary text-lg transition-colors"></i>
            </div>
            <span class="text-sm font-semibold text-text group-hover:text-primary transition-colors">مشاركة</span>
          </button>
          <button class="bg-white rounded-2xl border border-border shadow-sm p-4 flex flex-col items-center gap-3 hover:border-primary/30 hover:bg-primary-light/30 transition-all group col-span-2 md:col-span-1">
            <div class="w-11 h-11 bg-slate-100 group-hover:bg-primary-light rounded-xl flex items-center justify-center transition-colors">
              <i class="fa-solid fa-chart-line text-muted group-hover:text-primary text-lg transition-colors"></i>
            </div>
            <span class="text-sm font-semibold text-text group-hover:text-primary transition-colors">عرض التقارير</span>
          </button>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-3xl mx-auto px-4 md:px-6 py-4">
        <div class="flex items-center gap-3 fade-up-5">
          <button @click="router.push('/home')" class="flex items-center gap-2 px-5 py-3.5 bg-slate-100 text-muted rounded-xl text-sm font-semibold border border-border hover:bg-slate-200 transition-colors min-h-[52px]">
            <i class="fa-solid fa-house text-sm"></i>
            <span class="hidden sm:inline">الرئيسية</span>
          </button>
          <button @click="startNewBatch" class="flex-1 flex items-center justify-center gap-3 py-3.5 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-all min-h-[52px] shadow-lg shadow-primary/30 active:scale-95">
            <i class="fa-solid fa-plus text-lg"></i>
            بدء دُفعة جديدة
            <i class="fa-solid fa-arrow-left text-sm"></i>
          </button>
        </div>
      </div>
    </footer>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="copied" class="fixed top-24 left-1/2 -translate-x-1/2 z-[100]">
        <div class="bg-text text-white text-sm font-semibold px-5 py-3 rounded-2xl shadow-xl flex items-center gap-2">
          <i class="fa-regular fa-copy text-white/80"></i>
          <span>تم نسخ رقم الدفعة</span>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
@keyframes scaleIn {
  0% { transform: scale(0); opacity: 0; }
  60% { transform: scale(1.15); opacity: 1; }
  80% { transform: scale(0.95); }
  100% { transform: scale(1); opacity: 1; }
}
@keyframes checkDraw {
  0% { stroke-dashoffset: 100; opacity: 0; }
  30% { opacity: 1; }
  100% { stroke-dashoffset: 0; opacity: 1; }
}
@keyframes fadeSlideUp {
  0% { opacity: 0; transform: translateY(24px); }
  100% { opacity: 1; transform: translateY(0); }
}
@keyframes pulseRing {
  0% { transform: scale(0.9); opacity: 0.6; }
  50% { transform: scale(1.12); opacity: 0.2; }
  100% { transform: scale(0.9); opacity: 0.6; }
}
.circle-anim { animation: scaleIn 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) 0.2s both; }
.check-path { stroke-dasharray: 100; stroke-dashoffset: 100; animation: checkDraw 0.5s ease 0.75s forwards; }
.pulse-ring { animation: pulseRing 2s ease-in-out 1.2s infinite; }
.fade-up-1 { animation: fadeSlideUp 0.5s ease 1s both; }
.fade-up-2 { animation: fadeSlideUp 0.5s ease 1.15s both; }
.fade-up-3 { animation: fadeSlideUp 0.5s ease 1.3s both; }
.fade-up-4 { animation: fadeSlideUp 0.5s ease 1.45s both; }
.fade-up-5 { animation: fadeSlideUp 0.5s ease 1.6s both; }
.toast-enter-active, .toast-leave-active { transition: all 0.3s ease; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, -8px); }
</style>
