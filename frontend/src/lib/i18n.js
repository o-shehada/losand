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
