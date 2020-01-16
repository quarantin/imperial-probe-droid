#!/bin/bash

wget -q -O- swgoh.gg/api/characters/ | python -m json.tool  | less
