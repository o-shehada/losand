<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue"
import { BRANCH, ar } from "./data"
import { getPosProducts, previewOrder, submitOrder, checkGiftCard, parkOrder, listParked, resumeParked, discardParked } from "@/lib/api"
import { pos } from "@/stores/pos"
import { lineTotal, unitPrice, isUniform, giftApplied as calcGiftApplied, giftRemaining } from "./cartMath"
import PosCustomizeSheet from "./PosCustomizeSheet.vue"

const activeCat = ref("all")
const search = ref("")
const cart = ref([])
const discount = ref(0)
const tableLabel = ref("الطاولة الخامسة")

// The register only sells the live ERPNext catalog for the active POS Profile.
const categories = ref([{ key: "all", label: "الكل", icon: "fa-utensils" }])
const products = ref([])
const loadError = ref("")

onMounted(async () => {
  payment.value = pos.config?.payments?.find((p) => p.default)?.mode_of_payment || payMethods.value[0]?.key || "Cash"
  loadHeld()
  try {
    const res = await getPosProducts()
    if (res && Array.isArray(res.products)) {
      products.value = res.products
      categories.value = [
        { key: "all", label: "الكل", icon: "fa-utensils" },
        ...res.categories.map((c) => ({ ...c, icon: "fa-utensils" })),
      ]
    }
  } catch (e) {
    loadError.value = e.message
  }
})

const visibleProducts = computed(() => {
  const term = search.value.trim().toLocaleLowerCase()
  return products.value.filter(
    (product) =>
      (activeCat.value === "all" || product.category === activeCat.value) &&
      (!term ||
        product.name.toLocaleLowerCase().includes(term) ||
        product.id.toLocaleLowerCase().includes(term)),
  )
})

const hasAvailableQty = (product) => product.available_qty !== null && product.available_qty !== undefined
const controlsStock = (product) => !!pos.config?.update_stock && product.is_stock_item === true
const formatQty = (value) =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(Number(value) || 0)
const formatMoney = (value) =>
  `${Number(value || 0).toFixed(2)} ${pos.config?.currency_symbol || pos.config?.currency || "د.ل"}`
const productInCartQty = (product) => cart.value.find((line) => line.id === product.id)?.pieces.length || 0
const canAddProduct = (product) =>
  !controlsStock(product) || !hasAvailableQty(product) || productInCartQty(product) + 1 <= Number(product.available_qty)
const canIncrementLine = (line) =>
  !controlsStock(line) ||
  line.available_qty === null ||
  line.available_qty === undefined ||
  line.pieces.length + 1 <= Number(line.available_qty)
const addButtonLabel = (product) => {
  if (!controlsStock(product) || !hasAvailableQty(product)) return "إضافة"
  if (Number(product.available_qty) <= 0) return "غير متوفر"
  return canAddProduct(product) ? "إضافة" : "تمت إضافة المتاح"
}

// A line holds `pieces` (one per unit ordered). Each piece carries its own
// add-ons/notes, so N of the same product can be customized separately.
const emptyPiece = () => ({ extras: [], notes: [] })

function add(product) {
  if (!canAddProduct(product)) return
  const line = cart.value.find((l) => l.id === product.id)
  if (line) line.pieces.push(emptyPiece())
  else {
    cart.value.push({
      id: product.id,
      name: product.name,
      price: product.price,
      original_rate: product.price,
      available_qty: product.available_qty,
      uom: product.uom,
      is_stock_item: product.is_stock_item,
      pieces: [emptyPiece()],
    })
  }
}

watch([search, visibleProducts], ([term, matches]) => {
  if (pos.config?.auto_add_item_to_cart && term.trim() && matches.length === 1) {
    add(matches[0])
    search.value = ""
  }
})
function inc(line) {
  if (!canIncrementLine(line)) return
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
  gift.card = null
  gift.open = false
  gift.id = ""
  gift.error = ""
}

const lineQty = (line) => line.pieces.length
// lineTotal / unitPrice / isUniform live in cartMath.js (pricing has its own test).

// Payment methods come from the POS Profile (Mode of Payment names). Known modes
// get an Arabic label + icon; anything else shows its raw name.
const PAY_META = {
  Cash: { label: "نقدي", icon: "fa-money-bill-wave" },
  "Credit Card": { label: "بطاقة", icon: "fa-credit-card" },
  "Debit Card": { label: "بطاقة", icon: "fa-credit-card" },
}
const payMethods = computed(() =>
  (pos.config?.payments?.length ? pos.config.payments : [{ mode_of_payment: "Cash", default: true }]).map((p) => {
    const meta = PAY_META[p.mode_of_payment] || { label: p.mode_of_payment, icon: "fa-wallet" }
    return { key: p.mode_of_payment, label: meta.label, icon: meta.icon }
  }),
)
const payment = ref("Cash")
const paymentAmount = ref(null)
const showPaymentAmount = computed(
  () => !!pos.config?.disable_grand_total_to_default_mop || !!pos.config?.allow_partial_payment,
)

const count = computed(() => cart.value.reduce((s, l) => s + l.pieces.length, 0))
const localSubtotal = computed(() => cart.value.reduce((sum, line) => sum + lineTotal(line), 0))
const quote = reactive({ net_total: 0, taxes: 0, grand_total: 0, rounded_total: 0, ready: false, loading: false })
const subtotal = computed(() => (quote.ready ? quote.net_total : localSubtotal.value))
const total = computed(() =>
  quote.ready
    ? quote.rounded_total || quote.grand_total
    : Math.max(0, localSubtotal.value - Number(discount.value || 0)),
)

function cartItems() {
  const items = []
  for (const line of cart.value) {
    const item = { item_code: line.id, qty: lineQty(line) }
    if (
      pos.config?.allow_rate_change &&
      line.original_rate !== undefined &&
      Number(line.price) !== Number(line.original_rate)
    ) {
      item.rate = Number(line.price || 0)
    }
    items.push(item)
    const extraQty = {}
    for (const piece of line.pieces) {
      for (const extra of piece.extras) extraQty[extra.item_code] = (extraQty[extra.item_code] || 0) + 1
    }
    for (const [item_code, qty] of Object.entries(extraQty)) items.push({ item_code, qty })
  }
  return items
}

let quoteTimer
let quoteSequence = 0
watch(
  [cart, discount],
  () => {
    clearTimeout(quoteTimer)
    quote.ready = false
    if (!cart.value.length) {
      quote.loading = false
      return
    }
    const sequence = ++quoteSequence
    quote.loading = true
    quoteTimer = setTimeout(async () => {
      try {
        const result = await previewOrder({ cart: cartItems(), discount: Number(discount.value || 0) })
        if (sequence !== quoteSequence) return
        Object.assign(quote, result, { ready: true })
      } catch (error) {
        if (sequence === quoteSequence) checkoutError.value = error.message
      } finally {
        if (sequence === quoteSequence) quote.loading = false
      }
    }, 250)
  },
  { deep: true },
)

// Gift card / coupon — a credit tendered before the remaining payment method.
// Balance comes from the Los Andalus Gift Card doctype; the server computes the
// split (min of balance, total). Covers whole total → remaining 0; covers part →
// remaining paid by the selected method.
const gift = reactive({ open: false, id: "", card: null, checking: false, error: "" })
async function applyGift() {
  const code = gift.id.trim()
  if (!code) return
  gift.checking = true
  gift.error = ""
  try {
    const res = await checkGiftCard(code)
    gift.card = { id: res.card_no, value: res.balance }
    gift.open = false
    gift.id = ""
  } catch (e) {
    gift.error = e.message
  } finally {
    gift.checking = false
  }
}
function removeGift() {
  gift.card = null
}
const giftApplied = computed(() => (gift.card ? calcGiftApplied(total.value, gift.card.value) : 0))
const remaining = computed(() => (gift.card ? giftRemaining(total.value, gift.card.value) : total.value))
watch(remaining, (value) => {
  if (!pos.config?.disable_grand_total_to_default_mop) paymentAmount.value = value
}, { immediate: true })

// Paid add-ons are submitted as real Item rows alongside the base product.
const hasPaidExtras = computed(() => cart.value.some((l) => l.pieces.some((p) => p.extras.length)))
// Every add-on in the cart must carry a real item_code from the live catalog.
const extrasResolved = computed(() => cart.value.every((l) => l.pieces.every((p) => p.extras.every((e) => e.item_code))))
const stockIssue = computed(() => {
  for (const line of cart.value) {
    const product = products.value.find((p) => p.id === line.id)
    if (product && controlsStock(product) && hasAvailableQty(product) && lineQty(line) > Number(product.available_qty)) {
      return { name: line.name, available: Number(product.available_qty), uom: product.uom }
    }
  }
  return null
})
const blockReason = computed(() => {
  if (stockIssue.value) {
    if (stockIssue.value.available <= 0) return `الصنف "${stockIssue.value.name}" غير متوفر حالياً`
    return `الكمية المتاحة من "${stockIssue.value.name}" هي ${formatQty(stockIssue.value.available)} ${stockIssue.value.uom || ""}`
  }
  if (quote.loading) return "جارٍ حساب الأسعار والضرائب…"
  if (showPaymentAmount.value && remaining.value > 0) {
    const amount = Number(paymentAmount.value || 0)
    if (amount <= 0) return "أدخل المبلغ المدفوع"
    if (!pos.config?.allow_partial_payment && amount < remaining.value) {
      return "الدفع الجزئي غير مسموح في ملف نقطة البيع"
    }
  }
  if (hasPaidExtras.value && !extrasResolved.value) return "قائمة الإضافات غير محمّلة — أعد المحاولة"
  return ""
})
const canCheckout = computed(() => !!cart.value.length && !blockReason.value)

const checkingOut = ref(false)
const checkoutError = ref("")
const receipt = ref(null)

async function checkout() {
  if (!canCheckout.value || checkingOut.value) return
  const printWindow = pos.config?.print_receipt_on_order_complete ? window.open("about:blank", "_blank") : null
  checkingOut.value = true
  checkoutError.value = ""
  try {
    // Base line + its add-ons as separate priced lines. ponytail: per-piece grouping
    // is flattened (cheese on piece #1 becomes one cheese line) and free notes are
    // dropped — both money-correct; kitchen-ticket detail is a later phase.
    const items = cartItems()
    const selectedPayment = { mode_of_payment: payment.value }
    if (showPaymentAmount.value) selectedPayment.amount = Number(paymentAmount.value || 0)
    const res = await submitOrder({
      cart: items,
      payments: [selectedPayment],
      discount: Number(discount.value || 0),
      gift_card: gift.card?.id || null,
      table: tableLabel.value,
      request_id: crypto.randomUUID(),
    })
    receipt.value = res
    if (printWindow) printWindow.location.href = receiptUrl(res.name)
    clearCart()
  } catch (e) {
    printWindow?.close()
    const stockMatch = e.message.match(/Not enough batch stock of (.+?) in .+? \(short ([\d.,]+)\)\.?/i)
    checkoutError.value = stockMatch
      ? `الكمية المتاحة من "${stockMatch[1]}" غير كافية لإتمام الطلب. النقص: ${stockMatch[2]}.`
      : e.message
  } finally {
    checkingOut.value = false
  }
}

function receiptUrl(name) {
  const params = new URLSearchParams({
    doctype: "Sales Invoice",
    name,
    format: pos.config?.print_format || "POS Invoice",
    trigger_print: "1",
  })
  if (pos.config?.letter_head) params.set("letterhead", pos.config.letter_head)
  return `/printview?${params.toString()}`
}

function printReceipt(name) {
  window.open(receiptUrl(name), "_blank")
}

// Paused / parked orders. Snapshot the whole order, clear the register for a
// new one, resume later. Persisted server-side (Los Andalus Parked Order) so
// holds survive navigation/reload. The payload only restores the UI — money is
// re-priced server-side at checkout.
const held = ref([])
const showHeld = ref(false)
async function loadHeld() {
  held.value = (await listParked().catch(() => [])) || []
}
function resetOrder() {
  cart.value = []
  discount.value = 0
  payment.value = pos.config?.payments?.find((p) => p.default)?.mode_of_payment || "Cash"
  gift.card = null
  gift.open = false
  gift.id = ""
}
function snapshot() {
  return {
    table: tableLabel.value,
    cart: JSON.parse(JSON.stringify(cart.value)), // plain data (no fns) → safe clone
    discount: discount.value,
    payment: payment.value,
    gift: gift.card ? { ...gift.card } : null,
  }
}
async function parkCurrent() {
  await parkOrder({ payload: snapshot(), table: tableLabel.value, total: total.value })
}
async function pauseOrder() {
  if (!cart.value.length) return
  await parkCurrent()
  resetOrder()
  await loadHeld()
}
async function resumeOrder(h) {
  if (cart.value.length) await parkCurrent() // park the current order first
  const res = await resumeParked(h.name)
  const s = res?.payload
  if (s) {
    cart.value = s.cart || []
    discount.value = pos.config?.allow_discount_change ? s.discount || 0 : 0
    payment.value = s.payment || payment.value
    tableLabel.value = s.table || tableLabel.value
    gift.card = s.gift || null
  }
  showHeld.value = false
  await loadHeld()
}
async function dropHeld(h) {
  await discardParked(h.name)
  await loadHeld()
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
            <div v-for="h in held" :key="h.name" class="flex items-center gap-2 bg-pos-canvas border border-pos-border rounded-xl px-2.5 py-2">
              <button @click="resumeOrder(h)" class="flex-1 min-w-0 text-right">
                <p class="text-xs font-bold text-gray-800 leading-tight flex items-center gap-1.5"><i class="fa-solid fa-chair text-pos-brand text-[10px]"></i> {{ h.table_label }}</p>
                <p class="text-[10px] text-pos-muted font-semibold">{{ formatMoney(h.total) }}</p>
              </button>
              <button @click="resumeOrder(h)" class="text-[11px] font-bold text-pos-brand-dark bg-pos-brand-light border border-pos-brand/25 rounded-lg px-2.5 py-1.5 hover:bg-pos-brand hover:text-white transition-colors">استئناف</button>
              <button @click="dropHeld(h)" class="text-pos-muted hover:text-pos-danger transition-colors px-1"><i class="fa-solid fa-trash text-xs"></i></button>
            </div>
          </div>
        </div>
      </div>
      <div class="pos-shift-pill text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
        <i class="fa-solid fa-sun text-yellow-200 text-xs"></i>
        <span>{{ pos.config?.pos_profile || "…" }}</span>
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
          v-for="c in categories"
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
        <div v-if="loadError" class="mb-3 bg-pos-danger-light border border-pos-danger/30 text-pos-danger rounded-xl px-4 py-3 text-sm font-bold">
          <i class="fa-solid fa-triangle-exclamation ml-2"></i>{{ loadError }}
        </div>
        <div class="grid grid-cols-2 lg:grid-cols-3 gap-3">
          <div
            v-for="p in visibleProducts"
            :key="p.id"
            class="pos-product-card bg-pos-surface rounded-xl2 border border-pos-border overflow-hidden flex flex-col"
          >
            <div v-if="!pos.config?.hide_images" class="h-28 bg-pos-brand-light overflow-hidden">
              <img :src="p.img" :alt="p.name" class="w-full h-full object-cover" loading="lazy" />
            </div>
            <div class="p-3 flex flex-col gap-2 flex-1">
              <p class="font-bold text-gray-800 text-sm leading-tight">{{ p.name }}</p>
              <div
                v-if="p.is_stock_item && hasAvailableQty(p)"
                class="flex items-center gap-1.5 text-xs font-bold"
                :class="Number(p.available_qty) > 0 ? 'text-pos-green' : 'text-pos-danger'"
              >
                <i class="fa-solid fa-boxes-stacked text-[10px]"></i>
                <span>المتاح:</span>
                <span dir="ltr">{{ formatQty(p.available_qty) }} {{ p.uom || "" }}</span>
              </div>
              <div class="mt-auto flex items-center justify-between">
                <span class="text-pos-brand-dark font-extrabold text-sm">{{ formatMoney(p.price) }}</span>
                <button
                  @click="add(p)"
                  :disabled="!canAddProduct(p)"
                  class="pos-btn text-white text-xs font-bold px-4 py-2 rounded-xl min-h-[36px] flex items-center gap-1.5 transition-colors shadow-sm disabled:cursor-not-allowed"
                  :class="canAddProduct(p) ? 'bg-pos-brand hover:bg-pos-brand-dark shadow-pos-brand/20' : 'bg-pos-muted opacity-65 shadow-none'"
                >
                  <i class="fa-solid text-xs" :class="canAddProduct(p) ? 'fa-plus' : 'fa-ban'"></i>
                  {{ addButtonLabel(p) }}
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
          <label v-if="pos.config?.allow_rate_change" class="mt-2 flex items-center justify-between gap-2 text-[11px] font-bold text-pos-muted">
            <span>سعر الوحدة</span>
            <span class="flex items-center gap-1">
              <input
                v-model.number="line.price"
                type="number"
                min="0"
                step="0.01"
                dir="ltr"
                class="w-20 bg-pos-surface border border-pos-border rounded-lg px-2 py-1 text-xs font-bold text-gray-700 text-center focus:outline-none focus:border-pos-brand"
              />
              <span>{{ pos.config?.currency_symbol || pos.config?.currency }}</span>
            </span>
          </label>
          <div class="flex items-center justify-between mt-2">
            <div class="flex items-center gap-2">
              <button @click="dec(line)" class="w-7 h-7 rounded-lg bg-pos-surface border border-pos-border flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold">−</button>
              <span class="text-sm font-extrabold text-gray-800 w-5 text-center">{{ ar(lineQty(line)) }}</span>
              <button
                @click="inc(line)"
                :disabled="!canIncrementLine(line)"
                class="w-7 h-7 rounded-lg bg-pos-surface border border-pos-border flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold disabled:opacity-35 disabled:cursor-not-allowed"
              >+</button>
            </div>
            <div class="flex flex-col items-end leading-tight">
              <span v-if="lineQty(line) > 1" class="text-xs text-pos-muted font-semibold">
                {{ formatMoney(unitPrice(line)) }}<template v-if="isUniform(line)"> × {{ ar(lineQty(line)) }}</template>
              </span>
              <span class="text-pos-brand-dark font-extrabold text-base">{{ formatMoney(lineTotal(line)) }}</span>
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
            <span v-for="e in line.pieces[0].extras" :key="e.id" class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-pos-amber/10 text-pos-amber border border-pos-amber/20">{{ e.name }} +{{ formatMoney(e.price) }}</span>
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
                <span v-for="e in p.extras" :key="e.id" class="text-[9px] font-bold px-1.5 py-0.5 rounded-full bg-pos-amber/10 text-pos-amber border border-pos-amber/20">{{ e.name }} +{{ formatMoney(e.price) }}</span>
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
              <span class="text-xs font-extrabold text-pos-brand-dark">−{{ formatMoney(giftApplied) }}</span>
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
            <div v-else>
              <div class="flex items-center gap-2">
                <input
                  v-model="gift.id"
                  @keyup.enter="applyGift"
                  type="text"
                  placeholder="رقم البطاقة"
                  dir="ltr"
                  class="flex-1 bg-pos-surface border border-pos-border rounded-xl px-3 py-2 text-xs text-gray-700 focus:outline-none focus:border-pos-brand min-h-[40px]"
                />
                <button @click="applyGift" :disabled="gift.checking" class="bg-pos-brand text-white text-xs font-bold px-3 rounded-xl min-h-[40px] hover:bg-pos-brand-dark transition-colors disabled:opacity-40">{{ gift.checking ? "…" : "تطبيق" }}</button>
                <button @click="gift.open = false" class="text-pos-muted px-1 hover:text-pos-danger transition-colors"><i class="fa-solid fa-xmark"></i></button>
              </div>
              <p v-if="gift.error" class="text-[10px] text-pos-danger font-bold mt-1">{{ gift.error }}</p>
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
        <label v-if="showPaymentAmount && remaining > 0" class="flex items-center justify-between text-sm mb-2">
          <span class="text-pos-muted font-semibold">المبلغ المدفوع</span>
          <span class="flex items-center gap-1.5">
            <input
              v-model.number="paymentAmount"
              type="number"
              min="0"
              step="0.01"
              dir="ltr"
              class="w-24 bg-pos-surface border border-pos-border rounded-lg px-2 py-1 text-xs text-left font-bold text-gray-700 focus:outline-none focus:border-pos-brand"
            />
            <span class="text-xs text-pos-muted">{{ pos.config?.currency_symbol || pos.config?.currency }}</span>
          </span>
        </label>
        <div class="flex items-center justify-between text-sm mb-1.5">
          <span class="text-pos-muted font-semibold">المجموع الفرعي</span>
          <span class="font-bold text-gray-700">{{ formatMoney(subtotal) }}</span>
        </div>
        <div v-if="quote.ready && quote.taxes" class="flex items-center justify-between text-sm mb-1.5">
          <span class="text-pos-muted font-semibold">الضرائب والرسوم</span>
          <span class="font-bold text-gray-700">{{ formatMoney(quote.taxes) }}</span>
        </div>
        <div v-if="pos.config?.allow_discount_change" class="flex items-center justify-between text-sm mb-1.5">
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
          <span class="font-extrabold text-pos-brand-dark">{{ formatMoney(total) }}</span>
        </div>
        <template v-if="gift.card">
          <div class="flex items-center justify-between text-sm mt-1.5">
            <span class="text-pos-muted font-semibold flex items-center gap-1.5"><i class="fa-solid fa-gift text-xs text-pos-brand"></i> بطاقة هدية</span>
            <span class="font-bold text-pos-brand-dark">−{{ formatMoney(giftApplied) }}</span>
          </div>
          <div class="flex items-center justify-between text-base border-t border-dashed border-pos-border pt-2 mt-1">
            <span class="font-extrabold text-gray-800">الباقي</span>
            <span class="font-extrabold" :class="remaining === 0 ? 'text-pos-green' : 'text-pos-brand-dark'">{{ formatMoney(remaining) }}</span>
          </div>
        </template>
        <p v-if="blockReason && cart.length" class="text-[11px] text-pos-amber font-bold mt-2 flex items-center gap-1.5">
          <i class="fa-solid fa-circle-info text-[10px]"></i> {{ blockReason }}
        </p>
        <p v-if="checkoutError" class="text-[11px] text-pos-danger font-bold mt-2 flex items-center gap-1.5">
          <i class="fa-solid fa-triangle-exclamation text-[10px]"></i> {{ checkoutError }}
        </p>
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
            @click="checkout"
            :disabled="!canCheckout || checkingOut"
            class="col-span-2 pos-btn bg-pos-brand text-white text-sm font-extrabold py-2.5 rounded-xl min-h-[44px] flex items-center justify-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40"
          >
            <i class="fa-solid" :class="checkingOut ? 'fa-spinner fa-spin' : 'fa-credit-card'"></i>
            {{ checkingOut ? "جارٍ الإتمام…" : "إتمام الدفع" }}
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

  <!-- Order completed -->
  <div v-if="receipt" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="receipt = null">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl border border-pos-border p-8 flex flex-col items-center gap-4 max-w-sm w-full text-center">
      <div class="w-16 h-16 bg-pos-green-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-green text-3xl"></i></div>
      <div>
        <h3 class="font-extrabold text-gray-800 text-lg">تم إتمام الطلب!</h3>
        <p class="text-sm text-pos-muted font-semibold mt-1">فاتورة #{{ receipt.name }}</p>
      </div>
      <div class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-3 flex flex-col gap-1.5">
        <div class="flex items-center justify-between text-sm"><span class="text-pos-muted font-semibold">الإجمالي</span><span class="font-extrabold text-gray-800">{{ formatMoney(receipt.grand_total) }}</span></div>
        <div v-if="receipt.taxes" class="flex items-center justify-between text-sm"><span class="text-pos-muted font-semibold">الضرائب والرسوم</span><span class="font-bold text-gray-700">{{ formatMoney(receipt.taxes) }}</span></div>
        <div v-if="receipt.gift_applied" class="flex items-center justify-between text-sm"><span class="text-pos-muted font-semibold flex items-center gap-1.5"><i class="fa-solid fa-gift text-xs text-pos-brand"></i> بطاقة هدية</span><span class="font-bold text-pos-brand-dark">−{{ formatMoney(receipt.gift_applied) }}</span></div>
        <div class="flex items-center justify-between text-sm"><span class="text-pos-muted font-semibold">المدفوع</span><span class="font-bold text-gray-700">{{ formatMoney(receipt.paid_amount) }}</span></div>
        <div v-if="receipt.change_amount" class="flex items-center justify-between text-sm"><span class="text-pos-muted font-semibold">الباقي للعميل</span><span class="font-bold text-pos-brand-dark">{{ formatMoney(receipt.change_amount) }}</span></div>
      </div>
      <button @click="printReceipt(receipt.name)" class="bg-pos-canvas border border-pos-border text-pos-brand-dark font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:border-pos-brand transition-colors w-full"><i class="fa-solid fa-print ml-2"></i>طباعة الإيصال</button>
      <button @click="receipt = null" class="bg-pos-brand text-white font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:bg-pos-brand-dark transition-colors w-full">طلب جديد</button>
    </div>
  </div>
</template>
