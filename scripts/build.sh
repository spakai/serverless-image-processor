#!/usr/bin/env bash
# Build build/processor.zip with Pillow compiled for the Lambda runtime.
# Pillow ships native code, so we pull the manylinux wheel rather than whatever
# matches the machine running this script.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$ROOT/build"

rm -rf "$BUILD"
mkdir -p "$BUILD/package"

pip install -r "$ROOT/src/processor/requirements.txt" \
  --target "$BUILD/package" \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.12 \
  --only-binary=:all: --upgrade

cp "$ROOT/src/processor/handler.py" "$BUILD/package/"
( cd "$BUILD/package" && zip -qr "$BUILD/processor.zip" . )
echo "built $BUILD/processor.zip"
