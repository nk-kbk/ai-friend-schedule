#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# ✨✨ ここに追加！ ✨✨
# データベースの準備が全部終わった後に、初期データを流し込む！
python manage.py loaddata initial_data.json
