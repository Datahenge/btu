// Main entry point

/*
frappe.pages['btu-documentation'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'BTU Documentation',
		single_column: true
	});
}
*/

frappe.pages['btu-documentation'].on_page_load = (wrapper) => {
	frappe.btu_documentation = new BTUDocumentation(wrapper);
};


class BTUDocumentation {

	// constructor is the main entry point into the class.
	constructor(wrapper) {

		this.wrapper = $(wrapper);  // just a shortcut to avoid typing $(wrapper)  ?

		// We always need a page.
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("BTU Documentation and Links"),
			single_column: false,
			card_layout: false,
		});

		this.parent = wrapper;
		this.add_some_buttons();
		this.wrapper.bind('show', () => {
			this.show();
		});
	}

	add_some_buttons() {
		this.page.add_inner_button(__("BTU Workspace"), function () {
			frappe.set_route('/btu');
		});
	}

	show() {
		let route = frappe.get_route();
		// NOTE: This object is a pretty big deal:
		this.page.main.html(frappe.render_template('btu_documentation', {}));
		// $(frappe.render_template("btu_redis_queue")).appendTo(this.page.body.addClass("no-border"));
		// this.main_section.empty().append(frappe.render_template('btu_redis_queue'));  // implicitely means btu_redis_queue.html
	}
}
