<script setup>
import { BRANCH } from "./data"
</script>

<template>
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-chart-bar text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">التقارير</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }}</span>
        </div>
      </div>
    </div>
  </header>

  <div class="flex-1 flex flex-col items-center justify-center text-center gap-4 p-8">
    <div class="w-20 h-20 bg-pos-brand-light rounded-full flex items-center justify-center">
      <i class="fa-solid fa-chart-line text-pos-brand text-3xl"></i>
    </div>
    <div>
      <h2 class="font-extrabold text-gray-800 text-lg">التقارير قريباً</h2>
      <p class="text-sm text-pos-muted font-semibold mt-1 max-w-sm">لوحة تقارير المبيعات والأداء قيد التطوير وستتوفر في تحديث قادم.</p>
    </div>
  </div>
</template>
