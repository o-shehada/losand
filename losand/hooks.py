app_name = "losand"
app_title = "Los Andalus App"
app_publisher = "ARD"
app_description = "Los Andalus ERP App"
app_email = "o.shehada@ard.ly"
app_license = "mit"

# Branding
# ------------------
# App logo shown in the Desk navbar and on the login page
app_logo_url = "/assets/losand/images/losand-logo.jpg"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "losand",
# 		"logo": "/assets/losand/logo.png",
# 		"title": "Los Andalus App",
# 		"route": "/losand",
# 		"has_permission": "losand.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/losand/css/losand.css"
# app_include_js = "/assets/losand/js/losand.js"

# include js, css files in header of web template
# web_include_css = "/assets/losand/css/losand.css"
# web_include_js = "/assets/losand/js/losand.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "losand/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "losand/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Website Route Rules
# -------------------

website_route_rules = [
	{"from_route": "/los-andalus/manufacture/<path:app_path>", "to_route": "los-andalus/manufacture"},
	{"from_route": "/los-andalus/pos/<path:app_path>", "to_route": "los-andalus/pos"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "losand.utils.jinja_methods",
# 	"filters": "losand.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "losand.install.before_install"
# after_install = "losand.install.after_install"

# Re-seed Arabic translation overrides (ERPNext ar overrides our app CSV for shared strings).
after_migrate = ["losand.setup.arabic_translations.run"]

# Fixtures
# --------
# Custom Fields that travel with the app (applied on every `bench migrate`).
fixtures = [
	{
		"dt": "Custom Field",
		"filters": [["name", "in", [
			"Item-is_final_product",
			"Item-product_category",
			"Item-is_raw_material",
			"Item-classification",
			"Stock Entry-custom_workbench",
		]]],
	},
	{
		"dt": "Number Card",
		"filters": [["name", "in", [
			"LA Batches Today",
			"LA Total Produced",
			"LA Production Cost",
			"LA FG Stock Value",
		]]],
	},
	{
		"dt": "Dashboard Chart",
		"filters": [["name", "in", [
			"LA Daily Production",
			"LA Batches by Status",
		]]],
	},
]

# Uninstallation
# ------------

# before_uninstall = "losand.uninstall.before_uninstall"
# after_uninstall = "losand.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "losand.utils.before_app_install"
# after_app_install = "losand.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "losand.utils.before_app_uninstall"
# after_app_uninstall = "losand.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "losand.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"losand.tasks.all"
# 	],
# 	"daily": [
# 		"losand.tasks.daily"
# 	],
# 	"hourly": [
# 		"losand.tasks.hourly"
# 	],
# 	"weekly": [
# 		"losand.tasks.weekly"
# 	],
# 	"monthly": [
# 		"losand.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "losand.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "losand.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "losand.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["losand.utils.before_request"]
# after_request = ["losand.utils.after_request"]

# Job Events
# ----------
# before_job = ["losand.utils.before_job"]
# after_job = ["losand.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"losand.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []
