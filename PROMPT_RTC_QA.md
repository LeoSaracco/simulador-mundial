# PROMPT_RTC_QA.md
## Clase 5 - QA y Testing Potenciado por GenIA

Usar este prompt despues de cargar `QA.md` como contexto del proyecto.

El objetivo es trabajar en modo plan: el agente primero pregunta, despues propone un plan, y no aplica nada hasta recibir la instruccion explicita: `aplica el plan`.

---

## Prompt RTC principal

```text
[ROL]
Sos un QA Engineer Senior especializado en testing de APIs FastAPI, pytest, TestClient y smoke testing frontend con Playwright.

Tenes cargado como contexto el archivo QA.md del Simulador Mundial 2026. Usalo como fuente de verdad para endpoints, reglas de negocio, quality gates, contratos de respuesta, herramientas permitidas e IDs del DOM.

[TAREA]
Trabaja en modo plan para disenar una estrategia de QA sobre el Simulador Mundial 2026.

Quiero testear el endpoint POST /simulator/run.
Me preocupa que:
- el campeon coincida con el ganador de la final,
- los grupos tengan exactamente 4 equipos cada uno,
- las metricas del dashboard sean consistentes con la simulacion,
- el flujo principal del frontend funcione como smoke test.

Antes de generar codigo o modificar archivos:
1. Haceme las preguntas necesarias para cerrar alcance.
2. Revisa los tests existentes para evitar duplicar cobertura.
3. Proponeme un plan de prueba.
4. Espera mi aprobacion explicita.

No generes codigo todavia.
No modifiques archivos todavia.
No ejecutes comandos todavia.
No apliques el plan hasta que yo diga exactamente: "aplica el plan".

[CRITERIO]
El plan debe incluir:
- Alcance exacto de lo que se va a probar.
- Preguntas abiertas o supuestos.
- Casos de prueba propuestos, con ID, objetivo y resultado esperado.
- Que tests ya existen y cuales no conviene duplicar.
- Archivos que se crearian o modificarian.
- Comandos de ejecucion.
- Criterio GO / NO-GO.
- Seccion esperada de QA Report.
- Separacion clara entre tests API con pytest y smoke test frontend con Playwright.

Cuando yo diga "aplica el plan", recien ahi podes:
- generar o modificar archivos de test,
- proponer comandos,
- ejecutar pruebas si tenes acceso a terminal,
- documentar la evidencia en formato QA Report.
```

---

## Respuestas sugeridas para el ida y vuelta

Si el agente pregunta por datos:

```text
La DB de test debe arrancar limpia. Usa fixtures o TestClient segun el patron existente del proyecto.
```

Si pregunta por prioridad:

```text
Priorizo reglas de negocio y consistencia de metricas sobre cantidad de casos.
```

Si pregunta por cobertura existente:

```text
Revisa la carpeta tests/ y evita duplicar casos ya cubiertos. Si algo ya existe, mencionalo como cobertura existente.
```

Si pregunta por frontend:

```text
Inclui el smoke test frontend como checklist o validacion Playwright separada de los tests API.
```

Si el plan esta bien:

```text
El plan esta aprobado. Aplica el plan.
```

Si el plan no esta bien:

```text
No-GO por ahora. Ajusta el plan para no duplicar tests existentes, separar API de frontend y cerrar con QA Report.
No apliques todavia.
```

---

## Resultado esperado del agente

Antes de aplicar:

- Preguntas de alcance.
- Plan de QA.
- Casos propuestos.
- Archivos y comandos.
- Criterio GO / NO-GO.

Despues de `aplica el plan`:

- Tests o propuesta de tests.
- Comandos de ejecucion.
- Resultado esperado.
- Evidencia para QA Report.
- Recomendacion final: GO, NO-GO o GO con observaciones.

