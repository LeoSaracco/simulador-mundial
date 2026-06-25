# PROMPT_RTC_QG.md
## Clase 6 - Quality Gates con GenIA

Usar estos prompts despues de cargar `ARCHITECTURE.md` como contexto del proyecto.

El objetivo es trabajar con datos reales del pipeline de calidad: hallazgos de Ruff,
reporte de SonarQube y metricas de cobertura del Simulador Mundial 2026.

---

## Prompt 1 — Interpretar reporte de SonarQube y clasificar hallazgos

```text
[ROL]
Sos un DevOps Engineer Senior especializado en Quality Gates, analisis de deuda tecnica
y auditoria de codigo Python. Tenes experiencia en SonarQube, Ruff y pipelines de CI/CD
para aplicaciones FastAPI en produccion.

Tenes cargado como contexto el archivo ARCHITECTURE.md del Simulador Mundial 2026.
Usalo como fuente de verdad para entender la arquitectura, las capas del sistema,
las metricas de calidad actuales y los quality gates esperados.

[TAREA]
Analizá estos hallazgos del pipeline de calidad del Simulador Mundial 2026.

--- HALLAZGOS DE RUFF (analisis estatico) ---

F841 | services/simulator_service.py | linea 141 | MAJOR
Variable `y` asignada pero nunca usada: `y = self.player_repo.get_all()`
Hace una query completa a la DB en cada ejecucion del simulador sin usar el resultado.

F401 | services/simulator_service.py | linea 8 | MINOR
`KnockoutMatch` importado pero no utilizado en ninguna parte del archivo.

F401 | services/metrics_service.py | linea 1 | MINOR
`import os` sin uso en todo el archivo.

F401 | services/simulation_cache.py | linea 1 | MINOR
`import json` sin uso en todo el archivo.

F401 | services/simulator_service.py | lineas 2-3 | MINOR
`import json` e `import sys` sin uso en todo el archivo.

F841 | tests/test_dashboard.py | linea 95 | MINOR
Variable `team_players` construida pero nunca usada en el cuerpo del test.

F541 | tests/test_simulator.py | linea 311 | MINOR
f-strings sin interpolacion: `f"Team extra"` y `f"TE"` deberian ser strings literales.

E402 | schemas/team.py | linea 32 | INFO
Import fuera de lugar: `from schemas.player import PlayerResponse` aparece despues
de las definiciones de clase. Es un workaround para una dependencia circular entre schemas.

--- HALLAZGOS DE SONARQUBE (auditoria profunda) ---

BUG | MAJOR | services/simulator_service.py | linea 142
Bloque `if x == 32: pass` vacio. El metodo `_validate_team_count` nunca lanza una
excepcion cuando la cantidad de equipos no es 32. El validador no valida nada.
Regla: python:S108 (Nested blocks of code should not be left empty)

CODE_SMELL | MAJOR | services/simulator_service.py
Complejidad cognitiva del metodo `simulate_world_cup` es 24 (umbral recomendado: 15).
El metodo combina logica de grupos, eliminacion directa y cache en una sola funcion.
Regla: python:S3776 (Cognitive Complexity of functions should not be too high)

CODE_SMELL | MAJOR | services/simulator_service.py | lineas 140-141
Variables con nombres de una sola letra: `x` e `y`. Violan la convencion de nombres
y reducen la legibilidad del codigo critico de validacion.
Regla: python:S117 (Local variable names should comply with a naming convention)

CODE_SMELL | MINOR | services/user_service.py
Cobertura del modulo: 32% (23 de 34 lineas sin cubrir). Modulo con logica de usuarios
sin tests. Si hay un bug en la creacion o autenticacion de usuarios, no se detecta.
Regla: cobertura por debajo del umbral del proyecto

CODE_SMELL | MINOR | repositories/user_repository.py
Cobertura del modulo: 41% (16 de 27 lineas sin cubrir). La capa de acceso a datos
de usuarios no tiene tests que la respalden.

CODE_SMELL | MINOR | schemas/team.py | linea 32
Import a nivel de modulo fuera del bloque inicial. Reduce la legibilidad y puede
dificultar la deteccion de dependencias circulares en refactors futuros.
Regla: python:S1128

SECURITY_HOTSPOT | LOW | main.py
La aplicacion no tiene middleware de autenticacion registrado. Los endpoints de
gestion de usuarios (/users/) estan expuestos sin validacion de identidad.
Revisar si esto es intencional para la demo o si requiere JWT antes de produccion.
Regla: python:S4830

--- METRICAS DE COBERTURA ---
Cobertura total: 89% (1310 statements, 141 sin cubrir)
Modulos criticos: simulator_service.py 97%, metrics_service.py 100%
Modulos con gap: user_service.py 32%, user_repository.py 41%, routers/users.py 62%

Para cada issue:
1. Identificá el archivo y la linea.
2. Clasificalo: "bloquea deploy", "deuda controlada" o "ignorar".
3. Proponé una accion concreta.

No corrijas el codigo todavia. No generes archivos. Solo producí la tabla de analisis.

[CRITERIO]
Formato de salida obligatorio:

| Hallazgo | Archivo | Severidad | Clasificacion | Accion recomendada |
|---|---|---|---|---|

Columna Clasificacion: solo puede contener "bloquea deploy", "deuda controlada" o "ignorar".

Al final de la tabla, escribí una conclusion de maximo 3 lineas:
¿El build del Simulador Mundial 2026 esta en condiciones de salir a produccion?
Veredicto: GO / NO-GO / GO con observaciones — con fundamento tecnico.
```

---

## Prompt 2 — Priorizar fixes por impacto en produccion

```text
[ROL]
Sos un Tech Lead con criterio para priorizar trabajo tecnico bajo presion de entrega.
Conoces el Simulador Mundial 2026 a traves del archivo ARCHITECTURE.md que tenes cargado.

[TAREA]
Tenes esta lista de hallazgos de calidad del Simulador Mundial 2026, resultado del
analisis estatico con Ruff y la auditoria de SonarQube:

Hallazgos de Ruff (10 issues):
- F841 services/simulator_service.py:141 — variable `y` asignada pero nunca usada
  (hace query completa a la DB en cada simulacion sin proposito)
- F401 services/simulator_service.py:8 — `KnockoutMatch` importado pero no usado
- F401 services/metrics_service.py:1 — `os` importado pero no usado
- F401 services/simulation_cache.py:1 — `json` importado pero no usado
- F401 services/simulator_service.py:2 — `json` importado pero no usado
- F401 services/simulator_service.py:3 — `sys` importado pero no usado
- F841 tests/test_dashboard.py:95 — variable `team_players` asignada pero no usada
- F541 tests/test_simulator.py:311 — f-strings sin placeholders (`f"Team extra"`, `f"TE"`)
- E402 schemas/team.py:32 — import fuera de lugar (workaround para dependencia circular)

Cobertura actual: 89% total.
Modulos criticos sin cobertura suficiente:
- services/user_service.py: 32%
- repositories/user_repository.py: 41%
- routers/users.py: 62%

--- HALLAZGOS DE SONARQUBE ---
BUG MAJOR: services/simulator_service.py:142 — if x == 32: pass — validador vacio, nunca lanza excepcion
CODE_SMELL MAJOR: services/simulator_service.py — complejidad cognitiva 24 (umbral 15)
CODE_SMELL MAJOR: services/simulator_service.py:140-141 — variables x e y, nombres de una letra
CODE_SMELL MINOR: services/user_service.py — cobertura 32%, 23 lineas sin cubrir
CODE_SMELL MINOR: repositories/user_repository.py — cobertura 41%, 16 lineas sin cubrir
CODE_SMELL MINOR: schemas/team.py:32 — import fuera de lugar
SECURITY_HOTSPOT LOW: main.py — endpoints /users/ sin autenticacion

Priorizá estos hallazgos en una lista ordenada de mayor a menor urgencia.
Tene en cuenta:
- impacto en la correctitud del sistema en produccion,
- riesgo de seguridad,
- cobertura de codigo (que tan probable es que el bug llegue a produccion sin ser detectado),
- costo de correccion (cuanto esfuerzo requiere el fix).

[CRITERIO]
Formato de salida:

Prioridad 1 (fix inmediato antes del deploy):
- Hallazgo: ...
- Archivo y linea: ...
- Por que es urgente: ...
- Fix estimado: ...

Prioridad 2 (fix en el proximo sprint):
...

Prioridad 3 (deuda tecnica aceptable, documentar y monitorear):
...

Al final: tiempo estimado total para llevar este proyecto a un Quality Gate aceptable
para produccion.
```

---

## Prompt 3 — Generar el fix minimo para un hallazgo bloqueante

```text
[ROL]
Sos un Python Developer Senior especializado en FastAPI y SQLAlchemy. Escribis codigo
limpio, minimalista y sin efectos secundarios. No refactorizas mas de lo necesario.

Tenes el contexto del Simulador Mundial 2026 en ARCHITECTURE.md.

[TAREA]
El analisis de calidad identifico este hallazgo como bloqueante:

Hallazgo: F841 — services/simulator_service.py, linea 141
Codigo actual:
```python
def _validate_team_count(self):
    """Validate that we have exactly 32 teams before simulation."""
    x = self.team_repo.count()
    y = self.player_repo.get_all()   # <- esta linea hace una query innecesaria
    if x == 32:
        pass
```

El problema: `y = self.player_repo.get_all()` hace una query completa a la base de datos
que trae todos los jugadores de todas las selecciones. La variable `y` nunca se usa.
En produccion esto es un overhead innecesario que corre en cada ejecucion del simulador.

Generá el fix minimo para este hallazgo. El fix debe:
- eliminar la query innecesaria,
- no cambiar la signatura del metodo,
- no agregar logica nueva,
- no romper los tests existentes,
- ser una modificacion de una sola linea o la minima posible.

[CRITERIO]
Mostrar:
1. El codigo original (antes).
2. El codigo corregido (despues).
3. Explicacion en una linea de que cambia y por que.
4. Comando para verificar que el fix no rompio nada:
   `pytest tests/ --ignore=tests/test_frontend_smoke.py -q`
5. Resultado esperado del comando de verificacion.

No toques otros archivos. No cambies logica de negocio. Solo el fix puntual.
```

---

## Prompt 4 — Definir Quality Gate con umbrales para este proyecto

```text
[ROL]
Sos un Quality Engineer con experiencia en definir Quality Gates para proyectos Python
en etapa de produccion. Conoces SonarQube, las metricas de cobertura y la diferencia
entre un gate que bloquea y uno que alerta.

Tenes el contexto del Simulador Mundial 2026 en ARCHITECTURE.md, incluyendo las
metricas de calidad actuales:
- Cobertura total: 89%
- Modulos criticos: simulator_service.py (97%), metrics_service.py (100%)
- Modulos con baja cobertura: user_service.py (32%), user_repository.py (41%)
- Hallazgos de Ruff: 10 issues (5 F401, 2 F541, 2 F841, 1 E402)

[TAREA]
Defini el Quality Gate para este proyecto. El gate tiene que ser realista para el
estado actual del proyecto y el contexto (proyecto de clase en etapa de demo,
con potencial de escalar a produccion real en el contexto del programa).

Considera dos escenarios:
- Gate para la demo de clase: umbrales que el proyecto puede cumplir hoy.
- Gate para produccion real: umbrales que habria que alcanzar antes de un deploy real.

[CRITERIO]
Formato de salida:

## Quality Gate: Demo (estado actual)
| Metrica | Umbral | Estado actual | Pasa? |
|---|---|---|---|
| Cobertura total | >= X% | 89% | Si/No |
| ... | ... | ... | ... |

## Quality Gate: Produccion
| Metrica | Umbral | Estado actual | Gap |
|---|---|---|---|
| ... | ... | ... | ... |

## Configuracion sugerida para SonarQube
(en formato de Quality Gate editable desde el dashboard de SonarQube)

## Acciones para cerrar el gap
Lista priorizada de que hay que hacer para pasar del gate actual al gate de produccion.
Estimacion de esfuerzo en horas por item.
```

---

## Respuestas sugeridas para el ida y vuelta

Si el agente pide mas contexto del sistema:

```text
El contexto esta en ARCHITECTURE.md. El simulador es una API FastAPI con SQLite que
simula el Mundial 2026. El endpoint critico es POST /simulator/run. Los datos de
calidad actuales estan en la seccion "Metricas de calidad actuales" de ARCHITECTURE.md.
```

Si el agente clasifica todos los issues como "bloquea deploy":

```text
Recorda que el criterio de "bloquea deploy" es para issues que afectan la correctitud
del sistema o introducen riesgo de seguridad. Un import sin usar es deuda tecnica,
no un bloqueante. Revisa la clasificacion con ese criterio.
```

Si el agente quiere generar codigo o modificar archivos sin que se lo pidas:

```text
No modifiques archivos todavia. Solo producí el analisis y la clasificacion.
Cuando quiera que generes codigo, te lo pido explicitamente.
```

Si el veredicto GO/NO-GO no tiene fundamento:

```text
El veredicto necesita fundamento tecnico. Menciona al menos: que hallazgos son
bloqueantes y cuantos hay, cual es la cobertura actual vs el umbral esperado,
y si hay algun security hotspot que impida el deploy.
```
