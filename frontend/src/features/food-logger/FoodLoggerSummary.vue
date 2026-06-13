<script setup>
import { computed, reactive } from "vue"
import { useRouter } from "vue-router"
import { t } from "@/lib/i18n"
import { call } from "@/lib/api"
import { batchDraft, calculateTotals } from "./data"

const router = useRouter()
const draft = reactive(JSON.parse(sessionStorage.getItem("foodLoggerDraft") || JSON.stringify(batchDraft)))
const confirmed = defineModel("confirmed", { default: false })
const totals = computed(() => calculateTotals(draft))

async function save() {
  const result = await call("losand.api.manufacture.save_food_logger_batch", { draft, totals: totals.value })
  sessionStorage.setItem("foodLoggerSuccess", JSON.stringify(result))
  router.push("/food-logger/success")
}
</script>

<template>
  <section class="mx-auto max-w-5xl px-5 py-6">
    <h1 class="mb-6 text-3xl font-extrabold">{{ t("Production Summary") }}</h1>
    <div class="grid gap-4 md:grid-cols-3">
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Quantity") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ draft.producedQty }}</p>
      </div>
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Unit Cost") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ totals.unitCost.toFixed(2) }}</p>
      </div>
      <div class="rounded-2xl border border-manufacture-line bg-white p-5">
        <p class="text-sm text-manufacture-muted">{{ t("Total Cost") }}</p>
        <p class="mt-2 text-2xl font-bold">{{ totals.totalCost.toFixed(2) }}</p>
      </div>
    </div>
    <label class="mt-6 flex items-center gap-3 rounded-xl border border-manufacture-line bg-white p-4">
      <input v-model="confirmed" type="checkbox" class="h-5 w-5 accent-manufacture-green" />
      <span class="font-semibold">{{ t("I confirm this production batch is accurate.") }}</span>
    </label>
    <button class="mt-4 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white disabled:opacity-50" :disabled="!confirmed" @click="save">
      {{ t("Save Batch") }}
    </button>
  </section>
</template>
