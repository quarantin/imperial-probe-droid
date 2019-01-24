#!/bin/bash

wget -O- swgoh.gg/api/ships/ | python3 -m json.tool  | less
