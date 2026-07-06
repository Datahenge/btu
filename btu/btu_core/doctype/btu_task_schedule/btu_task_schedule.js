// Copyright (c) 2021-2026, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Task Schedule', {
	onload(frm) {
		frm.set_query('queue_name', 'btu.btu_core.form_options.get_rq_queue_names');
		btu_load_timezone_options(frm);
	},
});

/**
 * Fetch the IANA timezone list from the BTU Redis cache and populate the
 * cron_timezone Autocomplete field.  Results are stored on the frappe
 * namespace so repeated form opens within the same browser session make
 * only one round-trip to the server.
 */
function btu_load_timezone_options(frm) {
	const ctrl = frm.fields_dict['cron_timezone'];
	if (!ctrl || typeof ctrl.set_data !== 'function') return;

	if (frappe._btu_timezones) {
		ctrl.set_data(frappe._btu_timezones);
		return;
	}

	frappe.call({
		method: 'btu.btu_core.form_options.get_cron_timezones',
		callback(r) {
			if (r.message && r.message.length) {
				frappe._btu_timezones = r.message;
				ctrl.set_data(r.message);
			}
		},
	});
}
