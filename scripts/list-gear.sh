#!/bin/bash

wget -O- swgoh.gg/api/gear/ | python3 -m json.tool  | less
