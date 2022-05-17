// btu_configuration.js

// Copyright (c) 2022, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Configuration', {

	refresh: function(frm) {
		frm.events.add_button_list_failed_jobs(frm);
		frm.events.add_button_describe_job(frm);
		frm.events.add_button_delete_failed_jobs(frm);
	}

	,add_button_list_failed_jobs: function (frm) {
		// This function adds a button "List Failed RQ Jobs"
		frm.add_custom_button(__('List Failed RQ Jobs'), () => {
			frappe.call({
					type:"GET",
					method:"btu.list_failed_jobs",
				}).done(() => {
					frm.reload_doc();
				}).fail(() => {
					console.log("Error while listing Failed RQ Jobs.")					
				});
		}, 'Redis Queue');
	}

	,add_button_describe_job: function (frm) {

		frm.add_custom_button(__('Describe Job'), () => {

			var my_dialog = new frappe.ui.Dialog({
				title: 'Describe Job',
				width: 100,
				fields: [
					{
						'fieldtype': 'Data',
						'fieldname': 'queue_name',
						'label': __('Queue'),
						'default': 'default',
						reqd: 1
					},
					{
						'fieldtype': 'Data',
						'fieldname': 'job_id',
						'label': __('Job Id'),					
						reqd: 1
					}
				]
			});

			my_dialog.set_primary_action(__('Show'), args => {

				frappe.call({
					type:"POST",
					method:"btu.print_job_details",
					args: {
						"queue_name": args.queue_name,
						"job_id": args.job_id
					}
				}).done(() => {
					my_dialog.hide();
				}).fail(() => {
					my_dialog.hide();
				});
			});

			my_dialog.show();

		}, 'Redis Queue');
	}

	,add_button_delete_failed_jobs: function (frm) {
		// This function adds a button "Deleted Failed RQ Jobs"
		frm.add_custom_button(__('Delete Failed RQ Jobs'), () => {

			var my_dialog = new frappe.ui.Dialog({
				title: 'Delete Failed RQ Jobs',
				width: 100,
				fields: [
					{
						'fieldtype': 'Date',
						'fieldname': 'date_from',
						'label': __('From Date'),
						'default': frappe.datetime.add_days(frappe.datetime.get_today(), -28),
						reqd: 1
					},
					{
						'fieldtype': 'Date',
						'fieldname': 'date_to',
						'label': __('To Date'),
						'default': frappe.datetime.add_days(frappe.datetime.get_today(), -1),
						reqd: 1
					},
					{
						'fieldtype': 'Data',
						'fieldname': 'wildcard_text',
						'label': __('Wildcard Text'),					
						reqd: 0
					}

				]
			});

			my_dialog.set_primary_action(__('Run'), args => {

				frappe.call({
					type:"DELETE",
					method:"btu.remove_failed_jobs",
					args: { 
						"date_from": args.date_from,
						"date_to": args.date_to,
						"wildcard_text": args.wildcard_text
					}
				}).done(() => {
					my_dialog.hide();
				}).fail(() => {
					my_dialog.hide();
				});
			});

			my_dialog.show();

		}, 'Redis Queue');

	}  //end of function

});
