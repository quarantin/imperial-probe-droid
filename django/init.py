from swgoh.models import *

#test = BaseShip.get_all_ships()
#gears = Gear.get_all_gear()
#for gear in gears:
#	print(gear.get_url())
#	print(gear.get_image())

#test = BaseUnit.get_all_units()
#Gear.get_all_gear()
#BaseUnit.get_all_units()
#BaseUnitGear.get_all_unit_gear_levels()
test = BaseUnitGear.get_unit_gear_levels('COUNTDOOKU')
for level in test:
	print(level)
