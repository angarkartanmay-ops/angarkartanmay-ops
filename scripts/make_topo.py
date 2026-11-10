import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

W, H, M = 1000, 300, 40
rng = np.random.default_rng(19)
x = np.arange(-M, W + M + 1, 4.0)
y = np.arange(-M, H + M + 1, 4.0)
X, Y = np.meshgrid(x, y)
Z = np.zeros_like(X)
for _ in range(7):
    cx, cy = rng.uniform(0, W), rng.uniform(-40, H + 40)
    sx, sy = rng.uniform(90, 230), rng.uniform(40, 100)
    Z += rng.uniform(0.5, 1.2) * np.exp(-(((X - cx) / sx) ** 2 + ((Y - cy) / sy) ** 2))
for _ in range(5):
    fx, fy, ph = rng.uniform(0.002, 0.006), rng.uniform(0.004, 0.012), rng.uniform(0, 6.28)
    Z += 0.12 * np.sin(fx * X * 2 * np.pi + fy * Y * 2 * np.pi + ph)

levels = np.linspace(Z.min(), Z.max(), 24)
fig, ax = plt.subplots()
out = {"minor": [], "index": []}
for i, lv in enumerate(levels):
    cs = ax.contour(X, Y, Z, levels=[lv])
    segs = cs.allsegs[0]
    d = []
    for s in segs:
        if len(s) < 6:
            continue
        s = s[::2] if len(s) > 12 else s
        d.append("M" + "L".join(f"{px:.1f} {py:.1f}" for px, py in s))
    if d:
        out["index" if i % 5 == 0 else "minor"].append("".join(d))
json.dump({"minor": "".join(out["minor"]), "index": "".join(out["index"])}, open("data/topo.json", "w"))
print(sum(len(v) for v in out["minor"]) + sum(len(v) for v in out["index"]), "chars")
