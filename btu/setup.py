import frappe
from frappe.modules.import_file import import_file_by_path


def sync_desk():
	"""Import workspace and sidebar fixtures, create desktop icon, clear caches."""

	workspace_file = frappe.get_app_path(
		"btu", "btu_core", "workspace", "automated_tasks", "automated_tasks.json"
	)
	sidebar_file = frappe.get_app_path(
		"btu", "workspace_sidebar", "automated_tasks.json"
	)

	print("Importing workspace...")
	import_file_by_path(workspace_file, force=True)
	frappe.db.commit()

	print("Importing workspace sidebar...")
	import_file_by_path(sidebar_file, force=True)
	frappe.db.commit()

	print("Creating desktop icon...")
	_create_desktop_icon()
	frappe.db.commit()

	print("Clearing caches...")
	frappe.clear_cache()

	print("Done. Log out and log back in.")


def _create_desktop_icon():
	workspace = frappe.db.get_value(
		"Workspace", "Automated Tasks", ["name", "icon", "app", "module"], as_dict=True
	)
	if not workspace:
		print("Workspace 'Automated Tasks' not found — skipping desktop icon creation.")
		return

	if frappe.db.exists("Desktop Icon", {"label": "Automated Tasks", "icon_type": "Link"}):
		frappe.db.set_value(
			"Desktop Icon", "Automated Tasks",
			{"standard": 1, "bg_color": None, "icon": workspace.icon, "app": "btu"}
		)
		print("Updated existing desktop icon.")
		return

	icon = frappe.new_doc("Desktop Icon")
	icon.label = "Automated Tasks"
	icon.icon_type = "Link"
	icon.link_type = "Workspace Sidebar"
	icon.link_to = "Automated Tasks"
	icon.icon = workspace.icon
	icon.app = "btu"
	icon.standard = 1
	icon.hidden = 0
	icon.insert(ignore_permissions=True)
	print("Created desktop icon.")
