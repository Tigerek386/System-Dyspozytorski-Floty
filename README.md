# FleetRoute

Web app system dla małych firm transportowych (Django + SQLite) [FleetRoute.pdf](https://github.com/user-attachments/files/33556627/FleetRoute.pdf)

## Wymagania
git
uv/python3.12+(uv instaluje pythona automatycznie przy tworzeniu venv)

## Setup z uv (rekomendowane)
```bash
git clone https://github.com/Tigerek386/System-Dyspozytrski-Floty && cd System-Dyspozytrski-Floty
uv sync
uv run python manage.py migrate
uv run python manage.py seed     # opcjonalne: demo data
uv run python manage.py runserver
```
## Setup z base pythonem (nietestowane)
```bash
git clone https://github.com/Tigerek386/System-Dyspozytrski-Floty && cd System-Dyspozytrski-Floty
python -m venv .venv
.venv/Scripts/activate (zależne od systemu)
pip install django pytest pytest-django pytest-cov
python manage.py migrate
python manage.py seed     # opcjonalne: demo data
python manage.py runserver
```
Otwórz http://127.0.0.1:8000/ — zarejestruj konto (lub użyj zseedowanych użytkowników).

### Seeded konta

| username | role | password |
|---|---|---|
| `driver1` | driver | `password123`| 
| `dispatcher1` | dispatcher | `password123` |
| `fleetmanager1` | fleet manager | `password123` |

## Test

```bash
uv run pytest | python -m pytest
```

## Layout

- `fleetroute/` – projekt Django (ustawienia, urls)
- `accounts/` – custom użytkownicy z rolami, rejestracja/login/logout
- `fleet/` – pojazdy, kierowcy, zlecenia transportu, dashboard, komendy seed
- `templates/` – podstawowy układ + auth + strony dashboardu 
