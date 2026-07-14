<script setup>
import { ref, computed, onMounted } from "vue"
import { useRouter } from "vue-router"
import { getShiftInvoices, returnInvoice, editInvoice, cancelInvoice } from "@/lib/api"
import { pos } from "@/stores/pos"
import { setPendingEdit } from "@/stores/pendingEdit"

const router = useRouter()
const invoices = ref([])
const loading = ref(true)
const loadError = ref("")
const busy = ref("") // invoice name currently being acted on
const actionError = ref("")
const confirming = ref(null) // { invoice, action } awaiting a second tap

// Search + filter run client-side: get_shift_invoices already returns only the
// current shift's invoices, so the list is small and a server round-trip per
// keystroke would buy nothing.
const search = ref("")
const statusFilter = ref("all")
const STATUS_FILTERS = [
  { key: "all", label: "الكل" },
  { key: "sales", label: "مبيعات" },
  { key: "returns", label: "مرتجعات" },
  { key: "cancelled", label: "ملغاة" },
]
// docstatus 1 = submitted (live), 2 = cancelled/voided.
const matchesStatus = (inv, key) =>
  ({
    all: true,
    sales: inv.docstatus === 1 && !inv.is_return,
    returns: inv.docstatus === 1 && !!inv.is_return,
    cancelled: inv.docstatus === 2,
  })[key]
const visibleInvoices = computed(() => {
  const term = search.value.trim().toLocaleLowerCase()
  return invoices.value.filter((inv) => {
    if (!matchesStatus(inv, statusFilter.value)) return false
    if (!term) return true
    // Invoice no. (incl. the "-1" amendment suffix), customer, or table.
    return [inv.name, inv.customer, inv.po_no].some((field) => (field || "").toLocaleLowerCase().includes(term))
  })
})

const isManager = () => !!pos.config?.is_pos_manager
const formatMoney = (value) =>
  `${Number(value || 0).toFixed(2)} ${pos.config?.currency_symbol || pos.config?.currency || "د.ل"}`

async function load() {
  loading.value = true
  loadError.value = ""
  try {
    invoices.value = await getShiftInvoices()
  } catch (e) {
    loadError.value = e.message
  } finally {
    loading.value = false
  }
}
onMounted(load)

function printInvoice(name) {
  const params = new URLSearchParams({
    doctype: "Sales Invoice",
    name,
    format: pos.config?.print_format,
    trigger_print: "1",
  })
  window.open(`/printview?${params.toString()}`, "_blank")
}

// Return/edit/cancel reverse a submitted invoice's stock+GL impact — require an
// explicit second tap on the same row instead of a native confirm() dialog.
function askConfirm(invoice, action) {
  confirming.value = { invoice, action }
}
function cancelConfirm() {
  confirming.value = null
}

async function doReturn(invoice) {
  busy.value = invoice
  actionError.value = ""
  try {
    await returnInvoice(invoice)
    confirming.value = null
    await load()
  } catch (e) {
    actionError.value = e.message
  } finally {
    busy.value = ""
  }
}

async function doEdit(invoice) {
  busy.value = invoice
  actionError.value = ""
  try {
    const res = await editInvoice(invoice)
    setPendingEdit(res.cart, res.table, res.amended_from)
    router.push("/")
  } catch (e) {
    actionError.value = e.message
    busy.value = ""
  }
}

async function doCancel(invoice) {
  busy.value = invoice
  actionError.value = ""
  try {
    await cancelInvoice(invoice)
    confirming.value = null
    await load()
  } catch (e) {
    actionError.value = e.message
  } finally {
    busy.value = ""
  }
}
</script>

<template>
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-file-invoice text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">فواتير الوردية الحالية</h1>
        <p class="text-xs text-pos-muted font-semibold">{{ pos.config?.pos_profile || "…" }}</p>
      </div>
    </div>
    <button
      @click="load"
      class="pos-btn bg-pos-canvas border border-pos-border text-gray-600 text-xs font-bold px-3 py-2 rounded-xl min-h-[40px] flex items-center gap-1.5 hover:border-pos-brand hover:text-pos-brand transition-colors"
    >
      <i class="fa-solid fa-rotate text-xs"></i> تحديث
    </button>
  </header>

  <div class="flex-1 overflow-y-auto p-3 md:p-4">
    <div v-if="loading" class="text-center text-pos-muted py-16">
      <i class="fa-solid fa-spinner fa-spin text-2xl"></i>
    </div>
    <div v-else-if="loadError" class="bg-pos-danger-light border border-pos-danger/30 text-pos-danger rounded-xl px-4 py-3 text-sm font-bold max-w-2xl mx-auto">
      <i class="fa-solid fa-triangle-exclamation ml-2"></i>{{ loadError }}
    </div>
    <div v-else-if="!invoices.length" class="text-center text-pos-muted py-16 font-semibold">
      <i class="fa-solid fa-receipt text-2xl mb-2 block opacity-60"></i>
      لا توجد فواتير في هذه الوردية بعد
    </div>

    <div v-else class="max-w-3xl mx-auto flex flex-col gap-2">
      <p v-if="actionError" class="bg-pos-danger-light border border-pos-danger/30 text-pos-danger rounded-xl px-4 py-2.5 text-sm font-bold">
        <i class="fa-solid fa-triangle-exclamation ml-2"></i>{{ actionError }}
      </p>

      <!-- Search + status filter -->
      <div class="flex items-center gap-2 flex-wrap mb-1">
        <div class="relative flex-1 min-w-[180px]">
          <input
            v-model="search"
            type="text"
            placeholder="بحث برقم الفاتورة أو العميل أو الطاولة..."
            class="w-full bg-pos-surface border border-pos-border rounded-xl pr-4 pl-9 py-2 text-sm focus:outline-none focus:border-pos-brand text-gray-700 min-h-[44px]"
          />
          <i class="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-pos-muted text-sm"></i>
          <button
            v-if="search"
            @click="search = ''"
            class="absolute left-8 top-1/2 -translate-y-1/2 text-pos-muted hover:text-pos-danger transition-colors"
          >
            <i class="fa-solid fa-xmark text-xs"></i>
          </button>
        </div>
        <div class="flex items-center gap-1.5">
          <button
            v-for="f in STATUS_FILTERS"
            :key="f.key"
            @click="statusFilter = f.key"
            class="text-xs font-bold px-3 py-2 rounded-xl min-h-[44px] border transition-colors"
            :class="statusFilter === f.key ? 'bg-pos-brand text-white border-pos-brand shadow-sm shadow-pos-brand/30' : 'bg-pos-surface border-pos-border text-gray-600 hover:border-pos-brand hover:text-pos-brand'"
          >
            {{ f.label }}
          </button>
        </div>
      </div>

      <div v-if="!visibleInvoices.length" class="text-center text-pos-muted py-16 font-semibold">
        <i class="fa-solid fa-magnifying-glass-minus text-2xl mb-2 block opacity-60"></i>
        لا توجد فواتير مطابقة
      </div>

      <div
        v-for="inv in visibleInvoices"
        :key="inv.name"
        class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm px-4 py-3 flex items-center justify-between gap-3 flex-wrap"
      >
        <div class="min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="font-extrabold text-gray-800 text-sm">#{{ inv.name }}</span>
            <span v-if="inv.is_return" class="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-pos-amber-light text-pos-amber">مرتجع</span>
            <span v-if="inv.docstatus === 2" class="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-pos-danger-light text-pos-danger">ملغاة</span>
          </div>
          <p class="text-xs text-pos-muted font-semibold mt-0.5">
            {{ inv.customer }}
            <template v-if="inv.po_no"> · <i class="fa-solid fa-chair text-[10px]"></i> {{ inv.po_no }}</template>
          </p>
        </div>

        <div class="flex items-center gap-3">
          <span class="font-extrabold text-pos-brand-dark text-sm">{{ formatMoney(inv.grand_total) }}</span>

          <div v-if="confirming?.invoice === inv.name" class="flex items-center gap-1.5">
            <span class="text-[11px] font-bold text-pos-danger">تأكيد؟</span>
            <button
              @click="confirming.action === 'return' ? doReturn(inv.name) : doCancel(inv.name)"
              :disabled="busy === inv.name"
              class="bg-pos-danger text-white text-[11px] font-bold px-2.5 py-1.5 rounded-lg hover:bg-pos-danger/90 disabled:opacity-40"
            >
              {{ busy === inv.name ? "…" : "تأكيد" }}
            </button>
            <button @click="cancelConfirm" class="text-pos-muted text-[11px] font-bold px-2 py-1.5 hover:text-gray-700">إلغاء</button>
          </div>
          <div v-else class="flex items-center gap-1.5">
            <button
              @click="printInvoice(inv.name)"
              title="طباعة"
              class="w-8 h-8 rounded-lg border border-pos-border bg-pos-canvas text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors flex items-center justify-center"
            >
              <i class="fa-solid fa-print text-xs"></i>
            </button>
            <template v-if="isManager() && inv.docstatus === 1 && !inv.is_return">
              <button
                @click="askConfirm(inv.name, 'return')"
                title="إرجاع"
                class="w-8 h-8 rounded-lg border border-pos-amber/40 bg-pos-amber-light text-pos-amber hover:bg-pos-amber hover:text-white transition-colors flex items-center justify-center"
              >
                <i class="fa-solid fa-rotate-left text-xs"></i>
              </button>
              <button
                @click="doEdit(inv.name)"
                :disabled="busy === inv.name"
                title="تعديل"
                class="w-8 h-8 rounded-lg border border-pos-border bg-pos-canvas text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors flex items-center justify-center disabled:opacity-40"
              >
                <i class="fa-solid" :class="busy === inv.name ? 'fa-spinner fa-spin' : 'fa-pen'"></i>
              </button>
              <button
                @click="askConfirm(inv.name, 'cancel')"
                title="إلغاء الفاتورة"
                class="w-8 h-8 rounded-lg border border-pos-danger/30 bg-pos-danger-light text-pos-danger hover:bg-pos-danger hover:text-white transition-colors flex items-center justify-center"
              >
                <i class="fa-solid fa-ban text-xs"></i>
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
