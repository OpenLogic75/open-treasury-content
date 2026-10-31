#!/bin/sh
# Copy the current content into both apps' bundled fallback (run before each app release).
set -e
cd "$(dirname "$0")/.."
ANDROID="${ANDROID_ASSETS:-$HOME/AndroidStudioProjects/OpenTreasury/app/src/main/assets/content}"
IOS="${IOS_BUNDLE:-$HOME/Open-Treasury/ios/OpenTreasury/OpenTreasury/Content}"
for dest in "$ANDROID" "$IOS"; do
  if [ -d "$(dirname "$dest")" ]; then
    rm -rf "$dest/v1" && mkdir -p "$dest" && cp -R v1 "$dest/v1" && echo "Synced to $dest"
  fi
done
