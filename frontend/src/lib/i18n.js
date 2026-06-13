import { computed, ref } from "vue"

export const currentLanguage = ref(window.boot?.lang || "ar")

const localTranslations = {
  ar: {
    "Los Andalus Manufacture": "تصنيع الأندلس",
    "Manufacture Home": "الرئيسية",
    "Food Logger": "تسجيل الإنتاج",
    "Login": "تسجيل الدخول",
    "Email or username": "البريد الإلكتروني أو اسم المستخدم",
    Password: "كلمة المرور",
    "Sign in": "دخول",
    Logout: "تسجيل الخروج",
    "Record production batches, materials, waste, loss, and final cost.": "سجّل دفعات الإنتاج والمواد والهالك والفاقد والتكلفة النهائية.",
    "Raw Materials": "المواد الخام",
    "Production Output": "ناتج الإنتاج",
    "Notes": "ملاحظات",
    "Continue": "متابعة",
    "Production Summary": "ملخص الإنتاج",
    "Quantity": "الكمية",
    "Unit Cost": "تكلفة الوحدة",
    "Total Cost": "التكلفة الإجمالية",
    "I confirm this production batch is accurate.": "أؤكد أن بيانات دفعة الإنتاج صحيحة.",
    "Save Batch": "حفظ الدفعة",
    "Batch Saved": "تم حفظ الدفعة",
    "Start New Batch": "بدء دفعة جديدة",
  },
}

export const direction = computed(() => (currentLanguage.value === "ar" ? "rtl" : "ltr"))

export function setLanguage(language) {
  currentLanguage.value = language
  document.documentElement.lang = language
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr"
}

export function t(source) {
  if (window.__ && typeof window.__ === "function") {
    return window.__(source)
  }
  return localTranslations[currentLanguage.value]?.[source] || source
}
