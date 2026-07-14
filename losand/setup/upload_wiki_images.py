"""Upload manufacturing wiki screenshots as public Files.

Runs automatically on `bench migrate` (see hooks.after_migrate). Safe to
call repeatedly: files are matched and reused by name instead of duplicated.

Run manually:
    bench --site <site> execute losand.setup.upload_wiki_images.run
"""

from pathlib import Path

import frappe


def _images_dir():
    return Path(__file__).resolve().parents[2] / "docs" / "wiki" / "manufacturing" / "images"


def run():
    if "wiki" not in frappe.get_installed_apps():
        return {}

    urls = {}
    for path in sorted(_images_dir().glob("*.png")):
        content = path.read_bytes()
        existing = frappe.db.get_value("File", {"file_name": path.name, "is_private": 0}, "name")
        if existing:
            file_doc = frappe.get_doc("File", existing)
        else:
            file_doc = frappe.get_doc({
                "doctype": "File",
                "file_name": path.name,
                "is_private": 0,
                "content": content,
            })
            file_doc.insert(ignore_permissions=True)
        urls[path.name] = file_doc.file_url
    frappe.db.commit()
    return urls
