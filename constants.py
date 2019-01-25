#!/usr/bin/python3

MODSLOTS = {
	1: 'Square',
	2: 'Arrow',
	3: 'Diamond',
	4: 'Triangle',
	5: 'Circle',
	6: 'Cross',
}

MODSETS = {
	1: 'Health',
	2: 'Offense',
	3: 'Defense',
	4: 'Speed',
	5: 'Critical Chance',
	6: 'Critical Damage',
	7: 'Potency',
	8: 'Tenacity',
}

MODSETS_LIST = [
	'Health',
	'Defense',
	'Potency',
	'Tenacity',
	'Critical Chance',
	'Critical Damage',
	'Offense',
	'Speed',
]

MODSETS_NEEDED = {
	# Health
	1: 2, 
	# Offense
	2: 4,
	# Defense
	3: 2,
	# Speed
	4: 4,
	# Critical Chance
	5: 2,
	# Critical Damage
	6: 4,
	# Potency
	7: 2,
	# Tenacity
	8: 2,
}

EMOJIS = {
	'':                  '<:spa:535808549264162816>',
	'health':            '<:hea:535516510681301012>',
	'offense':           '<:off:535540883207094283>',
	'defense':           '<:def:535522549375959050>',
	'speed':             '<:spe:535522604782714890>',
	'cc':                '<:cc:535538316943294465>',
	'criticalchance':    '<:cc:535538316943294465>',
	'cd':                '<:cd:535538317132038164>',
	'criticaldamage':    '<:cd:535538317132038164>',
	'potency':           '<:pot:535522563414032405>',
	'tenacity':          '<:ten:535522621731635207>',
	'capitalgames':      '<:cg:535546505365422080>',
	'crouchingrancor':   '<:cr:535545454214119434>',
	'crimsondeathwatch': '<:cdw:535779958686089216>',
	'square':            '<:square:535541049570099211>',
	'arrow':             '<:arrow:535541036986925066>',
	'diamond':           '<:diamond:535541023112298496>',
	'triangle':          '<:triangle:535541010424660009>',
	'circle':            '<:circle:535540977516150799>',
	'cross':             '<:cross:535814108914909215>',
}
