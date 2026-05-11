# Stage Monitoring Tool

Een compleet stagevolgsysteem met:
- **Frontend**: Interactieve HTML/CSS/JS met API-integratie
- **Backend**: FastAPI + SQLite REST API
- **Authenticatie**: JWT-tokens met rolgebaseerde toegang

## 🚀 Snelle Start

### 1. Alles Starten

```bash
./start.sh
```

Dit start:
- **Backend API**: http://localhost:8001
- **Frontend**: http://localhost:8080

Ga dan naar **http://localhost:8080/index-api.html**

### 2. Eerste Keer Instellen

```bash
cd backend
python init_admin.py
```

Dit maakt de database en testgebruikers aan.

### 3. Inloggen

Gebruik een van deze testaccounts:

| Rol | E-mail | Wachtwoord |
|------|-------|----------|
| Admin | admin@school.be | admin123 |
| Student | student1@school.be | student123 |
| Commissie | commissie1@school.be | commissie123 |
| Docent | docent1@school.be | docent123 |
| Mentor | mentor1@school.be | mentor123 |

---

## 📁 Projectstructuur

```
prog-project-wt2/
├── prototype/                    # Frontend
│   ├── index.html               # Origineel prototype
│   ├── index-improved.html      # Lokaal (localStorage)
│   ├── index-api.html           # API-versie ⭐
│   ├── api-client.js            # API-client module
│   ├── app-api.js               # Geïntegreerde app
│   └── styles-improved.css      # Gedeelde stijlen
├── backend/                     # FastAPI Backend
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── database.py          # SQLAlchemy
│   │   ├── models.py            # Database-modellen
│   │   ├── schemas.py           # Pydantic schema's
│   │   ├── auth.py              # JWT-hulpprogramma's
│   │   └── routers/             # API-endpoints
│   ├── init_admin.py            # Eerste keer instellen
│   ├── seed.py                  # Extra testgegevens
│   └── requirements.txt
├── start.sh                     # Snelstart script
└── PLAN.md                      # Implementatieplan
```

---

## 🎯 Drie Beschikbare Versies

### 1. **index-api.html** ⭐ (Aanbevolen)
Volledige backend-integratie met:
- JWT-authenticatie (inloggen/uitloggen)
- Echte API-aanroepen naar FastAPI-backend
- Database-persistentie
- Rolgebaseerde weergaven
- Bestandsuploads (PDF-overeenkomsten)

### 2. **index-improved.html**
Lokaal-only versie met:
- localStorage-persistentie
- Toast-meldingen
- Laadtoestanden
- Geen backend nodig

### 3. **index.html**
Origineel prototype (ter referentie)

---

## 🔧 Handmatige Installatie

Als u `start.sh` liever niet gebruikt:

**Terminal 1 - Backend:**
```bash
cd backend
pip install -r requirements.txt
python init_admin.py        # Alleen eerste keer
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd prototype
python3 -m http.server 8080
```

Bezoek http://localhost:8080/index-api.html

---

## 📚 API-documentatie

Zodra de backend draait:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **Health Check**: http://localhost:8001/health

### Belangrijkste Endpoints

| Endpoint | Methode | Beschrijving | Auth |
|----------|--------|-------------|------|
| `/auth/login` | POST | Inloggen | Nee |
| `/auth/me` | GET | Huidige gebruiker | Ja |
| `/internships` | GET | Lijst stages | Ja |
| `/internships` | POST | Stage aanmaken | Student |
| `/internships/{id}/status` | PATCH | Status updaten | Commissie |
| `/internships/{id}/agreement` | POST | PDF uploaden | Student |
| `/internships/{id}/logbooks` | GET | Logboeken ophalen | Ja |
| `/internships/{id}/logbooks` | POST | Logboek aanmaken | Student |
| `/competencies` | GET | Competenties lijst | Ja |
| `/competencies` | POST | Competentie toevoegen | Admin |

---

## 🔐 Authenticatie-flow

1. Gebruiker logt in met e-mail/wachtwoord
2. Backend retourneert JWT-toegangstoken
3. Token opgeslagen in localStorage
4. API-client voegt token toe aan alle aanvragen: `Authorization: Bearer <token>`
5. Backend valideert token en stelt gebruikerscontext in

---

## 🧪 Testen

### Backend-tests:
```bash
cd backend
pytest
```

### API-test met curl:
```bash
# Inloggen
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@school.be&password=admin123"

# Stage aanmaken (met token)
curl -X POST "http://localhost:8001/internships" \
  -H "Authorization: Bearer UW_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Testbedrijf",
    "contact_person": "Jan Jansen",
    "contact_email": "jan@test.nl",
    "start_date": "2026-09-01",
    "end_date": "2027-01-31",
    "description": "Teststage"
  }'
```

---

## 🗄️ Databaseschema

### Gebruikers
- id, email, password_hash, rol
- first_name, last_name, is_active

### Stages (Internships)
- id, student_id, company_name
- contact_person, contact_email
- start_date, end_date, description
- status, agreement_uploaded
- committee_feedback

### Logboeken (Logbooks)
- id, internship_id, week_number
- tasks, reflection, issues
- status, mentor_validated

### Evaluaties (Evaluations)
- id, internship_id, evaluator_id
- type, scores (JSON), comments
- finalized

### Competenties (Competencies)
- id, name, weight, active

---

## 🚦 Statusflow

```
Ingediend → In Beoordeling → Goedgekeurd → Overeenkomst Ingediend → Lopend → Afgerond
                ↓
        Aanpassingen Vereist
                ↓
           Ingediend (opnieuw)
                
In Beoordeling → Afgekeurd
```

Speciale regel: Om naar "Lopend" te gaan, moet `agreement_uploaded = true` zijn

---

## 🎨 Frontend-architectuur

### api-client.js
- `AuthAPI`: Inloggen, registreren, uitloggen, tokenbeheer
- `InternshipsAPI`: Alle stage-operaties
- `CompetenciesAPI`: Competentiebeheer

### app-api.js
- Authenticatie-afhandeling
- Rolgebaseerde weergave-rendering
- Formulier-koppeling per rol
- Toast-meldingen
- Laadtoestanden

---

## 🔧 Veelvoorkomende Problemen

**CORS-fouten**: Backend is al geconfigureerd met CORS. Zorg dat u de frontend benadert via `localhost`, niet `file://`.

**Database vergrendeld**: Stop de backend en verwijder `backend/stage_monitoring.db`, voer daarna opnieuw `init_admin.py` uit.

**Poort al in gebruik**: Beëindig bestaande processen of wijzig poorten in `start.sh`.

---

## 📝 Volgende Stappen / TODO

- [ ] Meer dashboard-widgets toevoegen
- [ ] Mentor-validatie UI implementeren
- [ ] E-mailmeldingen toevoegen
- [ ] Rapporten exporteren naar PDF
- [ ] Batch-operaties voor commissie toevoegen
- [ ] Evaluatiefinalisatie implementeren

---

## 📄 Internationale Versie

- [README-EN.md](README-EN.md) - English documentation

---

## 📄 Licentie

Schoolproject - Groep 2
