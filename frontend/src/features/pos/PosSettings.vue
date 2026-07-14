<script setup>
import { computed, onMounted } from "vue"
import { ensurePos, pos } from "@/stores/pos"

onMounted(ensurePos)

const operationalSettings = computed(() => [
  { key: "hide_unavailable_items", label: "إخفاء الأصناف غير المتوفرة" },
  { key: "hide_images", label: "إخفاء صور الأصناف" },
  { key: "auto_add_item_to_cart", label: "إضافة نتيجة البحث الوحيدة تلقائياً" },
  { key: "update_stock", label: "تحديث المخزون عند البيع" },
  { key: "validate_stock_on_save", label: "التحقق من المخزون عند الحفظ" },
  { key: "print_receipt_on_order_complete", label: "طباعة الإيصال تلقائياً" },
])

const salesSettings = computed(() => [
  { key: "ignore_pricing_rule", label: "تجاهل قواعد التسعير" },
  { key: "allow_rate_change", label: "السماح بتعديل السعر" },
  { key: "allow_discount_change", label: "السماح بتعديل الخصم" },
  { key: "disable_grand_total_to_default_mop", label: "عدم تعبئة الإجمالي تلقائياً لطريقة الدفع" },
  { key: "allow_partial_payment", label: "السماح بالدفع الجزئي" },
  { key: "disable_rounded_total", label: "تعطيل تقريب الإجمالي" },
])

const documentSettings = computed(() => [
  { label: "الشركة", value: pos.config?.company },
  { label: "الدولة", value: pos.config?.country },
  { label: "عنوان الشركة", value: pos.config?.company_address || "الافتراضي" },
  { label: "الحملة", value: pos.config?.campaign || "غير محددة" },
  { label: "المخزن", value: pos.config?.warehouse },
  { label: "العميل الافتراضي", value: pos.config?.customer || "عميل نقدي تلقائي" },
  { label: "قائمة الأسعار", value: pos.config?.price_list },
  { label: "العملة", value: `${pos.config?.currency || ""} ${pos.config?.currency_symbol || ""}`.trim() },
  { label: "الضرائب والرسوم", value: pos.config?.taxes_and_charges || "بدون قالب" },
  { label: "فئة الضريبة", value: pos.config?.tax_category || "غير محددة" },
  { label: "تطبيق الخصم على", value: pos.config?.apply_discount_on },
  { label: "صيغة الطباعة", value: pos.config?.print_format },
  { label: "الترويسة", value: pos.config?.letter_head || "الافتراضية" },
  { label: "عنوان الطباعة", value: pos.config?.print_heading || "الافتراضي" },
  { label: "الشروط والأحكام", value: pos.config?.terms_and_conditions || "غير محددة" },
  { label: "حساب الشطب", value: pos.config?.write_off_account || "الافتراضي" },
  { label: "مركز تكلفة الشطب", value: pos.config?.write_off_cost_center || "الافتراضي" },
  { label: "حد الشطب", value: pos.config?.write_off_limit },
  { label: "حساب مبلغ الباقي", value: pos.config?.account_for_change_amount || "الافتراضي" },
  { label: "حساب الدخل", value: pos.config?.income_account || "الافتراضي" },
  { label: "حساب المصروف", value: pos.config?.expense_account || "الافتراضي" },
  { label: "مركز التكلفة", value: pos.config?.cost_center || "الافتراضي" },
  { label: "المشروع", value: pos.config?.project || "غير محدد" },
])

const editProfileUrl = computed(() =>
  pos.config?.pos_profile ? `/app/pos-profile/${encodeURIComponent(pos.config.pos_profile)}` : "/app/pos-profile",
)
</script>

<template>
  <header class="bg-pos-surface border-b border-pos-border px-4 py-2.5 flex items-center justify-between gap-3 flex-shrink-0 shadow-sm">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 bg-pos-brand-light rounded-xl flex items-center justify-center">
        <i class="fa-solid fa-gear text-pos-brand"></i>
      </div>
      <div>
        <h1 class="font-extrabold text-gray-800 text-base md:text-lg leading-tight">إعدادات نقطة البيع</h1>
        <p class="text-xs text-pos-muted font-semibold">{{ pos.config?.pos_profile || "جارٍ التحميل…" }}</p>
      </div>
    </div>
    <a
      :href="editProfileUrl"
      target="_blank"
      class="pos-btn bg-pos-brand text-white text-xs font-extrabold px-4 py-2 rounded-xl min-h-[44px] flex items-center gap-2 hover:bg-pos-brand-dark transition-colors"
    >
      <i class="fa-solid fa-arrow-up-right-from-square"></i>
      تعديل POS Profile
    </a>
  </header>

  <div class="flex-1 overflow-y-auto p-3 md:p-4">
    <div v-if="!pos.config" class="text-center text-pos-muted py-16">
      <i class="fa-solid fa-spinner fa-spin text-2xl"></i>
    </div>

    <div v-else class="grid grid-cols-1 xl:grid-cols-2 gap-4 max-w-6xl mx-auto">
      <section class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
        <div class="pos-section-title-bar px-4 py-3">
          <h2 class="font-extrabold text-gray-800 text-sm">سلوك الأصناف والمخزون</h2>
        </div>
        <div class="divide-y divide-pos-border px-4">
          <div v-for="setting in operationalSettings" :key="setting.key" class="flex items-center justify-between py-3">
            <span class="text-sm font-bold text-gray-700">{{ setting.label }}</span>
            <span
              class="text-[11px] font-extrabold px-2.5 py-1 rounded-full"
              :class="pos.config[setting.key] ? 'bg-pos-green-light text-pos-green' : 'bg-pos-canvas text-pos-muted'"
            >
              {{ pos.config[setting.key] ? "مفعّل" : "معطّل" }}
            </span>
          </div>
        </div>
      </section>

      <section class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden">
        <div class="pos-section-title-bar px-4 py-3">
          <h2 class="font-extrabold text-gray-800 text-sm">البيع والدفع</h2>
        </div>
        <div class="divide-y divide-pos-border px-4">
          <div v-for="setting in salesSettings" :key="setting.key" class="flex items-center justify-between py-3">
            <span class="text-sm font-bold text-gray-700">{{ setting.label }}</span>
            <span
              class="text-[11px] font-extrabold px-2.5 py-1 rounded-full"
              :class="pos.config[setting.key] ? 'bg-pos-green-light text-pos-green' : 'bg-pos-canvas text-pos-muted'"
            >
              {{ pos.config[setting.key] ? "مفعّل" : "معطّل" }}
            </span>
          </div>
        </div>
      </section>

      <section class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm overflow-hidden xl:col-span-2">
        <div class="pos-section-title-bar px-4 py-3">
          <h2 class="font-extrabold text-gray-800 text-sm">الحسابات والمستندات</h2>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-px bg-pos-border">
          <div v-for="setting in documentSettings" :key="setting.label" class="bg-pos-surface px-4 py-3">
            <p class="text-[10px] font-bold text-pos-muted mb-1">{{ setting.label }}</p>
            <p class="text-sm font-extrabold text-gray-700">{{ setting.value || "غير محدد" }}</p>
          </div>
        </div>
      </section>

      <section class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm p-4">
        <h2 class="font-extrabold text-gray-800 text-sm mb-3">طرق الدفع</h2>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="method in pos.config.payments"
            :key="method.mode_of_payment"
            class="text-xs font-bold px-3 py-2 rounded-xl border"
            :class="method.default ? 'bg-pos-brand text-white border-pos-brand' : 'bg-pos-canvas text-gray-700 border-pos-border'"
          >
            {{ method.mode_of_payment }}
            <small v-if="method.default" class="mr-1 opacity-80">(افتراضي)</small>
          </span>
        </div>
      </section>

      <section class="bg-pos-surface rounded-xl2 border border-pos-border shadow-sm p-4">
        <h2 class="font-extrabold text-gray-800 text-sm mb-3">نطاق الأصناف والعملاء</h2>
        <p class="text-xs text-pos-muted font-semibold mb-1">مجموعات الأصناف</p>
        <p class="text-sm font-bold text-gray-700 mb-3">{{ pos.config.item_groups?.join("، ") || "جميع المجموعات" }}</p>
        <p class="text-xs text-pos-muted font-semibold mb-1">مجموعات العملاء</p>
        <p class="text-sm font-bold text-gray-700 mb-3">{{ pos.config.customer_groups?.join("، ") || "جميع المجموعات" }}</p>
        <p class="text-xs text-pos-muted font-semibold mb-1">المستخدمون المطبّق عليهم</p>
        <p class="text-sm font-bold text-gray-700">
          {{ pos.config.applicable_users?.map((row) => row.user).join("، ") || "جميع المستخدمين" }}
        </p>
      </section>
    </div>
  </div>
</template>
