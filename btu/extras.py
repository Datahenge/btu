"""
btu.extras.py
"""

# Usage: `bench execute temporal.dbsync.remove_unused_columns`

DEFAULT_COLUMNS = ['name', 'creation', 'modified', 'modified_by', 'owner', 'docstatus', 'parent', 'parentfield', 'parentype', 'idx']

def remove_unused_columns():
	"""
	This is a rather big utility, missing in standard ERPNext.
	Remove unused SQL Tables and Columns, if they aren't in the schema.
	"""
	import frappe

	database_name = frappe.db.db_name

	query = """
	SELECT TABLE_NAME	as table_name, COLUMN_NAME as column_name,
	DATA_TYPE as data_type, column_type as COLUMN_TYPE
	FROM INFORMATION_SCHEMA.COLUMNS
	WHERE TABLE_SCHEMA = %(database_name)s ;
	"""

	result = frappe.db.sql(query, values={"database_name": database_name}, as_dict=True)
	columns_to_review = [ column for column in result if column['column_name'] not in DEFAULT_COLUMNS ]
	for column in columns_to_review:
		print(column['table_name'])
		print(column['column_name'])
