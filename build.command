#!/bin/bash

# スクリプトがある場所にディレクトリを移動
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "making virtual environment..."
    # python3.12がインストールされている前提です。
    # コマンドが見つからない場合は python3 に書き換えてください。
    python3.12 -m venv .venv
fi

echo "Checking and installing libraries..."

# mac/linuxでは 'Scripts' ではなく 'bin' ディレクトリになります
./.venv/bin/python -m pip install -r requirements.txt