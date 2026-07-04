<script setup>
import { ref, reactive, computed, onMounted } from "vue"
import { BRANCH, ar } from "./data"
import { getInventory, saveStocktake } from "@/lib/api"

// End-of-shift stocktake: count each item, submit the differences (backend posts
// Material Issue/Receipt to adjust stock to the counted qty).
const rows = ref([])
const counts = reactive({})
const loading = ref(true)
const submitting = ref(false)
const error = ref("")
const done = ref(null)

onMounted(async () => {
  try {
    const inv = await getInventory()
    rows.value = inv.items || []
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const entered = (it) => counts[it.id] !== "" && counts[it.id] != null
const variance = (it) => (entered(it) ? Number(counts[it.id]) - it.system_qty : null)
const countedCount = computed(() => rows.value.filter(entered).length)
const varianceCount = computed(() => rows.value.filter((it) => variance(it)).length)

async function submit() {
  error.value = ""
  const payload = rows.value.filter(entered).map((it) => ({ item_code: it.id, counted: Number(counts[it.id]) }))
  if (!payload.length) {
    error.value = "لم تُدخل أي كمية"
    return
  }
  submitting.value = true
  try {
    done.value = await saveStocktake(payload)
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}

function reset() {
  Object.keys(counts).forEach((k) => delete counts[k])
  done.value = null
}
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-clipboard-check text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">الجرد اليومي</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }} · جرد نهاية الوردية</span>
        </div>
      </div>
    </div>
    <button @click="submit" :disabled="submitting || loading" class="pos-btn bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25 disabled:opacity-40">
      <i class="fa-solid text-sm" :class="submitting ? 'fa-spinner fa-spin' : 'fa-floppy-disk'"></i><span>{{ submitting ? "جارٍ الحفظ…" : "حفظ الجرد" }}</span>
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
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">تم جردها</p><p class="text-sm font-extrabold text-pos-green leading-tight">{{ ar(countedCount) }} صنف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-amber-light border border-pos-amber/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-amber rounded-lg flex items-center justify-center"><i class="fa-solid fa-scale-unbalanced text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">فروقات</p><p class="text-sm font-extrabold text-pos-amber leading-tight">{{ ar(varianceCount) }} صنف</p></div>
    </div>
    <p v-if="error" class="text-xs text-pos-danger font-bold mr-auto">{{ error }}</p>
  </div>

  <!-- TABLE -->
  <div class="flex-1 overflow-hidden flex flex-col p-3 md:p-4">
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm flex-1 flex flex-col overflow-hidden">
      <div class="grid grid-cols-12 bg-pos-brand-light/70 border-b border-pos-border px-4 py-2.5 flex-shrink-0 rounded-t-xl2">
        <div class="col-span-5 text-xs font-extrabold text-gray-600">اسم الصنف</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600">بالنظام</div>
        <div class="col-span-3 text-xs font-extrabold text-gray-600">الكمية الفعلية</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600">الفرق</div>
      </div>
      <div class="flex-1 overflow-y-auto divide-y divide-pos-border">
        <div v-if="loading" class="text-center text-pos-muted py-16 font-semibold"><i class="fa-solid fa-spinner fa-spin text-2xl mb-2 block opacity-60"></i> جارٍ التحميل…</div>
        <div v-for="it in rows" :key="it.id" class="grid grid-cols-12 px-4 py-3 items-center">
          <div class="col-span-5 flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-pos-brand-light flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-box text-pos-brand text-sm"></i></div>
            <div><p class="text-sm font-bold text-gray-800 leading-tight">{{ it.name }}</p><p class="text-[10px] text-pos-muted font-semibold">{{ it.id }}</p></div>
          </div>
          <div class="col-span-2 text-sm font-bold text-gray-600">{{ ar(it.system_qty) }} {{ it.uom }}</div>
          <div class="col-span-3">
            <input
              v-model="counts[it.id]"
              type="number"
              min="0"
              placeholder="—"
              dir="ltr"
              class="w-24 bg-pos-canvas border border-pos-border rounded-lg px-3 py-2 text-sm font-bold text-gray-700 text-center focus:outline-none focus:border-pos-brand min-h-[40px]"
            />
          </div>
          <div class="col-span-2">
            <span v-if="variance(it) === null" class="text-xs text-pos-muted font-semibold">بانتظار الجرد</span>
            <span v-else-if="variance(it) === 0" class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-green/10 text-pos-green flex items-center gap-1 w-fit"><i class="fa-solid fa-circle-check text-[10px]"></i> مطابق</span>
            <span v-else-if="variance(it) > 0" class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-brand/10 text-pos-brand-dark flex items-center gap-1 w-fit"><i class="fa-solid fa-arrow-up text-[10px]"></i> زيادة {{ ar(variance(it)) }}</span>
            <span v-else class="text-[11px] font-extrabold px-2.5 py-1 rounded-full bg-pos-danger/10 text-pos-danger flex items-center gap-1 w-fit"><i class="fa-solid fa-arrow-down text-[10px]"></i> نقص {{ ar(Math.abs(variance(it))) }}</span>
          </div>
        </div>
        <div v-if="!loading && !rows.length" class="text-center text-pos-muted py-16 font-semibold">لا توجد أصناف في المخزن</div>
      </div>
    </div>
  </div>

  <!-- SUCCESS -->
  <div v-if="done" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="reset">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl border border-pos-border p-8 flex flex-col items-center gap-4 max-w-sm w-full text-center">
      <div class="w-16 h-16 bg-pos-green-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-green text-3xl"></i></div>
      <div><h3 class="font-extrabold text-gray-800 text-lg">تم حفظ الجرد!</h3><p class="text-sm text-pos-muted font-semibold mt-1">جُرد {{ ar(done.counted) }} صنف — {{ ar((done.entries || []).length) }} حركة تسوية.</p></div>
      <button @click="reset" class="bg-pos-brand text-white font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:bg-pos-brand-dark transition-colors w-full">حسناً</button>
    </div>
  </div>
</template>
