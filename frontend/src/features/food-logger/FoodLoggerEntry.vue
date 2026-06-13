<script setup>
import { reactive, computed, ref, onMounted, onUnmounted } from "vue"
import { useRouter } from "vue-router"
import { session, signOut } from "@/stores/session"
import { createDraft, calc, fmt, fmt1, products, productByKey } from "./data"

const router = useRouter()

async function logout() {
  await signOut()
  router.replace("/login")
}

const saved = sessionStorage.getItem("foodLoggerDraft")
const draft = reactive(saved ? JSON.parse(saved) : createDraft())

const totals = computed(() => calc(draft))
const selectedProduct = computed(() => productByKey(draft.product))
const completed = computed(() => draft.materials.filter((m) => Number(m.actual) > 0).length)

function selectProduct(key) {
  draft.product = key
}
function adjustQty(delta) {
  draft.producedQty = Math.max(0, (Number(draft.producedQty) || 0) + delta)
}
function addWaste() {
  draft.waste.push({ reason: "", qty: 0, unit: "قطعة", rate: 24 })
}
function removeWaste(i) {
  draft.waste.splice(i, 1)
}
function addLoss() {
  draft.loss.push({ reason: "", qty: 0, unit: "كجم", rate: 45 })
}
function removeLoss(i) {
  draft.loss.splice(i, 1)
}

function continueToSummary() {
  sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
  router.push("/food-logger/summary")
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

      <!-- Header Info Row -->
      <div class="px-6 py-4 bg-white">
        <div class="flex items-start justify-between gap-4">
          <div class="flex-1">
            <h1 class="text-xl font-bold text-text mb-1">تسجيل دُفعة إنتاج</h1>
            <div class="flex items-center gap-4 flex-wrap">
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
          <div class="flex flex-col items-end gap-2">
            <div class="flex items-center gap-2">
              <span class="text-xs text-muted">العامل:</span>
              <span class="text-sm font-bold text-text">{{ session.user }}</span>
            </div>
            <div class="flex items-center gap-2">
              <button @click="draft.shift = 'morning'" :class="draft.shift === 'morning' ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-500 border-slate-200'" class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border">
                <i class="fa-solid fa-sun text-xs"></i>
                وردية صباحية
              </button>
              <button @click="draft.shift = 'evening'" :class="draft.shift === 'evening' ? 'bg-amber-100 text-amber-700 border-amber-200' : 'bg-slate-100 text-slate-500 border-slate-200'" class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border">
                <i class="fa-solid fa-moon text-xs"></i>
                وردية مسائية
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="px-6 pb-3 bg-white">
        <div class="flex items-center gap-2">
          <div class="flex items-center gap-1.5">
            <div class="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
              <i class="fa-solid fa-check text-white text-xs"></i>
            </div>
            <span class="text-xs font-semibold text-primary">الإدخال</span>
          </div>
          <div class="flex-1 h-1 bg-border rounded-full mx-1">
            <div class="h-full bg-primary rounded-full w-1/3"></div>
          </div>
          <div class="flex items-center gap-1.5">
            <div class="w-6 h-6 bg-border rounded-full flex items-center justify-center">
              <span class="text-xs font-bold text-muted">2</span>
            </div>
            <span class="text-xs font-medium text-muted">الملخص</span>
          </div>
          <div class="flex-1 h-1 bg-border rounded-full mx-1"></div>
          <div class="flex items-center gap-1.5">
            <div class="w-6 h-6 bg-border rounded-full flex items-center justify-center">
              <span class="text-xs font-bold text-muted">3</span>
            </div>
            <span class="text-xs font-medium text-muted">التأكيد</span>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="px-4 md:px-6 py-6 pb-40 max-w-4xl mx-auto">

      <!-- Block 1: Product Selector -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-white font-bold text-sm">1</span>
          </div>
          <h2 class="text-base font-bold text-text">اختر المنتج</h2>
          <div class="flex-1 h-px bg-border"></div>
          <span class="text-xs text-danger font-medium">* مطلوب</span>
        </div>

        <div class="grid grid-cols-3 gap-3">
          <div v-for="p in products" :key="p.key" @click="selectProduct(p.key)"
            class="cursor-pointer rounded-2xl border-2 p-4 flex flex-col items-center gap-3 transition-all relative overflow-hidden"
            :class="draft.product === p.key ? 'border-primary bg-primary-light' : 'border-border bg-white'">
            <div v-if="draft.product === p.key" class="absolute top-2 left-2 w-5 h-5 bg-primary rounded-full flex items-center justify-center">
              <i class="fa-solid fa-check text-white text-xs"></i>
            </div>
            <div class="w-16 h-16 overflow-hidden rounded-xl">
              <img class="w-full h-full object-cover" :src="p.img" :alt="p.name_en" />
            </div>
            <div class="text-center">
              <p class="font-bold text-text text-sm">{{ p.name_ar }}</p>
              <p class="text-xs text-muted mt-0.5">{{ p.name_en }}</p>
            </div>
            <span class="text-xs font-bold px-2.5 py-1 rounded-full"
              :class="draft.product === p.key ? 'bg-primary text-white' : 'bg-slate-100 text-muted font-medium'">
              {{ draft.product === p.key ? "محدد" : "اختيار" }}
            </span>
          </div>
        </div>
      </section>

      <!-- Block 2: Raw Materials Table -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-white font-bold text-sm">2</span>
          </div>
          <h2 class="text-base font-bold text-text">المواد الخام</h2>
          <div class="flex-1 h-px bg-border"></div>
          <button class="flex items-center gap-1.5 text-primary text-xs font-semibold bg-primary-light px-3 py-1.5 rounded-lg border border-primary/20">
            <i class="fa-solid fa-plus text-xs"></i>
            إضافة مادة
          </button>
        </div>

        <div class="bg-white rounded-2xl border border-border overflow-hidden shadow-sm">
          <div class="grid grid-cols-12 bg-slate-50 border-b border-border px-4 py-3">
            <div class="col-span-4 text-xs font-bold text-muted">المادة الخام</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">الوحدة</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">الكمية المخططة</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">الكمية الفعلية</div>
            <div class="col-span-2 text-xs font-bold text-muted text-center">التكلفة/وحدة</div>
          </div>

          <div v-for="(m, i) in draft.materials" :key="i"
            class="grid grid-cols-12 px-4 py-3.5 items-center hover:bg-slate-50/50 transition-colors"
            :class="i < draft.materials.length - 1 ? 'border-b border-border' : ''">
            <div class="col-span-4 flex items-center gap-2.5">
              <div class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0" :class="m.wrap">
                <i class="fa-solid text-sm" :class="[m.icon, m.color]"></i>
              </div>
              <div>
                <p class="text-sm font-semibold text-text">{{ m.name_ar }}</p>
                <p class="text-xs text-muted">{{ m.name_en }}</p>
              </div>
            </div>
            <div class="col-span-2 text-center">
              <span class="bg-slate-100 text-slate-600 text-xs font-medium px-2 py-1 rounded-md">{{ m.unit }}</span>
            </div>
            <div class="col-span-2 text-center">
              <span class="text-sm font-semibold text-text">{{ m.planned }}</span>
            </div>
            <div class="col-span-2 flex justify-center">
              <input type="number" v-model.number="m.actual"
                class="w-20 text-center text-sm font-semibold border-2 rounded-lg py-1.5 px-2 focus:outline-none"
                :class="Number(m.actual) < Number(m.planned) ? 'border-warning/40 bg-amber-50 text-warning focus:border-warning' : 'border-primary/30 bg-primary-light text-primary focus:border-primary'" />
            </div>
            <div class="col-span-2 text-center">
              <span class="text-sm font-semibold text-text">{{ fmt(m.rate) }} ر.س</span>
            </div>
          </div>

          <div class="bg-slate-50 border-t-2 border-border px-4 py-3 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-circle-info text-muted text-sm"></i>
              <span class="text-xs text-muted">{{ draft.materials.length }} مواد خام - {{ completed }} قيم مكتملة</span>
            </div>
            <span class="text-sm font-bold text-text">الإجمالي: <span class="text-primary">{{ fmt(totals.materialTotal) }} ر.س</span></span>
          </div>
        </div>
      </section>

      <!-- Block 3: Production Output -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-white font-bold text-sm">3</span>
          </div>
          <h2 class="text-base font-bold text-text">ناتج الإنتاج</h2>
          <div class="flex-1 h-px bg-border"></div>
          <div class="flex items-center gap-1.5 bg-green-50 text-success px-3 py-1 rounded-lg border border-green-200">
            <i class="fa-solid fa-circle-check text-xs"></i>
            <span class="text-xs font-semibold">الدفعة جارية</span>
          </div>
        </div>

        <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden max-w-md">
          <div class="px-4 py-3 flex items-center gap-2.5 border-b" :class="[selectedProduct.headBg, selectedProduct.headBorder]">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center" :class="selectedProduct.iconBg">
              <i class="fa-solid text-base" :class="[selectedProduct.icon, selectedProduct.iconText]"></i>
            </div>
            <div>
              <p class="font-bold text-text text-sm">{{ selectedProduct.name_ar }}</p>
              <p class="text-xs text-muted">{{ selectedProduct.name_en }}</p>
            </div>
          </div>
          <div class="p-4 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs text-muted font-medium">الكمية المنتجة</span>
              <div class="flex items-center gap-2">
                <button @click="adjustQty(-10)" class="w-8 h-8 bg-slate-100 rounded-lg flex items-center justify-center">
                  <i class="fa-solid fa-minus text-xs text-muted"></i>
                </button>
                <input type="number" v-model.number="draft.producedQty" class="w-20 text-center text-lg font-bold border-2 border-border rounded-xl py-1 focus:outline-none focus:border-primary" />
                <button @click="adjustQty(10)" class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <i class="fa-solid fa-plus text-xs text-white"></i>
                </button>
              </div>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-xs text-muted font-medium">الوزن (جم/قطعة)</span>
              <input type="number" v-model.number="draft.weightPerPiece" class="w-24 text-center text-sm font-semibold border-2 border-border rounded-xl py-1.5 focus:outline-none focus:border-primary" />
            </div>
            <div class="bg-slate-50 rounded-xl p-3 flex items-center justify-between">
              <span class="text-xs text-muted">إجمالي الوزن</span>
              <span class="text-sm font-bold text-text">{{ fmt1(totals.totalWeight) }} كجم</span>
            </div>
            <div class="bg-primary-light rounded-xl p-3 flex items-center justify-between border border-primary/20">
              <span class="text-xs text-primary font-semibold">التكلفة / قطعة</span>
              <span class="text-sm font-bold text-primary">{{ fmt(totals.unitCost) }} ر.س</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Block 4: Waste and Loss -->
      <section class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
            <span class="text-white font-bold text-sm">4</span>
          </div>
          <h2 class="text-base font-bold text-text">الهالك والفاقد</h2>
          <div class="flex-1 h-px bg-border"></div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <!-- Waste -->
          <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
            <div class="bg-red-50 border-b border-red-100 px-4 py-3 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 bg-red-100 rounded-xl flex items-center justify-center">
                  <i class="fa-solid fa-trash-can text-red-500 text-base"></i>
                </div>
                <div>
                  <p class="font-bold text-text text-sm">الهالك</p>
                  <p class="text-xs text-muted">المنتج التالف الكلي</p>
                </div>
              </div>
              <div class="bg-red-100 text-danger text-xs font-bold px-2.5 py-1 rounded-full">{{ totals.wasteUnits }} قطعة</div>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div v-for="(w, i) in draft.waste" :key="i" class="flex items-center gap-3 p-2.5 bg-red-50/50 rounded-xl border border-red-100">
                  <div class="w-2 h-2 bg-danger rounded-full flex-shrink-0"></div>
                  <input v-model="w.reason" placeholder="السبب" class="text-sm text-text flex-1 bg-transparent focus:outline-none" />
                  <input type="number" v-model.number="w.qty" class="w-16 text-center text-sm font-semibold border-2 border-red-200 bg-white rounded-lg py-1 focus:outline-none focus:border-danger" />
                  <span class="text-xs text-muted w-8">{{ w.unit }}</span>
                  <button @click="removeWaste(i)" class="w-7 h-7 bg-red-100 rounded-lg flex items-center justify-center">
                    <i class="fa-solid fa-xmark text-danger text-xs"></i>
                  </button>
                </div>
              </div>
              <button @click="addWaste" class="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-red-200 rounded-xl text-danger text-sm font-semibold hover:bg-red-50 transition-colors">
                <i class="fa-solid fa-plus text-xs"></i>
                إضافة هالك
              </button>
              <div class="bg-red-50 rounded-xl p-3 flex items-center justify-between border border-red-100">
                <span class="text-xs text-danger font-semibold">إجمالي الهالك</span>
                <span class="text-base font-bold text-danger">{{ totals.wasteUnits }} قطعة / {{ fmt(totals.wasteTotal) }} ر.س</span>
              </div>
            </div>
          </div>

          <!-- Loss -->
          <div class="bg-white rounded-2xl border border-border shadow-sm overflow-hidden">
            <div class="bg-amber-50 border-b border-amber-100 px-4 py-3 flex items-center justify-between">
              <div class="flex items-center gap-2.5">
                <div class="w-9 h-9 bg-amber-100 rounded-xl flex items-center justify-center">
                  <i class="fa-solid fa-arrow-trend-down text-amber-500 text-base"></i>
                </div>
                <div>
                  <p class="font-bold text-text text-sm">الفاقد</p>
                  <p class="text-xs text-muted">الفقد في العملية</p>
                </div>
              </div>
              <div class="bg-amber-100 text-warning text-xs font-bold px-2.5 py-1 rounded-full">{{ fmt1(totals.lossUnits) }} كجم</div>
            </div>
            <div class="p-4 space-y-3">
              <div class="space-y-2">
                <div v-for="(l, i) in draft.loss" :key="i" class="flex items-center gap-3 p-2.5 bg-amber-50/50 rounded-xl border border-amber-100">
                  <div class="w-2 h-2 bg-warning rounded-full flex-shrink-0"></div>
                  <input v-model="l.reason" placeholder="السبب" class="text-sm text-text flex-1 bg-transparent focus:outline-none" />
                  <input type="number" step="0.1" v-model.number="l.qty" class="w-16 text-center text-sm font-semibold border-2 border-amber-200 bg-white rounded-lg py-1 focus:outline-none focus:border-warning" />
                  <span class="text-xs text-muted w-8">{{ l.unit }}</span>
                  <button @click="removeLoss(i)" class="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
                    <i class="fa-solid fa-xmark text-warning text-xs"></i>
                  </button>
                </div>
              </div>
              <button @click="addLoss" class="w-full flex items-center justify-center gap-2 py-2.5 border-2 border-dashed border-amber-200 rounded-xl text-warning text-sm font-semibold hover:bg-amber-50 transition-colors">
                <i class="fa-solid fa-plus text-xs"></i>
                إضافة فاقد
              </button>
              <div class="bg-amber-50 rounded-xl p-3 flex items-center justify-between border border-amber-100">
                <span class="text-xs text-warning font-semibold">إجمالي الفاقد</span>
                <span class="text-base font-bold text-warning">{{ fmt1(totals.lossUnits) }} كجم / {{ fmt(totals.lossTotal) }} ر.س</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notes -->
        <div class="mt-4 bg-white rounded-2xl border border-border shadow-sm p-4">
          <div class="flex items-center gap-2 mb-3">
            <i class="fa-regular fa-note-sticky text-muted text-sm"></i>
            <label class="text-sm font-semibold text-text">ملاحظات الوردية</label>
            <span class="text-xs text-muted">(اختياري)</span>
          </div>
          <textarea v-model="draft.notes" rows="3" placeholder="أضف أي ملاحظات أو مشاكل واجهتها خلال هذه الوردية..." class="w-full text-sm text-text border-2 border-border rounded-xl p-3 focus:outline-none focus:border-primary resize-none placeholder-slate-400 font-cairo"></textarea>
        </div>
      </section>
    </main>

    <!-- Sticky Footer -->
    <footer class="fixed bottom-0 left-0 right-0 z-50 bg-white border-t-2 border-border shadow-lg">
      <div class="max-w-4xl mx-auto px-4 md:px-6 py-3">
        <div class="flex items-center gap-4 mb-3">
          <div class="flex-1 grid grid-cols-3 gap-3">
            <div class="bg-slate-50 rounded-xl px-3 py-2 text-center border border-border">
              <p class="text-xs text-muted mb-0.5">تكلفة المواد</p>
              <p class="text-sm font-bold text-text">{{ fmt(totals.materialTotal) }} ر.س</p>
            </div>
            <div class="bg-red-50 rounded-xl px-3 py-2 text-center border border-red-100">
              <p class="text-xs text-danger mb-0.5">الهالك والفاقد</p>
              <p class="text-sm font-bold text-danger">{{ fmt(totals.wasteLossTotal) }} ر.س</p>
            </div>
            <div class="bg-primary-light rounded-xl px-3 py-2 text-center border border-primary/20">
              <p class="text-xs text-primary mb-0.5">التكلفة الإجمالية</p>
              <p class="text-sm font-bold text-primary">{{ fmt(totals.totalCost) }} ر.س</p>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button class="flex items-center gap-2 px-5 py-3 bg-slate-100 text-muted rounded-xl text-sm font-semibold border border-border hover:bg-slate-200 transition-colors min-h-[44px]">
            <i class="fa-regular fa-floppy-disk text-sm"></i>
            حفظ مسودة
          </button>
          <button @click="continueToSummary" class="flex-1 flex items-center justify-center gap-3 py-3 bg-primary text-white rounded-xl text-base font-bold hover:bg-primary-dark transition-colors min-h-[44px] shadow-md shadow-primary/30">
            <i class="fa-solid fa-calculator text-base"></i>
            احسب التكلفة وراجع الملخص
            <i class="fa-solid fa-arrow-left text-sm"></i>
          </button>
        </div>
      </div>
    </footer>
  </div>
</template>
