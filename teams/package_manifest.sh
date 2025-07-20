#!/usr/bin/env bash
# Package Teams manifest for deployment
mkdir -p package
zip -j package/teams_bot.zip manifest.json
