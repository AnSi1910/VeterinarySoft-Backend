# VeterinarySoft - Backend (практичне завдання № 16)

Навчальний серверний прототип ветеринарного застосунку на Python + FastAPI + SQLAlchemy + SQLite. Дві ролі: власник тварини (`owner`) та адміністратор клініки (`admin`). Продовжує рішення із ПЗ4, ПЗ9 і ПЗ10.

## Що вже реалізовано

SQL-таблиці `users`, `pets`, `veterinarians`, `appointments`, `medical_records`, `reminders` зі зв'язками та зовнішніми ключами.
ORM SQLAlchemy 2; перевірка структур запитів через Pydantic 2.
Реєстрація, вхід за email і паролем; JWT Bearer; паролі зберігаються як Argon2id-хеші.
Рольові обмеження: власник бачить лише своїх тварин/записи/медкартки; адміністратор керує лікарями і створює медичні записи.
REST API, OpenAPI/Swagger за адресою `/docs`.
Захист від подвійного бронювання одного часу у ветеринара (частковий унікальний індекс БД для активних записів).
Коди помилок 401, 403, 404, 409 і 422; автоматичні тести.

**Обмеження прототипу:** фактична доставка push-повідомлень через FCM ще не реалізована: API дозволяє лише створювати та переглядати заплановані нагадування. Також ще немає графіка робочих годин лікарів, перенесення прийомів, міграцій Alembic, захисту від перебору паролів, відновлення пароля, аудиту змін і production-розгортання. Для роботи з реальними даними пацієнтів і власників це треба реалізувати окремо.

## 1. Як запустити (Windows, PowerShell)

Відкрийте папку проєкту у VS Code, відкрийте Terminal → New Terminal.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

Для стабільного підпису токенів задайте довгий випадковий секрет:

```powershell
$env:VET_SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(48))"
python -m uvicorn app.main:app --reload
```

Відкрийте в браузері:

- **http://127.0.0.1:8000/docs** - інтерактивна документація Swagger UI;
- **http://127.0.0.1:8000/health** - швидка перевірка сервера;
- **http://127.0.0.1:8000/openapi.json** - автоматична специфікація API.

SQLite-файл `veterinarysoft.db` створюється автоматично при запуску сервера.

## 2. Створення адміністратора

Реєстрація через API створює лише власника тварини, не адміністратора. Для адміністратора відкрийте інший термінал у папці проєкту, активуйте середовище й виконайте:

```powershell
python -m scripts.create_admin --email admin@example.com --name "Адміністратор клініки"
```

Пароль вводиться приховано (мінімум 8 символів).

## 3. Як перевірити у Swagger UI

1. `POST /api/auth/register`: зареєструйте власника (вкажіть email, ім'я, пароль від 8 символів).
2. Натисніть Authorize. У формі логіну поле `username` - це ваш email, `password` - пароль.
3. `POST /api/pets`: додайте тварину (`name`, `species`, опційно `breed`).
4. `GET /api/pets`: переконайтеся, що тварина збережена у SQLite.
5. Увійдіть як адміністратор і викличте `POST /api/veterinarians` (додайте лікаря).
6. Знову увійдіть як власник і викличте `POST /api/appointments`, вказавши `pet_id`, `veterinarian_id` і майбутній час з поясом, наприклад `2030-03-10T13:00:00+02:00`.
7. Увійдіть як адміністратор і викличте `PATCH /api/appointments/{id}/status`, вказавши `{"status":"confirmed"}`.
8. Адміністратор може додати медичний запис у `POST /api/medical-records`; власник зможе прочитати його через `GET /api/medical-records/pet/{id}`.

## 4. Основні маршрути

| Метод | Шлях | Хто може |
|---|---|---|
| POST | `/api/auth/register` | Усі |
| POST | `/api/auth/login` | Усі |
| GET, PATCH | `/api/users/me` | Авторизований |
| GET | `/api/users`, `/api/users/{id}` | Адміністратор |
| GET, POST | `/api/pets` | Авторизований (власні тварини) |
| GET, PATCH, DELETE | `/api/pets/{id}` | Власник тварини / адміністратор |
| GET | `/api/veterinarians` | Усі |
| POST | `/api/veterinarians` | Адміністратор |
| PATCH | `/api/veterinarians/{id}/deactivate` | Адміністратор |
| GET, POST | `/api/appointments` | Авторизований |
| GET | `/api/appointments/{id}` | Власник тварини / адміністратор |
| PATCH | `/api/appointments/{id}/status` | Власник: скасувати; адміністратор: підтвердити/завершити/скасувати |
| POST | `/api/medical-records` | Адміністратор |
| GET | `/api/medical-records/pet/{id}` | Власник тварини / адміністратор |
| GET, POST | `/api/reminders` | Авторизований |
| DELETE | `/api/reminders/{id}` | Власник тварини / адміністратор |

## 5. Як запустити тести

```powershell
python -m pytest -q
```

Тести використовують тимчасову БД і не зачіпають основну базу `veterinarysoft.db`.

## 6. Структура

```text
VeterinarySoft_Backend/
├── app/
│   ├── main.py              # FastAPI та OpenAPI
│   ├── database.py          # SQLite/SQLAlchemy і сесії
│   ├── models.py            # SQL-таблиці (ORM)
│   ├── schemas.py           # Перевірка даних Pydantic
│   ├── security.py          # JWT та Argon2id
│   ├── services.py          # Перевірки доступу до тварини
│   └── routers/             # API за функціональними модулями
├── scripts/create_admin.py  # Безпечне створення адміністратора
├── tests/                   # Автотести API
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
└── README.md
```

## 7. Примітки до архітектури

- Frontend звертається до Backend через HTTPS/REST API, обмін - JSON.
- Сам Backend читає та змінює SQLite, прямого доступу Frontend до БД немає.
- Усі дати і час у відповідях API трактуються як UTC. У POST для записів і нагадувань слід передавати часовий пояс; сервер перетворює час на UTC.
- Прототип використовує `Base.metadata.create_all()` - для зміни структури існуючої БД надалі потрібні **Alembic-міграції**.
- Для реального доступу через інтернет потрібні TLS/HTTPS, постійний секрет, надійне зберігання конфігурації, резервні копії, обмеження частоти запитів та окреме налаштування CORS.

## Документація

- [FastAPI: SQL databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [FastAPI: OAuth2/JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/)
- [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/)
- [SQLite foreign keys](https://www.sqlite.org/foreignkeys.html)
