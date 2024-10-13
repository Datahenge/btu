/*
	Copyright (c) 2022-2024, Datahenge LLC and contributors
	For license information, please see LICENSE

	List Page for DocType 'BTU Task Log'
*/

frappe.listview_settings['BTU Task Log'] = {

	onload: function (listview) {
		// Add a button for cleaning up older Log records:
		listview.page.add_inner_button(__("Delete Log Records by Dates"), function () {
			delete_log_records(listview);
		})
		.addClass("btn-warning").css({'color':'darkred','font-weight': 'normal'});			
	}
};

function delete_log_records(listview) {

	// Create a dialog to capture the user's From Date and To Dates.
	var my_dialog = new frappe.ui.Dialog({
		title: 'Delete Log Records',
		width: 100,
		fields: [
			{
				'fieldtype': 'Date',
				'label': __('From Date'),
				'fieldname': 'from_date',
				reqd: 1
			},
			{
				'fieldtype': 'Date',
				'label': __('To Date'),
				'fieldname': 'to_date',
				reqd: 1
			}
		]
	});

	// Assign a primary action to the dialog, and handle the callback:
	my_dialog.set_primary_action(__('Run'), args => {

		if (!args.from_date || !args.to_date) {
			frappe.msgprint("From Date and To Date are mandatory.")
			return;
		}

		if (args.from_date > args.to_date) {
			frappe.msgprint("Value of 'From Date' cannot be greater than value of 'To Date'");
			return;
		}

		frappe.call({
			method: 'btu.btu_core.doctype.btu_task_log.btu_task_log.delete_logs_by_dates',
 			// Note to Developers: Ensure the Python function has identical argument names as below.
			args: { from_date: args.from_date,
				    to_date: args.to_date
			}, 
			callback: function(r) {
				if (r.message) {
					let user_message = `Deleted ${r.message} records from BTU Task Log.`;  // have to use backticks for template literals 
					console.log(user_message);
					frappe.msgprint(user_message);
					listview.refresh();  // This refreshes the List, but does -not- Reload each Document
				}
			}
		});
		my_dialog.hide();  // After callback, close dialog regardless of result.
	});

	// Now that dialog is defined, run it:
	my_dialog.show();
};
