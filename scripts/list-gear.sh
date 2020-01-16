#!/bin/bash

wget -q -O- swgoh.gg/api/gear/ | python -m json.tool  | less
