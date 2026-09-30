# Arxitektura

## Qarorlar
- **Modulli monolit** (bitta FastAPI ilova). Microservice va Redis hozircha yo'q: bitta dasturchi uchun keraksiz murakkablik.
- **Sync SQLAlchemy 2.0**: oddiyroq va xatosizroq. Yuk oshsa async'ga o'tish mumkin.
- **Multi-tenancy**: har bir biznes jadvalda `center_id`. Barcha so'rovlar `tenant_select()` orqali; boshqa markaz obyekti 404 qaytaradi.
- **Pul**: butun son (so'm). To'lovlar `payments` ledger'ida, o'chirilmaydi, tuzatish `adjustment` bilan.
- **Enum**: `native_enum=False` (PostgreSQL migratsiyasi oson).
- **Migratsiyalar**: Alembic (`alembic upgrade head` konteyner ishga tushganda avtomatik). Baseline 0001 yozilgan; keyingi o'zgarishlar `alembic revision --autogenerate` bilan.
- **Audit**: login, markaz/foydalanuvchi yaratish va keyingi barcha moliyaviy/baho/davomat o'zgarishlari.

## Papkalar
```
EnglishPlatform/
├── docker-compose.yml, .env.example
└── backend/
    ├── app/
    │   ├── main.py, config.py, db.py, security.py, deps.py, schemas.py
    │   ├── models/   base, core, education, attendance, finance
    │   ├── routers/  auth, centers, users   (keyingi bosqichlarda: education, attendance, finance ...)
    │   └── services/ audit, ratelimit
    ├── scripts/create_super_admin.py
    └── tests/        auth, tenancy
```
(bot/ va web/ papkalari 2 va 5-bosqichlarda qo'shiladi)

## Jadvallar
| Guruh | Jadvallar |
|---|---|
| Platforma | centers, plans, subscriptions |
| Foydalanuvchi | users, student_profiles, refresh_tokens, telegram_link_codes, audit_logs |
| Ta'lim | subjects, courses, units, lessons, groups, group_students |
| Savol va test | questions, tests, test_questions, test_attempts, attempt_answers, mistakes |
| Topshiriq | assignments, submissions, certificates |
| Davomat | class_sessions, attendance_records, attendance_qr_tokens |
| Moliya | payments, teacher_pay_rules, teacher_accruals, teacher_payouts |

## Ma'lumotlar oqimi (asosiylari)
- `questions.source=platform, center_id=NULL, is_locked=true` → daraja aniqlash (500 ta), faqat super admin o'zgartiradi
- `questions.source=teacher` → status: draft → pending → approved (center_admin tasdiqlaydi)
- Davomat: `class_sessions` (guruh + kun) → `attendance_records` (teacher/telegram/qr manbasi, `confirmed_by_teacher`)
- Maosh: `teacher_pay_rules` + davomat/tushum → `teacher_accruals`; haqiqiy to'lov → `teacher_payouts`

## Hali qilinmagan (halol ro'yxat)
- Telegram bot va mavjud bot.py'ni ulash (2-bosqich)
- Ta'lim, davomat, to'lov, maosh endpointlari (2–4-bosqichlar)
- Web panellar (5), analytics/AI/sertifikat (6), nginx/HTTPS/backup (7), sotuv paketi (8)
- Service qatlamida markaz mosligi tekshiruvi (masalan, guruh va o'quvchi bir markazdan ekani) — endpointlar yozilganda
