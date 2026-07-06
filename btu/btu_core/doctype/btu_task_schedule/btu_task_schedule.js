// Copyright (c) 2021-2026, Datahenge LLC and contributors
// For license information, please see license.txt

frappe.ui.form.on('BTU Task Schedule', {
	onload(frm) {
		frm.set_query('queue_name', 'btu.btu_core.form_options.get_rq_queue_names');
		btu_load_timezone_options(frm);
	},

	btn_set_schedule(frm) {
		btu_show_schedule_dialog(frm);
	},
});

/**
 * Fetch the IANA timezone list from the BTU Redis cache and populate the
 * cron_timezone Autocomplete field.  Results are stored on the frappe
 * namespace so repeated form opens within the same browser session make
 * only one round-trip to the server.
 */
function btu_load_timezone_options(frm) {
	const ctrl = frm.fields_dict['cron_timezone'];
	if (!ctrl || typeof ctrl.set_data !== 'function') return;

	if (frappe._btu_timezones) {
		ctrl.set_data(frappe._btu_timezones);
		return;
	}

	frappe.call({
		method: 'btu.btu_core.form_options.get_cron_timezones',
		callback(r) {
			if (r.message && r.message.length) {
				frappe._btu_timezones = r.message;
				ctrl.set_data(r.message);
			}
		},
	});
}

const BTU_DOW_MAP = {
	Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4,
	Friday: 5, Saturday: 6, Sunday: 0,
};

const BTU_MONTH_MAP = {
	January: 1, February: 2, March: 3, April: 4,
	May: 5, June: 6, July: 7, August: 8,
	September: 9, October: 10, November: 11, December: 12,
};

/**
 * Open a single dialog that guides the user through picking a schedule
 * frequency and the relevant time/date parameters, then writes the resulting
 * cron expression into the read-only cron_string field.
 */
function btu_show_schedule_dialog(frm) {
	const d = new frappe.ui.Dialog({
		title: __('Set Schedule'),
		fields: [
			{
				label: __('Frequency'),
				fieldname: 'frequency',
				fieldtype: 'Select',
				options: 'Hourly\nDaily\nWeekly\nMonthly\nYearly\nCustom Cron',
				reqd: 1,
				default: 'Daily',
			},
			// ── Custom Cron ──────────────────────────────────────────────────
			{
				label: __('Cron Expression'),
				fieldname: 'cron_string_input',
				fieldtype: 'Data',
				depends_on: "eval:doc.frequency === 'Custom Cron'",
				description: __('Format: minute hour day-of-month month day-of-week &nbsp;|&nbsp; Example: 0 22 * * 1-5'),
				placeholder: '0 8 * * *',
			},
			// ── Weekly ───────────────────────────────────────────────────────
			{
				label: __('Day of Week'),
				fieldname: 'day_of_week',
				fieldtype: 'Select',
				options: 'Monday\nTuesday\nWednesday\nThursday\nFriday\nSaturday\nSunday',
				depends_on: "eval:doc.frequency === 'Weekly'",
				default: 'Monday',
			},
			// ── Yearly ───────────────────────────────────────────────────────
			{
				label: __('Month'),
				fieldname: 'month',
				fieldtype: 'Select',
				options: 'January\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember',
				depends_on: "eval:doc.frequency === 'Yearly'",
			},
			// ── Monthly + Yearly ─────────────────────────────────────────────
			{
				label: __('Day of Month (1–28)'),
				fieldname: 'day',
				fieldtype: 'Int',
				default: 1,
				depends_on: "eval:doc.frequency === 'Monthly' || doc.frequency === 'Yearly'",
			},
			// ── All except Hourly + Custom Cron ──────────────────────────────
			{
				label: __('Hour (0–23)'),
				fieldname: 'hour',
				fieldtype: 'Int',
				default: 8,
				depends_on: "eval:doc.frequency !== 'Hourly' && doc.frequency !== 'Custom Cron'",
			},
			// ── All except Custom Cron ───────────────────────────────────────
			{
				label: __('Minute (0–59)'),
				fieldname: 'minute',
				fieldtype: 'Int',
				default: 0,
				depends_on: "eval:doc.frequency !== 'Custom Cron'",
			},
		],
		primary_action_label: __('Set Schedule'),
		primary_action(values) {
			const cron = btu_build_cron_string(values);
			if (!cron) return;
			frm.set_value('cron_string', cron);
			d.hide();
		},
	});
	d.show();
}

/**
 * Validate the dialog values and return a cron string, or null on error.
 */
function btu_build_cron_string(values) {
	const freq = values.frequency;

	if (freq === 'Custom Cron') {
		const s = (values.cron_string_input || '').trim();
		if (!s) {
			frappe.msgprint(__('Please enter a cron expression.'));
			return null;
		}
		return s;
	}

	const minute = parseInt(values.minute, 10);
	const hour   = parseInt(values.hour, 10);
	const day    = parseInt(values.day, 10);

	if (isNaN(minute) || minute < 0 || minute > 59) {
		frappe.msgprint(__('Minute must be between 0 and 59.'));
		return null;
	}
	if (freq !== 'Hourly' && (isNaN(hour) || hour < 0 || hour > 23)) {
		frappe.msgprint(__('Hour must be between 0 and 23.'));
		return null;
	}
	if ((freq === 'Monthly' || freq === 'Yearly') && (isNaN(day) || day < 1 || day > 28)) {
		frappe.msgprint(__('Day of month must be between 1 and 28.'));
		return null;
	}

	if (freq === 'Hourly')  return `${minute} * * * *`;
	if (freq === 'Daily')   return `${minute} ${hour} * * *`;
	if (freq === 'Weekly')  return `${minute} ${hour} * * ${BTU_DOW_MAP[values.day_of_week]}`;
	if (freq === 'Monthly') return `${minute} ${hour} ${day} * *`;
	if (freq === 'Yearly')  return `${minute} ${hour} ${day} ${BTU_MONTH_MAP[values.month]} *`;

	return null;
}
