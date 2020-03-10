#!/usr/bin/env python

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

from config import load_config
from swgohhelp import get_ability_name

skill_id = 'leaderskill_VADER'
language = 'eng_us'

test = get_ability_name(skill_id, language)
print(test)
