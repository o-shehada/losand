<script setup>
import { ref, computed } from "vue"
import { INVENTORY, stockStatus, itemCat, BRANCH, ar } from "./data"

const search = ref("")
const statusFilter = ref("all")
const showFilter = ref(false)
const showAdd = ref(false)

const rows = computed(() =>
  INVENTORY.filter(
    (it) => (statusFilter.value === "all" || it.status === statusFilter.value) && it.name.includes(search.value.trim()),
  ),
)

const stats = computed(() => ({
  total: INVENTORY.length,
  instock: INVENTORY.filter((i) => i.status === "instock").length,
  lowstock: INVENTORY.filter((i) => i.status === "lowstock").length,
  outstock: INVENTORY.filter((i) => i.status === "outstock").length,
}))

const pct = (it) => Math.min(100, Math.round((it.qty / it.max) * 100))
const filters = [
  { key: "all", label: "الكل", cls: "text-gray-700" },
  { key: "instock", label: "متوفر", cls: "text-pos-green" },
  { key: "lowstock", label: "منخفض", cls: "text-pos-orange" },
  { key: "outstock", label: "نفد", cls: "text-pos-danger" },
]
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0">
        <i class="fa-solid fa-boxes-stacked text-pos-brand text-base"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">إدارة المخزون</h1>
        <div class="flex items-center gap-2">
          <i class="fa-solid fa-store text-pos-brand text-xs"></i>
          <span class="text-xs text-pos-muted font-semibold">{{ BRANCH }}</span>
        </div>
      </div>
    </div>
    <div class="flex items-center gap-2 flex-wrap justify-end">
      <div class="relative">
        <input v-model="search" type="text" placeholder="بحث في المخزون..." class="bg-pos-canvas border border-pos-border rounded-xl pr-4 pl-9 py-2 text-sm focus:outline-none focus:border-pos-brand text-gray-700 w-40 md:w-56 min-h-[44px]" />
        <i class="fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-pos-muted text-sm"></i>
      </div>
      <div class="relative">
        <button @click.stop="showFilter = !showFilter" class="bg-pos-canvas border border-pos-border text-gray-600 text-xs font-bold px-3 py-2 rounded-xl min-h-[44px] flex items-center gap-1.5 hover:border-pos-brand hover:text-pos-brand transition-colors">
          <i class="fa-solid fa-sliders text-xs"></i><span class="hidden md:inline">تصفية</span>
        </button>
        <div v-if="showFilter" class="absolute left-0 top-12 bg-pos-surface border border-pos-border rounded-xl2 shadow-lg z-30 w-48 p-3">
          <p class="text-xs font-extrabold text-gray-700 mb-2">تصفية حسب الحالة</p>
          <div class="flex flex-col gap-1">
            <button v-for="f in filters" :key="f.key" @click="statusFilter = f.key; showFilter = false"
              class="text-right text-xs font-semibold px-2 py-1.5 rounded-lg hover:bg-pos-brand-light transition-colors"
              :class="[f.cls, statusFilter === f.key ? 'bg-pos-brand-light' : '']">
              {{ f.label }}
            </button>
          </div>
        </div>
      </div>
      <div class="pos-shift-pill text-white text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5">
        <i class="fa-solid fa-sun text-yellow-200 text-xs"></i><span>وردية الصباح</span>
      </div>
      <button @click="showAdd = true" class="bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25">
        <i class="fa-solid fa-plus text-sm"></i><span>إضافة صنف</span>
      </button>
    </div>
  </header>

  <!-- STATS -->
  <div class="bg-pos-surface border-b border-pos-border px-4 py-3 flex items-center gap-3 flex-shrink-0 flex-wrap">
    <div class="flex items-center gap-2.5 bg-pos-brand-light border border-pos-brand/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-brand rounded-lg flex items-center justify-center"><i class="fa-solid fa-layer-group text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">إجمالي الأصناف</p><p class="text-sm font-extrabold text-gray-800 leading-tight">{{ ar(stats.total) }} صنف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-green-light border border-pos-green/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-green rounded-lg flex items-center justify-center"><i class="fa-solid fa-circle-check text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">متوفر</p><p class="text-sm font-extrabold text-pos-green leading-tight">{{ ar(stats.instock) }} صنف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-orange-light border border-pos-orange/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-orange rounded-lg flex items-center justify-center"><i class="fa-solid fa-triangle-exclamation text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">مخزون منخفض</p><p class="text-sm font-extrabold text-pos-orange leading-tight">{{ ar(stats.lowstock) }} أصناف</p></div>
    </div>
    <div class="flex items-center gap-2.5 bg-pos-danger-light border border-pos-danger/25 rounded-xl px-3 py-2 min-h-[44px]">
      <div class="w-7 h-7 bg-pos-danger rounded-lg flex items-center justify-center"><i class="fa-solid fa-circle-xmark text-white text-xs"></i></div>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">نفد المخزون</p><p class="text-sm font-extrabold text-pos-danger leading-tight">{{ ar(stats.outstock) }} أصناف</p></div>
    </div>
    <div class="mr-auto flex items-center gap-2 bg-pos-canvas border border-pos-border rounded-xl px-3 py-2 min-h-[44px]">
      <i class="fa-solid fa-rotate text-pos-brand text-xs pos-sync-dot"></i>
      <div><p class="text-[10px] text-pos-muted font-semibold leading-none">آخر تحديث</p><p class="text-xs font-bold text-gray-700 leading-tight">منذ 5 دقائق</p></div>
    </div>
  </div>

  <!-- TABLE -->
  <div class="flex-1 overflow-hidden flex flex-col p-3 md:p-4">
    <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm flex-1 flex flex-col overflow-hidden">
      <!-- table head -->
      <div class="grid grid-cols-12 bg-pos-brand-light/70 border-b border-pos-border px-4 py-2.5 flex-shrink-0 rounded-t-xl2">
        <div class="col-span-4 text-xs font-extrabold text-gray-600">اسم الصنف</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600">الفئة</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600">الكمية</div>
        <div class="col-span-1 text-xs font-extrabold text-gray-600">الوحدة</div>
        <div class="col-span-2 text-xs font-extrabold text-gray-600">الحالة</div>
        <div class="col-span-1 text-xs font-extrabold text-gray-600 text-center">إجراءات</div>
      </div>
      <!-- rows -->
      <div class="flex-1 overflow-y-auto divide-y divide-pos-border">
        <div v-for="it in rows" :key="it.sku" class="pos-table-row grid grid-cols-12 px-4 py-3 items-center" :class="stockStatus(it.status).row">
          <div class="col-span-4 flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-pos-brand-light flex items-center justify-center flex-shrink-0"><i class="fa-solid text-pos-brand text-sm" :class="it.icon"></i></div>
            <div><p class="text-sm font-bold text-gray-800 leading-tight">{{ it.name }}</p><p class="text-[10px] text-pos-muted font-semibold">SKU: {{ it.sku }}</p></div>
          </div>
          <div class="col-span-2"><span class="pos-cat" :class="itemCat(it.cat).pill">{{ itemCat(it.cat).label }}</span></div>
          <div class="col-span-2">
            <p class="text-sm" :class="stockStatus(it.status).qty">{{ ar(it.qty) }} {{ it.unitShort }}</p>
            <div class="w-20 bg-pos-border rounded-full h-1.5 mt-1"><div class="h-1.5 rounded-full" :class="stockStatus(it.status).bar" :style="{ width: pct(it) + '%' }"></div></div>
            <p class="text-[10px] text-pos-muted font-semibold mt-0.5">من {{ ar(it.max) }} {{ it.unitShort }}</p>
          </div>
          <div class="col-span-1"><span class="text-xs font-bold text-gray-600">{{ it.unit }}</span></div>
          <div class="col-span-2">
            <span class="text-[11px] font-extrabold px-2.5 py-1 rounded-full flex items-center gap-1.5 w-fit" :class="stockStatus(it.status).badge">
              <i class="fa-solid text-[10px]" :class="stockStatus(it.status).icon"></i> {{ stockStatus(it.status).label }}
            </span>
          </div>
          <div class="col-span-1 flex items-center justify-center gap-1.5">
            <button class="pos-btn w-8 h-8 bg-pos-brand-light rounded-lg flex items-center justify-center hover:bg-pos-brand hover:text-white text-pos-brand transition-colors"><i class="fa-solid fa-pen text-xs"></i></button>
            <button class="pos-btn w-8 h-8 bg-pos-danger-light rounded-lg flex items-center justify-center hover:bg-pos-danger hover:text-white text-pos-danger transition-colors"><i class="fa-solid fa-trash text-xs"></i></button>
          </div>
        </div>
        <div v-if="!rows.length" class="text-center text-pos-muted py-16 font-semibold">لا توجد أصناف مطابقة</div>
      </div>
      <!-- footer -->
      <div class="bg-pos-brand-light/40 border-t border-pos-border px-4 py-2.5 flex items-center justify-between flex-shrink-0 rounded-b-xl2">
        <span class="text-xs text-pos-muted font-semibold">عرض {{ ar(rows.length) }} من {{ ar(stats.total) }} صنف</span>
        <div class="text-xs text-pos-muted font-semibold">صفحة 1 من 1</div>
      </div>
    </div>
  </div>

  <!-- ADD MODAL -->
  <div v-if="showAdd" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="showAdd = false">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl w-full max-w-lg border border-pos-border">
      <div class="flex items-center justify-between px-5 py-4 border-b border-pos-border bg-pos-brand-light/60 rounded-t-xl2">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 bg-pos-brand rounded-xl flex items-center justify-center"><i class="fa-solid fa-plus text-white text-sm"></i></div>
          <h2 class="font-extrabold text-gray-800 text-base">إضافة صنف جديد</h2>
        </div>
        <button @click="showAdd = false" class="w-8 h-8 bg-pos-canvas border border-pos-border rounded-lg flex items-center justify-center text-pos-muted hover:text-pos-danger hover:border-pos-danger transition-colors"><i class="fa-solid fa-xmark text-sm"></i></button>
      </div>
      <div class="px-5 py-4 flex flex-col gap-3">
        <div>
          <label class="text-xs font-extrabold text-gray-600 mb-1 block">اسم الصنف <span class="text-pos-danger">*</span></label>
          <input type="text" placeholder="مثال: لحم بقري مفروم" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-extrabold text-gray-600 mb-1 block">الفئة <span class="text-pos-danger">*</span></label>
            <select class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]">
              <option>لحوم</option><option>خضروات</option><option>ألبان وبيض</option><option>مشروبات</option><option>جافة</option><option>مخبوزات</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-extrabold text-gray-600 mb-1 block">وحدة القياس <span class="text-pos-danger">*</span></label>
            <select class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]">
              <option>كيلوغرام</option><option>لتر</option><option>علبة</option><option>رغيف</option><option>حبة</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div><label class="text-xs font-extrabold text-gray-600 mb-1 block">الكمية الحالية <span class="text-pos-danger">*</span></label><input type="number" placeholder="0" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></div>
          <div><label class="text-xs font-extrabold text-gray-600 mb-1 block">الكمية القصوى</label><input type="number" placeholder="0" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></div>
        </div>
        <div><label class="text-xs font-extrabold text-gray-600 mb-1 block">رمز الصنف (SKU)</label><input type="text" placeholder="مثال: MTB-001" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></div>
      </div>
      <div class="px-5 py-3.5 border-t border-pos-border flex items-center justify-end gap-2.5 bg-pos-canvas/60 rounded-b-xl2">
        <button @click="showAdd = false" class="bg-pos-canvas border border-pos-border text-gray-600 text-sm font-bold px-5 py-2.5 rounded-xl min-h-[44px] hover:border-pos-danger hover:text-pos-danger transition-colors">إلغاء</button>
        <button @click="showAdd = false" class="bg-pos-brand text-white text-sm font-extrabold px-6 py-2.5 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25"><i class="fa-solid fa-floppy-disk text-sm"></i>حفظ الصنف</button>
      </div>
    </div>
  </div>
</template>
