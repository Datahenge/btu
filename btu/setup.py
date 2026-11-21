import frappe

SCHEDULER_ROLE = "BTU Scheduler"


def ensure_scheduler_role():
	"""Create the API-only role the scheduler daemon's user holds, without Desk access.

	Frappe also creates it while syncing the DocType permissions that name it, but with Desk access.
	"""
	if frappe.db.exists("Role", SCHEDULER_ROLE):
		frappe.db.set_value("Role", SCHEDULER_ROLE, "desk_access", 0)
	else:
		role = frappe.new_doc("Role")
		role.update({"role_name": SCHEDULER_ROLE, "desk_access": 0})
		role.insert(ignore_permissions=True)


def after_install():
	ensure_scheduler_role()
