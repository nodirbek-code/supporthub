# SupportHub — mijozlar murojaatlarini boshqarish tizimi

Django REST Framework asosida qurilgan backend tizim: kompaniya mijozlari yuborgan
murojaatlarni (ticket) qabul qilish va operatorlar tomonidan boshqarish uchun.


## Loyiha strukturasi

```
supporthub/
├── supporthub/         # asosiy sozlamalar (settings, urls, asgi, celery)
├── users/              # User modeli, JWT auth (register/login/profile)
├── tickets/            # Category, Ticket, Message, TicketHistory + API
├── chat/               # WebSocket consumer (real vaqt yozishma)
├── common/             # middleware, pagination, permissions, exceptions
├── requirements.txt
├── .env.example
└── manage.py
```

## O'rnatish va ishga tushirish

### 1. Virtual muhit va kutubxonalar

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. .env faylini sozlash

```bash
cp .env.example .env
# .env faylidagi qiymatlarni o'zingizga moslang
```

### 3. PostgreSQL va Redis'ni ishga tushirish (Docker orqali)

```bash
docker compose up -d
```

### 4. Migratsiyalar

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Superuser yaratish

```bash
python manage.py createsuperuser
```

### 6. Serverlarni ishga tushirish

Loyiha to'liq ishlashi uchun **5 ta jarayon** parallel ishlashi kerak (har birini
alohida terminalda ishga tushiring):

```bash
# 1) Django + WebSocket server (Daphne, ASGI orqali)
daphne -b 0.0.0.0 -p 8000 supporthub.asgi:application

# 2) Celery worker
celery -A supporthub worker -l info

# 3) Celery Beat (davriy vazifalar uchun)
celery -A supporthub beat -l info

# 4) PostgreSQL va Redis (agar Docker orqali ishlatmasangiz, alohida o'rnatilgan bo'lishi kerak)

# 5) (ixtiyoriy) oddiy development uchun:
python manage.py runserver
```

> Eslatma: WebSocket (`/ws/...`) ishlashi uchun albatta **Daphne** (yoki boshqa ASGI server)
> orqali ishga tushirish kerak — oddiy `runserver` WebSocket'ni qo'llab-quvvatlamaydi.

## Testlarni ishga tushirish

Testlar SQLite va in-memory backendlar bilan ishlaydi — Docker shart emas:

```bash
python manage.py test --settings=supporthub.settings_test
# yoki
pytest
```

21 ta test mavjud: autentifikatsiya, ticket CRUD, permissionlar, filter/search,
pagination, Redis cache, middleware va WebSocket funksiyalari qamrab olingan.

## API hujjatlari

Server ishga tushgandan so'ng:

- Swagger UI: `http://localhost:8000/api/docs/`
- Redoc: `http://localhost:8000/api/redoc/`
- OpenAPI schema: `http://localhost:8000/api/schema/`

## Asosiy endpointlar

| Metod | Endpoint | Tavsif |
|---|---|---|
| POST | `/api/auth/register/` | Ro'yxatdan o'tish |
| POST | `/api/auth/login/` | Tizimga kirish (JWT olish) |
| POST | `/api/auth/token/refresh/` | Tokenni yangilash |
| GET/PATCH | `/api/auth/profile/` | Profil |
| GET/POST | `/api/categories/` | Kategoriyalar |
| GET/PATCH/DELETE | `/api/categories/{id}/` | Kategoriya tafsiloti |
| GET/POST | `/api/tickets/` | Murojaatlar ro'yxati / yaratish |
| GET/PATCH/DELETE | `/api/tickets/{id}/` | Murojaat tafsiloti |
| GET | `/api/tickets/statistics/` | Statistika (Redis cache, 5 daqiqa) |
| GET | `/api/tickets/{id}/messages/` | Ticket xabarlari tarixi |
| WS | `ws://localhost:8000/ws/tickets/{id}/?token=<access>` | Real vaqt chat |

## Rollarga oid qoidalar

- **client** — faqat o'z ticketlarini ko'radi va yaratadi; status/operator maydonlarini o'zgartira olmaydi.
- **operator** — faqat o'ziga biriktirilgan ticketlarni ko'radi va boshqaradi.
- **admin** — barcha ticket va kategoriyalarni to'liq boshqaradi.
