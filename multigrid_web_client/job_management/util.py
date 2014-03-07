import json


def decode_list(data):
	rv = []
	for item in data:
		if isinstance(item, unicode):
			item = item.encode('utf-8')
		elif isinstance(item, list):
			item = decode_list(item)
		elif isinstance(item, dict):
			item = decode_dict(item)
		rv.append(item)
	return rv

def decode_dict(data):
	rv = {}
	for key, value in data.iteritems():
		if isinstance(key, unicode):
			key = key.encode('utf-8')
		if isinstance(value, unicode):
			value = value.encode('utf-8')
		elif isinstance(value, list):
			value = decode_list(value)
		elif isinstance(value, dict):
			value = decode_dict(value)
		rv[key] = value
	return rv


# def parse_input_params(param):
# 	parameter = json.loads(param, object_hook=decode_dict)
# 	return parameter


def parse_input_params(input_params):
	result_list = []
	import re
	# regular expression for finding 'range' function
	pattern = re.compile('range\(\d+(?:,\d+){0,2}\)')
	match_list = pattern.finditer(input_params)
	# find positions of all pattern occurrences in input_params
	spans = [match.span() for match in match_list]
	# list of list evaluated from 'range' statements in input_params
	eval_list = [eval(input_params[span[0]:span[1]]) for span in spans]
	combinations = generate_combinations(eval_list)
	splited_input = pattern.split(input_params)
	#raplace all 'range' statements with generated digit
	for combination in combinations:
		if not isinstance(combination, list):
			combination = [combination]
		new_param_string = splited_input[0]
		for item, splited_item in zip(combination, splited_input[1:-1]):
			new_param_string += str(item) + splited_item
		new_param_string += str(combination[-1])
		new_param_string += splited_input[-1]
		result_list.append(new_param_string)
	return result_list


def generate_combinations(list_of_lists):
	"""
	Generate all possible combinations of elements in lists
	"""
	if len(list_of_lists) > 1:
		result_list = []
		combinations_without_first_list = generate_combinations(list_of_lists[1:])
		for item in list_of_lists[0]:
			for combination in combinations_without_first_list:
				if type(combination) is list:
					result_list.append([item] + combination)
				else:
					result_list.append([item] + [combination])
		return result_list
	else:
		return list_of_lists[0]


