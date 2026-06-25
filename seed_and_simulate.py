"""
seed_and_simulate.py
Clase 7 — CI/CD con GenIA | Simulador Mundial 2026

Corre en el job 'simulate' de GitHub Actions:
  1. Levanta la app FastAPI con BD en memoria
  2. Llama a POST /simulator/run
  3. Llama a GET /metrics/dashboard
  4. Llama a GET /teams/
  5. Guarda los tres JSON en dist/data/
  6. Copia static/index.html → dist/index.html (versión estática sin fetch)

NO importar ni modificar. Ejecutar como:
  python seed_and_simulate.py
"""

import json
import os
import shutil
import sys
import time
import threading
import urllib.request
import urllib.error

# ── configurar BD en memoria antes de importar la app ──────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import main as app_module  # importa la app FastAPI y dispara Base.metadata.create_all

BASE_URL = "http://127.0.0.1:8765"
DIST_DIR = "dist"
DATA_DIR = os.path.join(DIST_DIR, "data")


def _start_server():
    """Levanta uvicorn en un thread daemon."""
    import uvicorn
    uvicorn.run(app_module.app, host="127.0.0.1", port=8765, log_level="warning")


def _wait_for_server(timeout=30):
    """Espera hasta que el servidor responda en /docs."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/docs", timeout=2)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _get(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def _post(path):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=b"",
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _save(data, filename):
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ {path}")


def _build_static_html(simulation, metrics, teams):
    """
    Versión estática del index.html:
    - Elimina el botón 'Simular Mundial' (ya simulado)
    - Reemplaza los fetch() por datos embebidos como JS const
    - Llama directamente a mostrarResultados() y renderiza equipos/dashboard
      con los JSON del pipeline
    """
    with open("static/index.html", encoding="utf-8") as f:
        html = f.read()

    # Inyectar banner de pipeline sobre el hero
    pipeline_badge = (
        '<div style="text-align:center;padding:6px 0 2px;">'
        '<span style="background:#16a34a;color:#fff;font-size:0.78rem;'
        'font-weight:600;padding:3px 12px;border-radius:12px;letter-spacing:0.5px;">'
        '⚡ Simulado por GitHub Actions CI/CD</span></div>'
    )
    html = html.replace(
        "<title>CDA Simulador Mundial 2026</title>",
        "<title>CDA Simulador Mundial 2026 — CI/CD</title>"
    )

    # Reemplazar el bloque <script> completo
    old_script_start = '  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n  <script>'
    new_script = f"""  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <script>
    // ── Datos generados por GitHub Actions CI/CD ──────────────────────────
    const SIMULATION = {json.dumps(simulation, ensure_ascii=False)};
    const METRICS    = {json.dumps(metrics,    ensure_ascii=False)};
    const TEAMS      = {json.dumps(teams,       ensure_ascii=False)};
    // ──────────────────────────────────────────────────────────────────────

    document.addEventListener("DOMContentLoaded", function() {{
      renderEquipos(TEAMS);
      mostrarResultados(SIMULATION);
      mostrarDashboardStatic(METRICS);
    }});

    function renderEquipos(teams) {{
      const container = document.getElementById("teamsContainer");
      const groups = {{}};
      teams.forEach(t => {{
        const g = t.group_name || "X";
        if (!groups[g]) groups[g] = [];
        groups[g].push(t);
      }});
      container.innerHTML = "";
      for (const [letter, gteams] of Object.entries(groups).sort()) {{
        const col = document.createElement("div");
        col.className = "col-md-3 col-sm-6";
        col.innerHTML = `
          <div class="group-card">
            <div class="group-header">Grupo ${{letter}}</div>
            <table class="group-table">
              <thead><tr><th></th><th>Equipo</th><th>Cod.</th></tr></thead>
              <tbody>
                ${{gteams.map((t, i) => `
                  <tr class="${{i < 2 ? 'qualified' : 'eliminated'}}">
                    <td><span class="position-badge pos-${{i+1}}">${{i+1}}</span></td>
                    <td><span class="team-name">${{t.name}}</span></td>
                    <td>${{t.code}}</td>
                  </tr>`).join("")}}
              </tbody>
            </table>
          </div>`;
        container.appendChild(col);
      }}
    }}

    function mostrarDashboardStatic(m) {{
      const container = document.getElementById("dashboardResult");
      container.innerHTML = `
        <h3 class="section-title">Dashboard Ejecutivo</h3>
        <div class="dashboard-grid">
          <div class="kpi-card accent-gold">
            <div class="kpi-icon">🏆</div>
            <div class="kpi-value">${{m.champion}}</div>
            <div class="kpi-label">Campeón</div>
          </div>
          <div class="kpi-card accent-blue">
            <div class="kpi-icon">⚽</div>
            <div class="kpi-value">${{m.top_scorer.player_name}}</div>
            <div class="kpi-label">Botín de Oro</div>
            <div class="kpi-sub">${{m.top_scorer.team_name}} · ${{m.top_scorer.goals}} goles</div>
          </div>
          <div class="kpi-card accent-green">
            <div class="kpi-icon">📊</div>
            <div class="kpi-value">${{m.avg_goals_per_match}}</div>
            <div class="kpi-label">Prom. Goles/Partido</div>
          </div>
          <div class="kpi-card accent-secondary">
            <div class="kpi-icon">🥅</div>
            <div class="kpi-value">${{m.total_goals}}</div>
            <div class="kpi-label">Goles Totales</div>
            <div class="kpi-sub">en ${{m.total_matches}} partidos</div>
          </div>
        </div>`;
    }}"""

    # Pegar la función mostrarResultados original (sin cambios — misma estructura de datos)
    script_end_marker = "\n    async function mostrarDashboard()"
    orig_script_body = html[html.index(old_script_start):]
    mr_start = orig_script_body.index("\n    function mostrarResultados(data)")
    mr_end   = orig_script_body.index(script_end_marker)
    mostrar_resultados_fn = orig_script_body[mr_start:mr_end]

    new_script += mostrar_resultados_fn + "\n  </script>"

    # Reemplazar desde <script src=bootstrap> hasta </script>
    script_block_start = html.index(old_script_start)
    html = html[:script_block_start] + new_script + "\n</body>\n</html>"

    # Ocultar botón Simular (ya no tiene sentido en la versión estática)
    html = html.replace(
        'onclick="simularMundial()"',
        'onclick="simularMundial()" style="display:none"'
    )

    # Inyectar badge de pipeline antes del cierre del hero
    html = html.replace(
        "<p>Fase de Grupos a la Final &mdash; por CDA Soluciones Confiables</p>",
        f"<p>Fase de Grupos a la Final &mdash; por CDA Soluciones Confiables</p>\n    {pipeline_badge}"
    )

    return html


def main():
    print("🚀 seed_and_simulate.py — Simulador Mundial 2026")
    print("   BD: sqlite:///:memory: (volátil, se destruye al terminar)")
    print()

    # Arrancar servidor en background
    print("▶ Iniciando servidor FastAPI...")
    t = threading.Thread(target=_start_server, daemon=True)
    t.start()

    if not _wait_for_server():
        print("✗ El servidor no respondió en 30s")
        sys.exit(1)
    print("  ✓ Servidor listo en", BASE_URL)
    print()

    # Llamar endpoints
    print("▶ Simulando el Mundial...")
    simulation = _post("/simulator/run")
    print(f"  ✓ Campeón: {simulation['champion']}")

    print("▶ Obteniendo métricas...")
    metrics = _get("/metrics/dashboard")
    print(f"  ✓ Goleador: {metrics['top_scorer']['player_name']} ({metrics['top_scorer']['goals']} goles)")

    print("▶ Obteniendo equipos...")
    teams = _get("/teams/")
    print(f"  ✓ {len(teams)} equipos")
    print()

    # Guardar JSONs
    print("▶ Guardando datos en dist/data/...")
    _save(simulation, "simulation.json")
    _save(metrics,    "metrics.json")
    _save(teams,      "teams.json")
    print()

    # Construir index.html estático
    print("▶ Generando dist/index.html (estático, sin backend)...")
    static_html = _build_static_html(simulation, metrics, teams)
    os.makedirs(DIST_DIR, exist_ok=True)
    with open(os.path.join(DIST_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(static_html)
    print("  ✓ dist/index.html")

    # Copiar imágenes
    img_src = os.path.join("static", "images")
    img_dst = os.path.join(DIST_DIR, "images")
    if os.path.isdir(img_src):
        shutil.copytree(img_src, img_dst, dirs_exist_ok=True)
        print("  ✓ dist/images/")
    print()
    print("✅ dist/ listo para GitHub Pages")
    print(f"   Campeón del Mundo 2026: {simulation['champion']} 🏆")


if __name__ == "__main__":
    main()
