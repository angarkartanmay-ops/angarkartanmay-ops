import base64
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG, PANEL, LINE, IDX = "#12151A", "#161A20", "#2B3038", "#46505C"
INK, MUTED, ACC, CELL0 = "#E7E9EC", "#8B94A0", "#D9A15B", "#1B2027"
MARKUP = {"CSS", "HTML", "PLpgSQL", "Jupyter Notebook", "Shell", "Batchfile", "Dockerfile",
          "Makefile", "Procfile", "Linker Script"}


def font_css(*names):
    out = []
    for n in names:
        fam, weight = n.rsplit("-", 1)
        family = "Geist Mono" if fam == "geist-mono" else "Geist"
        data = (ROOT / "scripts" / "fonts" / f"{n}.b64").read_text().strip()
        out.append(f'@font-face{{font-family:"{family}";font-weight:{weight};'
                   f'src:url(data:font/woff2;base64,{data}) format("woff2")}}')
    return "".join(out)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def api(path, token, query=None):
    url = "https://api.github.com" + path
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-build"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(query).encode() if query else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_data(cfg):
    snap = json.loads((ROOT / "data" / "snapshot.json").read_text())
    token = os.environ.get("GH_TOKEN")
    if not token or "--offline" in sys.argv:
        return snap, "snapshot"
    login = cfg["login"]
    first = dt.date.today().replace(day=1).isoformat() + "T00:00:00Z"
    q = {"query": """query($login:String!,$from:DateTime!){user(login:$login){
      year:contributionsCollection{contributionCalendar{weeks{contributionDays{date contributionLevel}}}}
      month:contributionsCollection(from:$from){totalCommitContributions totalPullRequestContributions
        commitContributionsByRepository(maxRepositories:100){repository{nameWithOwner}}}}}""",
         "variables": {"login": login, "from": first}}
    u = api("/graphql", token, q)["data"]["user"]
    lv = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}
    days = [d for w in u["year"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    live = {
        "start": days[0]["date"],
        "levels": "".join(str(lv[d["contributionLevel"]]) for d in days),
        "month": {"commits": u["month"]["totalCommitContributions"],
                  "prs": u["month"]["totalPullRequestContributions"],
                  "repos": len(u["month"]["commitContributionsByRepository"])},
        "langs": {},
    }
    for p in cfg["featured"]:
        live["langs"][p["repo"]] = api(f"/repos/{login}/{p['repo']}/languages", token)
    (ROOT / "data" / "snapshot.json").write_text(json.dumps(live, indent=1))
    return live, "live"


def hero(cfg, topo):
    h = cfg["hero"]
    W, H = 1000, 300
    lines = h["lines"]
    n = len(lines)
    slot = 5.4
    T = slot * n
    adv = 0.6 * 17
    x0, ty = 78, 206
    css = []
    body = []
    for i, text in enumerate(lines):
        chars = len(text)
        width = chars * adv
        s = i * slot
        d = chars * 0.045
        e = s + slot - 0.35
        pc = lambda t: f"{t / T * 100:.3f}%"
        start_vis = "0%{opacity:1}" if i == 0 else f"0%,{pc(s - 0.02)}{{opacity:0}}{pc(s)}{{opacity:1}}"
        css.append(f"@keyframes o{i}{{{start_vis}{pc(e)}{{opacity:1}}{pc(e + 0.02)}{{opacity:0}}100%{{opacity:0}}}}")
        css.append(f"@keyframes t{i}{{0%,{pc(s)}{{transform:scaleX(0);animation-timing-function:steps({chars},end)}}"
                   f"{pc(s + d)}{{transform:scaleX(1)}}100%{{transform:scaleX(1)}}}}")
        css.append(f"@keyframes c{i}{{0%,{pc(s)}{{transform:translateX(0);animation-timing-function:steps({chars},end)}}"
                   f"{pc(s + d)}{{transform:translateX({width:.1f}px)}}100%{{transform:translateX({width:.1f}px)}}}}")
        css.append(f".l{i}{{animation:o{i} {T}s linear infinite}}.k{i}{{animation:t{i} {T}s linear infinite;transform-origin:{x0}px 0}}"
                   f".m{i}{{animation:c{i} {T}s linear infinite}}")
        op = 1 if i == 0 else 0
        body.append(
            f'<g class="ln l{i}" style="opacity:{op}">'
            f'<clipPath id="cp{i}"><rect class="k{i}" x="{x0}" y="{ty - 20}" width="{width + 4:.1f}" height="28"/></clipPath>'
            f'<text x="{x0}" y="{ty}" class="mono t" clip-path="url(#cp{i})">{esc(text)}</text>'
            f'<g class="m{i}"><rect class="caret" x="{x0}" y="{ty - 16}" width="2" height="21" fill="{ACC}"/></g>'
            f'</g>')
    # first line is shown fully (and caret at end) when animation is off
    static_first = ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(h['name'])} - {esc(lines[0])}">
<style>
{font_css('geist-600', 'geist-mono-400', 'geist-mono-500')}
.name{{font-family:"Geist",sans-serif;font-weight:600;font-size:56px;letter-spacing:-0.04em;fill:{INK}}}
.mono{{font-family:"Geist Mono",monospace}}
.tag{{font-family:"Geist Mono",monospace;font-weight:500;font-size:12.5px;letter-spacing:.14em;fill:{ACC}}}
.t{{font-size:17px;fill:{INK}}}
.foot{{font-size:12.5px;fill:{MUTED};letter-spacing:.01em}}
.caret{{opacity:1}}
.m0{{transform:translateX({0.6 * 17 * len(lines[0]):.1f}px)}}
@media (prefers-reduced-motion:no-preference){{
.drift{{animation:drift 46s ease-in-out infinite alternate}}
@keyframes drift{{from{{transform:translate(0,0)}}to{{transform:translate(-16px,7px)}}}}
.caret{{animation:blink 1.06s steps(1,end) infinite}}
@keyframes blink{{0%{{opacity:1}}50%{{opacity:0}}}}
{''.join(css)}
}}
</style>
<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="14"/></clipPath>
<linearGradient id="fade" x1="0" x2="1" y1="0" y2="0">
<stop offset="0" stop-color="{BG}" stop-opacity=".95"/><stop offset=".5" stop-color="{BG}" stop-opacity=".86"/><stop offset="1" stop-color="{BG}" stop-opacity=".05"/>
</linearGradient>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="{BG}"/>
<g class="drift" fill="none" stroke-linejoin="round">
<path d="{topo['minor']}" stroke="{LINE}" stroke-width=".7"/>
<path d="{topo['index']}" stroke="{IDX}" stroke-width="1"/>
</g>
<rect width="{W}" height="{H}" fill="url(#fade)"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{LINE}"/>
<line x1="56" x2="80" y1="74" y2="74" stroke="{ACC}"/>
<text x="92" y="78" class="tag">{esc(h['tag'])}</text>
<text x="54" y="148" class="name">{esc(h['name'])}</text>
<text x="56" y="{ty}" class="mono t" style="fill:{ACC}">&gt;</text>
{''.join(body)}
<text x="56" y="262" class="mono foot">{esc(h['footer'])}</text>
</g>
</svg>"""


def wrap_chips(tags, maxw):
    out, x = [], 0
    for t in tags:
        w = len(t) * 6.4 + 16
        if x + w > maxw:
            break
        out.append((t, x, w))
        x += w + 6
    return out


def card(i, p, primary):
    W, H = 320, 190
    chips = wrap_chips(p["tags"], 280)
    chip_svg = "".join(
        f'<rect x="{20 + x:.1f}" y="124" width="{w:.1f}" height="22" rx="5" fill="#1D222A" stroke="{LINE}"/>'
        f'<text x="{20 + x + 8:.1f}" y="139" class="mono chip">{esc(t)}</text>' for t, x, w in chips)
    for ln in p["pitch"]:
        assert len(ln) <= 40, f"pitch line too long: {ln}"
    delay = -i * 1.3
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{esc(p['name'])}: {esc(' '.join(p['pitch']))}">
<style>
{font_css('geist-400', 'geist-600', 'geist-mono-400', 'geist-mono-500')}
.st{{font-family:"Geist Mono",monospace;font-weight:500;font-size:10.5px;letter-spacing:.12em;fill:{ACC}}}
.nm{{font-family:"Geist",sans-serif;font-weight:600;font-size:23px;letter-spacing:-.03em;fill:{INK}}}
.pt{{font-family:"Geist",sans-serif;font-weight:400;font-size:13px;fill:{MUTED}}}
.mono{{font-family:"Geist Mono",monospace}}
.chip{{font-size:10.5px;fill:{MUTED}}}
.ft{{font-size:11px;fill:{MUTED}}}
@media (prefers-reduced-motion:no-preference){{
.sweep{{animation:sw 7.8s ease-in-out {delay:.1f}s infinite alternate}}
@keyframes sw{{from{{transform:translateX(0)}}to{{transform:translateX(236px)}}}}
}}
</style>
<defs><clipPath id="r"><rect width="{W}" height="{H}" rx="12"/></clipPath></defs>
<g clip-path="url(#r)">
<rect width="{W}" height="{H}" fill="{PANEL}"/>
<rect class="sweep" x="22" y="0" width="40" height="2" fill="{ACC}" opacity=".9"/>
</g>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="11.5" fill="none" stroke="{LINE}"/>
<text x="20" y="38" class="st">{esc(p['status'])}</text>
<text x="20" y="72" class="nm">{esc(p['name'])}</text>
<text x="20" y="94" class="pt">{esc(p['pitch'][0])}</text>
<text x="20" y="112" class="pt">{esc(p['pitch'][1])}</text>
{chip_svg}
<circle cx="25" cy="170" r="3.5" fill="{IDX}"/>
<text x="35" y="174" class="mono ft">{esc(primary)}</text>
<text x="262" y="174" class="mono ft" text-anchor="end">view repo</text>
<path d="M270 170h22M286 165l6 5-6 5" fill="none" stroke="{ACC}" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>"""


def lang_totals(langs):
    tot = {}
    for repo in langs.values():
        for k, v in repo.items():
            if k not in MARKUP:
                tot[k] = tot.get(k, 0) + v
    s = sum(tot.values()) or 1
    return sorted(((k, v / s) for k, v in tot.items()), key=lambda kv: -kv[1])


def mix(op):
    c = int(ACC[1:], 16)
    r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
    br, bg_, bb = int(CELL0[1:3], 16), int(CELL0[3:5], 16), int(CELL0[5:7], 16)
    return "#%02x%02x%02x" % (round(br + (r - br) * op), round(bg_ + (g - bg_) * op), round(bb + (b - bb) * op))


def activity(data):
    W, H = 1000, 216
    start = dt.date.fromisoformat(data["start"])
    levels = [int(c) for c in data["levels"]]
    end = start + dt.timedelta(days=len(levels) - 1)
    grid_start = end - dt.timedelta(days=(end.weekday() + 1) % 7) - dt.timedelta(weeks=25)
    shades = [CELL0, mix(.30), mix(.55), mix(.80), mix(1.0)]
    cell, gap, gx, gy = 14, 4, 28, 62
    base, over, pos, tg = [], [], {}, []
    for c in range(26):
        for r in range(7):
            d = grid_start + dt.timedelta(weeks=c, days=r)
            if d > end:
                continue
            idx = (d - start).days
            lv = levels[idx] if 0 <= idx < len(levels) else 0
            x, y = gx + c * (cell + gap), gy + r * (cell + gap)
            pos[(c, r)] = (x, y)
            base.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{CELL0}"/>')
            if lv:
                tg.append((c, r))
                over.append(f'<rect class="e e{c}_{r}" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{shades[lv]}"/>')
    path = []
    for c in range(26):
        rows = [r for r in range(7) if (c, r) in pos]
        path += [(c, r) for r in (rows[::-1] if c % 2 else rows)]
    N = len(path)
    tgs = set(tg)
    tm = [0.0]
    for q in range(1, N):
        tm.append(tm[-1] + (0.085 if path[q] in tgs else 0.03))
    move = tm[-1]
    T = move + 5.0
    pc = lambda t: f"{t / T * 100:.3f}%"
    anim = []
    for (c, r) in tg:
        j = tm[path.index((c, r))]
        anim.append(f"@keyframes e{c}_{r}{{0%,{pc(j)}{{opacity:1}}{pc(j + 0.05)}{{opacity:0}}{pc(move + 1.0)}{{opacity:0}}{pc(move + 1.6)}{{opacity:1}}100%{{opacity:1}}}}"
                    f".e{c}_{r}{{animation:e{c}_{r} {T:.2f}s linear infinite}}")
    seg_svg = []
    for k in range(5):
        stops = "".join(f"{pc(tm[i])}{{transform:translate({pos[path[max(i - k, 0)]][0]}px,{pos[path[max(i - k, 0)]][1]}px)}}" for i in range(N))
        anim.append(f"@keyframes g{k}{{{stops}100%{{transform:translate({pos[path[N - 1 - 0]][0] if k == 0 else pos[path[N - 1]][0]}px,{pos[path[N - 1]][1]}px)}}}}.g{k}{{animation:g{k} {T:.2f}s linear infinite}}")
        size, off, op = (cell, 0, 1) if k == 0 else (cell - 3 - k // 2, (3 + k // 2) / 2, [0, .8, .6, .45, .32][k])
        seg_svg.append(f'<rect class="g{k}" x="{off}" y="{off}" width="{size}" height="{size}" rx="{4 if k == 0 else 3}" fill="{INK}" opacity="{op}"/>')
    anim.append(f"@keyframes sf{{0%{{opacity:1}}{pc(move + 0.15)}{{opacity:1}}{pc(move + 0.6)}{{opacity:0}}100%{{opacity:0}}}}.snake{{animation:sf {T:.2f}s linear infinite}}")
    cells = base + over
    sweeps = ['<g class="snake" style="opacity:0">' + "".join(reversed(seg_svg)) + "</g>"]
    snake_css = "".join(anim)
    m = data["month"]
    stats = [(m["commits"], "commits this month"), (m["prs"], "pull requests this month"), (m["repos"], "repos touched")]
    stat_svg = "".join(
        f'<text x="{560 + k * 150}" y="104" class="num">{v}</text><text x="{560 + k * 150}" y="126" class="mono lab">{esc(t)}</text>'
        for k, (v, t) in enumerate(stats))
    stat_svg = stat_svg.replace("pull requests this month", "pull requests").replace("commits this month", "commits")
    langs = lang_totals(data["langs"])[:4]
    barx, barw, bary = 560, 412, 158
    segs, legend, x = [], [], barx
    for k, (name, share) in enumerate(langs):
        w = share / sum(s for _, s in langs) * barw
        op = [1, .7, .5, .35][k]
        segs.append(f'<rect x="{x:.1f}" y="{bary}" width="{max(w - 2, 2):.1f}" height="8" rx="2" fill="{ACC}" opacity="{op}"/>')
        lx = barx + sum(len(f"{n_} {round(sh * 100)}%") * 6.6 + 34 for n_, sh in langs[:k])
        legend.append(f'<rect x="{lx}" y="182" width="8" height="8" rx="2" fill="{ACC}" opacity="{op}"/>'
                      f'<text x="{lx + 14}" y="190" class="mono lab">{esc(name)} {round(share * 100)}%</text>')
        x += w
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Recent GitHub activity: {m['commits']} commits and {m['prs']} pull requests this month across {m['repos']} repositories">
<style>
{font_css('geist-600', 'geist-mono-400', 'geist-mono-500')}
.mono{{font-family:"Geist Mono",monospace}}
.eyebrow{{font-family:"Geist Mono",monospace;font-weight:500;font-size:11px;letter-spacing:.14em;fill:{ACC}}}
.lab{{font-size:11px;fill:{MUTED}}}
.num{{font-family:"Geist",sans-serif;font-weight:600;font-size:38px;letter-spacing:-.04em;fill:{INK}}}
@media (prefers-reduced-motion:no-preference){{
{snake_css}
}}
</style>
<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="13.5" fill="none" stroke="{LINE}"/>
<text x="28" y="38" class="eyebrow">CONTRIBUTIONS</text>
<text x="150" y="38" class="mono lab">last 26 weeks</text>
{''.join(cells)}
{''.join(sweeps)}
<line x1="520" x2="520" y1="30" y2="186" stroke="{LINE}"/>
<text x="560" y="38" class="eyebrow">THIS MONTH</text>
{stat_svg}
{''.join(segs)}
{''.join(legend)}
<text x="560" y="150" class="mono lab" style="font-size:10px;letter-spacing:.08em">LANGUAGES / BY BYTES / FEATURED REPOS</text>
</svg>"""


def main():
    cfg = json.loads((ROOT / "projects.json").read_text())
    topo = json.loads((ROOT / "data" / "topo.json").read_text())
    data, mode = load_data(cfg)
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)
    (out / "hero.svg").write_text(hero(cfg, topo))
    for i, p in enumerate(cfg["featured"]):
        langs = data["langs"].get(p["repo"], {})
        prim = next(iter(sorted(((k, v) for k, v in langs.items() if k not in MARKUP), key=lambda kv: -kv[1])), ("", 0))[0] or "n/a"
        (out / f"card-{i + 1}.svg").write_text(card(i, p, prim))
    (out / "activity.svg").write_text(activity(data))
    print(f"built ({mode} data)")


if __name__ == "__main__":
    main()
