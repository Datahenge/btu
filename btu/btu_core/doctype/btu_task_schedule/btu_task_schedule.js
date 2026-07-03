// Copyright (c) 2021-2026, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Task Schedule', {
	onload(frm) {
		frm.set_query('queue_name', 'btu.btu_core.form_options.get_rq_queue_names');
		frm.set_query('cron_timezone', 'btu.btu_core.form_options.get_cron_timezones');
	},
});
