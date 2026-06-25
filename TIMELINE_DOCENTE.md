# TIMELINE — Clase 7: CI/CD e Infraestructura con GenIA
## Segundo monitor. Cues cortos + comandos copy-paste.

```
FLUJO: git push → ruff → pytest (sqlite:///:memory:) → Quality Gate ≥80% → simular mundial → GitHub Pages
```

---

## SETUP PREVIO

```powershell
# Terminal 1 — verificar que la app funciona local
python -m uvicorn main:app --reload --port 8000

# Terminal 2 — verificar tests con BD en memoria (lo que hará el pipeline)
$env:DATABASE_URL="sqlite:///:memory:"
python -m pytest tests/ --ignore=tests/test_frontend_smoke.py -q
# esperado: 69 passed

# Terminal 3 — libre para comandos live coding
```

**Tabs pre-abiertas:**
- `http://localhost:8000/docs` — Swagger del simulador
- GitHub → repo → pestaña Actions (para mostrar el pipeline corriendo en vivo)
- `database.py` — línea 4 (la URL hardcodeada que vamos a refactorizar)
- `tests/conftest.py` — línea 12 (`TEST_DB_URL = "sqlite:///:memory:"` — ya lo hacía)
- Agente IA con `ARCHITECTURE.md` cargado
- `PROMPT_RTC_CICD.md` abierto en Prompt 1

**Archivos a crear durante la clase:**
- `database.py` → refactor `os.getenv`
- `Dockerfile`
- `seed_and_simulate.py` (ya está en el repo — mostrar, no crear)
- `.github/workflows/ci.yml` → generado con IA (Prompt 1)

---

## APERTURA (5 min)

> Mostrar la UI del simulador. Clicar "Simular Mundial". El campeón aparece.

- Clase 5: testeamos. Clase 6: auditamos. Hoy: **automatizamos todo eso — y además el Mundial lo simula el pipeline**.
- Pregunta del día: *"¿Qué pasaría si el pipeline pudiera simular el torneo y publicar el resultado sin que nadie toque el servidor?"*
- Eso es lo que vamos a construir: cada push a main → lint → tests → quality gate → **simula el Mundial** → publica en GitHub Pages.

---

## PARTE 1 — CONCEPTOS BASE (15 min)

> Slides 7-11. Ir rápido — el foco está en el live coding.

### Los 4 conceptos en 4 minutos

- **Pipeline**: línea de ensamblaje. Si una estación falla, la línea para. Nuestro pipeline tiene 5 estaciones.
- **Runner**: VM limpia de GitHub. Cada job arranca desde cero — sin estado del job anterior.
- **Artifact**: `coverage.xml` que genera job 2 y necesita job 3. Sin artifact → Quality Gate no tiene datos.
- **Secret**: `API keys` encriptadas en GitHub Settings → nunca en el código.

### El flujo según el evento (slide 11)

| Evento | Jobs | Deploy |
|---|---|---|
| push a feature branch | lint + tests + quality-gate | NO |
| PR a main | lint + tests + quality-gate + simulate | NO |
| merge a main | los 5 jobs completos | SÍ → GitHub Pages |

> **Cue**: *"El job 4 no hace docker push ni kubectl. Simula el Mundial y publica el resultado. Sin servidor."*

---

## PARTE 2 — LIVE CODING (30 min)

### 2.1 — Refactor `database.py` (5 min)

> Abrir `database.py`. Mostrar el problema: URL hardcodeada en línea 4.

**Antes (hardcodeado):**
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./worldcup.db"
```

**Después (lee del entorno):**
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./worldcup.db")
```

> Mostrar `conftest.py` línea 12: `TEST_DB_URL = "sqlite:///:memory:"` — los tests ya lo hacían a mano.
> Ahora la app también puede. Esto es lo que permite que el pipeline simule sin archivo de BD.

---

### 2.2 — Mostrar `seed_and_simulate.py` (5 min)

> Abrir el archivo — NO crearlo. Ya está en el repo. Recorrer las partes clave.

```python
# 1. Configura BD en memoria antes de importar la app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# 2. Levanta FastAPI en un thread daemon
t = threading.Thread(target=_start_server, daemon=True)

# 3. Llama a los 3 endpoints
simulation = _post("/simulator/run")   # ← simula el Mundial
metrics    = _get("/metrics/dashboard") # ← goleador, promedios
teams      = _get("/teams/")           # ← 32 equipos con grupos

# 4. Guarda JSONs en dist/data/
# 5. Genera dist/index.html estático (misma UI, datos embebidos, sin fetch)
```

Puntos a marcar:
- `SimulatorService` auto-seedea los 32 equipos si la BD está vacía (línea 37 del servicio) → el pipeline no necesita fixtures
- El `index.html` de `dist/` es el mismo HTML del proyecto pero **sin fetch** → los datos están embebidos como JS const
- Cada push a main → el campeón puede ser diferente (simulación aleatoria)

**Demostrar localmente:**
```powershell
$env:DATABASE_URL="sqlite:///:memory:"
python seed_and_simulate.py
# Ver: dist/index.html generado + campeón impreso en consola
# Abrir dist/index.html en el browser → misma UI, sin backend
```

---

### 2.3 — Crear `.github/workflows/ci.yml` con IA (20 min)

```powershell
mkdir .github\workflows
```

> Copiar **Prompt 1** de `PROMPT_RTC_CICD.md` al agente (ya tiene `ARCHITECTURE.md` cargado).
> El prompt tiene todos los datos estáticos — no hay que editar nada antes de pegar.

Mientras el agente genera, anticipar los 5 jobs:

**Job ① lint** → Ruff. Si el F841 de `simulator_service.py:141` no fue corregido, para acá.

**Job ② tests** → pytest 69 tests, BD en memoria, sube `coverage.xml` como artifact.

**Job ③ quality-gate** → parsea el XML con stdlib (`xml.etree.ElementTree`), verifica 89% ≥ 80%.
> *"Si alguien sube código sin tests y baja a 79%, el pipeline para aquí. El Mundial no se simula."*

**Job ④ simulate** → `python seed_and_simulate.py` → el runner levanta FastAPI, llama al endpoint, guarda JSONs, genera `dist/index.html`.
> *"El campeón del Mundial 2026 lo decide el pipeline de CI/CD."*

**Job ⑤ deploy** → `actions/deploy-pages@v4` sube `dist/` a GitHub Pages. Solo en `main`.

---

### ⭐ Demo: pipeline rojo + IA diagnóstica (3 min al final)

> Comentar un assert en cualquier test → push → mostrar el job ② rojo en Actions.

```powershell
# Abrir PROMPT_RTC_CICD.md → Prompt 2
# Pegar el log del job fallido → la IA identifica step exacto + fix mínimo
```

- **El punto pedagógico**: el pipeline detecta en segundos. La IA lee 200 líneas de log y te da el fix en 3 líneas. Vos hacés el push.

---

## PARTE 3 — EJERCICIO ALUMNOS (20 min)

> Slide divisor → slide "¡Vamos a ejercitar! 💪"

Consigna:
1. Fork del repo → habilitar GitHub Pages en Settings (source: GitHub Actions)
2. Hacer push → ver los 5 jobs correr en la pestaña Actions
3. Verificar que el `dist/index.html` se publica con el campeón del Mundial
4. Romper el pipeline intencionalmente (borrar un test) → usar Prompt 2 para diagnosticar el log
5. Fix → nuevo push → pipeline verde → nuevo campeón

> Verificar que todos habilitaron GitHub Pages antes de hacer el primer push.

---

## CIERRE (5 min)

- CI/CD no es solo automatizar tests — el pipeline puede **razonar y producir** (simuló el Mundial).
- La IA complementa el pipeline: el pipeline detecta el fallo, la IA explica por qué y propone el fix.
- Preview Clase 8 (presencial): **Observabilidad** — cuando el pipeline está verde pero algo falla en producción igual. Logs, stacktraces, métricas. Av. Caseros 3515 piso 6.

---

## PLAN B

| Problema | Fix |
|---|---|
| GitHub Actions no dispara | Verificar ruta exacta: `.github/workflows/ci.yml` (punto incluido) |
| `ruff check .` falla en CI | Correr local primero → arreglar antes del push |
| `pytest` falla en CI | Verificar que `database.py` tiene el `os.getenv` — sin esto usa `worldcup.db` que no existe en el runner |
| `seed_and_simulate.py` falla | Correr `python seed_and_simulate.py` local con `$env:DATABASE_URL="sqlite:///:memory:"` |
| `dist/index.html` no se genera | Ver el log completo del job simulate → `test -f dist/index.html` falla si el script rompió antes |
| GitHub Pages no publica | Settings → Pages → Source: GitHub Actions (no "Deploy from branch") |
| artifact `coverage-report` no encontrado | Verificar que el `name` en `upload-artifact` y `download-artifact` es exactamente igual |

---

## REFERENCIA RÁPIDA

### Comandos clave
```powershell
# Simular el Mundial localmente (mismo que hace el pipeline)
$env:DATABASE_URL="sqlite:///:memory:"
python seed_and_simulate.py
# Resultado: dist/index.html con el campeón embebido

# Correr tests con BD en memoria (mismo que hace job 2)
$env:DATABASE_URL="sqlite:///:memory:"
python -m pytest tests/ --ignore=tests/test_frontend_smoke.py -q
# esperado: 69 passed

# Generar coverage.xml (mismo que hace job 2)
python -m pytest tests/ --cov=. --cov-report=xml --ignore=tests/test_frontend_smoke.py
```

### Cobertura real — 89% total (69 tests)

| Módulo | Cobertura | Estado |
|---|---|---|
| services\simulator_service.py | 97% | ✅ OK |
| services\metrics_service.py | 100% | ✅ OK |
| repositories\player_repository.py | 100% | ✅ OK |
| repositories\team_repository.py | 100% | ✅ OK |
| routers\users.py | 62% | ⚠️ Medio |
| repositories\user_repository.py | 41% | 🔴 Bajo |
| services\user_service.py | 32% | 🔴 Bajo |
| **TOTAL** | **89%** | **✅ Quality Gate pasa (≥80%)** |

### Checklist pre-clase
- [ ] `python -m uvicorn main:app --reload` → UI y Swagger abren
- [ ] `pytest -q --ignore=tests/test_frontend_smoke.py` → 69 passed
- [ ] `python seed_and_simulate.py` local → `dist/index.html` generado, campeón impreso
- [ ] Repo en GitHub con Pages habilitado (Settings → Pages → GitHub Actions)
- [ ] `ARCHITECTURE.md` cargado en el agente
- [ ] `PROMPT_RTC_CICD.md` abierto en Prompt 1
