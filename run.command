#!/bin/bash

# このスクリプトがある場所にディレクトリを移動
# (macOSでダブルクリック起動した場合に必要です)
cd "$(dirname "$0")"

# 仮想環境内のpythonを直接指定して実行
# Windowsの Scripts フォルダではなく、Macでは bin フォルダになります
echo "Running main.py using the virtual environment's Python..."
./.venv/bin/python main.py

# --- Pause機能の再現 ---
# 処理が終わった後、ウィンドウがすぐに閉じないように入力を待ちます
echo ""
echo "-------------------------------------------------------"
echo "Process finished. Press Enter to exit..."
read