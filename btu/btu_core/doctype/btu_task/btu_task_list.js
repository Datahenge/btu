/*
	Copyright (c) 2022-2024, Datahenge LLC and contributors
	For license information, please see license.txt

	List Page for DocType 'BTU Task'
*/

frappe.listview_settings['BTU Task'] = {

	onload: function (listview) {

		/*
			Amazing solution for adding a Standard Filter for DocStatus, without creating a pointless, new column named 'status'
			https://discuss.erpnext.com/t/how-to-include-docstatus-in-standard-filter/76382
		*/

		const df = {
			condition: "=",
			default: null,
			fieldname: "docstatus",
			fieldtype: "Select",
			input_class: "input-xs",
			label: "Status",
			is_filter: 1,
			onchange: function() {
				listview.refresh();
			},
			options: [0,1,2],
			placeholder: "Status"
		};
			
		//Add the filter to standard filter section
		let standard_filters_wrapper = listview.page.page_form.find('.standard-filter-section');
		listview.page.add_field(df, standard_filters_wrapper);
		
		//It will be a dropdown with options 1, 2, 3
		//To replace it with Blank space, Draft, Submitted and Cancelled.
		//First selecting the select option, may subject to changes as the the system
		let doc_filter = document.querySelector('select[data-fieldname = "docstatus"]')
		
		//Add first option as blank space
		doc_filter.options.add(new Option(), 0);
		
		//Changing just options' inner html for better user experience
		doc_filter.options[1].innerHTML = 'Draft';
		doc_filter.options[2].innerHTML = 'Submitted';
		doc_filter.options[3].innerHTML = 'Cancelled';
	}
};
