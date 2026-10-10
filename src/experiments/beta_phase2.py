"""Fase 2 de la eleccion de beta (tarea 2.2.3): PPO corto por valor de beta.

Elaborado por PS con apoyo de Claude Code; pendiente de revision por BF
(responsable de la 2.2.3) y MR (PPO).

La fase 1 (`beta_sweep.py`, de BF) uso politicas heuristicas, que no miran la
recompensa: beta solo cambia como se mide, no lo que se hace. Esta fase 2
entrena un Ejecutor con PPO por cada beta candidato (el multiplo 0,1; 0,3 y 1,0
de beta*, mas un control beta = 0) y compara las politicas aprendidas en
semillas de evaluacion NUEVAS por slippage y cumplimiento.

Regla de seleccion (fijada antes de ver datos):
  1. Candidatos: los betas > 0 (con beta = 0 el riesgo pesa 0 %, descartado por
     la regla de BF) cuya politica cumple en promedio >= 95 % de la orden.
  2. Se elige el de menor slippage medio (bps) si su diferencia con el
     segundo mejor es significativa (Wilcoxon pareado por semilla, p < 0,05).
  3. Si no lo es, no se puede distinguir entre candidatos y se usa el valor
     central, 0,3 x beta* (peso del riesgo de 20 a 25 %), declarandolo.
  4. Si ningun candidato cumple el 95 %, tambien se usa el valor central.
Con entrenamiento corto, el resultado es indicativo y se revalida en el
Sprint 5 (tarea 2.3.5, entrenamiento inicial).
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

import numpy as np

from src.envs.spaces import EjecutorActionSpace
from src.experiments import beta_sweep as bs

MULTIPLOS = (0.1, 0.3, 1.0)
MULT_CENTRAL = 0.3
CUMPLIMIENTO_MIN = 0.95
ALPHA = 0.05
PPO_CFG = {"gamma": 0.95, "gae_lambda": 0.95, "lr": 3e-4, "clip": 0.2, "entropy": 0.01,
           "value_coef": 0.5, "epochs": 4, "minibatch": 64, "episodios_por_update": 10}


def clave(mult: float) -> str:
    return f"{mult:g}x"


def betas_candidatos(beta_star: float, multiplos: Sequence[float] = MULTIPLOS) -> Dict[str, float]:
    """{clave: beta} con el control beta = 0 incluido ("0x")."""
    out = {clave(0.0): 0.0}
    out.update({clave(m): float(beta_star * m) for m in multiplos})
    return out


# ---------------------------------------------------------------------------
# Entrenamiento y evaluacion (torch se importa aqui, no al cargar el modulo)
# ---------------------------------------------------------------------------

def entrenar(factory: Callable, beta: float, tramo: str, train_seeds: Sequence[int], q_slice: int,
             ventana_min: int, cfg: Optional[Dict] = None, torch_seed: int = 0,
             log: Callable[[str], None] = print):
    """Entrena un ExecutorActorCritic con PPO, un episodio por semilla. Devuelve
    (red, historial). `factory(executor_id=, q_slice=, ventana_min=, seed=, beta=)`
    crea el entorno (ABIDES calibrado o el simulador de respaldo)."""
    import torch
    from experiments.test_ppo_short_run import RolloutBuffer, ppo_update  # PPO de MR (2.2.1)
    from src.models.actor_critic import ExecutorActorCritic

    cfg = {**PPO_CFG, **(cfg or {})}
    torch.manual_seed(torch_seed)
    np.random.seed(torch_seed)
    net = ExecutorActorCritic(obs_dim=27, action_dim=240)
    opt = torch.optim.Adam(net.parameters(), lr=cfg["lr"])
    space = EjecutorActionSpace()
    buf = RolloutBuffer()
    device = next(net.parameters()).device
    hist: List[Dict] = []

    for i, seed in enumerate(train_seeds, start=1):
        env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=int(seed), beta=beta)
        t0 = time.time()
        try:
            obs, _ = env.reset()
            done, ret, pasos = False, 0.0, 0
            while not done:
                with torch.no_grad():
                    a, lp, _, v = net.get_action_and_value(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
                a_idx = int(a.item())
                obs2, r, done, trunc, _ = env.step(space.decode_flat(a_idx))
                done = bool(done or trunc)
                buf.add(obs, a_idx, float(lp.item()), float(r), float(v.item()), done)
                ret += float(r)
                pasos += 1
                obs = obs2
        finally:
            env.close()
        hist.append({"episodio": i, "seed": int(seed), "retorno": ret, "pasos": pasos,
                     "segundos": round(time.time() - t0, 1)})
        if i % cfg["episodios_por_update"] == 0 or i == len(train_seeds):
            buf.compute_returns_advantages(cfg["gamma"], cfg["gae_lambda"])
            for _ in range(cfg["epochs"]):
                for batch in buf.get_batches(cfg["minibatch"], device):
                    ppo_update(net, opt, batch, clip_ratio=cfg["clip"], entropy_coef=cfg["entropy"],
                               value_coef=cfg["value_coef"])
            buf.clear()
            log(f"  beta={beta:.5g} episodio {i}/{len(train_seeds)}: retorno medio (ult. 10) "
                f"{np.mean([h['retorno'] for h in hist[-10:]]):.3f}")
    return net, hist


def evaluar_red(net, factory: Callable, tramo: str, seeds: Sequence[int], q_slice: int,
                ventana_min: int) -> List[Dict]:
    """Politica determinista (argmax) en semillas de evaluacion; devuelve el
    resumen de cada episodio (`beta_sweep.summarize_episode`). Se evalua con
    beta = 0: slippage y cumplimiento no dependen de beta."""
    import torch

    space = EjecutorActionSpace()
    out = []
    for seed in seeds:
        env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=int(seed), beta=0.0)
        try:
            obs, info = env.reset()
            p_ref = info.get("p_referencia")
            if p_ref is None:
                p_ref = float(info["entry_price"]) / float(info.get("unidades_por_clp", 1.0))
            pasos, done = [], False
            while not done:
                with torch.no_grad():
                    logits, _ = net(torch.as_tensor(obs, dtype=torch.float32).unsqueeze(0))
                obs, _, done, trunc, info = env.step(space.decode_flat(int(torch.argmax(logits, dim=-1).item())))
                done = bool(done or trunc)
                pasos.append(bs.step_record(info))
            out.append(bs.summarize_episode(pasos, float(q_slice), float(p_ref)))
        finally:
            env.close()
    return out


def evaluar_heuristica(nombre: str, factory: Callable, entorno: str, tramo: str, seeds: Sequence[int],
                       q_slice: int, ventana_min: int) -> List[Dict]:
    """Politicas de referencia de la fase 1 en las mismas semillas."""
    out = []
    for seed in seeds:
        env = factory(executor_id=tramo, q_slice=q_slice, ventana_min=ventana_min, seed=int(seed), beta=0.0)
        try:
            out.append(bs.run_episode(env, bs.POLITICAS[nombre], bs.NIVEL_PASIVO[entorno], q_slice))
        finally:
            env.close()
    return out


# ---------------------------------------------------------------------------
# Resumen y seleccion
# ---------------------------------------------------------------------------

def _vals(eps: Sequence[Dict], key: str) -> np.ndarray:
    return np.array([e[key] for e in eps if e.get(key) is not None and np.isfinite(e[key])], dtype=float)


def resumen_evaluacion(eps: Sequence[Dict], beta: float) -> Dict:
    sl, cu = _vals(eps, "slippage_bps"), _vals(eps, "cumplimiento")
    n = len(sl)
    return {"n": len(eps), "slippage_bps_medio": float(sl.mean()) if n else None,
            "slippage_bps_ee": float(sl.std(ddof=1) / np.sqrt(n)) if n > 1 else None,
            "cumplimiento_medio": float(cu.mean()) if len(cu) else None,
            "peso_riesgo": bs.risk_weight(list(eps), beta) if eps else None,
            "slippage_por_semilla": [e.get("slippage_bps") for e in eps]}


def seleccionar_beta(evaluaciones: Dict[str, Dict], beta_star: float) -> Dict:
    """Aplica la regla del encabezado. `evaluaciones[clave]` = resumen_evaluacion
    + "beta". La clave "0x" es solo control."""
    from scipy import stats

    central_k = clave(MULT_CENTRAL)
    central = beta_star * MULT_CENTRAL
    cand = {k: v for k, v in evaluaciones.items() if k != clave(0.0) and v.get("slippage_bps_medio") is not None}
    ok = {k: v for k, v in cand.items() if (v.get("cumplimiento_medio") or 0.0) >= CUMPLIMIENTO_MIN}
    if not ok:
        return {"clave": central_k, "beta": central, "criterio": "central_sin_candidato_que_cumpla",
                "texto": "Ningun candidato cumple el 95 % de la orden: se usa el valor central 0,3 x beta*."}
    orden = sorted(ok, key=lambda k: ok[k]["slippage_bps_medio"])
    mejor = orden[0]
    if len(orden) == 1:
        return {"clave": mejor, "beta": ok[mejor]["beta"], "criterio": "unico_candidato_que_cumple",
                "texto": f"Solo {mejor} cumple el 95 % de la orden."}
    segundo = orden[1]
    a = np.array(ok[mejor]["slippage_por_semilla"], dtype=float)
    b = np.array(ok[segundo]["slippage_por_semilla"], dtype=float)
    m = np.isfinite(a) & np.isfinite(b)
    p = None
    if m.sum() >= 6 and np.any(a[m] != b[m]):
        p = float(stats.wilcoxon(a[m], b[m]).pvalue)
    if p is not None and p < ALPHA:
        return {"clave": mejor, "beta": ok[mejor]["beta"], "criterio": "menor_slippage_significativo", "p": p,
                "texto": f"{mejor} tiene el menor slippage y la diferencia con {segundo} es significativa (p = {p:.3f})."}
    elegido = central_k if central_k in ok else mejor
    return {"clave": elegido, "beta": ok[elegido]["beta"], "criterio": "sin_diferencia_significativa_valor_central",
            "p": p, "texto": "No se distingue entre candidatos con este entrenamiento corto: se usa el valor central "
                             "0,3 x beta* (peso del riesgo de 20 a 25 %). Revalidar en el Sprint 5."}


def correr_fase2(factory: Callable, entorno: str, beta_star: float, tramo: str, n_train: int, n_eval: int,
                 q_slice: int, ventana_min: int, estado: Dict, guardar: Callable[[Dict], None],
                 out_dir: Path, presupuesto_s: Optional[float] = None, cfg: Optional[Dict] = None,
                 train_seed_base: int = 1000, eval_seed_base: int = 5000,
                 log: Callable[[str], None] = print) -> bool:
    """Corre (o reanuda) la fase 2 completa. El avance se guarda tras cada beta
    entrenado y evaluado; si se agota el presupuesto devuelve False."""
    import torch

    t_ini = time.time()
    train_seeds = [train_seed_base + i for i in range(1, n_train + 1)]
    eval_seeds = [eval_seed_base + i for i in range(1, n_eval + 1)]
    for sec in ("entrenamiento", "evaluacion", "episodios_eval", "referencias"):
        estado.setdefault(sec, {})
    out_dir = Path(out_dir)

    for k, b in betas_candidatos(beta_star).items():
        if k in estado["evaluacion"]:
            continue
        if presupuesto_s is not None and time.time() - t_ini > presupuesto_s:
            log("Presupuesto de tiempo agotado: volver a ejecutar para continuar.")
            return False
        log(f"=== beta = {b:.5g} ({k}) ===")
        t0 = time.time()
        net, hist = entrenar(factory, b, tramo, train_seeds, q_slice, ventana_min, cfg, log=log)
        out_dir.mkdir(parents=True, exist_ok=True)
        torch.save(net.state_dict(), out_dir / f"fase2_modelo_{tramo}_{k}.pt")
        eps = evaluar_red(net, factory, tramo, eval_seeds, q_slice, ventana_min)
        ev = resumen_evaluacion(eps, b)
        ev["beta"] = b
        ev["segundos"] = round(time.time() - t0, 1)
        estado["entrenamiento"][k] = {"beta": b, "historial": hist}
        estado["episodios_eval"][k] = eps
        estado["evaluacion"][k] = ev
        guardar(estado)
        log(f"  evaluacion: slippage {ev['slippage_bps_medio']:.2f} bps, cumplimiento {ev['cumplimiento_medio']:.3f}")

    for nombre in bs.POLITICAS:
        if nombre in estado["referencias"]:
            continue
        eps = evaluar_heuristica(nombre, factory, entorno, tramo, eval_seeds, q_slice, ventana_min)
        estado["referencias"][nombre] = resumen_evaluacion(eps, beta_star * MULT_CENTRAL)
        guardar(estado)
    estado["seleccion"] = seleccionar_beta(estado["evaluacion"], beta_star)
    guardar(estado)
    log(estado["seleccion"]["texto"])
    return True


def informe_markdown(estado: Dict) -> str:
    """Tabla del resultado a partir del estado guardado (sin transcribir cifras)."""
    def f(x, d=2):
        return "—" if x is None else f"{x:.{d}f}".replace(".", ",")

    L = ["# Fase 2 de la elección de β (tarea 2.2.3)", "",
         "**Elaborado por:** Paolo Sepúlveda (PS) con apoyo de Claude Code. **Pendiente de revisión por:** Benjamín Farias (BF) y Mauricio Reynoso (MR).", "",
         f"Tramo: {estado['firma']['tramo']} · episodios de entrenamiento por β: {estado['firma']['n_train']} · "
         f"semillas de evaluación: {estado['firma']['n_eval']} · β* = {f(estado['firma']['beta_star'], 4)}", "",
         "| β | Múltiplo | Slippage medio (bps) | Error estándar | Cumplimiento | Peso del riesgo |",
         "|---|---|---:|---:|---:|---:|"]
    for k, e in estado.get("evaluacion", {}).items():
        L.append(f"| {f(e['beta'], 5)} | {k} | {f(e['slippage_bps_medio'])} | {f(e['slippage_bps_ee'])} | "
                 f"{f(e['cumplimiento_medio'], 3)} | {f(e['peso_riesgo'], 3)} |")
    if estado.get("referencias"):
        L += ["", "Políticas heurísticas de referencia (mismas semillas):", "",
              "| Política | Slippage medio (bps) | Cumplimiento |", "|---|---:|---:|"]
        for k, e in estado["referencias"].items():
            L.append(f"| {k} | {f(e['slippage_bps_medio'])} | {f(e['cumplimiento_medio'], 3)} |")
    s = estado.get("seleccion")
    if s:
        L += ["", f"**Selección:** β = {f(s['beta'], 5)} ({s['clave']}). {s['texto']}"]
    L += ["", "**Limitaciones:** entrenamiento corto (indicativo), un solo tramo, una sola semilla de red por β. "
          "Se revalida en el Sprint 5.", "", "🤖 Generado con [Claude Code](https://claude.com/claude-code)"]
    return "\n".join(L) + "\n"
