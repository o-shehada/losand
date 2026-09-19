// Filters for the branch performance report. Accounting dimensions are appended by
// ERPNext itself (add_dimensions) so a dimension added later shows up here without a
// code change — `branch` already has its own filter below and is skipped.
frappe.query_reports["Los Andalus Branch Performance"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.month_start(),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch",
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
		},
		{
			fieldname: "user",
			label: __("Cashier"),
			fieldtype: "Link",
			options: "User",
		},
	],

	onload: function () {
		erpnext.utils.add_dimensions("Los Andalus Branch Performance", 6);
	},

	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "profit" && data) {
			const color = data.profit < 0 ? "var(--red-500)" : "var(--green-600)";
			value = `<span style="color:${color};font-weight:600">${value}</span>`;
		}
		if (column.fieldname === "cash_difference" && data && data.cash_difference) {
			value = `<span style="color:var(--red-500)">${value}</span>`;
		}
		return value;
	},
};
