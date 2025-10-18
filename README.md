...existing code...
# AI Character Chat — Local setup & usage

คำอธิบายสั้น ๆ
โปรเจกต์นี้รันเป็นเว็บแอป Flask ที่ให้คุณเลือกตัวละครและคุยกับโมเดล LLM ผ่านหน้าเว็บ (มีระบบผู้ใช้แบบ guest และตัวเลือกเชื่อมต่อ Firebase)  

ความต้องการระบบ (prerequisites)
- Python 3.10+ (หรือเวอร์ชันที่รองรับ)
- (เลือก) MongoDB ถ้าต้องการเก็บข้อมูลแบบถาวร — ถ้าไม่ได้ใช้แอปจะใช้ฐานข้อมูล in-memory
- คีย์ OpenAI ในตัวแปรสภาพแวดล้อม: OPENAI_API_KEY

ติดตั้ง (local)
1. คลอน/ดาวน์โหลด repository นี้ แล้วเข้าโฟลเดอร์โปรเจกต์
2. สร้าง virtual environment และติดตั้ง dependencies:
```bash
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS / Linux
# source .venv/bin/activate

pip install -r [requirements.txt](http://_vscodecontentref_/9) 

3. คัดลอกไฟล์ .env หรือกำหนดตัวแปรสภาพแวดล้อมที่จำเป็น:
สร้างไฟล์ .env ใน root ของโปรเจกต์ หรือตั้ง environment variables
ตัวอย่าง .env ที่ควรใส่ (อย่าใส่คีย์จริงในที่สาธารณะ):
OPENAI_API_KEY=sk-xxxx
MONGO_URI=mongodb://localhost:27017
DB_NAME=ai_character_mvp
USE_GUEST_AUTH=true

# (ถ้าต้องการ) ค่า Firebase:
FIREBASE_PROJECT_ID=...
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_APP_ID=...
FIREBASE_CREDENTIALS_JSON='{"type": "...", ... }'

การเตรียมข้อมูลตัวละคร (seed)

ถ้าต้องการใส่ข้อมูลตัวละครเริ่มต้นลง DB ให้รัน:
python [seed_characters.py](http://_vscodecontentref_/10) 
สคริปต์นี้จะใช้ get_default_characters และ get_db เพื่ออัพเดต/สร้างเอกสารตัวละครในฐานข้อมูล
แล้วเปิดเบราว์เซอร์ไปที่ http://127.0.0.1:5000/

การตั้งค่า Firebase (ออปชัน)

ถ้าจะใช้ Firebase Authentication ให้ตั้งค่าใน .env แล้วในเทมเพลตรับค่าไปยังฝั่งไคลเอนต์ผ่าน Config.firebase_client_config และตรวจสอบสถานะด้วย Config.firebase_enabled
ฝั่งคลไอนต์โค้ดที่เกี่ยวข้องอยู่ที่ static/app.js
จุดที่ควรรู้

การติดต่อกับโมเดลทำผ่านโค้ดใน services/llm_client.py ซึ่งอ่าน persona จาก character_settings.py
หากไม่ตั้งค่า MongoDB แอปจะทำงานโดยใช้ in-memory DB (ดู get_db)
หน้าตาและการโต้ตอบฝั่งไคลเอนต์อยู่ใน static/app.js และ CSS ใน static/main.css
ปัญหาทั่วไป

ถ้าไม่ได้ตั้ง OPENAI_API_KEY แอปจะไม่สามารถเรียก LLM ได้
ตรวจสอบค่า MONGO_URI หากต้องการ persistence
ดู log ในเทอร์มินัลเมื่อรัน python app.py เพื่อดู error details
ไฟล์ที่เกี่ยวข้อง (สำคัญ)

app.py — entry point และ routing ของเว็บแอป
config.py — การอ่านค่าคอนฟิกจาก .env และ helper ของ Firebase
services/db.py — การตั้งค่า DB (MongoDB หรือ in-memory)
character_settings.py — รายการ persona ของตัวละคร
seed_characters.py — สคริปต์ seed ข้อมูลตัวละคร
static/app.js — โลจิกฝั่งลูกค้า (guest token, auth modal, chat flow)