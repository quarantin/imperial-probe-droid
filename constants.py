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
	1,
	3,
	7,
	8,
	5,
	6,
	2,
	4,
]

MODSETS_NEEDED = {
	1: 2, # Health
	2: 4, # Offense
	3: 2, # Defense
	4: 4, # Speed
	5: 2, # Critical Chance
	6: 4, # Critical Damage
	7: 2, # Potency
	8: 2, # Tenacity
}

MODSPRIMARIES = {
	'Accuracy',
	'Critical Avoidance',
	'Critical Chance',
	'Critical Damage',
	'Defense',
	'Health',
	'Offense',
	'Protection',
	'Tenacity',
	'Speed',
}

SHORT_STATS = {
	'Accuracy':           'Ac',
	'Critical Avoidance': 'CA',
	'Critical Chance':    'CC',
	'Critical Damage':    'CD',
	'Defense':            'De',
	'Health':             'He',
	'Offense':            'Of',
	'Potency':            'Po',
	'Protection':         'Pr',
	'Speed':              'Sp',
	'Tenacity':           'Te',
	'NA':                 'NA',
}

EMOJIS = {
	'':                  '<:spa:535808549264162816>',
	'zeta':              '<:zeta:547487955476938753>',
	'omega':             '<:omega:547487976230355004>',
	'health':            '<:hea:535516510681301012>',
	'offense':           '<:off:535540883207094283>',
	'defense':           '<:def:535522549375959050>',
	'speed':             '<:spe:535522604782714890>',
	'cc':                '<:cc:535538316943294465>',
	'critchance':        '<:cc:535538316943294465>',
	'criticalchance':    '<:cc:535538316943294465>',
	'cd':                '<:cd:535538317132038164>',
	'critdamage':        '<:cd:535538317132038164>',
	'criticaldamage':    '<:cd:535538317132038164>',
	'potency':           '<:pot:535522563414032405>',
	'tenacity':          '<:ten:535522621731635207>',
	'capitalgames':      '<:ea:546234326191308801>',
	'crouchingrancor':   '<:cr:535545454214119434>',
	'swgoh.gg':          '<:gg:546166559123701770>',
	'crimsondeathwatch': '<:cdw:535779958686089216>',
	'square':            '<:square:535541049570099211>',
	1:                   '<:square:535541049570099211>',
	'arrow':             '<:arrow:535541036986925066>',
	2:                   '<:arrow:535541036986925066>',
	'diamond':           '<:diamond:535541023112298496>',
	3:                   '<:diamond:535541023112298496>',
	'triangle':          '<:triangle:535541010424660009>',
	4:                   '<:triangle:535541010424660009>',
	'circle':            '<:circle:535540977516150799>',
	5:                   '<:circle:535540977516150799>',
	'cross':             '<:cross:535814108914909215>',
	6:                   '<:cross:535814108914909215>',
}
