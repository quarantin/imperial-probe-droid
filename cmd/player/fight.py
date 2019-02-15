#!/usr/bin/python3

from opts import *

help_fight = {
	'title': 'Fight Help',
	'description': """Record statistics submitted by players about combat outcomes.

**Syntax**
```
%prefixfight win|lose auto|manual <player1> <char1> ... <char5> <player2> <char1> ... <char5>```
**Options**
**`win`** (or **`w`**): To indicate player1 won against player2.
**`lose`** (or **`l`**): To indicate player1 lost againt player2.
**`auto`** (or **`a`**): To indicate the fight was in automatic mode.
**`manual`** (or **`m`**): To indicate the fight was in manual mode.

**Aliases**
```
%prefixc```
**Examples**
Assuming your sith/empire team won against **OtherPlayer** nightsisters in automatic mode, you should type a command similar to this one:
```
%prefixc win auto @You ep dn dv gat darthsion @OtherPlayer mt od zombi asajj talia```
Alternatively, if your ewok team was defeated in manual mode by the first order team of **OtherPlayer**, then you should type a command similar to this one:
```
%prefixc lose manual @You chirpa elder wicket logray paploo @OtherPlayer kru kr fox fotp fosftp```"""
}

def cmd_fight(config, author, channel, args):

	if len(args) < 14:
		return [{
			'title': 'Invalid Number of Parameters',
			'color': 'red',
			'description': 'You supplied %d parameters but I need exactly %d. Please see **`%shelp fight`** for more information.' % (len(args), 14),
		}]

	status = args[0]
	if status in [ 'w', 'win' ]:
		status = 'win'
	elif status in [ 'l', 'lose' ]:
		status = 'lose'
	else:
		return [{
			'title': 'Invalid Parameter',
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter: **`%s`**.\nI need either **`win`** or **`lose`**.' % status,
		}]

	mode = args[1]
	if mode in [ 'a', 'auto' ]:
		mode = 'auto'
	elif mode in [ 'm', 'manual' ]:
		mode = 'manual'
	else:
		return [{
			'title': 'Invalid Parameter',
			'color': 'red',
			'description': 'I don\'t know what to do with the following parameter: **`%s`**.\nI need either **`auto`** or **`manual`**.' % mode,
		}]

	player1 = args[2]
	team1 = args[3:8]

	player2 = args[8]
	team2 = args[9:14]

	print("DEBUG1 %s" % team1)
	print("DEBUG2 %s" % team2)

	player_one = parse_opts_ally_code(config, author, player1)
	player_two = parse_opts_ally_code(config, author, player2)

	args, team1_list = parse_opts_unit_names(config, list(team1))
	args, team2_list = parse_opts_unit_names(config, list(team2))

	team1_nlist = [ x['name'] for x in team1_list ]
	team2_nlist = [ x['name'] for x in team2_list ]

	print("DEBUG3 %s" % team1_nlist)
	print("DEBUG4 %s" % team2_nlist)

	player1_name = get_player_name(player_one)
	player2_name = get_player_name(player_two)

	status_str = status == 'win' and 'won' or 'lost'
	mode_str = mode == 'auto' and 'automatic' or 'manual'

	return [{
		'title': 'Combat Result',
		'description': '**%s vs %s**\n%s %s the fight in %s mode against %s\n\nRespective teams:\n**%s**\n- %s\n**%s**\n- %s' % (player1_name, player2_name, player1_name, status_str, mode_str, player2_name, player1_name, '\n - '.join(team1_nlist), player2_name, '\n - '.join(team2_nlist)),
	}]
