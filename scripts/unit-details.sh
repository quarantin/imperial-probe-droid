#!/bin/bash

wget -O- swgoh.gg/api/characters/80/ | python3 -m json.tool  | less
