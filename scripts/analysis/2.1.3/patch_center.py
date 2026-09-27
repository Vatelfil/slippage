p = 'src/envs/calibration_poisson.py'
s = open(p, encoding='utf-8').read()


def rep(a, b, n=1):
    global s
    assert s.count(a) == n, (a[:70], s.count(a))
    s = s.replace(a, b)


rep('''                        steps_per_event: int = 1,
                        target_std: Optional[float] = 0.01) -> np.ndarray:''', '''                        steps_per_event: int = 1,
                        target_std: Optional[float] = 0.01,
                        center: bool = False) -> np.ndarray:''')
rep('''        impacto por orden neta queda fijado por momentos).
        """''', '''        impacto por orden neta queda fijado por momentos). `center=True`
        resta la media muestral (elimina la deriva 10*(lambda+ - lambda-)
        por vela que este modelo reducido asocia a cualquier desbalance).
        """''')
rep('''        events = (raw_impact * damping).sum(axis=1)
        if target_std''', '''        events = (raw_impact * damping).sum(axis=1)
        if center:
            events = events - events.mean()
        if target_std''')
rep('''                   steps_per_event: int = 1, target_std: Optional[float] = 0.01) -> float:''', '''                   steps_per_event: int = 1, target_std: Optional[float] = 0.01,
                   center: bool = False) -> float:''')
rep('''        events = self.generate_events(n_events=n_events, rng=rng,
                                      steps_per_event=steps_per_event, target_std=target_std)
        sim_vol''', '''        events = self.generate_events(n_events=n_events, rng=rng, steps_per_event=steps_per_event,
                                      target_std=target_std, center=center)
        sim_vol''')
rep('''    target_std: Optional[float] = 0.01,
) -> Dict[str, float]:
    """MLE-proxy''', '''    target_std: Optional[float] = 0.01,
    center: bool = False,
) -> Dict[str, float]:
    """MLE-proxy''')
rep('''        return -model.likelihood(obs_spread, obs_skew, obs_vol, n_events=4000, rng=rng,
                                 steps_per_event=steps_per_event, target_std=target_std)''', '''        return -model.likelihood(obs_spread, obs_skew, obs_vol, n_events=4000, rng=rng,
                                 steps_per_event=steps_per_event, target_std=target_std,
                                 center=center)''')
rep('''    steps_per_event: int = 1,
    target_std: Optional[float] = 0.01,
) -> Dict[str, float]:
    """KS de 2 muestras''', '''    steps_per_event: int = 1,
    target_std: Optional[float] = 0.01,
    center: bool = False,
) -> Dict[str, float]:
    """KS de 2 muestras''')
rep('''    calibracion por tramo se usa steps_per_event=10 y target_std=std observada.
    """''', '''    calibracion por tramo se usa steps_per_event=10, target_std=std
    observada y center=True (ambas muestras centradas: el KS evalua forma).
    `sim_drift_sd` reporta la deriva que tendria la simulacion sin centrar,
    en desviaciones estandar.
    """''')
rep('''    simulated = model.generate_events(n_events=n_events, rng=rng,
                                      steps_per_event=steps_per_event, target_std=target_std)
    observed = np.asarray(observed_returns)
    observed = observed[~np.isnan(observed)]
''', '''    simulated = model.generate_events(n_events=n_events, rng=rng,
                                      steps_per_event=steps_per_event, target_std=target_std)
    observed = np.asarray(observed_returns)
    observed = observed[~np.isnan(observed)]
    sim_std = simulated.std()
    sim_drift_sd = float(simulated.mean() / sim_std) if sim_std > 0 else 0.0
    if center:
        simulated = simulated - simulated.mean()
        if len(observed):
            observed = observed - observed.mean()
''')
rep('''            "n_simulated": int(len(simulated)),
            "alpha": alpha,
        }

    ks_stat''', '''            "n_simulated": int(len(simulated)),
            "alpha": alpha,
            "sim_drift_sd": sim_drift_sd,
        }

    ks_stat''')
rep('''        "n_simulated": int(len(simulated)),
        "alpha": alpha,
    }''', '''        "n_simulated": int(len(simulated)),
        "alpha": alpha,
        "sim_drift_sd": sim_drift_sd,
    }''')
rep('''    val = validate_calibration(direct, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                               steps_per_event=STEPS_PER_BAR, target_std=target_std)''', '''    val = validate_calibration(direct, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                               steps_per_event=STEPS_PER_BAR, target_std=target_std, center=True)''')
rep('''    out["directo"] = {**direct, "ks_stat": val["ks_statistic"], "p_value": val["p_value"]}''', '''    out["sim_drift_sd"] = val["sim_drift_sd"]
    out["directo"] = {**direct, "ks_stat": val["ks_statistic"], "p_value": val["p_value"]}''')
rep('''            seed=tramo_seed, bounds=bounds, steps_per_event=STEPS_PER_BAR, target_std=target_std,
        )''', '''            seed=tramo_seed, bounds=bounds, steps_per_event=STEPS_PER_BAR, target_std=target_std,
            center=True,
        )''')
rep('''        mle_val = validate_calibration(mle, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                                       steps_per_event=STEPS_PER_BAR, target_std=target_std)''', '''        mle_val = validate_calibration(mle, returns, n_events=N_SIM_VALIDATION, seed=tramo_seed,
                                       steps_per_event=STEPS_PER_BAR, target_std=target_std,
                                       center=True)''')
rep('''            out["method"] = "mle_proxy"''', '''            out["method"] = "mle_proxy"
            out["sim_drift_sd"] = mle_val["sim_drift_sd"]''')
rep('''        "obs_return_std": float(np.std(returns)) if len(returns) else float("nan"),''', '''        "obs_return_std": float(np.std(returns)) if len(returns) else float("nan"),
        "obs_return_mean": float(np.mean(returns)) if len(returns) else float("nan"),''')
rep('''            target_std=r["obs_return_std"]) * 1e4''', '''            target_std=r["obs_return_std"], center=True) * 1e4
        obs = obs - obs.mean()''')
rep('''        ax.set_xlabel("retorno log 5 min (bps)")''', '''        ax.set_xlabel("retorno log 5 min centrado (bps)")''')
rep('''            "Validacion KS: el impacto por orden neta se fija por momentos (std simulada = std observada); el KS evalua la forma de la distribucion.",''', '''            ("Validacion KS: el impacto por orden neta se fija por momentos (std simulada = std observada) y ambas muestras se centran; "
             "el KS evalua la forma de la distribucion. Sin centrar, el modelo reducido convierte el desbalance lambda+ - lambda- en una "
             "deriva por vela (campo sim_drift_sd) que los retornos observados no presentan."),''')
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print("ok")
