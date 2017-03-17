import epics
import time
def is_within_limits(pv, low_limit, high_limit):
	val = epics.caget(pv)
	ok = False
	if low_limit is not None and high_limit is not None:
		ok = low_limit < val < high_limit
	elif low_limit is None and high_limit is not None:
		ok = val < high_limit
	elif low_limit is not None and high_limit is None:
		ok = val > low_limit
	else:
		raise ValueError("Both high and low limit cannot be None.")
	return (val, ok)

def is_below_limit(pv, high_limit):
	return is_within_limits(pv, low_limit=None, high_limit=high_limit)

def is_above_limit(pv, low_limit):
	return is_within_limits(pv, low_limit=low_limit, high_limit=None)

def is_updating(pv, timeout=10.0):
	p = epics.PV(pv)
	try:
		connected = p.wait_for_conection()
		if not connected:
			raise Exception("Could not connect to PV {}".format(pv))
	except AttributeError:
		pass
	first_val = p.get()
	elapsed_time = 0.0
	wait_time = 0.1
	while elapsed_time < timeout:
		second_val = p.get()
		if first_val != second_val:
			return True
		time.sleep(wait_time)
		elapsed_time += wait_time
	return False

def has_value(pv, val, tolerance=None):
	if tolerance:
		return is_within_limits(pv, low_limit=val-tolerance, high_limit=val+tolerance)[1]
	else:
		return epics.caget(pv) == val
