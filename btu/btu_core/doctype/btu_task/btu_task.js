// Copyright (c) 2021-2026, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Task', {
	onload(frm) {
		frm.set_query('queue_name', 'btu.btu_core.form_options.get_rq_queue_names');
		if (frm.is_new()) {
			frappe.xcall('btu.btu_core.task_defaults.get_new_task_defaults').then((defaults) => {
				if (!defaults) {
					return;
				}
				for (const [fieldname, value] of Object.entries(defaults)) {
					frm.set_value(fieldname, value);
				}
			});
		}
	},

	refresh(frm) {
		if (frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Unlock (revert to Draft)'), () => frm.events._revert_to_draft(frm));
		}
	},

	button_run_on_webserver(frm) {
		frm.events._run_task_on_webserver(frm);
	},

	button_push_into_queue(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'btn_push_into_queue',
			freeze: true,
			freeze_message: __('Submitting to Redis Queue...'),
			error: (r) => {
				frappe.msgprint({
					title: __('Queue submission failed'),
					indicator: 'red',
					message: r?.message || __('Unable to submit task to the Redis queue.'),
				});
			},
		});
	},

	_revert_to_draft(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'revert_to_draft',
			callback: function () {
				frm.reload_doc();
				frm.refresh();
			},
		});
	},

	_run_task_on_webserver(frm) {
		let message = "Running Task '" + frm.doc.name + "' on web server.";
		message += " <br> Will send an Alert on completion (do not refresh your browser).";
		frappe.msgprint(message);
		frappe.call({
			doc: frm.doc,
			method: 'run_task_on_webserver',
			callback: function (r) {
				let log_message = ` <br>Check log '${r.message[2]}' for details.`;

				if (r.message[1] == true) {
					frappe.show_alert({
						message: __('Task Successful' + log_message),
						indicator: 'green',
					});
				} else {
					frappe.show_alert({
						message: __('Task Failed' + log_message),
						indicator: 'red',
					});
				}
			},
		});
	},
});
