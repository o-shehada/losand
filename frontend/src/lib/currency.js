// Currency comes from ERPNext via the boot context injected in
// losand/www/los-andalus/manufacture.py (Global Defaults default_currency + symbol).
export const currency = window.boot?.currency || "LYD"
export const cur = window.boot?.currency_symbol || "ل.د"
export const factoryName = window.boot?.factory_name || "مصنع الغذاء الحديث"
