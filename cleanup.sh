#!/bin/sh

set -e

./scowl sort --replace adjust data/variants
./scowl sort --replace adjust data/fixes
./scowl sort --replace merge data/signature
