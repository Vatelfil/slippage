import numpy as np, pandas as pd, sys
t = sys.argv[1] if len(sys.argv)>1 else "FALABELLA"
df = pd.read_parquet(f"data/processed/clean_5m_2026-08-23/{t}.parquet")
tm = df.datetime_santiago.dt.hour*60+df.datetime_santiago.dt.minute
df["tramo"] = np.where(tm<690,"apertura",np.where(tm<840,"media","cierre"))
df["day"]=df.datetime_santiago.dt.date
obs = df[~df.is_imputed]
print("imputed share by tramo", df.groupby("tramo").is_imputed.mean().round(3).to_dict())
print("mean vol obs by tramo", obs.groupby("tramo").volume_raw.mean().round(0).to_dict())
print("median vol obs by tramo", obs.groupby("tramo").volume_raw.median().round(0).to_dict())
print("mean vol obs 15:55", obs[tm[obs.index]==955].volume_raw.mean(), " 09:30", obs[tm[obs.index]==570].volume_raw.mean())
o=obs[tm[obs.index]!=955]
print("mean vol obs excl 15:55", o.groupby("tramo").volume_raw.mean().round(0).to_dict())
sgn=np.sign(obs.close_raw-obs.open_raw); print("sign dist", sgn.value_counts().to_dict())
hl=(obs.high_raw-obs.low_raw)/((obs.high_raw+obs.low_raw)/2)
print("HL rel bps", (hl.groupby(obs.tramo).mean()*1e4).round(2).to_dict())
d=df.copy(); d["lp"]=np.log(d.close_raw); d["dp"]=d.groupby("day").lp.diff()
ok=(~d.is_imputed)&(~d.groupby("day").is_imputed.shift(1).fillna(True).astype(bool))
d.loc[~ok,"dp"]=np.nan
d["dpl"]=d.groupby(["day","tramo"]).dp.shift(1)
for tr,g in d.groupby("tramo"):
    g=g.dropna(subset=["dp","dpl"]); c=np.cov(g.dp,g.dpl)[0,1]
    print(tr,"roll cov",c,"S_bps", 2*np.sqrt(-c)*1e4 if c<0 else None, "n",len(g), "ret std", g.dp.std())
d["hl"]=np.where(d.is_imputed,np.nan,(d.high_raw-d.low_raw)/((d.high_raw+d.low_raw)/2))
d["hll"]=d.groupby(["day","tramo"]).hl.shift(1)
for tr,g in d.groupby("tramo"):
    g=g.dropna(subset=["hl","hll"]); print(tr,"HL ac1",np.corrcoef(g.hl,g.hll)[0,1])
