# ARCHITECTURE.md
## Simulador Mundial 2026 — Contexto para Quality Gates

Este archivo es el contexto del proyecto para cargar en el agente antes del live coding
de la Clase 6 "Quality Gates con GenIA". Usalo como fuente de verdad para interpretar
los hallazgos de Ruff y SonarQube.

---

## Stack tecnologico

| Capa | Tecnologia | Version |
|---|---|---|
| Framework web | FastAPI | >= 0.110.0 |
| ORM | SQLAlchemy | >= 2.0.0 |
| Base de datos | SQLite | (archivo local worldcup.db) |
| Validacion | Pydantic v2 | >= 2.10.0 |
| Servidor | Uvicorn | >= 0.29.0 |
| HTTP client (tests) | HTTPX | >= 0.27.0 |
| Testing | pytest | >= 8.0.0 |
| Cobertura | pytest-cov | >= 5.0.0 |
| E2E frontend | Playwright | >= 1.44.0 |
| Analisis estatico | Ruff | ultima version |
| Auditoria de calidad | SonarQube | (Docker local) |
| Reportes de test | Allure | >= 2.13.0 |
| Runtime | Python | 3.12 |

---

## Estructura de carpetas

```
live-coding/
├── main.py                    Entrada de la app: crea la app FastAPI y registra los routers
├── database.py                Configuracion de SQLAlchemy: engine, SessionLocal, Base
│
├── models/                    Modelos ORM (mapeo a tablas SQLite)
│   ├── player.py              Jugador: id, name, position, rating, team_id
│   ├── team.py                Seleccion: id, name, code, group
│   └── user.py                Usuario del sistema: id, email, hashed_password
│
├── repositories/              Acceso a datos — unica capa que toca la DB
│   ├── player_repository.py   CRUD de jugadores
│   ├── team_repository.py     CRUD de selecciones (incluye count())
│   └── user_repository.py     CRUD de usuarios (BAJA COBERTURA: 41%)
│
├── services/                  Logica de negocio — orquesta repositorios
│   ├── simulator_service.py   Motor principal: simula fase de grupos y eliminacion directa
│   ├── metrics_service.py     Calcula estadisticas post-simulacion
│   ├── player_service.py      Logica de jugadores
│   ├── team_service.py        Logica de selecciones
│   ├── user_service.py        Logica de usuarios (BAJA COBERTURA: 32%)
│   └── simulation_cache.py    Cache en memoria para resultados de simulacion
│
├── routers/                   Endpoints FastAPI — reciben HTTP, delegan a services
│   ├── simulator.py           POST /simulator/run — endpoint principal
│   ├── metrics.py             GET /metrics/... — estadisticas del dashboard
│   ├── players.py             CRUD /players/
│   ├── teams.py               CRUD /teams/
│   └── users.py               CRUD /users/ (COBERTURA: 62%)
│
├── schemas/                   Pydantic: contratos de request/response
│   ├── simulator.py           SimulatorResponse, MatchResult, GroupStanding, etc.
│   ├── metrics.py             Schemas de metricas del dashboard
│   ├── player.py              PlayerCreate, PlayerResponse
│   ├── team.py                TeamCreate, TeamResponse, TeamWithPlayers
│   └── user.py                UserCreate, UserResponse
│
├── tests/                     Suite de tests con pytest + TestClient
│   ├── conftest.py            Fixtures: app de test, client, DB en memoria
│   ├── test_simulator.py      Tests del endpoint POST /simulator/run (cobertura alta)
│   ├── test_dashboard.py      Tests de metricas del dashboard
│   ├── test_players.py        Tests CRUD de jugadores
│   ├── test_teams.py          Tests CRUD de selecciones
│   └── test_frontend_smoke.py Tests E2E con Playwright (requiere browser, excluir en CI)
│
├── static/                    Frontend: HTML + imagenes
│   └── index.html             UI del simulador (formulario + resultados)
│
├── ARCHITECTURE.md            Este archivo — contexto para el agente
├── PROMPT_RTC_QG.md           Prompts RTC para Quality Gates
├── TIMELINE_DOCENTE.md        Storytelling del live coding
└── requirements.txt           Dependencias del proyecto
```

---

## Endpoint principal

```
POST /simulator/run
```

- No recibe body.
- Valida que existan exactamente 32 selecciones con al menos 1 jugador cada una.
- Simula fase de grupos (8 grupos de 4, 3 partidos por grupo, clasifican los 2 mejores).
- Simula eliminacion directa (octavos, cuartos, semifinal, final).
- Devuelve `SimulatorResponse` con resultado completo.
- Cachea el resultado en memoria (ultima simulacion disponible en GET /metrics).

---

## Metricas de calidad actuales

### Ruff — Analisis estatico

Ejecutado con: `ruff check .`
Resultado: **10 errores en 4 categorias**

```
5  F401  unused-import
2  F541  f-string-missing-placeholders
2  F841  unused-variable
1  E402  module-import-not-at-top-of-file

[*] 7 fixable automaticamente con --fix
```

**Detalle de cada hallazgo:**

| Codigo | Categoria | Archivo | Linea | Descripcion |
|--------|-----------|---------|-------|-------------|
| E402 | Estilo | schemas\team.py | 32 | Import fuera de lugar — workaround para dependencia circular con schemas\player.py |
| F401 | Imports | services\metrics_service.py | 1 | `import os` — nunca se usa en este archivo |
| F401 | Imports | services\simulation_cache.py | 1 | `import json` — nunca se usa en este archivo |
| F401 | Imports | services\simulator_service.py | 2 | `import json` — nunca se usa en este archivo |
| F401 | Imports | services\simulator_service.py | 3 | `import sys` — nunca se usa en este archivo |
| F401 | Imports | services\simulator_service.py | 8 | `KnockoutMatch` — schema importado pero no integrado a la logica |
| F841 | Bugs | services\simulator_service.py | 141 | `y = self.player_repo.get_all()` — query completa a la DB, variable nunca usada |
| F841 | Bugs | tests\test_dashboard.py | 95 | `team_players` — lista construida pero nunca usada en el test |
| F541 | Estilo | tests\test_simulator.py | 311 | `f"Team extra"` — f-string sin interpolacion |
| F541 | Estilo | tests\test_simulator.py | 311 | `f"TE"` — f-string sin interpolacion |

**Hallazgos criticos para Quality Gate:**
- `F841 simulator_service.py:141` — impacto en performance (query innecesaria en ruta critica)
- `F401 simulator_service.py:8` — feature incompleta o codigo muerto en el motor de simulacion

### pytest-cov — Cobertura de tests

Ejecutado con: `pytest tests/ --cov=. --cov-report=term-missing --ignore=tests/test_frontend_smoke.py`
Resultado: **89% total — 69 tests pasados**

```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
database.py                            11      4    64%
demo_playwright.py                     55     55     0%   (script standalone, no forma parte del flujo)
main.py                                12      0   100%
models\__init__.py                      4      0   100%
models\player.py                       12      0   100%
models\team.py                        12      0   100%
models\user.py                          9      0   100%
repositories\__init__.py                4      0   100%
repositories\player_repository.py      30      0   100%
repositories\team_repository.py        29      0   100%
repositories\user_repository.py        27     16    41%   <- BAJA COBERTURA
routers\__init__.py                     6      0   100%
routers\metrics.py                     10      0   100%
routers\players.py                     26      0   100%
routers\simulator.py                   10      0   100%
routers\teams.py                       26      0   100%
routers\users.py                       26     10    62%   <- COBERTURA MEDIA
schemas\__init__.py                    6      0   100%
schemas\metrics.py                     11      0   100%
schemas\player.py                      18      0   100%
schemas\simulator.py                   30      0   100%
schemas\team.py                        21      0   100%
schemas\user.py                         9      0   100%
services\__init__.py                    6      0   100%
services\metrics_service.py            17      0   100%
services\player_service.py             47      1    98%
services\simulation_cache.py            9      0   100%
services\simulator_service.py         168      5    97%
services\team_service.py               39      1    97%
services\user_service.py               34     23    32%   <- BAJA COBERTURA
tests\conftest.py                      29      0   100%
tests\test_dashboard.py               120      0   100%
tests\test_frontend_smoke.py           26     26     0%   (excluido — requiere browser)
tests\test_players.py                  58      0   100%
tests\test_simulator.py               314      0   100%
tests\test_teams.py                    39      0   100%
-------------------------------------------------------
TOTAL                                1310    141    89%
```

**Modulos criticos con baja cobertura:**

| Modulo | Cobertura | Riesgo | Lineas sin cubrir |
|---|---|---|---|
| services\user_service.py | 32% | Alto | 9,12,15-18,21-24,27-35,38-41 |
| repositories\user_repository.py | 41% | Alto | 8,11,14,17,20-24,27-31,34-35 |
| routers\users.py | 62% | Medio | 12-13,18-19,24-25,30-31,36-37 |
| database.py | 64% | Bajo | 14-18 (error handling de conexion) |

**Nota**: La capa de usuarios (user_service, user_repository, routers/users) tiene cobertura muy baja porque los tests actuales no cubren los endpoints de gestion de usuarios. Esto es una deuda tecnica conocida: el proyecto priorizó el flujo de simulacion.

---

## Quality Gates recomendados

### Gate actual (estado del proyecto)

| Metrica | Umbral minimo | Estado actual | Pasa |
|---|---|---|---|
| Cobertura total | >= 80% | 89% | Si |
| Cobertura modulos criticos (simulator, metrics) | >= 90% | 97-100% | Si |
| Bugs criticos (SonarQube) | 0 | Por verificar | ? |
| Security Hotspots sin revisar | 0 | Por verificar | ? |
| Hallazgos Ruff bloqueantes | 0 | 1 (F841 query innecesaria) | No |

### Gate para produccion

| Metrica | Umbral | Gap actual |
|---|---|---|
| Cobertura total | >= 85% | OK (89%) |
| Cobertura de todos los modulos | >= 70% | Gap: user_service 32%, user_repo 41% |
| Bugs criticos Ruff/Sonar | 0 | Gap: F841 en simulator_service |
| Code Smells Sonar (bloqueantes) | 0 | Por verificar en dashboard |
| Security Hotspots | 0 revisados | Por verificar en dashboard |
| Duplicaciones | < 3% | Por verificar en dashboard |

---

## Comandos clave del flujo de Quality Gates

```powershell
# Analisis estatico (instantaneo, sin ejecutar)
ruff check . --statistics
ruff check .

# Ver cuantos se pueden auto-corregir
ruff check . --diff

# Cobertura de tests (genera coverage.xml para SonarQube)
pytest tests/ --cov=. --cov-report=xml --ignore=tests/test_frontend_smoke.py

# Cobertura con detalle en terminal (para revisar en clase)
pytest tests/ --cov=. --cov-report=term-missing --ignore=tests/test_frontend_smoke.py

# Scanner de SonarQube (requiere sonar-project.properties y token)
pysonar-scanner -Dsonar.host.url=http://localhost:9000 -Dsonar.token=TOKEN

# Levantar la app
python -m uvicorn main:app --reload --port 8000
```

---

## Reglas de negocio del simulador

- El simulador requiere exactamente 32 selecciones para correr.
- Se forman 8 grupos de 4 equipos cada uno.
- En la fase de grupos, cada equipo juega 3 partidos (contra los otros 3 del grupo).
- Clasifican los 2 mejores de cada grupo (puntos, luego diferencia de gol).
- Las 16 selecciones clasificadas pasan a eliminacion directa (octavos → cuartos → semi → final).
- El campeon es el ganador de la final.
- Los resultados se cachean: el dashboard muestra la ultima simulacion corrida.

---

## Notas para el agente

- **Endpoint critico**: `POST /simulator/run` — cualquier bug aqui es bloqueante.
- **Capa mas riesgosa sin cobertura**: usuarios — no afecta la simulacion pero si la seguridad de la app.
- **El hallazgo F841 en linea 141 de simulator_service.py** es el mas relevante: query innecesaria en la ruta de validacion del endpoint principal.
- **El E402 en schemas/team.py:32** es un workaround documentado para una dependencia circular. No es un bug.
- **test_frontend_smoke.py** requiere browser Playwright instalado. En CI se excluye con `--ignore`.
- **demo_playwright.py** es un script standalone de demostracion, no forma parte del flujo de tests del proyecto.
