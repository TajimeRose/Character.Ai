
python -m venv .venv
. .venv/Scripts/activate  # บน Windows
pip install -r requirements.txt
copy .env.example .env    # แล้วแก้ค่าใน .env
python seed_characters.py
python app.py
