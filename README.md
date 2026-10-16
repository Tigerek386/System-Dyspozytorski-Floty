# FleetRoute

Web dispatch system for small transport companies (Django + SQLite), built from the
FleetRoute project brief.

## Features (MVP scope)

- Web interface with registration and login for two user roles: **dispatcher** and **fleet manager**
- SQLite database with relations: vehicles, drivers, transport orders
- Visible transport deadlines (planned start/end per order)
- Validation of **time conflicts** (a vehicle/driver can't have two overlapping active orders)
  and of the **max load capacity** (cargo weight vs. vehicle limit)
- Order lifecycle statuses: new → assigned → in progress → completed / cancelled
- Profitability calculator: `profit = price − estimated cost` per order
- Single dashboard page to view and add vehicles, drivers and orders
- Unit + integration tests with pytest / pytest-cov

## Setup (uv)

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed     # optional: demo data
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000/ — register an account (or use the seeded users).

### Seeded accounts

| username | role | password |
|---|---|---|
| `dispatcher1` | dispatcher | `password123` |
| `fleetmanager1` | fleet manager | `password123` |

## Tests

```bash
uv run pytest
```

## Layout

- `fleetroute/` – Django project (settings, urls)
- `accounts/` – custom user with role, registration/login/logout
- `fleet/` – vehicles, drivers, transport orders, dashboard, seed command
- `templates/` – base layout + auth + dashboard pages
