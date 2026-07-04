<script setup>
import { ref, computed, onMounted } from "vue"
import { BRANCH, ar } from "./data"
import { getInventory, receiveGoods } from "@/lib/api"

// Morning goods receipt: pick items, enter received qty, optional supplier/note,
// submit → backend posts a Material Receipt Stock Entry into the store.
const catalog = ref([])
const supplier = ref("")
const note = ref("")
const pick = ref("")
const qty = ref(1)
const lines = ref([])
const submitting = ref(false)
const error = ref("")
const done = ref(null)

onMounted(async () => {
  try {
    const inv = await getInventory()
    catalog.value = inv.items || []
  } catch (e) {
    error.value = e.message
  }
})

function addLine() {
  const it = catalog.value.find((i) => i.id === pick.value)
  const q = Number(qty.value)
  if (!it || q < 1) return
  const ex = lines.value.find((l) => l.id === it.id)
  if (ex) ex.qty += q
  else lines.value.push({ id: it.id, name: it.name, uom: it.uom, qty: q })
  pick.value = ""
  qty.value = 1
}
function removeLine(l) {
  lines.value = lines.value.filter((x) => x.id !== l.id)
}
const totalUnits = computed(() => lines.value.reduce((s, l) => s + l.qty, 0))

async function submit() {
  if (!lines.value.length) return
  error.value = ""
  submitting.value = true
  try {
    done.value = await receiveGoods({
      lines: lines.value.map((l) => ({ item_code: l.id, qty: l.qty })),
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
  lines.value = []
  supplier.value = ""
  note.value = ""
  done.value = null
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

  <!-- BODY -->
  <div class="flex-1 overflow-y-auto p-3 md:p-4 flex flex-col gap-4">
    <p v-if="error" class="text-xs text-pos-danger font-bold">{{ error }}</p>

    <!-- supplier / note -->
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm px-4 py-4 grid grid-cols-1 md:grid-cols-2 gap-4">
      <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">المورّد (اختياري)</span>
        <input v-model="supplier" type="text" placeholder="مثال: مخبز الأندلس" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
      <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">ملاحظة (اختياري)</span>
        <input v-model="note" type="text" placeholder="رقم الفاتورة / ملاحظة" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
    </div>

    <!-- add item -->
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm px-4 py-4">
      <p class="text-xs font-extrabold text-gray-700 mb-2 pr-2 border-r-4 border-pos-brand">إضافة صنف مستلَم</p>
      <div class="flex flex-col md:flex-row gap-2">
        <select v-model="pick" class="flex-1 bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]">
          <option value="">اختر صنفاً...</option>
          <option v-for="it in catalog" :key="it.id" :value="it.id">{{ it.name }}</option>
        </select>
        <input v-model.number="qty" type="number" min="1" dir="ltr" class="w-full md:w-28 bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm font-bold text-gray-700 text-center focus:outline-none focus:border-pos-brand min-h-[44px]" />
        <button @click="addLine" :disabled="!pick" class="bg-pos-brand text-white text-sm font-extrabold px-5 py-2.5 rounded-xl min-h-[44px] flex items-center justify-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40">
          <i class="fa-solid fa-plus text-sm"></i> إضافة
        </button>
      </div>
    </div>

    <!-- received lines -->
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm flex-1 flex flex-col overflow-hidden">
      <div class="grid grid-cols-12 bg-pos-brand-light/70 border-b border-pos-border px-4 py-2.5 flex-shrink-0 rounded-t-xl2">
        <div class="col-span-7 text-xs font-extrabold text-gray-600">الصنف المستلَم</div>
        <div class="col-span-3 text-xs font-extrabold text-gray-600">الكمية</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600 text-center">حذف</div>
      </div>
      <div class="divide-y divide-pos-border">
        <div v-for="l in lines" :key="l.id" class="grid grid-cols-12 px-4 py-3 items-center">
          <div class="col-span-7 text-sm font-bold text-gray-800">{{ l.name }}</div>
          <div class="col-span-3 text-sm font-extrabold text-pos-brand-dark">{{ ar(l.qty) }} {{ l.uom }}</div>
          <div class="col-span-2 flex justify-center">
            <button @click="removeLine(l)" class="pos-btn w-8 h-8 bg-pos-danger-light rounded-lg flex items-center justify-center hover:bg-pos-danger hover:text-white text-pos-danger transition-colors"><i class="fa-solid fa-trash text-xs"></i></button>
          </div>
        </div>
        <div v-if="!lines.length" class="text-center text-pos-muted py-16 font-semibold">
          <i class="fa-solid fa-dolly text-2xl mb-2 block opacity-60"></i>
          لم تُضَف أصناف بعد — اختر صنفاً وأضِف الكمية المستلَمة
        </div>
      </div>
      <div v-if="lines.length" class="bg-pos-brand-light/40 border-t border-pos-border px-4 py-2.5 flex items-center justify-between flex-shrink-0 rounded-b-xl2 mt-auto">
        <span class="text-xs text-pos-muted font-semibold">{{ ar(lines.length) }} أصناف</span>
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
