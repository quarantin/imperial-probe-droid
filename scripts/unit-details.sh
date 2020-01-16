#!/bin/bash

wget -q -O- swgoh.gg/api/characters/80/ | python -m json.tool  | less
