<script setup>
import { reactive } from "vue"
import { useRouter } from "vue-router"
import { t } from "@/lib/i18n"
import { batchDraft } from "./data"

const router = useRouter()
const draft = reactive(batchDraft)

function continueToSummary() {
  sessionStorage.setItem("foodLoggerDraft", JSON.stringify(draft))
  router.push("/food-logger/summary")
}
</script>

<template>
  <section class="mx-auto max-w-5xl px-5 py-6">
    <header class="mb-6">
      <p class="text-sm font-semibold text-manufacture-green">{{ draft.batchRef }}</p>
      <h1 class="text-3xl font-extrabold">{{ t("Food Logger") }}</h1>
    </header>
    <div class="grid gap-4">
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Raw Materials") }}</h2>
        <div class="grid gap-3">
          <div v-for="material in draft.materials" :key="material.item" class="grid gap-2 rounded-xl border border-manufacture-line p-3 md:grid-cols-[1fr_110px_110px]">
            <div>
              <p class="font-bold">{{ material.item }}</p>
              <p class="text-xs text-manufacture-muted">{{ material.unit }}</p>
            </div>
            <input v-model.number="material.actual" type="number" class="rounded-lg border border-manufacture-line px-3 py-2" />
            <input v-model.number="material.rate" type="number" class="rounded-lg border border-manufacture-line px-3 py-2" />
          </div>
        </div>
      </section>
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Production Output") }}</h2>
        <input v-model.number="draft.producedQty" type="number" class="w-full rounded-lg border border-manufacture-line px-3 py-2" />
      </section>
      <section class="rounded-2xl border border-manufacture-line bg-white p-5">
        <h2 class="mb-4 text-lg font-bold">{{ t("Notes") }}</h2>
        <textarea v-model="draft.notes" rows="3" class="w-full rounded-xl border border-manufacture-line p-3"></textarea>
      </section>
    </div>
    <button class="mt-6 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white" @click="continueToSummary">
      {{ t("Continue") }}
    </button>
  </section>
</template>
