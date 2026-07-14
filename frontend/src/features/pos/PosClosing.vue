<script setup>
import { ref, reactive, onMounted } from "vue"
import { useRouter } from "vue-router"
import { getShiftSummary, closeShift } from "@/lib/api"
import { pos, setShift } from "@/stores/pos"
import { ar } from "./data"
import "./pos.css"

const router = useRouter()
const summary = ref(null)
const counted = reactive({})
const loading = ref(true)
const submitting = ref(false)
const error = ref("")
const result = ref(null)

onMounted(async () => {
  try {
    const s = await getShiftSummary()
    summary.value = s
    for (const r of s.reconciliation || []) counted[r.mode] = r.expected
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const diff = (r) => Number(counted[r.mode] || 0) - r.expected
const money = (value) =>
  `${Number(value || 0).toFixed(2)} ${summary.value?.currency_symbol || pos.config?.currency_symbol || "د.ل"}`

async function close() {
  error.value = ""
  submitting.value = true
  try {
    result.value = await closeShift({ ...counted })
    setShift(null) // shift is now closed → next entry goes through the opening gate
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
function newShift() {
  router.replace("/opening")
}
</script>

<template>
  <div class="pos-root flex items-center justify-center w-full bg-pos-canvas" dir="rtl" style="height: 100dvh; overflow-y: auto">
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-lg w-full max-w-lg p-6 m-4">
      <!-- header -->
      <div class="flex items-center gap-3 mb-5">
        <div class="w-12 h-12 bg-pos-amber rounded-xl2 flex items-center justify-center shadow-md">
          <i class="fa-solid fa-lock text-white text-lg"></i>
        </div>
        <div>
          <h1 class="font-extrabold text-gray-800 text-lg leading-tight">إغلاق الوردية</h1>
          <p class="text-xs text-pos-muted font-semibold">{{ summary?.pos_profile || "…" }}</p>
        </div>
      </div>

      <div v-if="loading" class="text-center text-pos-muted py-12 font-semibold"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2 block opacity-60"></i> جارٍ الحساب…</div>

      <!-- result state -->
      <template v-else-if="result">
        <div class="flex flex-col items-center gap-3 text-center py-2">
          <div class="w-16 h-16 bg-pos-green-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-green text-3xl"></i></div>
          <h3 class="font-extrabold text-gray-800 text-lg">تم إغلاق الوردية</h3>
          <p class="text-sm text-pos-muted font-semibold">إجمالي المبيعات: {{ money(result.sales_total) }}</p>
        </div>
        <div class="mt-4 flex flex-col gap-1.5">
          <div v-for="r in result.reconciliation" :key="r.mode" class="flex items-center justify-between bg-pos-canvas border border-pos-border rounded-xl px-3 py-2 text-sm">
            <span class="font-bold text-gray-700">{{ r.mode }}</span>
            <span class="flex items-center gap-3">
              <span class="text-pos-muted">متوقع {{ money(r.expected) }}</span>
              <span :class="r.difference === 0 ? 'text-pos-green' : r.difference > 0 ? 'text-pos-brand-dark' : 'text-pos-danger'" class="font-extrabold">{{ r.difference > 0 ? "+" : "" }}{{ money(r.difference) }}</span>
            </span>
          </div>
        </div>
        <button @click="newShift" class="pos-btn w-full mt-5 bg-pos-brand text-white font-extrabold text-sm py-3 rounded-xl min-h-[48px] hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25">بدء وردية جديدة</button>
      </template>

      <!-- count state -->
      <template v-else>
        <div class="bg-pos-brand-light/60 border border-pos-brand/20 rounded-xl px-4 py-3 mb-4 flex items-center justify-between">
          <span class="text-sm font-bold text-gray-700">إجمالي المبيعات</span>
          <span class="text-lg font-extrabold text-pos-brand-dark">{{ money(summary?.sales_total || 0) }} <span class="text-xs text-pos-muted font-semibold">({{ ar(summary?.invoice_count || 0) }} فاتورة)</span></span>
        </div>

        <p class="text-xs font-extrabold text-gray-700 mb-2 pr-2 border-r-4 border-pos-brand">جرد الصندوق حسب طريقة الدفع</p>
        <div class="flex flex-col gap-2 mb-4">
          <div class="grid grid-cols-12 gap-2 px-1 text-[10px] font-extrabold text-pos-muted">
            <span class="col-span-4">الطريقة</span><span class="col-span-3 text-center">المتوقع</span><span class="col-span-3 text-center">المعدود</span><span class="col-span-2 text-center">الفرق</span>
          </div>
          <div v-for="r in summary?.reconciliation || []" :key="r.mode" class="grid grid-cols-12 gap-2 items-center bg-pos-canvas border border-pos-border rounded-xl px-2 py-2">
            <span class="col-span-4 text-sm font-bold text-gray-700">{{ r.mode }}</span>
            <span class="col-span-3 text-center text-xs font-bold text-pos-muted">{{ money(r.expected) }}</span>
            <input v-model.number="counted[r.mode]" type="number" dir="ltr" class="col-span-3 bg-pos-surface border border-pos-border rounded-lg px-2 py-1.5 text-sm font-bold text-gray-700 text-center focus:outline-none focus:border-pos-brand min-h-[36px]" />
            <span class="col-span-2 text-center text-xs font-extrabold" :class="diff(r) === 0 ? 'text-pos-green' : diff(r) > 0 ? 'text-pos-brand-dark' : 'text-pos-danger'">{{ diff(r) > 0 ? "+" : "" }}{{ ar(diff(r).toFixed(2)) }}</span>
          </div>
          <p v-if="!(summary?.reconciliation || []).length" class="text-center text-pos-muted text-xs font-semibold py-4">لا توجد حركات في هذه الوردية</p>
        </div>

        <p v-if="error" class="text-xs text-pos-danger font-bold mb-3 text-center">{{ error }}</p>

        <div class="flex gap-2">
          <button @click="router.back()" class="flex-1 bg-pos-canvas border border-pos-border text-gray-600 font-bold text-sm py-3 rounded-xl min-h-[48px] hover:border-pos-brand hover:text-pos-brand transition-colors">رجوع</button>
          <button @click="close" :disabled="submitting" class="pos-btn flex-[2] bg-pos-amber text-white font-extrabold text-sm py-3 rounded-xl min-h-[48px] flex items-center justify-center gap-2 hover:opacity-90 transition-opacity shadow-md disabled:opacity-40">
            <i class="fa-solid text-sm" :class="submitting ? 'fa-spinner fa-spin' : 'fa-lock'"></i> {{ submitting ? "جارٍ الإغلاق…" : "تأكيد إغلاق الوردية" }}
          </button>
        </div>
      </template>
    </div>
  </div>
</template>
