"""Force-correct Arabic for strings where ERPNext's own ar translation is wrong or awkward.

The app CSV (losand/translations/ar.csv) covers every losand-specific label, but ERPNext is
installed AFTER losand, so its translations override the app CSV for shared strings. User
translations (Translation doctype) load last and win, so the genuinely-wrong ones are fixed here.

Idempotent — safe to re-run. Wire into migrate via after_migrate hook if desired.
"""

import frappe

LANG = "ar"

# Only the strings where ERPNext's ar is wrong/broken/awkward for our doctypes.
OVERRIDES = {
	"Draft": "مسودة",          # ERPNext: مشروع (= project)
	"Transferred": "محوّلة",    # ERPNext: نقل
	"Issued": "مصروفة",        # ERPNext: نشر (= published)
	"Completed": "مكتملة",      # ERPNext: أكتمل
	"Failed": "فاشلة",          # ERPNext: باءت بالفشل
	"Amount": "المبلغ",         # ERPNext: كمية (= quantity)
	"Consumed Qty": "الكمية المستهلكة",  # ERPNext: تستهلك الكمية (broken)
}


def run():
	for source, translated in OVERRIDES.items():
		name = frappe.db.get_value(
			"Translation", {"language": LANG, "source_text": source, "context": ["in", ["", None]]}, "name"
		)
		if name:
			doc = frappe.get_doc("Translation", name)
			if doc.translated_text != translated:
				doc.translated_text = translated
				doc.save(ignore_permissions=True)
		else:
			frappe.get_doc(
				{
					"doctype": "Translation",
					"language": LANG,
					"source_text": source,
					"translated_text": translated,
				}
			).insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()
	print(f"Seeded {len(OVERRIDES)} Arabic translation overrides.")
