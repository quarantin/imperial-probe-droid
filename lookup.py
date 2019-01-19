#!/usr/bin/python3

PROBE_DIALOG = [
	'bIp',
	'bIp bIp',
	'bEp',
	'blEp',
	'BVN'
	'bOp',
	'brZ',
	'chInk',
	'schlIk',
	'stZS',
	'wOm',
]

PERCENT_STATS = [
	'armor',
	'critical-damage',
	'physical-critical-chance',
	'potency',
	'resistance',
	'special-critical-chance',
	'tenacity',
]

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
}

MODSETS_NEEDED = {
	'Health': 2,
	'Offense': 4,
	'Defense': 2,
	'Speed': 4,
	'Critical Chance': 2,
	'Critical Damage': 4,
	'Potency': 2,
	'Tenacity': 2,
}

MODSLOTS = {
	1: 'Square',
	2: 'Arrow',
	3: 'Diamond',
	4: 'Triangle',
	5: 'Circle',
	6: 'Cross',
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

FORMAT_LUT = {
	'gear':  'gear_level',
	'id':    'base_id',
	'level': 'level',
	'name':  'name',
	'power': 'power',
	'stars': 'rarity',
}

STATS_LUT = {
	'health':                      '1',
	'strength':                    '2',
	'agility':                     '3',
	'tactics':                     '4',
	'speed':                       '5',
	'physical-damage':             '6',
	'special-damage':              '7',
	'armor':                       '8',
	'resistance':                  '9',
	'armor-penetration':           '10',
	'resistance-penetration':      '11',
	'dodge-chance':                '12',
	'deflection-chance':           '13',
	'physical-critical-chance':    '14',
	'special-critical-chance':     '15',
	'critical-damage':             '16',
	'potency':                     '17',
	'tenacity':                    '18',
	'health-steal':                '27',
	'protection':                  '28',
	'physical-accuracy':           '37',
	'special-accuracy':            '38',
	'physical-critical-avoidance': '39',
	'special-critical-avoidance':  '40',
}

COLORS = {
	'blue':       0x268bd2,
	'cyan':       0x2aa198,
	'dark-gray':  0x586e75,
	'green':      0x859900,
	'light-gray': 0x839496,
	'orange':     0xcb4b16,
	'red':        0xdc322f,
	'yellow':     0xb58900,
}

UNITS_SHORT_NAMES = {

	'aa':    'Admiral Ackbar',
	'bf':    'Boba Fett',
	'cc':    'Chief Chirpa',
	'chs':   'Captain Han Solo',
	'cls':   'Commander Luke Skywalker',
	'cup':   'Coruscant Underworld Police',
	'cwc':   'Clone Wars Chewbacca',
	'dk':    'Director Krennic',
	'dn':    'Darth Nihilus',
	'dv':    'Darth Vader',
	'ee':    'Ewok Elder',
	'ep':    'Emperor Palpatine',
	'foe':   'First Order Executioner',
	'fox':   'First Order Executioner',
	'foo':   'First Order Officer',
	'fostp': 'First Order SF TIE Pilot',
	'fost':  'First Order Stormtrooper',
	'fotp':  'First Order TIE Pilot',
	'gk':    'General Kenobi',
	'gat':   'Grand Admiral Thrawn',
	'gmt':   'Grand Moff Tarkin',
	'gmy':   'Grand Master Yoda',
	'hy':    'Hermit Yoda',
	'hoda':  'Hermit Yoda',
	'hyoda': 'Hermit Yoda',
	'hs':    'Han Solo',
	'hst':   'Stormtrooper Han',
	'ipd':   'Imperial Probe Droid',
	'jf':    'Jango Fett',
	'jka':   'Jedi Knight Anakin',
	'jkg':   'Jedi Knight Guardian',
	'jkr':   'Jedi Knight Revan',
	'jtr':   'Rey (Jedi Training)',
	'kr':    'Kylo Ren',
	'kru':   'Kylo Ren (Unmasked)',
	'mt':    'Mother Talzin',
	'qgj':   'Qui-Gon Jinn',
	'sth':   'Stormtrooper Han',
	'rex':   'CT-7567',
	'rolo':  'Rebel Officer Leia Organa',
	'rp':    'Resistance Pilot',
	'rjt':   'Rey (Jedi Training)',
	'yhs':   'Young Han Solo',
	'ylc':   'Young Lando Calrissian',
}

