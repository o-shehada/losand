<script setup>
import { computed } from "vue"
import { useRouter } from "vue-router"
import { CheckCircle2 } from "lucide-vue-next"
import { t } from "@/lib/i18n"

const router = useRouter()
const saved = computed(() => JSON.parse(sessionStorage.getItem("foodLoggerSuccess") || "{}"))
</script>

<template>
  <section class="mx-auto grid min-h-screen max-w-2xl place-items-center px-5 py-8">
    <div class="w-full rounded-2xl border border-manufacture-line bg-white p-8 text-center shadow-sm">
      <CheckCircle2 class="mx-auto h-16 w-16 text-manufacture-green" />
      <h1 class="mt-5 text-3xl font-extrabold">{{ t("Batch Saved") }}</h1>
      <p class="mt-2 text-manufacture-muted">{{ saved.batchRef }}</p>
      <button class="mt-8 w-full rounded-xl bg-manufacture-green px-4 py-3 font-bold text-white" @click="router.push('/food-logger/new')">
        {{ t("Start New Batch") }}
      </button>
    </div>
  </section>
</template>
