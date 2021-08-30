frappe.listview_settings['BTU Task List'] = {

	onload: function (listview) {
		// Add a button above the List View filters.
		listview.page.add_inner_button(__("Rewrite all Task Schedules into Redis Queue"), function () {
			rebuild_all_tasks(listview);
		});			
	}
};

function rebuild_all_tasks() {

	// Ask Python for the current Delivery Period, then run the dialog.
	frappe.call({
		method: "btu.scheduler.doctype.btu_task_schedule.btu_task_schedule.rebuild_all_schedules",
		args: null,
		callback: (r) => {
			if (r.message) {
				console.log(r.message);
				frappe.msgprint("All tasks rescheduled: {0}", r.message);
			}
		},
	});
};
