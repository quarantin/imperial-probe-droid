
HOUR = 3600
MINUTE = 60

MAX_GEAR = 13
MAX_LEVEL = 85
MAX_GEAR_LEVEL = 13
MAX_RARITY = 7
MAX_RELIC = 7
MAX_SKILL_TIER = 8

ROMAN = {
	1: 'I',
	2: 'II',
	3: 'II',
	4: 'IV',
	5: 'V',
	6: 'VI',
	7: 'VII',
	8: 'VIII',
	9: 'IX',
	10: 'X',
	11: 'XI',
	12: 'XII',
	13: 'XIII',
}

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

# See https://github.com/r3volved/scorpio/blob/master/core/SWAPI/util/enums.js#L712
UNIT_STATS = {
	0: 'None', # NOUNITSTAT
	1: 'Health',
	2: 'Strength',
	3: 'Agility',
	4: 'Intelligence',
	5: 'Speed',
	6: 'UNITSTATATTACKDAMAGE',
	7: 'UNITSTATABILITYPOWER',
	8: 'UNITSTATARMOR',
	9: 'UNITSTATSUPPRESSION',
	10: 'UNITSTATARMORPENETRATION',
	11: 'UNITSTATSUPPRESSIONPENETRATION',
	12: 'UNITSTATDODGERATING',
	13: 'UNITSTATDEFLECTIONRATING',
	14: 'UNITSTATATTACKCRITICALRATING',
	15: 'UNITSTATABILITYCRITICALRATING',
	16: 'Critical Damage', # UNITSTATCRITICALDAMAGE
	17: 'Potency', # UNITSTATACCURACY
	18: 'Tenacity', # UNITSTATRESISTANCE
	19: 'UNITSTATDODGEPERCENTADDITIVE',
	20: 'UNITSTATDEFLECTIONPERCENTADDITIVE',
	21: 'UNITSTATATTACKCRITICALPERCENTADDITIVE',
	22: 'UNITSTATABILITYCRITICALPERCENTADDITIVE',
	23: 'UNITSTATARMORPERCENTADDITIVE',
	24: 'UNITSTATSUPPRESSIONPERCENTADDITIVE',
	25: 'UNITSTATARMORPENETRATIONPERCENTADDITIVE',
	26: 'UNITSTATSUPPRESSIONPENETRATIONPERCENTADDITIVE',
	27: 'UNITSTATHEALTHSTEAL',
	28: 'Protection', # UNITSTATMAXSHIELD
	29: 'UNITSTATSHIELDPENETRATION',
	30: 'UNITSTATHEALTHREGEN',
	31: 'UNITSTATATTACKDAMAGEPERCENTADDITIVE',
	32: 'UNITSTATABILITYPOWERPERCENTADDITIVE',
	33: 'UNITSTATDODGENEGATEPERCENTADDITIVE',
	34: 'UNITSTATDEFLECTIONNEGATEPERCENTADDITIVE',
	35: 'UNITSTATATTACKCRITICALNEGATEPERCENTADDITIVE',
	36: 'UNITSTATABILITYCRITICALNEGATEPERCENTADDITIVE',
	37: 'UNITSTATDODGENEGATERATING',
	38: 'UNITSTATDEFLECTIONNEGATERATING',
	39: 'UNITSTATATTACKCRITICALNEGATERATING',
	40: 'UNITSTATABILITYCRITICALNEGATERATING',
	41: 'Offense', # UNITSTATOFFENSE
	42: 'Defense', # UNITSTATDEFENSE
	43: 'UNITSTATDEFENSEPENETRATION',
	44: 'UNITSTATEVASIONRATING',
	45: 'UNITSTATCRITICALRATING',
	46: 'UNITSTATEVASIONNEGATERATING',
	47: 'UNITSTATCRITICALNEGATERATING',
	48: 'Offense %', # UNITSTATOFFENSEPERCENTADDITIVE
	49: 'Defense %', # UNITSTATDEFENSEPERCENTADDITIVE
	50: 'UNITSTATDEFENSEPENETRATIONPERCENTADDITIVE',
	51: 'UNITSTATEVASIONPERCENTADDITIVE',
	52: 'Accuracy %', # UNITSTATEVASIONNEGATEPERCENTADDITIVE
	53: 'Critical Chance %', # UNITSTATCRITICALCHANCEPERCENTADDITIVE
	54: 'Critical Avoidance %', # UNITSTATCRITICALNEGATECHANCEPERCENTADDITIVE
	55: 'Health %', # UNITSTATMAXHEALTHPERCENTADDITIVE
	56: 'Protection %', # UNITSTATMAXSHIELDPERCENTADDITIVE
	57: 'UNITSTATSPEEDPERCENTADDITIVE',
	58: 'UNITSTATCOUNTERATTACKRATING',
	59: 'UNITSTATTAUNT',
}

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
	'Potency',
	'Protection',
	'Tenacity',
	'Speed',
}

EMOJI_HOURGLASS = '\N{HOURGLASS}'
EMOJI_THUMBSUP  = '\N{THUMBS UP SIGN}'

EMOJIS = {
	'':                  '<:spa:535808549264162816>',
	'jedi':              '<:jedi:696639062022291517>',
	'ship':              '<:ship:696639760499867718>',
	'zeta':              '<:zeta:547487955476938753>',
	'zetadisabled':      '<:zetadisabled:706542863131082772>',
	'omega':             '<:omega:547487976230355004>',
	'omegadisabled':     '<:omegadisabled:706542825436610650>',
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
	'slot1':             '<:slot1:585454664170864652>',
	'slot2':             '<:slot2:585454664548352003>',
	'slot3':             '<:slot3:585454664472985650>',
	'slot4':             '<:slot4:585454664548614155>',
	'slot5':             '<:slot5:585454664779169822>',
	'slot6':             '<:slot6:585454664594489344>',

	# Guild banners

	'blacksun':     '<:blacksun:590894952297267203>',
	'blast':        '<:blast:590894952486141955>',
	'cis':          '<:cis:590894952683405322>',
	'empire':       '<:empire:590894952695857162>',
	'firstorder':   '<:firstorder:590894952767160350>',
	'flame':        '<:flame:590894952863498270>',
	'fulcrum':      '<:fulcrum:590894953065087027>',
	'havoc':        '<:havoc:590894953337585687>',
	'hero':         '<:hero:590894952972550167>',
	'jedi':         '<:jedi:590894953371140105>',
	'mandalorian':  '<:mandalorian:590894952968355867>',
	'newrepublic':  '<:newrepublic:590894953371140123>',
	'niteowl':      '<:niteowl:590894953110962177>',
	'oldrepublic':  '<:oldrepublic:590894953094185000>',
	'pyke':         '<:pyke:590894953023143948>',
	'rebel':        '<:rebel:590894953123807232>',
	'sabine':       '<:sabine:590894952800714773>',
	'senate':       '<:senate:590894953232859146>',
	'seventhfleet': '<:seventhfleet:590894953610084352>',
	'sithempire':   '<:sithempire:590894953174138920>',
	'sith':         '<:sith:590894953131933707>',
	'triangle-2':   '<:triangle:590894953379528790>',
	'wolffe':       '<:wolffe:590894953329066015>',
}
