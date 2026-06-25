# QA.md — Simulador Mundial 2026
## Archivo de contexto para testing asistido por IA

---

## ¿Para qué sirve este archivo?

Este archivo es el equivalente del `BACKEND.md` y `FRONTEND.md` pero para el área de QA.
Antes de generar cualquier caso de prueba, datos sintéticos o reporte con IA, cargá este archivo en el agente.
Sin este contexto, la IA genera tests genéricos. Con él, genera tests que respetan el stack real, los endpoints reales y los criterios de aceptación del proyecto.

---

## 🤖 Modo interactivo — Cómo trabajar con el agente

Este archivo activa en el agente un **modo de diseño colaborativo de casos de prueba**.
El flujo tiene 4 etapas. El agente no genera nada hasta completarlas.

### Cómo activar el modo

Escribí una línea describiendo qué querés testear y por qué te preocupa. Ejemplos:

> "Quiero testear el endpoint de simulación, me preocupa que el campeón siempre sea el ganador de la final."

> "Quiero testear el CRUD de equipos, me preocupa qué pasa con códigos duplicados."

> "Quiero testear el dashboard, me preocupa que las métricas sean consistentes con la simulación."

### Las 4 etapas del flujo

```
ETAPA 1 — ENTENDER
El agente hace preguntas dinámicas para entender el alcance.
No todas las conversaciones tienen las mismas preguntas.
Las preguntas dependen de lo que describiste y de tus respuestas anteriores.
Máximo 3 preguntas por ronda — nunca te bombardea con todo junto.

ETAPA 2 — PLAN
El agente muestra un plan de casos de prueba ANTES de generarlos:
  - Qué casos va a diseñar y por qué
  - Qué datos sintéticos necesita
  - Qué archivos va a crear o modificar
  - Tiempo estimado de ejecución
El QA valida el plan. Si algo no cierra, se ajusta antes de ejecutar.
→ El agente espera un GO explícito antes de continuar.

ETAPA 3 — GENERAR Y EJECUTAR
Solo tras el GO:
  - Genera los casos de prueba en formato tabla (ID, nombre, precondición, pasos, resultado esperado)
  - Genera el código pytest correspondiente
  - Indica el comando exacto para correrlos
  - Muestra el output esperado si todos pasan

ETAPA 4 — DOCUMENTAR
El agente genera automáticamente:
  - Sección del QA Report con los casos ejecutados
  - Cobertura de reglas de negocio alcanzada con estos tests
  - Conclusión parcial: ¿estos casos dan confianza para el deploy?
```

### Instrucción para el agente (no borrar)

> **Cuando este archivo esté cargado en el contexto y el usuario describa algo que quiere testear, activá el modo interactivo:**
> 1. NO generes casos de prueba de inmediato.
> 2. Hacé preguntas dinámicas para entender el alcance, el riesgo principal y el estado de la DB.
> 3. Máximo 2-3 preguntas por turno. Esperá la respuesta antes de continuar.
> 4. Cuando tengas suficiente contexto, mostrá un PLAN y pedí GO explícito.
> 5. Solo tras el GO: generá casos en tabla + código pytest + comando de ejecución.
> 6. Al final generá automáticamente la sección del QA Report para estos casos.
> 7. Si el usuario responde algo que cambia el alcance, ajustá el plan antes de ejecutar.
> 8. Siempre anclá los casos en los contratos y reglas de negocio definidos en este QA.md.

---

## Stack del proyecto

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy 2.0 · Pydantic v2 |
| Base de datos | SQLite (desarrollo) — archivo `mundial.db` |
| Frontend | HTML5 · Vanilla JS · Bootstrap 5.3 · Tailwind CSS |
| Testing backend | pytest · httpx · TestClient de FastAPI |
| Testing frontend | Manual (checklist) · Playwright (E2E automatizado) |

---

## Arquitectura de la app

```
FastAPI (main.py)
├── /teams/          → CRUD de equipos
├── /players/        → CRUD de jugadores
├── /simulator/run   → POST — ejecuta la simulación completa
└── /metrics/dashboard → GET — métricas del torneo (solo tras simular)

Frontend (static/index.html)
├── Tabla de equipos por grupo
├── Botón "Simular Mundial"
├── Bracket eliminatorio
└── Dashboard ejecutivo (campeón, goleador, promedios)
```

---

## Endpoints y contratos

### `POST /teams/`
- **Body:** `{ "name": string, "code": string (3 chars, único) }`
- **201:** equipo creado con `id`, `name`, `code`, `group_name: null`
- **409:** código duplicado
- **422:** datos inválidos

### `GET /teams/`
- **200:** lista de equipos. `group_name` es `null` hasta que se simula.

### `GET /teams/{id}`
- **200:** equipo con su lista de `players`
- **404:** equipo no existe

### `PUT /teams/{id}`
- **200:** equipo actualizado
- **404:** no existe · **409:** código duplicado

### `DELETE /teams/{id}`
- **204:** eliminado
- **404:** no existe

### `POST /players/`
- **Body:** `{ "name": string, "position": "GK"|"DF"|"MF"|"FW", "team_id": int }`
- **201:** jugador creado
- **404:** equipo no existe
- **400:** posición inválida (solo GK, DF, MF, FW)

### `POST /simulator/run`
- **200:** respuesta con `groups`, `round_of_16`, `quarterfinals`, `semifinals`, `third_place`, `final`, `champion`
- Si hay menos de 32 equipos → los genera automáticamente
- Si hay menos de 3 jugadores por equipo → los genera automáticamente
- Cada grupo tiene exactamente 4 equipos (A-H)
- Fase de grupos: 8 grupos × 6 partidos = 48 partidos
- Eliminatoria: 8 (Octavos) + 4 (Cuartos) + 2 (Semis) + 1 (3er puesto) + 1 (final) = 16 partidos
- Total: 64 partidos

### `GET /metrics/dashboard`
- **200:** `{ champion, top_scorer: { player_name, team_name, goals }, avg_goals_per_match, total_goals, total_matches }`
- **404:** si no se ejecutó ninguna simulación

---

## Reglas de negocio críticas

| Regla | Descripción |
|-------|-------------|
| Equipos únicos | El código de equipo debe ser único — 409 si se repite |
| Posiciones válidas | Solo: `GK`, `DF`, `MF`, `FW` — 400 si es otra cosa |
| 32 equipos exactos | La simulación requiere exactamente 32 equipos |
| 3 jugadores mínimo | Cada equipo necesita al menos 3 jugadores para simular |
| Sin empates en eliminatoria | En Octavos, Cuartos, Semis, 3er Puesto y Final debe haber ganador |
| Empates válidos en grupos | En fase de grupos los partidos pueden terminar empatados |
| Goles entre 0 y 5 | Cada equipo puede marcar entre 0 y 5 goles por partido |
| Campeón = ganador de la final | `champion` siempre debe coincidir con `final.winner` |
| Grupos balanceados | Exactamente 4 equipos por cada grupo (A-H) |
| Dashboard post-simulación | `/metrics/dashboard` devuelve 404 si no hay simulación previa |

---

## Configuración del entorno de testing

```bash
# Instalar dependencias
pip install -r requirements.txt

# Correr todos los tests
pytest tests/ -v

# Correr con reporte de cobertura
pytest tests/ --cov=. --cov-report=term-missing

# Correr un archivo específico
pytest tests/test_simulator.py -v

# Correr un test específico
pytest tests/test_simulator.py::test_simulator_run_champion_is_final_winner -v
```

---

## Estructura de tests existentes

```
tests/
├── conftest.py              ← fixture client con DB en memoria
├── test_teams.py            ← CRUD de equipos (happy path + edge cases)
├── test_simulator.py        ← simulación completa (happy path + reglas + edge cases)
├── test_dashboard.py        ← métricas post-simulación
└── test_players.py          ← CRUD de jugadores
```

### Cobertura actual (referencia)
- `test_teams.py`: happy path CRUD + duplicados + not found
- `test_simulator.py`: estructura de respuesta + conteos + consistencia + edge cases de DB
- `test_dashboard.py`: métricas post-simulación + consistencia con simulación
- `test_players.py`: happy path CRUD + posiciones inválidas + equipo inexistente

---

## Criterios de calidad (Quality Gates)

| Métrica | Umbral mínimo |
|---------|--------------|
| Cobertura de código | ≥ 80% en código nuevo |
| Tests que deben pasar | 100% antes de cualquier deploy |
| Tiempo máximo de ejecución por test | < 5 segundos |
| Tests de regresión | Correr la suite completa ante cualquier cambio |

---

## Datos sintéticos — patrones para generación

### Equipo válido
```json
{ "name": "Argentina", "code": "ARG" }
```

### Jugador válido
```json
{ "name": "Lionel Messi", "position": "FW", "team_id": 1 }
```

### Posiciones válidas
`GK` (Arquero) · `DF` (Defensor) · `MF` (Mediocampista) · `FW` (Delantero)

### Escenarios de edge case para datos sintéticos
- Equipo con nombre de 1 carácter
- Equipo con código de 2 caracteres (debería fallar si hay validación)
- Jugador con nombre muy largo (> 100 caracteres)
- 31 equipos (un equipo menos del requerido para simular)
- 33 equipos (uno de más)
- Equipo sin jugadores
- Equipo con 1 solo jugador

---

## IDs del DOM para testing frontend (Playwright)

| Elemento | ID / Selector |
|----------|--------------|
| Contenedor de equipos | `#teamsContainer` |
| Botón simular | `#btnSimular` |
| Spinner de carga | `#spinner` |
| Sección de resultados | `#resultsSection` |
| Resultado del campeón | `#championResult` |
| Dashboard de métricas | `#dashboardResult` |
| Resultados del bracket | `#bracketResult` |
| Stats bar superior | `#statsBar` |

---

## Checklist de smoke test — Frontend manual

Ejecutar después de cada deploy o cambio significativo:

- [ ] La app carga en `http://localhost:8000` sin errores en consola
- [ ] Los equipos se muestran agrupados (A-H) tras simular
- [ ] El botón "Simular Mundial" queda deshabilitado durante la simulación
- [ ] El spinner aparece y desaparece correctamente
- [ ] El bracket muestra el ganador destacado en cada partido
- [ ] El dashboard muestra campeón, goleador, promedio y total de goles
- [ ] La app es responsive en mobile (375px): dashboard en 2 columnas, sin scroll horizontal
- [ ] Los nombres de equipos se muestran con caracteres especiales correctamente

---

*Archivo de contexto QA — Simulador Mundial 2026 | Clase 5 — IA para Developers · CDA × Alkemy*
