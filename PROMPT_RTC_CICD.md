# PROMPT_RTC_CICD.md
## Clase 7 — CI/CD e Infraestructura con GenIA

Usar estos prompts después de cargar `ARCHITECTURE.md` como contexto del proyecto.
Todos los prompts tienen datos estáticos del proyecto — no hay que editar nada antes de pegar.

**Instrucción para el agente antes de cada prompt:**
> NO resuelvas nada. NO modifiques el código. Analizá y respondé según lo que se pide.

---

## Prompt 1 — Generar el workflow completo de GitHub Actions

```text
[ROL]
Sos un DevOps engineer senior con experiencia en GitHub Actions, pipelines de CI/CD
y aplicaciones FastAPI en Python 3.12.

Tenés cargado como contexto el archivo ARCHITECTURE.md del Simulador Mundial 2026.
Usalo como fuente de verdad: stack tecnológico, estructura del proyecto, quality gates,
cobertura actual (89% — 69 tests) y hallazgos reales de Ruff.

[TAREA]
Generá el archivo .github/workflows/ci.yml completo para el Simulador Mundial 2026.

El pipeline tiene una arquitectura específica: en vez de hacer deploy de un backend,
el job 4 SIMULA EL MUNDIAL durante el build de GitHub Actions y genera un sitio
estático en dist/ que se publica en GitHub Pages — sin ningún servidor en producción.

Esto es posible porque el SimulatorService auto-seedea 32 equipos si la BD está vacía
(services/simulator_service.py línea 37-38). Con sqlite:///:memory: el pipeline puede
correr POST /simulator/run sin preparación previa.
En caso de no contar con un repositorio para subir el archivo para ver en acción el pipeline pedime el remoto
El workflow debe tener exactamente 5 jobs encadenados con needs:

JOB 1 — lint
  runs-on: ubuntu-latest
  - pip install ruff
  - ruff check .
  (Si algún hallazgo de Ruff es MAJOR, el pipeline para acá)

JOB 2 — tests
  needs: lint | runs-on: ubuntu-latest
  - pip install -r requirements.txt
  - python -m pytest tests/ --cov=. --cov-report=xml --ignore=tests/test_frontend_smoke.py -q
  - env: DATABASE_URL=sqlite:///:memory:
  - upload-artifact: name=coverage-report, path=coverage.xml

JOB 3 — quality-gate
  needs: tests | runs-on: ubuntu-latest
  - download-artifact: coverage-report
  - Parsear coverage.xml con xml.etree.ElementTree (solo stdlib, no instalar nada)
  - Verificar line-rate >= 0.80 → si falla: "Quality Gate FAIL: cobertura X% < 80%"
  (Cobertura actual del proyecto: 89% → pasa. Si alguien sube código sin tests y baja a
  79%, el pipeline para aquí y nadie llega al Mundial)

JOB 4 — simulate
  needs: quality-gate | runs-on: ubuntu-latest
  - pip install -r requirements.txt
  - python seed_and_simulate.py
    (Este script levanta FastAPI con BD en memoria, llama a POST /simulator/run,
     GET /metrics/dashboard y GET /teams/, guarda los JSON en dist/data/ y genera
     dist/index.html estático con los datos embebidos — sin fetch al backend)
  - env: DATABASE_URL=sqlite:///:memory:
  - Validar que dist/index.html existe
  - Imprimir el campeón del mundo (leer dist/data/simulation.json)
  - upload-pages-artifact: path=dist/

JOB 5 — deploy
  needs: simulate | runs-on: ubuntu-latest
  - if: github.ref == 'refs/heads/main'
  - environment: github-pages
  - uses: actions/deploy-pages@v4

El workflow debe dispararse en:
- push a branches: [main]   → pipeline completo + deploy
- pull_request a branches: [main] → jobs 1-4, sin deploy

Permissions necesarios para GitHub Pages:
  contents: read
  pages: write
  id-token: write

[CRITERIO]
- YAML válido, listo para commitear en .github/workflows/ci.yml
- Cada job tiene un name descriptivo con el número de step (ej: "② Tests + Coverage")
- El job quality-gate parsea el XML con xml.etree.ElementTree — cero dependencias extra
- El job simulate imprime el campeón al final para que aparezca en el log del pipeline
- El job deploy usa environment: github-pages para mostrar la URL publicada en Actions
- NO incluyas pasos innecesarios ni comentarios de más de 2 líneas
- Al final del archivo, agregá un comentario con el comando PowerShell para probar
  todo localmente antes del push: $env:DATABASE_URL="sqlite:///:memory:"; python seed_and_simulate.py
```

---

## Prompt 2 — Diagnosticar un pipeline rojo

```text
[ROL]
Sos un DevOps engineer senior con experiencia en GitHub Actions y aplicaciones FastAPI
en Python. Tenés cargado como contexto el archivo ARCHITECTURE.md del Simulador
Mundial 2026.

Stack del proyecto:
- FastAPI + SQLite + SQLAlchemy (BD en memoria en CI/CD: sqlite:///:memory:)
- pytest-cov 5.x — cobertura actual 89%, umbral Quality Gate: 80%
- Ruff — 10 hallazgos conocidos en la codebase (ver ARCHITECTURE.md)
- seed_and_simulate.py — levanta FastAPI internamente y llama a /simulator/run
- GitHub Pages — deploy del dist/ generado por el job 'simulate'
- test_frontend_smoke.py SIEMPRE excluido en CI (requiere browser)

[TAREA]
El pipeline del Simulador Mundial 2026 falló. Este es el log completo del job:

--- LOG DE GITHUB ACTIONS ---
[PEGAR AQUÍ EL LOG COMPLETO DEL JOB QUE FALLÓ]
--- FIN DEL LOG ---

Respondé con exactamente esta estructura:

## Job que falló
[nombre del job — ①lint / ②tests / ③quality-gate / ④simulate / ⑤deploy]

## Step exacto
[nombre del step dentro del job]

## Causa raíz
[1-2 oraciones. Técnico, sin rodeos.]

## Fix mínimo
Archivo: [nombre del archivo o configuración]
Cambio: [qué modificar y dónde]

## Verificación local antes del próximo push
[comando PowerShell para reproducir y confirmar el fix]

## ¿Bloquea el Mundial?
[¿el error impide que el simulador corra? sí/no + por qué en una línea]

[CRITERIO]
- NO modifiques el workflow ni archivos que no sean el fix mínimo necesario
- Si el log no tiene suficiente información, indicá qué flag agregar al comando fallido
- Si el problema es en el job simulate: revisar primero si DATABASE_URL está seteado
  y si seed_and_simulate.py puede importar la app sin errores de dependencias
- El fix debe lograr pipeline verde en el siguiente push
- NO resuelvas nada. Solo analizá y reportá.
```

---

## Prompt 3 — Revisar el workflow generado contra la arquitectura real

```text
[ROL]
Sos un DevOps engineer senior y code reviewer. Tenés cargado el archivo
ARCHITECTURE.md del Simulador Mundial 2026 como fuente de verdad.

[TAREA]
Revisá el siguiente workflow de GitHub Actions:

--- WORKFLOW ---
[PEGAR AQUÍ EL CONTENIDO DE .github/workflows/ci.yml]
--- FIN DEL WORKFLOW ---

Verificá que el workflow es consistente con estos datos reales del proyecto:

PROYECTO (fuente: ARCHITECTURE.md):
- Python: 3.12
- Tests: 69 pasados | Cobertura: 89% | Umbral Quality Gate: 80%
- BD en CI: sqlite:///:memory: (NO worldcup.db — es un archivo, no sirve en CI)
- Excluir siempre: tests/test_frontend_smoke.py (requiere browser)
- Script de simulación: seed_and_simulate.py (auto-seedea, no necesita fixtures)
- Hallazgos Ruff conocidos: 10 errores — el F841 en simulator_service.py:141 es MAJOR
- Deploy target: GitHub Pages vía actions/upload-pages-artifact@v3 + actions/deploy-pages@v4

Respondé con:

## Consistencia con el proyecto
[tabla: ítem | esperado | encontrado en el workflow | ¿OK?]

## Problemas encontrados
[lista numerada — archivo y línea del workflow si aplica]

## Riesgos en producción
[¿qué puede fallar en un repo real que no se nota en este ejemplo?]

## Veredicto
GO ✅ / NO-GO 🚨 + razón en una línea

[CRITERIO]
- NO sugieras cambios de arquitectura ni herramientas alternativas
- NO resuelvas nada — solo analizá y reportá
- El veredicto GO requiere que los 5 jobs estén presentes, la BD sea en memoria
  y el deploy target sea GitHub Pages
```
