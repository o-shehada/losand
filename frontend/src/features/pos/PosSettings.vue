<script setup>
import { ref, reactive, computed } from "vue"
import { cur } from "@/lib/currency"
import { BRANCH, ar } from "./data"

const toggles = reactive({
  print: true,
  kds: true,
  stock: true,
  discount: true,
  pin: true,
  offline: false,
  refund: false,
})

const toggleRows = [
  { key: "print", icon: "fa-print", bg: "bg-pos-brand-light", fg: "text-pos-brand", title: "طباعة الفاتورة تلقائياً", sub: "طباعة عند إتمام كل طلب فوراً" },
  { key: "kds", icon: "fa-desktop", bg: "bg-pos-orange-light", fg: "text-pos-orange", title: "شاشة المطبخ (KDS)", sub: "إرسال الطلبات لشاشة المطبخ" },
  { key: "stock", icon: "fa-bell", bg: "bg-pos-amber-light", fg: "text-pos-amber", title: "تنبيهات المخزون المنخفض", sub: "إشعار فوري عند نقص الأصناف" },
  { key: "discount", icon: "fa-tag", bg: "bg-pos-green-light", fg: "text-pos-green", title: "السماح بالخصومات", sub: "تفعيل حقل الخصم في نقطة البيع" },
  { key: "pin", icon: "fa-lock", bg: "bg-pos-danger-light", fg: "text-pos-danger", title: "تأمين إلغاء الطلبات بـ PIN", sub: "يتطلب موافقة المدير لإلغاء أي طلب" },
  { key: "offline", icon: "fa-wifi", bg: "bg-pos-brand-light", fg: "text-pos-brand", title: "وضع العمل دون إنترنت", sub: "حفظ البيانات محلياً ومزامنتها لاحقاً" },
  { key: "refund", icon: "fa-rotate-left", bg: "bg-pos-amber-light", fg: "text-pos-amber", title: "السماح بالاسترداد", sub: "تفعيل خيار استرداد المبالغ للعملاء" },
]
const summaryRows = [
  { key: "print", icon: "fa-print", fg: "text-pos-brand", label: "طباعة تلقائية" },
  { key: "kds", icon: "fa-desktop", fg: "text-pos-orange", label: "شاشة المطبخ" },
  { key: "stock", icon: "fa-bell", fg: "text-pos-amber", label: "تنبيهات المخزون" },
  { key: "discount", icon: "fa-tag", fg: "text-pos-green", label: "الخصومات" },
  { key: "pin", icon: "fa-lock", fg: "text-pos-danger", label: "PIN الإلغاء" },
  { key: "offline", icon: "fa-wifi", fg: "text-pos-brand", label: "وضع أوفلاين" },
  { key: "refund", icon: "fa-rotate-left", fg: "text-pos-amber", label: "الاسترداد" },
]

const copies = ref(1)
const incCopies = () => copies.value < 5 && copies.value++
const decCopies = () => copies.value > 1 && copies.value--

const showSuccess = ref(false)
const pin = reactive({ open: false, label: "", value: "" })
function openPin(label) {
  pin.label = label
  pin.value = ""
  pin.open = true
}
function pressPin(d) {
  if (pin.value.length >= 4) return
  pin.value += d
  if (pin.value.length === 4) setTimeout(() => (pin.open = false), 400)
}
const filledDots = computed(() => pin.value.length)
</script>

<template>
  <!-- HEADER -->
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-gear text-pos-brand text-base"></i></div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">إعدادات الفرع</h1>
        <div class="flex items-center gap-2"><i class="fa-solid fa-store text-pos-brand text-xs"></i><span class="text-xs text-pos-muted font-semibold">{{ BRANCH }}</span></div>
      </div>
    </div>
    <div class="flex items-center gap-2 flex-wrap justify-end">
      <div class="bg-pos-amber/15 border border-pos-amber text-pos-amber text-xs font-bold px-3 py-1.5 rounded-full flex items-center gap-1.5"><i class="fa-solid fa-user-tie text-xs"></i><span>مدير الفرع</span></div>
      <button @click="showSuccess = true" class="pos-btn bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25"><i class="fa-solid fa-floppy-disk text-sm"></i><span>حفظ التغييرات</span></button>
    </div>
  </header>

  <!-- BODY -->
  <div class="flex-1 overflow-y-auto p-3 md:p-4">
    <div class="flex flex-col lg:flex-row gap-4 items-start">
      <!-- FORM -->
      <div class="flex-1 flex flex-col gap-4 min-w-0">
        <!-- basic info -->
        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
          <div class="pos-section-title-bar px-4 py-3 flex items-center gap-3">
            <div class="w-8 h-8 bg-pos-brand rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-store text-white text-sm"></i></div>
            <div><h2 class="font-extrabold text-gray-800 text-sm leading-tight">المعلومات الأساسية</h2><p class="text-[10px] text-pos-muted font-semibold">بيانات التعريف بالفرع</p></div>
            <span class="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-pos-brand-light text-pos-brand border border-pos-brand/30 mr-auto">مطلوب</span>
          </div>
          <div class="px-4 py-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">اسم الفرع <span class="text-pos-danger">*</span></span>
              <input type="text" value="فرع وسط المدينة" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">رمز الفرع</span>
              <input type="text" value="BR-001" readonly class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-pos-muted min-h-[44px]" dir="ltr" /></label>
            <label class="block md:col-span-2"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">الموقع / العنوان <span class="text-pos-danger">*</span></span>
              <input type="text" value="شارع عمر المختار، وسط المدينة، طرابلس" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" /></label>
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">وقت الافتتاح</span>
              <input type="time" value="08:00" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></label>
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">وقت الإغلاق</span>
              <input type="time" value="23:00" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></label>
          </div>
        </div>

        <!-- financials -->
        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
          <div class="pos-section-title-bar px-4 py-3 flex items-center gap-3">
            <div class="w-8 h-8 bg-pos-green rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-coins text-white text-sm"></i></div>
            <div><h2 class="font-extrabold text-gray-800 text-sm leading-tight">الإعدادات المالية</h2><p class="text-[10px] text-pos-muted font-semibold">العملة والضرائب والأسعار</p></div>
          </div>
          <div class="px-4 py-4 flex flex-col gap-4">
            <div class="bg-pos-green-light border border-pos-green/20 rounded-xl2 p-4">
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-extrabold text-gray-700 flex items-center gap-2"><i class="fa-solid fa-percent text-pos-green text-sm"></i> نسبة الضريبة (VAT)</span>
                <span class="bg-pos-green/15 border border-pos-green/30 text-pos-green text-xs font-extrabold px-3 py-1 rounded-full flex items-center gap-1.5"><i class="fa-solid fa-circle-check text-xs"></i> معفى من الضريبة</span>
              </div>
              <p class="text-[11px] text-pos-green font-bold mt-1 flex items-center gap-1.5"><i class="fa-solid fa-circle-info text-[10px]"></i> جميع الأسعار شاملة — لا تُطبَّق ضريبة على المبيعات حالياً ({{ cur }})</p>
            </div>
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">الحد الأدنى للطلب ({{ cur }})</span>
              <input type="number" value="5" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></label>
          </div>
        </div>

        <!-- operations toggles -->
        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
          <div class="pos-section-title-bar px-4 py-3 flex items-center gap-3">
            <div class="w-8 h-8 bg-pos-orange rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-sliders text-white text-sm"></i></div>
            <div><h2 class="font-extrabold text-gray-800 text-sm leading-tight">إعدادات التشغيل</h2><p class="text-[10px] text-pos-muted font-semibold">طباعة، تنبيهات، وضبط العمليات</p></div>
          </div>
          <div class="px-4 py-1 flex flex-col divide-y divide-pos-border">
            <div v-for="row in toggleRows" :key="row.key" class="flex items-center justify-between py-3.5 gap-4">
              <div class="flex items-center gap-3 flex-1 min-w-0">
                <div class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" :class="row.bg"><i class="fa-solid text-sm" :class="[row.icon, row.fg]"></i></div>
                <div class="min-w-0"><p class="text-sm font-bold text-gray-800 leading-tight">{{ row.title }}</p><p class="text-[11px] text-pos-muted font-semibold">{{ row.sub }}</p></div>
              </div>
              <label class="pos-toggle flex-shrink-0">
                <input type="checkbox" v-model="toggles[row.key]" />
                <span class="pos-toggle-slider"></span>
              </label>
            </div>
          </div>
        </div>

        <!-- printer -->
        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
          <div class="pos-section-title-bar px-4 py-3 flex items-center gap-3">
            <div class="w-8 h-8 bg-pos-brand rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-print text-white text-sm"></i></div>
            <div><h2 class="font-extrabold text-gray-800 text-sm leading-tight">إعدادات الطباعة</h2><p class="text-[10px] text-pos-muted font-semibold">تخصيص الفاتورة والطابعة</p></div>
          </div>
          <div class="px-4 py-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">اسم الطابعة</span>
              <input type="text" value="Epson TM-T82III" class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]" dir="ltr" /></label>
            <label class="block"><span class="text-xs font-extrabold text-gray-600 mb-1.5 block">حجم الورق</span>
              <select class="w-full bg-pos-canvas border border-pos-border rounded-xl px-4 py-2.5 text-sm text-gray-700 focus:outline-none focus:border-pos-brand min-h-[44px]"><option>80 مم (معياري)</option><option>58 مم</option></select></label>
            <div class="md:col-span-2">
              <span class="text-xs font-extrabold text-gray-600 mb-1.5 block">عدد نسخ الفاتورة</span>
              <div class="flex items-center gap-2">
                <button @click="decCopies" class="w-10 h-10 bg-pos-canvas border border-pos-border rounded-xl flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold text-lg leading-none">−</button>
                <span class="w-16 text-center bg-pos-canvas border border-pos-border rounded-xl py-2.5 text-sm font-extrabold text-gray-700">{{ ar(copies) }}</span>
                <button @click="incCopies" class="w-10 h-10 bg-pos-canvas border border-pos-border rounded-xl flex items-center justify-center text-gray-600 hover:border-pos-brand hover:text-pos-brand transition-colors font-bold text-lg leading-none">+</button>
              </div>
            </div>
          </div>
        </div>

        <!-- danger zone -->
        <div class="bg-pos-surface rounded-xl2 border border-pos-danger/30 shadow-sm overflow-hidden mb-4">
          <div class="px-4 py-3 flex items-center gap-3 bg-pos-danger-light/60 border-b border-pos-danger/20" style="border-right: 4px solid #e84c3d">
            <div class="w-8 h-8 bg-pos-danger rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-triangle-exclamation text-white text-sm"></i></div>
            <div><h2 class="font-extrabold text-pos-danger text-sm leading-tight">منطقة الخطر</h2><p class="text-[10px] text-pos-muted font-semibold">إجراءات لا يمكن التراجع عنها — تتطلب PIN المدير</p></div>
          </div>
          <div class="px-4 py-4 flex flex-col md:flex-row gap-3">
            <button @click="openPin('إعادة ضبط الوردية — أدخل رمز PIN للتأكيد')" class="flex-1 flex items-center gap-3 bg-pos-canvas border border-pos-danger/30 rounded-xl px-4 py-3 min-h-[56px] hover:bg-pos-danger-light hover:border-pos-danger transition-colors text-right">
              <div class="w-9 h-9 bg-pos-danger-light rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-rotate text-pos-danger text-sm"></i></div>
              <div><p class="text-sm font-extrabold text-pos-danger leading-tight">إعادة ضبط الوردية</p><p class="text-[11px] text-pos-muted font-semibold">مسح بيانات الوردية الحالية</p></div>
            </button>
            <button @click="openPin('مسح بيانات الفرع — أدخل رمز PIN للتأكيد')" class="flex-1 flex items-center gap-3 bg-pos-canvas border border-pos-danger/30 rounded-xl px-4 py-3 min-h-[56px] hover:bg-pos-danger-light hover:border-pos-danger transition-colors text-right">
              <div class="w-9 h-9 bg-pos-danger-light rounded-xl flex items-center justify-center flex-shrink-0"><i class="fa-solid fa-trash-can text-pos-danger text-sm"></i></div>
              <div><p class="text-sm font-extrabold text-pos-danger leading-tight">مسح بيانات الفرع</p><p class="text-[11px] text-pos-muted font-semibold">حذف الكاش والبيانات المحلية</p></div>
            </button>
          </div>
        </div>
      </div>

      <!-- SUMMARY COLUMN -->
      <div class="w-full lg:w-72 flex-shrink-0 flex flex-col gap-4">
        <div class="pos-preview-card rounded-xl2 p-4 text-white shadow-lg shadow-pos-brand/30 relative overflow-hidden">
          <div class="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-full -translate-x-10 -translate-y-10"></div>
          <div class="relative z-10">
            <div class="flex items-center gap-2.5 mb-3">
              <div class="w-10 h-10 bg-white/25 rounded-xl2 flex items-center justify-center"><i class="fa-solid fa-store text-white text-base"></i></div>
              <div><p class="text-[10px] font-semibold text-white/70">معاينة الفرع</p><p class="text-sm font-extrabold leading-tight">فرع وسط المدينة</p></div>
            </div>
            <div class="flex flex-col gap-2 text-white/85">
              <div class="flex items-center gap-2"><i class="fa-solid fa-location-dot text-xs w-4 text-center"></i><span class="text-xs font-semibold">شارع عمر المختار، طرابلس</span></div>
              <div class="flex items-center gap-2"><i class="fa-solid fa-clock text-xs w-4 text-center"></i><span class="text-xs font-semibold">08:00 — 23:00</span></div>
              <div class="flex items-center gap-2"><i class="fa-solid fa-money-bill text-xs w-4 text-center"></i><span class="text-xs font-semibold">{{ cur }} — بدون ضريبة</span></div>
            </div>
            <div class="mt-3 pt-3 border-t border-white/25 flex items-center gap-1.5">
              <div class="w-2 h-2 bg-green-200 rounded-full pos-sync-dot"></div><span class="text-[11px] font-bold text-white/80">متزامن — آخر تحديث الآن</span>
            </div>
          </div>
        </div>

        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm p-4">
          <h3 class="text-xs font-extrabold text-gray-700 mb-3 flex items-center gap-2"><i class="fa-solid fa-list-check text-pos-brand"></i> ملخص الإعدادات</h3>
          <div class="flex flex-col gap-2.5">
            <div v-for="row in summaryRows" :key="row.key" class="flex items-center justify-between">
              <span class="text-xs font-semibold text-gray-600 flex items-center gap-1.5"><i class="fa-solid text-[10px]" :class="[row.icon, row.fg]"></i> {{ row.label }}</span>
              <span class="text-[11px] font-extrabold flex items-center gap-1" :class="toggles[row.key] ? 'text-pos-green' : 'text-pos-muted'">
                <i class="fa-solid text-[10px]" :class="toggles[row.key] ? 'fa-circle-check' : 'fa-circle-xmark'"></i> {{ toggles[row.key] ? "مفعّل" : "معطّل" }}
              </span>
            </div>
          </div>
        </div>

        <div class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm p-4 flex flex-col gap-2.5">
          <button @click="showSuccess = true" class="pos-btn w-full bg-pos-brand text-white font-extrabold text-sm py-3 rounded-xl min-h-[48px] flex items-center justify-center gap-2 hover:bg-pos-brand-dark transition-colors shadow-md shadow-pos-brand/25"><i class="fa-solid fa-floppy-disk"></i> حفظ جميع التغييرات</button>
          <button class="w-full bg-pos-canvas border border-pos-border text-gray-600 font-bold text-sm py-3 rounded-xl min-h-[44px] flex items-center justify-center gap-2 hover:border-pos-danger hover:text-pos-danger transition-colors"><i class="fa-solid fa-xmark text-sm"></i> تجاهل التغييرات</button>
        </div>
      </div>
    </div>
  </div>

  <!-- SUCCESS OVERLAY -->
  <div v-if="showSuccess" class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4" style="backdrop-filter: blur(4px)" @click.self="showSuccess = false">
    <div class="pos-modal bg-pos-surface rounded-xl2 shadow-2xl border border-pos-border p-8 flex flex-col items-center gap-4 max-w-sm w-full text-center">
      <div class="w-16 h-16 bg-pos-brand-light rounded-full flex items-center justify-center"><i class="fa-solid fa-circle-check text-pos-brand text-3xl"></i></div>
      <div><h3 class="font-extrabold text-gray-800 text-lg">تم الحفظ بنجاح!</h3><p class="text-sm text-pos-muted font-semibold mt-1">تم تحديث إعدادات الفرع وسيتم مزامنتها قريباً</p></div>
      <button @click="showSuccess = false" class="bg-pos-brand text-white font-extrabold text-sm px-8 py-2.5 rounded-xl min-h-[44px] hover:bg-pos-brand-dark transition-colors w-full">حسناً</button>
    </div>
  </div>

  <!-- PIN SHEET -->
  <div v-if="pin.open" class="fixed inset-0 bg-black/50 z-50 flex items-end justify-center" style="backdrop-filter: blur(4px)" @click.self="pin.open = false">
    <div class="pos-modal bg-pos-surface rounded-t-2xl shadow-2xl border border-pos-border w-full max-w-md p-6">
      <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 bg-pos-danger-light rounded-xl flex items-center justify-center"><i class="fa-solid fa-lock text-pos-danger text-sm"></i></div>
          <div><h3 class="font-extrabold text-gray-800 text-sm">تأكيد هوية المدير</h3><p class="text-[11px] text-pos-muted font-semibold">{{ pin.label }}</p></div>
        </div>
        <button @click="pin.open = false" class="w-8 h-8 bg-pos-canvas border border-pos-border rounded-lg flex items-center justify-center text-pos-muted hover:text-pos-danger hover:border-pos-danger transition-colors"><i class="fa-solid fa-xmark text-sm"></i></button>
      </div>
      <div class="flex justify-center gap-4 my-4">
        <div v-for="i in 4" :key="i" class="w-4 h-4 rounded-full border-2" :class="i <= filledDots ? 'bg-pos-brand border-pos-brand' : 'bg-pos-canvas border-pos-border'"></div>
      </div>
      <div class="grid grid-cols-3 gap-2.5 mt-2">
        <button v-for="n in [1,2,3,4,5,6,7,8,9]" :key="n" @click="pressPin(String(n))" class="bg-pos-canvas border border-pos-border rounded-xl font-extrabold text-gray-700 text-xl min-h-[56px] hover:bg-pos-brand-light hover:border-pos-brand transition-colors">{{ ar(n) }}</button>
        <div></div>
        <button @click="pressPin('0')" class="bg-pos-canvas border border-pos-border rounded-xl font-extrabold text-gray-700 text-xl min-h-[56px] hover:bg-pos-brand-light hover:border-pos-brand transition-colors">{{ ar(0) }}</button>
        <button @click="pin.value = pin.value.slice(0, -1)" class="bg-pos-danger-light border border-pos-danger/30 rounded-xl flex items-center justify-center min-h-[56px] hover:bg-pos-danger/15 transition-colors"><i class="fa-solid fa-delete-left text-pos-danger text-lg"></i></button>
      </div>
    </div>
  </div>
</template>
