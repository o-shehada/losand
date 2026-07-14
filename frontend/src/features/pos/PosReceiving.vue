<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { BRANCH, ar } from "./data"
import { getReceivingItems, receiveGoods } from "@/lib/api"

// Morning goods receipt: every item configured on the POS Profile is a row with a
// received-qty box (same shape as الجرد اليومي — no picking, just fill the sheet).
// Rows left at 0 are simply not received; submit posts a Material Receipt Stock
// Entry into the store for the rest.
const rows = ref([])
const qty = reactive({}) // id -> received qty, seeded 0
const supplier = ref("")
const note = ref("")
const loading = ref(true)
const submitting = ref(false)
const error = ref("")
const done = ref(null)

async function load() {
  loading.value = true
  try {
    // Which raw materials appear here is configured on the POS Profile
    // (losand_receiving_items); empty picker = nothing shown.
    const inv = await getReceivingItems()
    rows.value = inv.items || []
    rows.value.forEach((it) => (qty[it.id] = 0))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

const lineQty = (it) => Number(qty[it.id]) || 0
// 0 = not received; only the filled rows are posted.
const lines = computed(() => rows.value.filter((it) => lineQty(it) > 0))
const totalUnits = computed(() => lines.value.reduce((s, it) => s + lineQty(it), 0))

async function submit() {
  if (!lines.value.length) return
  error.value = ""
  submitting.value = true
  try {
    done.value = await receiveGoods({
      lines: lines.value.map((it) => ({ item_code: it.id, qty: lineQty(it) })),
      supplier: supplier.value || null,
      note: note.value || null,
    })
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

function reset() {
  supplier.value = ""
  note.value = ""
  done.value = null
  load() // re-read بالنظام — the receipt just moved it
}
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-truck-ramp-box text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">استلام الطلبات</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }} · استلام بضاعة الصباح</span>
        </div>
      </div>
    </div>
    <button @click="submit" :disabled="!lines.length || submitting" class="pos-btn bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40">
      <i class="fa-solid text-sm" :class="submitting ? 'fa-spinner fa-spin' : 'fa-check'"></i><span>{{ submitting ? "جارٍ التأكيد…" : "تأكيد الاستلام" }}</span>
    </button>
  </header>

  <!-- STATS -->
  <div class="bg-pos-surface border-b border-pos-border px-4 py-3 flex items-center gap-3 flex-shrink-0 flex-wrap">
    <div class="flex items-center gap-2.5 bg-pos-brand-light border border-pos-brand/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-brand rounded-lg flex items-center justify-center"><i class="fa-solid fa-layer-group text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">إجمالي الأصناف</p><p class="text-sm font-extrabold text-gray-800 leading-tight">{{ ar(rows.length) }} صنف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-green-light border border-pos-green/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-green rounded-lg flex items-center justify-center"><i class="fa-solid fa-check text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">تم استلامها</p><p class="text-sm font-extrabold text-pos-green leading-tight">{{ ar(lines.length) }} صنف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-amber-light border border-pos-amber/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-amber rounded-lg flex items-center justify-center"><i class="fa-solid fa-dolly text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">إجمالي الكميات</p><p class="text-sm font-extrabold text-pos-amber leading-tight">{{ ar(totalUnits) }}</p></div>
    </div>
    <p v-if="error" class="text-xs text-pos-danger font-bold mr-auto">{{ error }}</p>
  </div>

  <!-- BODY -->
  <div class="flex-1 overflow-y-auto p-3 md:p-4 flex flex-col gap-4">
    <!-- supplier / note -->
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm px-4 py-4 grid grid-cols-1 md:grid-cols-2 gap-4">
      <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">المورّد (اختياري)</span>
        <input v-model="supplier" type="text" placeholder="مثال: مخبز الأندلس" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
      <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">ملاحظة (اختياري)</span>
        <input v-model="note" type="text" placeholder="رقم الفاتورة / ملاحظة" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
    </div>

    <!-- received table -->
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm flex flex-col overflow-hidden">
      <div class="px-4 py-2.5 border-b border-pos-border flex items-center gap-2 bg-pos-brand-light/40">
        <i class="fa-solid fa-dolly text-pos-brand text-xs"></i>
        <span class="text-sm font-extrabold text-gray-800">الأصناف المستلَمة — المواد الخام</span>
      </div>
      <div class="grid grid-cols-12 bg-pos-brand-light/70 border-b border-pos-border px-4 py-2.5 flex-shrink-0">
        <div class="col-span-5 text-xs font-extrabold text-gray-600">اسم الصنف</div>
        <div class="col-span-3 text-xs font-extrabold text-gray-600">بالنظام</div>
        <div class="col-span-4 text-xs font-extrabold text-gray-600">الكمية المستلَمة</div>
      </div>
      <div class="divide-y divide-pos-border">
        <div v-if="loading" class="text-center text-pos-muted py-16 font-semibold"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2 block opacity-60"></i> جارٍ التحميل…</div>
        <div v-for="it in rows" :key="it.id" class="grid grid-cols-12 px-4 py-3 items-center">
          <div class="col-span-5 flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-pos-brand-light flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-box text-pos-brand text-sm"></i></div>
            <div><p class="text-sm font-bold text-gray-800 leading-tight">{{ it.name }}</p><p class="text-[10px] text-pos-muted font-semibold">{{ it.id }}</p></div>
          </div>
          <div class="col-span-3 text-sm font-bold text-gray-600">{{ ar(it.system_qty) }} {{ it.uom }}</div>
          <div class="col-span-4 flex items-center gap-2">
            <input
              v-model.number="qty[it.id]"
              type="number"
              min="0"
              step="0.001"
              dir="ltr"
              class="w-24 bg-pos-canvas border rounded-lg px-3 py-2 text-sm font-bold text-center focus:outline-none focus:border-pos-brand min-h-[40px]"
              :class="lineQty(it) > 0 ? 'border-pos-brand/50 text-gray-700' : 'border-pos-border text-pos-muted'"
            />
            <span class="text-xs text-pos-muted font-semibold">{{ it.uom }}</span>
            <span v-if="lineQty(it) > 0" class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-green/10 text-pos-green flex items-center gap-1 w-fit">
              <i class="fa-solid fa-arrow-up text-[10px]"></i> {{ ar(it.system_qty + lineQty(it)) }}
            </span>
          </div>
        </div>
        <div v-if="!loading && !rows.length" class="text-center text-pos-muted py-10 font-semibold">
          <i class="fa-solid fa-sliders text-xl mb-2 block opacity-60"></i>
          لم تُحدَّد أصناف الاستلام في ملف نقطة البيع
        </div>
      </div>
      <div v-if="lines.length" class="bg-pos-brand-light/40 border-t border-pos-border px-4 py-2.5 flex items-center justify-between flex-shrink-0">
        <span class="text-xs text-pos-muted font-semibold">{{ ar(lines.length) }} صنف مستلَم</span>
        <span class="text-xs font-extrabold text-gray-700">إجمالي الكميات: {{ ar(totalUnits) }}</span>
      </div>
    </div>
  </div>

  <!-- SUCCESS -->
  <div v-if="done" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="reset">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl border border-pos-border p-8 flex flex-col items-center gap-4 max-w-sm w-full text-center">
      <div class="w-16 h-16 bg-pos-green-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-green text-3xl"></i></div>
      <div><h3 class="font-extrabold text-gray-800 text-lg">تم تأكيد الاستلام!</h3><p class="text-sm text-pos-muted font-semibold mt-1">إدخال مخزون #{{ done.name }} — {{ ar(done.lines) }} أصناف.</p></div>
      <button @click="reset" class="bg-pos-brand text-white font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:bg-pos-brand-dark transition-colors w-full">استلام جديد</button>
    </div>
  </div>
</template>
