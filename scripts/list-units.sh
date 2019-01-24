#!/bin/bash

wget -O- swgoh.gg/api/characters/ | python3 -m json.tool  | less
