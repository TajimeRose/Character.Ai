
python -m venv .venv
. .venv/Scripts/activate  # บน Windows
pip install -r requirements.txt
pip install flask pymongo
copy .env.example .env    # แล้วแก้ค่าใน .env
pip install flask pymongo
python app.py
