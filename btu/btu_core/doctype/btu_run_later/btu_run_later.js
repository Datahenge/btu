// Copyright (c) 2021-2026, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Run Later', {
	onload(frm) {
		frm.set_query('redis_queue_name', 'btu.btu_core.form_options.get_rq_queue_names');
	},
});
