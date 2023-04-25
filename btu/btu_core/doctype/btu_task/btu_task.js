// Copyright (c) 2021-2023, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Task', {

	refresh: function(frm) {
		if (frm.doc.docstatus == 1) {
			// This button reverts the Task from Submitted (read only) back to Draft.
			frm.add_custom_button(__('Unlock (revert to Draft)'), () => frm.events._revert_to_draft(frm));
		}
	},

	button_run_on_webserver(frm) {
		// This is a button defined on the DocType 'BTU Task'
		frm.events._run_task_on_webserver(frm)
	},

	_revert_to_draft(frm) {
		frappe.call({
			doc: frm.doc,
			method: 'revert_to_draft',
			callback: function() {
				frm.reload_doc();
				frm.refresh();
			}
		});
	},

	_run_task_on_webserver(frm) {
		// Call the 'run_now() method on the class document.
		let message = "Running Task '" + frm.doc.name + "' on web server."
		message += " <br> Will send an Alert on completion (do not refresh your browser)."
		frappe.msgprint(message);
		frappe.call({
			doc: frm.doc,
			method: 'run_task_on_webserver',
			callback: function(r) {
				// Note: Variable 'r.message' should be a tuple [ task_id, success, log_id ]

				// let log_message = ` <br> Check log <a href='/app/${frappe.router.slug('BTU Task Log')}/${r.message[2]}'></a>`
				let log_message = ` <br>Check log '${r.message[2]}' for details.`

				if (r.message[1] == true) {
					frappe.show_alert({ message: __('Task Successful' + log_message),
					                    indicator: 'green' });
				}
				else {
					frappe.show_alert({ message: __('Task Failed' + log_message),
					                    indicator: 'red' });
				}
			}
		});
	},

});
