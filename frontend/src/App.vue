<script setup>
import { onMounted, watch } from "vue"
import { currentLanguage, direction, setLanguage } from "@/lib/i18n"

onMounted(() => setLanguage(currentLanguage.value))
watch(currentLanguage, setLanguage)
</script>

<template>
  <main :dir="direction" class="min-h-screen bg-manufacture-warm text-manufacture-ink">
    <RouterView />
  </main>
</template>
