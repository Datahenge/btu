

// Looks like this is the main entry point?

/*
frappe.pages['btu-redis-queue'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'None',
		single_column: true
	});
}
*/

frappe.pages['btu-redis-queue'].on_page_load = (wrapper) => {
	frappe.btu_redis_queue = new BTURedisQueue(wrapper);
};


class BTURedisQueue {

	// constructor is the main entry point into the class.
	constructor(wrapper) {

		this.wrapper = $(wrapper);  // just a shortcut to avoid typing $(wrapper)  ?

		// We always need a page.
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Redis Queue (RQ)"),
			single_column: false,
			card_layout: false,
		});
		parent: wrapper,
		this.parent = parent;

		this.add_some_buttons();
		this.wrapper.bind('show', () => {
			this.show();
		});
		// this.page.sidebar.html(`<ul class="standard-sidebar leaderboard-sidebar overlay-sidebar"></ul>`);
		// this.$sidebar_list = this.page.sidebar.find('ul');
		// this.get_leaderboard_config();
	}

	add_some_buttons() {
		this.page.add_inner_button(__("Goto: BTU Configuration"), function () {
			frappe.set_route('Form', 'BTU Configuration');
		});
	}

	show() {
		let route = frappe.get_route();
		this.user_id = frappe.session.user;
		this.say_hello();

		// This object is a pretty big deal:
		this.page.main.html(frappe.render_template('btu_redis_queue', {}));

		// $(frappe.render_template("btu_redis_queue")).appendTo(this.page.body.addClass("no-border"));
		// this.main_section.empty().append(frappe.render_template('btu_redis_queue'));  // implicitely means btu_redis_queue.html
	}

	say_hello() {
		console.log("Hello there " + this.user_id);
	}
}

// this.sidebar = this.wrapper.find('.layout-side-section');
// this.main_section = this.wrapper.find('.layout-main-section');
