from opts import *
from errors import *
from swgohhelp import fetch_players, get_unit_name

help_list = {
	'title': 'List Help',
	'description': """List character or ship names.

**Syntax**
```
%prefixlist [units or factions]```
**Examples**
List all bounty hunters:
```
%prefixlist bh```
List Darth Malak and both Revan:
```
%prefixlist malak revan```"""
}

def cmd_list(request):

	args = request.args
	config = request.config

	language = parse_opts_lang(request)

	selected_units = parse_opts_unit_names(request)
	if not selected_units:
		return error_no_unit_selected()

	if args:
		return error_unknown_parameters(args)

	msgs = []
	translations = []
	for unit in selected_units:
		translated_name = get_unit_name(config, unit.base_id, language)
		translations.append(translated_name)

	unit_list = '\n- '.join(translations)
	return [{
		'title': 'Unit List',
		'description': 'Here is the list of units you selected:\n- %s\n' % unit_list,
	}]
