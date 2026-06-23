<script setup>
import { ref, computed } from "vue"
import { CATEGORIES, PRODUCTS, BRANCH, money, ar } from "./data"

const activeCat = ref("all")
const search = ref("")
const cart = ref([])
const discount = ref(0)
const tableLabel = ref("الطاولة الخامسة")

const visibleProducts = computed(() =>
  PRODUCTS.filter((p) => (activeCat.value === "all" || p.category === activeCat.value) && p.name.includes(search.value.trim())),
)

function add(product) {
  const line = cart.value.find((l) => l.id === product.id)
  if (line) line.qty += 1
  else cart.value.push({ id: product.id, name: product.name, price: product.price, qty: 1 })
}
function inc(line) {
  line.qty += 1
}
function dec(line) {
  line.qty -= 1
  if (line.qty <= 0) remove(line)
}
function remove(line) {
  cart.value = cart.value.filter((l) => l.id !== line.id)
}
function clearCart() {
  cart.value = []
  discount.value = 0
}

const count = computed(() => cart.value.reduce((s, l) => s + l.qty, 0))
const subtotal = computed(() => cart.value.reduce((s, l) => s + l.price * l.qty, 0))
const total = computed(() => Math.max(0, subtotal.value - Number(discount.value || 0)))
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-cash-register text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">نقطة البيع</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }}</span>
          <span class="text-xs text-pos-muted">·</span>
          <i class="fa-regular fa-calendar text-pos-muted text-xs"></i>
          <span class="text-xs text-pos-muted">الأربعاء، 22 يناير 2025</span>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-2 flex-wrap justify-end">
      <div class="relative">
        <input
          v-model="search"
          type="text"
          placeholder="بحث عن صنف..."
          class="bg-pos-canvas border border-pos-border rounded-xl pr-4 pl-9 py-2 text-sm focus:outline-none focus:border-pos-brand text-gray-700 w-44 md:w-56 min-h-[44px]"
        />
        <i class="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-pos-muted text-sm"></i>
      </div>
      <div class="pos-shift-pill text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
        <i class="fa-solid fa-sun text-yellow-200 text-xs"></i>
        <span>وردية الصباح</span>
      </div>
      <div class="bg-pos-amber/15 border border-pos-amber text-pos-amber text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
        <i class="fa-solid fa-user-tie text-xs"></i>
        <span>كاشير</span>
      </div>
    </div>
  </header>

  <!-- BODY: products + cart -->
  <div class="flex-1 flex overflow-hidden">
    <!-- Products -->
    <section class="flex-1 flex flex-col overflow-hidden min-w-0">
      <!-- Category tabs -->
      <div class="px-3 md:px-4 py-3 flex items-center gap-2 overflow-x-auto flex-shrink-0">
        <button
          v-for="c in CATEGORIES"
          :key="c.key"
          @click="activeCat = c.key"
          class="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold whitespace-nowrap transition-colors min-h-[44px]"
          :class="activeCat === c.key ? 'bg-pos-brand text-white shadow-sm shadow-pos-brand/30' : 'bg-pos-surface border border-pos-border text-gray-600 hover:border-pos-brand hover:text-pos-brand'"
        >
          <i class="fa-solid" :class="c.icon"></i>
          {{ c.label }}
        </button>
      </div>

      <!-- Grid -->
      <div class="flex-1 overflow-y-auto px-3 md:px-4 pb-4">
        <div class="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="p in visibleProducts"
            :key="p.id"
            class="pos-product-card bg-pos-surface rounded-xl2 border border-pos-border overflow-hidden flex flex-col"
          >
            <div class="h-28 bg-pos-brand-light overflow-hidden">
              <img :src="p.img" :alt="p.name" class="w-full h-full object-cover" loading="lazy" />
            </div>
            <div class="p-3 flex flex-col gap-2 flex-1">
              <p class="font-bold text-gray-800 text-sm leading-tight">{{ p.name }}</p>
              <div class="mt-auto flex items-center justify-between">
                <span class="text-pos-brand-dark font-extrabold text-sm">{{ money(p.price) }}</span>
                <button
                  @click="add(p)"
                  class="pos-btn bg-pos-brand text-white text-xs font-bold px-4 py-2 rounded-xl min-h-[36px] flex items-center gap-1.5 hover:bg-pos-brand-dark transition-colors shadow-sm shadow-pos-brand/20"
                >
                  <i class="fa-solid fa-plus text-xs"></i> إضافة
                </button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="!visibleProducts.length" class="text-center text-pos-muted py-16 font-semibold">
          <i class="fa-solid fa-magnifying-glass-minus text-2xl mb-2 block opacity-60"></i>
          لا توجد أصناف مطابقة
        </div>
      </div>
    </section>

    <!-- Cart / current order -->
    <aside class="w-[300px] xl:w-[340px] flex-shrink-0 bg-pos-surface border-r border-pos-border flex flex-col overflow-hidden">
      <!-- Cart header -->
      <div class="px-4 py-3 border-b border-pos-border bg-pos-brand-light/60 flex items-center justify-between flex-shrink-0">
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-cart-shopping text-pos-brand"></i>
          <span class="font-extrabold text-gray-800 text-sm">الطلب الحالي</span>
        </div>
        <span class="bg-pos-brand text-white text-[11px] font-extrabold px-2.5 py-0.5 rounded-full">{{ ar(count) }} صنف</span>
      </div>
      <!-- Table + type -->
      <div class="px-4 py-2.5 border-b border-pos-border flex items-center justify-between flex-shrink-0">
        <span class="flex items-center gap-1.5 text-xs font-bold text-gray-700">
          <i class="fa-solid fa-chair text-pos-brand text-xs"></i> {{ tableLabel }}
        </span>
        <span class="pos-type-dine text-[10px] font-bold px-2 py-0.5 rounded-full">داخلي</span>
      </div>

      <!-- Lines -->
      <div class="flex-1 overflow-y-auto px-3 py-2 space-y-2">
        <div v-if="!cart.length" class="h-full flex flex-col items-center justify-center text-center gap-2 text-pos-muted py-10">
          <div class="w-12 h-12 bg-pos-canvas rounded-full flex items-center justify-center">
            <i class="fa-solid fa-basket-shopping text-pos-muted"></i>
          </div>
          <p class="text-xs font-semibold">السلة فارغة — اختر صنفاً للبدء</p>
        </div>
        <div
          v-for="line in cart"
          :key="line.id"
          class="bg-pos-canvas rounded-xl border border-pos-border px-3 py-2"
        >
          <div class="flex items-center justify-between gap-2">
            <p class="text-sm font-bold text-gray-800 leading-tight flex-1 min-w-0">{{ line.name }}</p>
            <button @click="remove(line)" class="text-pos-muted hover:text-pos-danger transition-colors flex-shrink-0">
              <i class="fa-solid fa-xmark text-xs"></i>
            </button>
          </div>
          <div class="flex items-center justify-between mt-2">
            <div class="flex items-center gap-2">
              <button @click="dec(line)" class="w-7 h-7 rounded-lg bg-pos-surface border border-pos-border flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold">−</button>
              <span class="text-sm font-extrabold text-gray-800 w-5 text-center">{{ ar(line.qty) }}</span>
              <button @click="inc(line)" class="w-7 h-7 rounded-lg bg-pos-surface border border-pos-border flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold">+</button>
            </div>
            <span class="text-pos-brand-dark font-bold text-xs">{{ money(line.price * line.qty) }}</span>
          </div>
        </div>
      </div>

      <!-- Footer / totals -->
      <div class="border-t border-pos-border px-4 py-3 flex-shrink-0 bg-pos-canvas/60">
        <div class="flex items-center justify-between text-sm mb-1.5">
          <span class="text-pos-muted font-semibold">المجموع الفرعي</span>
          <span class="font-bold text-gray-700">{{ money(subtotal) }}</span>
        </div>
        <div class="flex items-center justify-between text-sm mb-1.5">
          <span class="text-pos-muted font-semibold">الخصم</span>
          <div class="relative w-24">
            <input
              v-model.number="discount"
              type="number"
              min="0"
              class="w-full bg-pos-surface border border-pos-border rounded-lg px-2 py-1 text-xs text-left font-bold text-gray-700 focus:outline-none focus:border-pos-brand"
              dir="ltr"
            />
          </div>
        </div>
        <div class="flex items-center justify-between text-base border-t border-dashed border-pos-border pt-2 mt-1">
          <span class="font-extrabold text-gray-800">الإجمالي</span>
          <span class="font-extrabold text-pos-brand-dark">{{ money(total) }}</span>
        </div>
        <div class="grid grid-cols-3 gap-2 mt-3">
          <button
            @click="clearCart"
            :disabled="!cart.length"
            class="col-span-1 pos-btn bg-pos-danger-light border border-pos-danger/30 text-pos-danger text-xs font-bold py-2.5 rounded-xl min-h-[44px] flex items-center justify-center gap-1.5 hover:bg-pos-danger hover:text-white transition-colors disabled:opacity-40"
          >
            <i class="fa-solid fa-trash text-xs"></i>
          </button>
          <button
            :disabled="!cart.length"
            class="col-span-2 pos-btn bg-pos-brand text-white text-sm font-extrabold py-2.5 rounded-xl min-h-[44px] flex items-center justify-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40"
          >
            <i class="fa-solid fa-credit-card"></i> إتمام الدفع
          </button>
        </div>
      </div>
    </aside>
  </div>
</template>
