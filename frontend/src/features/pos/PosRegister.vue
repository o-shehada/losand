<script setup>
import { ref, reactive, computed } from "vue"
import { CATEGORIES, PRODUCTS, BRANCH, money, ar } from "./data"
import { lineTotal, unitPrice, isUniform, giftApplied as calcGiftApplied, giftRemaining } from "./cartMath"
import PosCustomizeSheet from "./PosCustomizeSheet.vue"

const activeCat = ref("all")
const search = ref("")
const cart = ref([])
const discount = ref(0)
const tableLabel = ref("الطاولة الخامسة")

const visibleProducts = computed(() =>
  PRODUCTS.filter((p) => (activeCat.value === "all" || p.category === activeCat.value) && p.name.includes(search.value.trim())),
)

// A line holds `pieces` (one per unit ordered). Each piece carries its own
// add-ons/notes, so N of the same product can be customized separately.
const emptyPiece = () => ({ extras: [], notes: [] })

function add(product) {
  const line = cart.value.find((l) => l.id === product.id)
  if (line) line.pieces.push(emptyPiece())
  else cart.value.push({ id: product.id, name: product.name, price: product.price, pieces: [emptyPiece()] })
}
function inc(line) {
  line.pieces.push(emptyPiece())
}
function dec(line) {
  line.pieces.pop()
  if (!line.pieces.length) remove(line)
}
function remove(line) {
  cart.value = cart.value.filter((l) => l.id !== line.id)
}
function clearCart() {
  cart.value = []
  discount.value = 0
}

const lineQty = (line) => line.pieces.length
// lineTotal / unitPrice / isUniform live in cartMath.js (pricing has its own test).

const payMethods = [
  { key: "cash", label: "نقدي", icon: "fa-money-bill-wave" },
  { key: "card", label: "بطاقة", icon: "fa-credit-card" },
  { key: "presto", label: "بريستو", icon: "fa-mobile-screen-button" },
]
const payment = ref("cash")

const count = computed(() => cart.value.reduce((s, l) => s + l.pieces.length, 0))
const subtotal = computed(() => cart.value.reduce((s, l) => s + lineTotal(l), 0))
const total = computed(() => Math.max(0, subtotal.value - Number(discount.value || 0)))

// Gift card / coupon — a credit applied before the remaining payment method.
// ponytail: fixed mock value; real balance lookup comes with the ERPNext gift
// card doctype. Covers the whole total → remaining 0 (invoice settles at 0);
// covers part → remaining paid by the selected method.
const MOCK_GIFT_VALUE = 10
const gift = reactive({ open: false, id: "", card: null })
function applyGift() {
  const id = gift.id.trim()
  if (!id) return
  gift.card = { id, value: MOCK_GIFT_VALUE }
  gift.open = false
  gift.id = ""
}
function removeGift() {
  gift.card = null
}
const giftApplied = computed(() => (gift.card ? calcGiftApplied(total.value, gift.card.value) : 0))
const remaining = computed(() => (gift.card ? giftRemaining(total.value, gift.card.value) : total.value))

// Paused / parked orders. Snapshot the whole order, clear the register for a
// new one, resume later. ponytail: component-local, so it clears on nav away —
// same as the live cart today; move to a store + backend with the ERPNext wiring.
const held = ref([])
const showHeld = ref(false)
let heldSeq = 0
const heldTotal = (h) => Math.max(0, h.cart.reduce((s, l) => s + lineTotal(l), 0) - Number(h.discount || 0))
function resetOrder() {
  cart.value = []
  discount.value = 0
  payment.value = "cash"
  gift.card = null
  gift.open = false
  gift.id = ""
}
function snapshot() {
  return {
    key: ++heldSeq,
    at: new Date(),
    table: tableLabel.value,
    cart: JSON.parse(JSON.stringify(cart.value)), // plain data (no fns) → safe clone
    discount: discount.value,
    payment: payment.value,
    gift: gift.card ? { ...gift.card } : null,
  }
}
function pauseOrder() {
  if (!cart.value.length) return
  held.value.push(snapshot())
  resetOrder()
}
function resumeOrder(h) {
  if (cart.value.length) held.value.push(snapshot()) // park the current order first
  cart.value = h.cart
  discount.value = h.discount
  payment.value = h.payment
  tableLabel.value = h.table
  gift.card = h.gift
  held.value = held.value.filter((x) => x.key !== h.key)
  showHeld.value = false
}
function dropHeld(h) {
  held.value = held.value.filter((x) => x.key !== h.key)
}

// Per-line expand toggle for the per-piece editor list.
const expanded = reactive({})
const toggleExpand = (id) => (expanded[id] = !expanded[id])

// Customization sheet — one sheet, parent decides how to apply the result.
const sheet = reactive({ open: false, title: "", extras: [], notes: [], apply: null })
function openLineCustomize(line) {
  // ponytail: whole-line edit seeds from piece #1 and OVERWRITES every piece on
  // done (bulk apply). Same path serves "دمج التخصيص" collapsing per-piece edits
  // back to one uniform set. Split whole-line vs per-piece intent when the
  // kitchen actually needs the distinction.
  const seed = line.pieces[0]
  sheet.title = "تخصيص الصنف"
  sheet.extras = seed.extras
  sheet.notes = seed.notes
  sheet.apply = (res) =>
    line.pieces.forEach((p) => {
      p.extras = res.extras.map((e) => ({ ...e }))
      p.notes = [...res.notes]
    })
  sheet.open = true
}
function openPieceCustomize(line, i) {
  const p = line.pieces[i]
  sheet.title = `تخصيص — قطعة ${ar(i + 1)}`
  sheet.extras = p.extras
  sheet.notes = p.notes
  sheet.apply = (res) => {
    p.extras = res.extras
    p.notes = res.notes
  }
  sheet.open = true
}
function sheetDone(res) {
  sheet.apply?.(res)
  sheet.open = false
}
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
      <!-- Paused orders -->
      <div class="relative">
        <button
          @click.stop="showHeld = !showHeld"
          class="relative border text-xs font-bold px-3 py-2 rounded-xl min-h-[44px] flex items-center gap-1.5 transition-colors"
          :class="held.length ? 'bg-pos-amber-light border-pos-amber text-pos-amber' : 'bg-pos-canvas border-pos-border text-gray-500 hover:border-pos-brand hover:text-pos-brand'"
        >
          <i class="fa-solid fa-pause text-xs"></i>
          <span class="hidden md:inline">معلّقة</span>
          <span v-if="held.length" class="bg-pos-amber text-white text-[10px] font-extrabold rounded-full w-4 h-4 flex items-center justify-center">{{ ar(held.length) }}</span>
        </button>
        <div v-if="showHeld" class="absolute left-0 top-12 bg-pos-surface border border-pos-border rounded-xl2 shadow-lg z-30 w-72 p-2">
          <p class="text-xs font-extrabold text-gray-700 px-2 py-1.5">الطلبات المعلّقة</p>
          <div v-if="!held.length" class="text-center text-pos-muted text-xs font-semibold py-6">لا توجد طلبات معلّقة</div>
          <div v-else class="flex flex-col gap-1.5 max-h-72 overflow-y-auto">
            <div v-for="h in held" :key="h.key" class="flex items-center gap-2 bg-pos-canvas border border-pos-border rounded-xl px-2.5 py-2">
              <button @click="resumeOrder(h)" class="flex-1 min-w-0 text-right">
                <p class="text-xs font-bold text-gray-800 leading-tight flex items-center gap-1.5"><i class="fa-solid fa-chair text-pos-brand text-[10px]"></i> {{ h.table }}</p>
                <p class="text-[10px] text-pos-muted font-semibold">{{ h.cart.length }} أصناف · {{ money(heldTotal(h)) }}</p>
              </button>
              <button @click="resumeOrder(h)" class="text-[11px] font-bold text-pos-brand-dark bg-pos-brand-light border border-pos-brand/25 rounded-lg px-2.5 py-1.5 hover:bg-pos-brand hover:text-white transition-colors">استئناف</button>
              <button @click="dropHeld(h)" class="text-pos-muted hover:text-pos-danger transition-colors px-1"><i class="fa-solid fa-trash text-xs"></i></button>
            </div>
          </div>
        </div>
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
              <span class="text-sm font-extrabold text-gray-800 w-5 text-center">{{ ar(lineQty(line)) }}</span>
              <button @click="inc(line)" class="w-7 h-7 rounded-lg bg-pos-surface border border-pos-border flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold">+</button>
            </div>
            <div class="flex flex-col items-end leading-tight">
              <span v-if="lineQty(line) > 1" class="text-xs text-pos-muted font-semibold">
                {{ money(unitPrice(line)) }}<template v-if="isUniform(line)"> × {{ ar(lineQty(line)) }}</template>
              </span>
              <span class="text-pos-brand-dark font-extrabold text-base">{{ money(lineTotal(line)) }}</span>
            </div>
          </div>

          <!-- customize actions -->
          <div class="flex items-center gap-2 mt-2">
            <button
              @click="openLineCustomize(line)"
              class="flex items-center gap-1.5 text-[11px] font-bold text-pos-brand-dark bg-pos-brand-light border border-pos-brand/25 rounded-lg px-2.5 py-1.5 hover:bg-pos-brand hover:text-white transition-colors"
            >
              <i class="fa-solid fa-pen text-[10px]"></i> تخصيص
            </button>
            <button
              v-if="lineQty(line) > 1"
              @click="toggleExpand(line.id)"
              class="flex items-center gap-1.5 text-[11px] font-bold text-gray-600 border border-pos-border rounded-lg px-2.5 py-1.5 hover:border-pos-brand hover:text-pos-brand transition-colors"
            >
              <i class="fa-solid text-[9px]" :class="expanded[line.id] ? 'fa-chevron-up' : 'fa-chevron-down'"></i>
              {{ expanded[line.id] ? "دمج التخصيص" : "تخصيص كل قطعة" }}
            </button>
          </div>

          <!-- uniform customization (single piece, or bulk-applied to all): show aggregate chips -->
          <div
            v-if="isUniform(line) && (line.pieces[0].extras.length || line.pieces[0].notes.length)"
            class="flex flex-wrap gap-1 mt-2"
          >
            <span v-for="e in line.pieces[0].extras" :key="e.id" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pos-amber/10 text-pos-amber border border-pos-amber/20">{{ e.name }} +{{ money(e.price) }}</span>
            <span v-for="n in line.pieces[0].notes" :key="n" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pos-brand-light text-pos-brand-dark border border-pos-brand/20">{{ n }}</span>
          </div>

          <!-- multiple pieces, expanded: per-piece editor rows -->
          <div v-if="lineQty(line) > 1 && expanded[line.id]" class="mt-2 space-y-1.5 border-t border-dashed border-pos-border pt-2">
            <div v-for="(p, i) in line.pieces" :key="i" class="bg-pos-surface rounded-lg border border-pos-border px-2.5 py-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-extrabold text-gray-700">{{ line.name }} #{{ ar(i + 1) }}</span>
                <button @click="openPieceCustomize(line, i)" class="text-pos-brand hover:text-pos-brand-dark transition-colors">
                  <i class="fa-solid fa-pen text-[11px]"></i>
                </button>
              </div>
              <div v-if="p.extras.length || p.notes.length" class="flex flex-wrap gap-1 mt-1.5">
                <span v-for="e in p.extras" :key="e.id" class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-pos-amber/10 text-pos-amber border border-pos-amber/20">{{ e.name }} +{{ money(e.price) }}</span>
                <span v-for="n in p.notes" :key="n" class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-pos-brand-light text-pos-brand-dark border border-pos-brand/20">{{ n }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer / totals -->
      <div class="border-t border-pos-border px-4 py-3 flex-shrink-0 bg-pos-canvas/60">
        <!-- Gift card / coupon -->
        <div class="mb-3">
          <div v-if="gift.card" class="flex items-center justify-between bg-pos-brand-light border border-pos-brand/25 rounded-xl px-3 py-2">
            <span class="flex items-center gap-1.5 text-xs font-bold text-pos-brand-dark">
              <i class="fa-solid fa-gift text-xs"></i> بطاقة هدية #{{ gift.card.id }}
            </span>
            <span class="flex items-center gap-2">
              <span class="text-xs font-extrabold text-pos-brand-dark">−{{ money(giftApplied) }}</span>
              <button @click="removeGift" class="text-pos-muted hover:text-pos-danger transition-colors"><i class="fa-solid fa-xmark text-xs"></i></button>
            </span>
          </div>
          <template v-else>
            <button
              v-if="!gift.open"
              @click="gift.open = true"
              class="w-full flex items-center justify-center gap-1.5 text-xs font-bold text-pos-brand-dark bg-pos-brand-light/50 border border-dashed border-pos-brand/40 rounded-xl py-2 min-h-[40px] hover:bg-pos-brand-light transition-colors"
            >
              <i class="fa-solid fa-gift text-xs"></i> بطاقة هدية / قسيمة
            </button>
            <div v-else class="flex items-center gap-2">
              <input
                v-model="gift.id"
                @keyup.enter="applyGift"
                type="text"
                placeholder="رقم البطاقة"
                dir="ltr"
                class="flex-1 bg-pos-surface border border-pos-border rounded-xl px-3 py-2 text-xs text-gray-700 focus:outline-none focus:border-pos-brand min-h-[40px]"
              />
              <button @click="applyGift" class="bg-pos-brand text-white text-xs font-bold px-3 rounded-xl min-h-[40px] hover:bg-pos-brand-dark transition-colors">تطبيق</button>
              <button @click="gift.open = false" class="text-pos-muted px-1 hover:text-pos-danger transition-colors"><i class="fa-solid fa-xmark"></i></button>
            </div>
          </template>
        </div>

        <!-- Payment method (pays the remaining balance) -->
        <div class="grid grid-cols-3 gap-2 mb-3" :class="gift.card && remaining === 0 ? 'opacity-40 pointer-events-none' : ''">
          <button
            v-for="m in payMethods"
            :key="m.key"
            @click="payment = m.key"
            class="flex items-center justify-center gap-1.5 py-2 rounded-xl text-xs font-bold min-h-[40px] border transition-colors"
            :class="payment === m.key ? 'bg-pos-brand border-pos-brand text-white shadow-sm shadow-pos-brand/25' : 'bg-pos-brand-light/50 border-pos-border text-gray-600 hover:border-pos-brand hover:text-pos-brand'"
          >
            <i class="fa-solid text-xs" :class="m.icon"></i>
            {{ m.label }}
          </button>
        </div>
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
        <template v-if="gift.card">
          <div class="flex items-center justify-between text-sm mt-1.5">
            <span class="text-pos-muted font-semibold flex items-center gap-1.5"><i class="fa-solid fa-gift text-xs text-pos-brand"></i> بطاقة هدية</span>
            <span class="font-bold text-pos-brand-dark">−{{ money(giftApplied) }}</span>
          </div>
          <div class="flex items-center justify-between text-base border-t border-dashed border-pos-border pt-2 mt-1">
            <span class="font-extrabold text-gray-800">الباقي</span>
            <span class="font-extrabold" :class="remaining === 0 ? 'text-pos-green' : 'text-pos-brand-dark'">{{ money(remaining) }}</span>
          </div>
        </template>
        <button
          @click="pauseOrder"
          :disabled="!cart.length"
          class="w-full mt-3 bg-pos-amber-light border border-pos-amber/40 text-pos-amber text-xs font-bold py-2.5 rounded-xl min-h-[44px] flex items-center justify-center gap-2 hover:bg-pos-amber hover:text-white transition-colors disabled:opacity-40"
        >
          <i class="fa-solid fa-pause text-xs"></i> تعليق الطلب
        </button>
        <div class="grid grid-cols-3 gap-2 mt-2">
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
            <i class="fa-solid" :class="gift.card && remaining === 0 ? 'fa-circle-check' : 'fa-credit-card'"></i>
            {{ gift.card && remaining === 0 ? "إتمام — مدفوع بالكامل" : "إتمام الدفع" }}
          </button>
        </div>
      </div>
    </aside>
  </div>

  <!-- Item customization sheet -->
  <PosCustomizeSheet
    v-if="sheet.open"
    :title="sheet.title"
    :extras="sheet.extras"
    :notes="sheet.notes"
    @done="sheetDone"
    @close="sheet.open = false"
  />
</template>
