import epics
import time
from ipywidgets import widgets, Layout
from IPython.display import display, HTML

class Checklist(object):
	def __init__(self):
		self._checklist = []
		self.result_template = "<span style='color: {color}; font-weight: bold;'>{msg}</span>"

	def to_html(self):
		table = "<table>\n\t<tr><th>Description</th><th>Condition</th><th>Recorded Value</th><th>Result</th></tr>\n"
		for row in self._checklist:
			row = "\t<tr><td>{desc}</td><td>{cond}</td><td>{val}</td><td>{res}</td></tr>\n".format(desc=row['description'], cond=row['condition'], val=row['val'], res=row['result'])
			table += row
		table += "</table>"
		return table

	def display_results(self):
		display(HTML(self.to_html()))

	def append(self, new_item):
		self._checklist.append(new_item)

	def append_custom_item(self, description, condition, value, result):
		self._checklist.append({"description": description, "condition": condition, "val": value, "result": result})

	def is_within_limits(self, pv, low_limit, high_limit, description=None):
		val, ok = is_within_limits(pv, low_limit, high_limit, description, self)
		msg = None
		if ok:
			msg = "Value of {pv} ({val}) is above low limit ({low_limit}) and below high limit ({high_limit}): Test Passed".format(pv=pv, val=val, low_limit=low_limit, high_limit=high_limit)
		else:
			if val < low_limit:
				msg = "Value of {pv} ({val}) is below low limit ({low_limit}): Test Failed".format(pv=pv, val=val, low_limit=low_limit)
			elif val > high_limit:
				msg = "Value of {pv} ({val}) is above high limit ({high_limit}): Test Failed".format(pv=pv, val=val, high_limit=high_limit)
		print(msg)

	def is_below_limit(self, pv, high_limit, description=None):
		val, ok = is_below_limit(pv, high_limit, description, self)
		msg = None
		if ok:
			msg = "Value of {pv} ({val}) is below high limit ({high_limit}): Test Passed".format(pv=pv, val=val, high_limit=high_limit)
		else:
			msg = "Value of {pv} ({val}) is above high limit ({high_limit}): Test Failed".format(pv=pv, val=val, high_limit=high_limit)
		print(msg)

	def is_above_limit(self, pv, low_limit, description=None):
		val, ok = is_above_limit(pv, low_limit, description, self)
		msg = None
		if ok:
			msg = "Value of {pv} ({val}) is above low limit ({low_limit}): Test Passed".format(pv=pv, val=val, low_limit=low_limit)
		else:
			msg = "Value of {pv} ({val}) is below low limit ({low_limit}): Test Failed".format(pv=pv, val=val, low_limit=low_limit)
		print(msg)

	def is_updating(self, pv, timeout=10.0, description=None):
		ok = is_updating(pv, timeout, description, self)
		msg = None
		if ok:
			msg = "{pv} updated within {timeout} seconds: Test Passed".format(pv=pv, timeout=timeout)
		else:
			msg = "{pv} did not update within {timeout} seconds: Test Failed".format(pv=pv, timeout=timeout)
		print(msg)

	def has_value(self, pv, val, tolerance=None, description=None):
		recorded_val, ok = has_value(pv, val, tolerance, description, self)
		msg = None
		if ok:
			msg = "Value of {pv} ({recorded_val}) is equal to {val}".format(pv=pv, recorded_val=recorded_val, val=val)
			if tolerance is not None:
				msg += " +/- {tol}".format(tol=tolerance)
			msg += ": Test Passed"
		else:
			msg = "Value of {pv} ({recorded_val}) is not equal to {val}".format(pv=pv, recorded_val=recorded_val, val=val)
			if tolerance is not None:
				msg += " +/- {tol}".format(tol=tolerance)
			msg += ": Test Failed"
		print(msg)

	def custom_with_checkbox(self, description, condition):
		item_index = len(self._checklist)
		def toggle_cb(change):
			val = change['new']
			msg = "Not OK"
			if val == True:
				msg = "OK"
			self._checklist[item_index]['result'] = msg
		self.append_custom_item(description, condition, "", "Not OK")
		l = widgets.Label(description, layout=Layout(width='75%'))
		cb = widgets.Checkbox(value=False, description="OK?", layout=Layout(width='25%'))
		cb.observe(toggle_cb, names='value')
		item = widgets.HBox([l, cb])
		display(item)

def is_within_limits(pv, low_limit, high_limit, description=None, checklist=None):
	val = epics.caget(pv)
	ok = False
	msg = None
	if val is None:
		ok = False
		msg = "Error: Could not connect to PV"
	elif low_limit is not None and high_limit is not None:
		ok = low_limit < val < high_limit
		if ok:
			msg = "Within Limits"
		elif val < low_limit:
			msg = "Too Low"
		elif val > high_limit:
			msg = "Too High"
	elif low_limit is None and high_limit is not None:
		ok = val < high_limit
		if ok:
			msg = "Within Limits"
		else:
			msg = "Too High"
	elif low_limit is not None and high_limit is None:
		ok = val > low_limit
		if ok:
			msg = "Within Limits"
		else:
			msg = "Too Low"
	else:
		raise ValueError("Both high and low limit cannot be None.")
	if checklist is not None:
		if description is None:
			description = pv
		colors = {True: "green", False: "red"}
		result = checklist.result_template.format(color=colors[ok], msg=msg)
		condition = ""
		if low_limit is not None:
			condition += "{} < ".format(low_limit)
		condition += "Recorded Value"
		if high_limit is not None:
			condition += " < {}".format(high_limit)
		checklist.append({'description': description, 'condition': condition, 'val': val, 'result': result})
	return (val, ok)

def is_below_limit(pv, high_limit, description=None, checklist=None):
	return is_within_limits(pv, low_limit=None, high_limit=high_limit, description=description, checklist=checklist)

def is_above_limit(pv, low_limit, description=None, checklist=None):
	return is_within_limits(pv, low_limit=low_limit, high_limit=None, description=description, checklist=checklist)

def is_updating(pv, timeout=10.0, description=None, checklist=None):
	p = epics.PV(pv)
	try:
		connected = p.wait_for_conection(timeout=timeout)
		if not connected:
			raise Exception("Could not connect to PV {}".format(pv))
	except AttributeError:
		pass
	first_val = p.get(timeout=timeout)
	if first_val is None:
		raise Exception("Could not connect to PV {}".format(pv))
	elapsed_time = 0.0
	wait_time = 0.1
	ok = False
	while elapsed_time < timeout:
		second_val = p.get(timeout=timeout)
		if second_val is None:
			raise Exception("Unexpected disconnection from PV {}".format(pv))
		if first_val != second_val:
			ok = True
			break
		time.sleep(wait_time)
		elapsed_time += wait_time
	if checklist is not None:
		if description is None:
			description = pv
		colors = {True: "green", False: "red"}
		msg = {True: "PV is updating", False: "PV is not updating"}
		condition = "is updating"
		result = checklist.result_template.format(color=colors[ok], msg=msg[ok])
		checklist.append({"description": description, "condition": condition, "val": second_val, "result": result})
	return ok

def has_value(pv, val, tolerance=None, description=None, checklist=None):
	if tolerance is not None:
		return is_within_limits(pv, low_limit=val-tolerance, high_limit=val+tolerance, description=description, checklist=checklist)
	readback = epics.caget(pv)
	ok = readback == val
	if checklist is not None:
		if description is None:
			description = pv
		colors = {True: "green", False: "red"}
		msg = {True: "Equal", False: "Not Equal"}
		condition = "Recorded Value == {}".format(val)
		result = checklist.result_template.format(color=colors[ok], msg=msg[ok])
		checklist.append({"description": description, "condition": condition, "val": readback, "result": result})
	return (readback, ok)
