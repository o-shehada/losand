<script setup>
import { ref, reactive, onMounted } from "vue"
import { useRouter } from "vue-router"
import { createOpeningShift } from "@/lib/api"
import { pos, ensurePos, setShift } from "@/stores/pos"
import "./pos.css"

const router = useRouter()
const opening = reactive({}) // { [mode]: amount }
const submitting = ref(false)
const error = ref("")

onMounted(async () => {
  await ensurePos()
  for (const p of pos.config?.payments || []) {
    if (!(p.mode_of_payment in opening)) opening[p.mode_of_payment] = 0
  }
})

async function openShift() {
  error.value = ""
  const cfg = pos.config
  if (!cfg) {
    error.value = "لا يوجد ملف نقاط بيع مُهيّأ"
    return
  }
  submitting.value = true
  try {
    const balances = (cfg.payments || []).map((p) => ({
      mode_of_payment: p.mode_of_payment,
      opening_amount: Number(opening[p.mode_of_payment] || 0),
    }))
    const shift = await createOpeningShift(cfg.pos_profile, cfg.company, balances)
    setShift(shift)
    router.replace("/")
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="pos-root flex items-center justify-center w-full bg-pos-canvas" dir="rtl" style="height: 100dvh">
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-lg w-full max-w-md p-6 m-4">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-12 h-12 bg-pos-brand rounded-xl2 flex items-center justify-center shadow-md">
          <i class="fa-solid fa-cash-register text-white text-lg"></i>
        </div>
        <div>
          <h1 class="font-extrabold text-gray-800 text-lg leading-tight">فتح الوردية</h1>
          <p class="text-xs text-pos-muted font-semibold">{{ pos.config?.pos_profile || "…" }} · {{ pos.config?.company }}</p>
        </div>
      </div>

      <p class="text-xs font-extrabold text-gray-700 mb-2 pr-2 border-r-4 border-pos-brand">رصيد افتتاح الصندوق</p>
      <div class="flex flex-col gap-3 mb-5">
        <label v-for="p in pos.config?.payments || []" :key="p.mode_of_payment" class="flex items-center justify-between gap-3 bg-pos-canvas border border-pos-border rounded-xl px-3 py-2.5">
          <span class="text-sm font-bold text-gray-700 flex items-center gap-2"><i class="fa-solid fa-wallet text-pos-brand text-xs"></i> {{ p.mode_of_payment }}</span>
          <span class="flex items-center gap-1.5">
            <input v-model.number="opening[p.mode_of_payment]" type="number" min="0" dir="ltr" class="w-28 bg-pos-surface border border-pos-border rounded-lg px-2 py-1.5 text-sm font-bold text-gray-700 text-center focus:outline-none focus:border-pos-brand" />
            <span class="text-xs text-pos-muted font-semibold">{{ pos.config?.currency_symbol || pos.config?.currency }}</span>
          </span>
        </label>
        <p v-if="!(pos.config?.payments || []).length" class="text-center text-pos-muted text-xs font-semibold py-4">لا توجد طرق دفع في ملف نقاط البيع</p>
      </div>

      <p v-if="error" class="text-xs text-pos-danger font-bold mb-3 text-center">{{ error }}</p>

      <button
        @click="openShift"
        :disabled="submitting || !pos.config"
        class="pos-btn w-full bg-pos-brand text-white font-extrabold text-sm py-3 rounded-xl min-h-[48px] flex items-center justify-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40"
      >
        <i class="fa-solid fa-unlock text-sm"></i> {{ submitting ? "جارٍ الفتح…" : "فتح الوردية وبدء البيع" }}
      </button>
    </div>
  </div>
</template>
