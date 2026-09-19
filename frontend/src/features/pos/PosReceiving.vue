<script setup>
import { ref, computed, onMounted } from "vue"
import { BRANCH, ar } from "./data"
import { listIncomingTransfers, getTransfer, confirmTransfer } from "@/lib/api"

// استلام الطلبات = inbox of DRAFT Material Transfers already addressed to this branch's
// warehouse (created in the desk by whoever ships). Open one, edit what actually
// arrived, confirm → the draft is submitted and the stock moves. Nothing is created
// here: the transfer is the document.
const transfers = ref([])
const open = ref(null) // the opened transfer {name, items, ...}
const received = ref({}) // row name -> received qty, seeded with the sent qty
const loading = ref(true)
const opening = ref(false)
const submitting = ref(false)
const error = ref("")
const done = ref(null)

async function load() {
  loading.value = true
  error.value = ""
  try {
    const res = await listIncomingTransfers()
    transfers.value = res.transfers || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function openTransfer(name) {
  opening.value = true
  error.value = ""
  try {
    const t = await getTransfer(name)
    received.value = Object.fromEntries(t.items.map((it) => [it.row, it.sent_qty]))
    open.value = t
  } catch (e) {
    error.value = e.message
  } finally {
    opening.value = false
  }
}

const rowQty = (it) => Number(received.value[it.row]) || 0
const lines = computed(() => (open.value?.items || []).filter((it) => rowQty(it) > 0))
const totalUnits = computed(() => lines.value.reduce((s, it) => s + rowQty(it), 0))
const shortRows = computed(() => (open.value?.items || []).filter((it) => rowQty(it) !== it.sent_qty))

async function confirm() {
  if (!lines.value.length) return
  error.value = ""
  submitting.value = true
  try {
    done.value = await confirmTransfer(
      open.value.name,
      (open.value.items || []).map((it) => ({ row: it.row, qty: rowQty(it) })),
    )
    open.value = null
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

function reset() {
  done.value = null
  load() // the confirmed transfer is submitted — it leaves the inbox
}
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <button v-if="open" @click="open = null" class="w-9 h-9 rounded-xl border border-pos-border flex items-center justify-center text-pos-muted hover:text-gray-700">
        <i class="fa-solid fa-arrow-right text-sm"></i>
      </button>
      <div v-else class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-truck-ramp-box text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">استلام الطلبات</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">
            {{ BRANCH }} · <template v-if="open">تحويل #{{ open.name }}</template><template v-else>التحويلات الواردة</template>
          </span>
        </div>
      </div>
    </div>
    <button v-if="open" @click="confirm" :disabled="!lines.length || submitting" class="pos-btn bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40">
      <i class="fa-solid text-sm" :class="submitting ? 'fa-spinner fa-spin' : 'fa-check'"></i><span>{{ submitting ? "جارٍ التأكيد…" : "تأكيد الاستلام" }}</span>
    </button>
    <button v-else @click="load" :disabled="loading" class="pos-btn border border-pos-border text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 text-gray-700 disabled:opacity-40">
      <i class="fa-solid text-sm" :class="loading ? 'fa-spinner fa-spin' : 'fa-rotate-right'"></i><span>تحديث</span>
    </button>
  </header>

  <!-- STATS -->
  <div class="bg-pos-surface border-b border-pos-border px-4 py-3 flex items-center gap-3 flex-shrink-0 flex-wrap">
    <div class="flex items-center gap-2.5 bg-pos-brand-light border border-pos-brand/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-brand rounded-lg flex items-center justify-center"><i class="fa-solid fa-layer-group text-white text-xs"></i></div>
      <div>
        <p class="text-[10px] text-pos-muted font-semibold leading-none">{{ open ? "أصناف التحويل" : "تحويلات بانتظار الاستلام" }}</p>
        <p class="text-sm font-extrabold text-gray-800 leading-tight">{{ ar(open ? open.items.length : transfers.length) }}</p>
      </div>
    </div>
    <template v-if="open">
      <div class="flex items-center gap-2.5 bg-pos-green-light border border-pos-green/25 rounded-xl px-3 py-2 min-h-[44px]">
        <div class="w-7 h-7 bg-pos-green rounded-lg flex items-center justify-center"><i class="fa-solid fa-check text-white text-xs"></i></div>
        <div><p class="text-[10px] text-pos-muted font-semibold leading-none">سيتم استلامها</p><p class="text-sm font-extrabold text-pos-green leading-tight">{{ ar(lines.length) }} صنف</p></div>
      </div>
      <div class="flex items-center gap-2.5 bg-pos-amber-light border border-pos-amber/25 rounded-xl px-3 py-2 min-h-[44px]">
        <div class="w-7 h-7 bg-pos-amber rounded-lg flex items-center justify-center"><i class="fa-solid fa-dolly text-white text-xs"></i></div>
        <div><p class="text-[10px] text-pos-muted font-semibold leading-none">إجمالي الكميات</p><p class="text-sm font-extrabold text-pos-amber leading-tight">{{ ar(totalUnits) }}</p></div>
      </div>
    </template>
    <p v-if="error" class="text-xs text-pos-danger font-bold mr-auto">{{ error }}</p>
  </div>

  <!-- BODY -->
  <div class="flex-1 overflow-y-auto p-3 md:p-4 flex flex-col gap-4">
    <!-- INBOX -->
    <template v-if="!open">
      <div v-if="loading" class="text-center text-pos-muted py-16 font-semibold"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2 block opacity-60"></i> جارٍ التحميل…</div>
      <div v-else-if="!transfers.length" class="text-center text-pos-muted py-16 font-semibold">
        <i class="fa-solid fa-inbox text-2xl mb-2 block opacity-60"></i>
        لا توجد تحويلات بانتظار الاستلام
      </div>
      <button
        v-for="t in transfers"
        :key="t.name"
        @click="openTransfer(t.name)"
        :disabled="opening"
        class="pos-btn bg-pos-surface rounded-xl2 border border-pos-border shadow-sm px-4 py-3.5 flex items-center gap-3 text-right hover:border-pos-brand/50 transition-colors disabled:opacity-50"
      >
        <div class="w-10 h-10 rounded-xl bg-pos-brand-light flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-truck-fast text-pos-brand"></i></div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-extrabold text-gray-800 leading-tight">تحويل #{{ t.name }}</p>
          <p class="text-[11px] text-pos-muted font-semibold truncate">
            {{ t.from_warehouse || "—" }} · {{ t.date }} · {{ ar(t.lines) }} صنف · {{ ar(t.total_qty) }} وحدة
          </p>
        </div>
        <span class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-amber/10 text-pos-amber flex-shrink-0">بانتظار الاستلام</span>
      </button>
    </template>

    <!-- OPENED TRANSFER -->
    <div v-else class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm flex flex-col overflow-hidden">
      <div class="px-4 py-2.5 border-b border-pos-border flex items-center gap-2 bg-pos-brand-light/40 flex-wrap">
        <i class="fa-solid fa-dolly text-pos-brand text-xs"></i>
        <span class="text-sm font-extrabold text-gray-800">أصناف التحويل — من {{ open.from_warehouse || "—" }}</span>
        <span v-if="open.note" class="text-[11px] text-pos-muted font-semibold">· {{ open.note }}</span>
      </div>
      <div class="grid grid-cols-12 bg-pos-brand-light/70 border-b border-pos-border px-4 py-2.5 flex-shrink-0">
        <div class="col-span-5 text-xs font-extrabold text-gray-600">اسم الصنف</div>
        <div class="col-span-3 text-xs font-extrabold text-gray-600">الكمية المرسَلة</div>
        <div class="col-span-4 text-xs font-extrabold text-gray-600">الكمية المستلَمة</div>
      </div>
      <div class="divide-y divide-pos-border">
        <div v-for="it in open.items" :key="it.row" class="grid grid-cols-12 px-4 py-3 items-center">
          <div class="col-span-5 flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-pos-brand-light flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-box text-pos-brand text-sm"></i></div>
            <div><p class="text-sm font-bold text-gray-800 leading-tight">{{ it.name }}</p><p class="text-[10px] text-pos-muted font-semibold">{{ it.id }} · بالنظام {{ ar(it.system_qty) }}</p></div>
          </div>
          <div class="col-span-3 text-sm font-bold text-gray-600">{{ ar(it.sent_qty) }} {{ it.uom }}</div>
          <div class="col-span-4 flex items-center gap-2">
            <input
              v-model.number="received[it.row]"
              type="number"
              min="0"
              step="0.001"
              dir="ltr"
              class="w-24 bg-pos-canvas border rounded-lg px-3 py-2 text-sm font-bold text-center focus:outline-none focus:border-pos-brand min-h-[40px]"
              :class="rowQty(it) > 0 ? 'border-pos-brand/50 text-gray-700' : 'border-pos-border text-pos-muted'"
            />
            <span class="text-xs text-pos-muted font-semibold">{{ it.uom }}</span>
            <span v-if="rowQty(it) !== it.sent_qty" class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-amber/10 text-pos-amber flex items-center gap-1 w-fit">
              <i class="fa-solid text-[10px]" :class="rowQty(it) > it.sent_qty ? 'fa-arrow-up' : 'fa-arrow-down'"></i>
              {{ ar(Math.abs(rowQty(it) - it.sent_qty)) }}
            </span>
          </div>
        </div>
      </div>
      <div class="bg-pos-brand-light/40 border-t border-pos-border px-4 py-2.5 flex items-center justify-between flex-shrink-0 gap-3 flex-wrap">
        <span class="text-xs text-pos-muted font-semibold">{{ ar(lines.length) }} صنف · إجمالي {{ ar(totalUnits) }}</span>
        <span v-if="shortRows.length" class="text-xs font-extrabold text-pos-amber">
          <i class="fa-solid fa-triangle-exclamation ml-1"></i>{{ ar(shortRows.length) }} صنف بكمية مختلفة عن المرسَل — سيُسجَّل الفرق في الملاحظات
        </span>
      </div>
    </div>
  </div>

  <!-- SUCCESS -->
  <div v-if="done" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="reset">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl border border-pos-border p-8 flex flex-col items-center gap-4 max-w-sm w-full text-center">
      <div class="w-16 h-16 bg-pos-green-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-green text-3xl"></i></div>
      <div><h3 class="font-extrabold text-gray-800 text-lg">تم تأكيد الاستلام!</h3><p class="text-sm text-pos-muted font-semibold mt-1">تحويل #{{ done.name }} — {{ ar(done.lines) }} صنف · {{ ar(done.total_qty) }} وحدة.</p></div>
      <button @click="reset" class="bg-pos-brand text-white font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:bg-pos-brand-dark transition-colors w-full">رجوع للتحويلات</button>
    </div>
  </div>
</template>
