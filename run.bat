@echo off
:: バッチファイルがある場所にカレントディレクトリを移動
cd /d %~dp0

:: 仮想環境内のpython.exeを直接叩いて実行
".\.venv\Scripts\python.exe" main.py


:: to only activate the virtual environment, execute the following line instead of this script
:: .\.venv\Scripts\activate

pause