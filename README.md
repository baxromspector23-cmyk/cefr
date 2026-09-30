# English Platform (SaaS) — 1-bosqich: Core

Kurs markazlari uchun ingliz tili o'qitish platformasi. Hozir tayyor: database sxemasi (barcha modullar uchun),
auth (JWT + refresh rotation), rollar, multi-tenancy, audit log, login limiter, Docker.

## Ishga tushirish (Docker)
1. `.env.example` ni `.env` ga nusxalang, `SECRET_KEY` ni almashtiring
2. `docker compose up -d --build`
3. Super admin yaratish: `docker compose exec api python -m scripts.create_super_admin`
4. Brauzerda oching: http://localhost:8000/docs  (API sinash sahifasi)

## Ishga tushirish (Docker'siz, Windows)
```
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy ..\.env.example .env      (DATABASE_URL ni sqlite:///./dev.db qilib qo'ying)
python -m scripts.create_super_admin
uvicorn app.main:app --reload
```

## Testlar
```
cd backend
pytest -v
```

## Tekshirish ro'yxati
- /docs da `POST /auth/login` (telefon + parol, center_slug bo'sh) → token oling
- Authorize tugmasiga tokenni kiriting
- `POST /centers` bilan markaz yarating → markaz admini bilan (center_slug bilan) kiring
- `POST /users` bilan ustoz va o'quvchi yarating
- Boshqa markaz admini bu foydalanuvchilarni ko'rmasligini tekshiring
