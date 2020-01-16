#!/bin/bash

wget -q -O- swgoh.gg/api/ships/ | python -m json.tool  | less
