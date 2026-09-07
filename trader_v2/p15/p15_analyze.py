#!/usr/bin/env python3
"""
Phase 15 analysis. Reads only committed arm run files in trader_v2/p15/runs/.
Changes nothing. Applies the Phase 13G clustering identities verbatim.

Per-fold PERFORMANCE is reconstructed from each ledger row's sweep timestamp,
because fold membership is decided at the arm bar. Per-fold FUNNEL counters are
NOT reconstructable from a pooled run and are never presented as such.
"""
import re, os, sys, glob, statistics
from collections import OrderedDict

D = os.path.dirname(os.path.abspath(__file__))
FB = "2026-07-16 00:00"; FC = "2026-08-09 00:00"; FE = "2026-08-31 00:00"

def fold_of(sw):                      # sweep timestamp -> fold, decided at the arm bar
    return "A" if sw < FB else ("B" if sw < FC else ("C" if sw < FE else "?"))

def parse_led(line):
    p = line.split("|")
    def v(i, pre):
        s = p[i]; return s[len(pre):].strip() if s.startswith(pre) else s.strip()
    return dict(inst=p[0], dir=p[1], ltf=p[2],
        sw=v(4,"sw "), swtype=p[5].strip(), swX=float(v(6,"swX ")),
        ch=v(7,"ch "), chL=float(v(8,"chL ")), rt=v(9,"rt "),
        bos=v(10,"bos "), bosL=float(v(11,"bosL ")), fvg=v(12,"fvg "),
        en=v(13,"en "), enPx=float(v(14,"enPx ")), stop=float(v(15,"stop ")),
        outcome=p[16].strip(), R=float(p[17].replace("R","")),
        usd=float(p[18].replace("$","")), reason=p[19].strip(),
        bars=int(p[20].replace("bars","")), fold=fold_of(v(4,"sw ")))

CELL = re.compile(r"^(MGC|MNQ) ([LS]) (1m|3m) ALL \| bars (\d+) \| cov (\d+) \| sw (\d+) \| ch (\d+) \| "
                  r"rt (\d+) \| bos (\d+) \| fvg (\d+) \| fill (\d+) \| W(\d+) Ls(\d+) TO(\d+) \| "
                  r"Rpre (-?\d+) \| Rpost (-?[\d.]+) \|")

def load(arm):
    f = os.path.join(D, "runs", arm + ".txt")
    cells, led = [], []
    for line in open(f):
        m = CELL.match(line.strip())
        if m:
            g = m.groups()
            cells.append(dict(inst=g[0], d=g[1], ltf=g[2], bars=int(g[3]), cov=int(g[4]),
                sw=int(g[5]), ch=int(g[6]), rt=int(g[7]), bos=int(g[8]), fvg=int(g[9]),
                fill=int(g[10]), W=int(g[11]), Ls=int(g[12]), TO=int(g[13]),
                Rpre=float(g[14]), Rpost=float(g[15])))
        elif re.match(r"^(MGC1!|MNQ1!)\|", line):
            led.append(parse_led(line.rstrip("\n")))
    return cells, led

def funnel(cells, ltf=None):
    g = [c for c in cells if ltf is None or c["ltf"] == ltf]
    t = {k: sum(c[k] for c in g) for k in ["sw","ch","rt","bos","fvg","fill"]}
    return t

def pct(a, b): return 100.0*a/b if b else 0.0

def perf(rows):
    n = len(rows)
    if n == 0:
        return dict(n=0, W=0, L=0, TO=0, wr=None, Rpre=0.0, Rpost=0.0,
                    avg=None, med=None, mcl=0, ddR=0.0, ddU=0.0, usd=0.0)
    W = sum(1 for r in rows if r["outcome"] == "WIN")
    TO = sum(1 for r in rows if r["reason"] == "timeout")
    Rs = [r["R"] for r in rows]
    Rpre = sum(5.0 if r["outcome"] == "WIN" else -1.0 for r in rows)
    # equity path in entry order for drawdown
    o = sorted(rows, key=lambda r: r["en"])
    cum = peak = dd = 0.0; cu = pk = ddu = 0.0; cl = mcl = 0
    for r in o:
        cum += r["R"]; peak = max(peak, cum); dd = max(dd, peak-cum)
        cu  += r["usd"]; pk = max(pk, cu);   ddu = max(ddu, pk-cu)
        if r["outcome"] == "WIN": cl = 0
        else:
            cl += 1; mcl = max(mcl, cl)
    return dict(n=n, W=W, L=n-W, TO=TO, wr=100.0*W/n, Rpre=Rpre, Rpost=sum(Rs),
                avg=sum(Rs)/n, med=statistics.median(Rs), mcl=mcl, ddR=dd, ddU=ddu,
                usd=sum(r["usd"] for r in rows))

kp = lambda r: (r["inst"], r["dir"], r["ltf"], r["ch"], r["chL"], r["bos"], r["bosL"], r["en"], r["enPx"])
ka = lambda r: (r["inst"], r["dir"], r["ltf"], r["bos"], r["bosL"], r["en"], r["enPx"])

def clusters(rows, fn):
    g = OrderedDict()
    for r in rows: g.setdefault(fn(r), []).append(r)
    return g

def clus_stats(rows):
    out = {}
    for nm, fn in [("primary", kp), ("alternative", ka)]:
        g = clusters(rows, fn)
        multi = [v for v in g.values() if len(v) > 1]
        nm2 = sum(len(v) for v in multi)
        out[nm] = dict(clusters=len(g), multi=len(multi),
                       largest=max((len(v) for v in g.values()), default=0),
                       in_multi=nm2, pct=pct(nm2, len(rows)))
    return out

def report(arm, label):
    cells, led = load(arm)
    print("=" * 112)
    print(f"ARM: {label}   ({arm})   cells run: {len(cells)}/8   execution fills: {len(led)}")
    print("=" * 112)
    print("\nPOOLED A+B+C FUNNEL  (pooled counters; NOT per-fold measurements)")
    hdr = f"  {'':<6}{'sweeps':>8}{'CHOCH':>8}{'%':>7}{'retest':>8}{'%':>7}{'BOS+d':>7}{'%':>7}{'FVG':>6}{'%':>7}{'fills':>7}{'%':>7}{'sw->fill':>10}"
    print(hdr)
    for ltf in ["1m", "3m"]:
        t = funnel(cells, ltf)
        print(f"  {ltf:<6}{t['sw']:>8}{t['ch']:>8}{pct(t['ch'],t['sw']):>6.1f}%{t['rt']:>8}{pct(t['rt'],t['ch']):>6.1f}%"
              f"{t['bos']:>7}{pct(t['bos'],t['rt']):>6.2f}%{t['fvg']:>6}{pct(t['fvg'],t['bos']):>6.1f}%"
              f"{t['fill']:>7}{pct(t['fill'],t['fvg']):>6.1f}%{pct(t['fill'],t['sw']):>9.2f}%")
    print("\nPER-CELL (pooled A+B+C)")
    h2 = f"  {'cell':<14}{'bars':>7}{'cov':>7}{'sw':>6}{'ch':>6}{'rt':>6}{'bos':>5}{'fvg':>5}{'fill':>6}{'W':>3}{'Ls':>4}{'TO':>4}{'Rpost':>9}{'avg':>9}"
    print(h2)
    for c in cells:
        a = c["Rpost"]/c["fill"] if c["fill"] else None
        print(f"  {c['inst']+' '+c['d']+' '+c['ltf']:<14}{c['bars']:>7}{c['cov']:>7}{c['sw']:>6}{c['ch']:>6}{c['rt']:>6}"
              f"{c['bos']:>5}{c['fvg']:>5}{c['fill']:>6}{c['W']:>3}{c['Ls']:>4}{c['TO']:>4}{c['Rpost']:>9.3f}"
              + (f"{a:>9.4f}" if a is not None else f"{'-':>9}"))
    print("\nPERFORMANCE — pooled and per fold (reconstructed from each fill's sweep timestamp)")
    h3 = (f"  {'scope':<14}{'fills':>6}{'W':>3}{'L':>4}{'TO':>4}{'win%':>7}{'Rpre':>7}{'Rpost':>9}"
          f"{'avgR':>9}{'medR':>9}{'mcL':>5}{'ddR':>8}{'ddUSD':>10}{'USD':>11}")
    print(h3)
    for ltf in ["1m", "3m"]:
        for fold in ["A", "B", "C", "ALL"]:
            rows = [r for r in led if r["ltf"] == ltf and (fold == "ALL" or r["fold"] == fold)]
            p = perf(rows)
            nm = f"{'H1' if ltf=='1m' else 'H2'} {ltf} {fold}"
            print(f"  {nm:<14}{p['n']:>6}{p['W']:>3}{p['L']:>4}{p['TO']:>4}"
                  + (f"{p['wr']:>6.1f}%" if p['wr'] is not None else f"{'-':>7}")
                  + f"{p['Rpre']:>7.0f}{p['Rpost']:>9.3f}"
                  + (f"{p['avg']:>9.4f}" if p['avg'] is not None else f"{'-':>9}")
                  + (f"{p['med']:>9.4f}" if p['med'] is not None else f"{'-':>9}")
                  + f"{p['mcl']:>5}{p['ddR']:>8.3f}{p['ddU']:>10.2f}{p['usd']:>11.2f}")
    print("\nEVENT CLUSTERING (Phase 13G identities, unchanged)")
    for ltf in [None, "1m", "3m"]:
        rows = [r for r in led if ltf is None or r["ltf"] == ltf]
        if not rows: continue
        cs = clus_stats(rows)
        tag = ltf or "all"
        print(f"  {tag:<4} execution N {len(rows):>3} | primary {cs['primary']['clusters']:>3} "
              f"| alternative {cs['alternative']['clusters']:>3} "
              f"| multi(alt) {cs['alternative']['multi']:>2} | largest {cs['alternative']['largest']} "
              f"| fills in multi {cs['alternative']['in_multi']:>3} ({cs['alternative']['pct']:.1f}%)")
    return cells, led

def deltas(arm, label, base_arm="BASE_pooled"):
    bc, bl = load(base_arm); ec, el = load(arm)
    print("\nDELTA vs FROZEN BASELINE  (absolute, and % of baseline)")
    print(f"  {'':<6}{'sweeps':>16}{'CHOCH':>16}{'retest':>16}{'BOS+disp':>16}{'FVG':>14}{'fills':>14}")
    for ltf in ["1m", "3m"]:
        b = funnel(bc, ltf); e = funnel(ec, ltf); out = f"  {ltf:<6}"
        for k in ["sw","ch","rt","bos","fvg","fill"]:
            d = e[k]-b[k]; p = pct(d, b[k]) if b[k] else 0.0
            w = 16 if k not in ("fvg","fill") else 14
            out += f"{d:>+7} ({p:>+5.1f}%)".rjust(w)
        print(out)
    for ltf in ["1m", "3m"]:
        bp = perf([r for r in bl if r["ltf"] == ltf]); ep = perf([r for r in el if r["ltf"] == ltf])
        da = (ep['avg'] or 0) - (bp['avg'] or 0)
        print(f"  {'H1' if ltf=='1m' else 'H2'} {ltf}: fills {bp['n']} -> {ep['n']} ({ep['n']-bp['n']:+d}) | "
              f"wins {bp['W']} -> {ep['W']} ({ep['W']-bp['W']:+d}) | losses {bp['L']} -> {ep['L']} ({ep['L']-bp['L']:+d}) | "
              f"R {bp['Rpost']:+.3f} -> {ep['Rpost']:+.3f} ({ep['Rpost']-bp['Rpost']:+.3f}) | "
              f"expectancy {bp['avg'] or 0:+.4f} -> {ep['avg'] or 0:+.4f} ({da:+.4f}) | "
              f"maxDD_R {bp['ddR']:.3f} -> {ep['ddR']:.3f}")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        args = [os.path.basename(f)[:-4] for f in sorted(glob.glob(os.path.join(D,"runs","*_pooled.txt")))]
    for a in args:
        lbl = {"BASE_pooled":"FROZEN BASELINE (swLen 3, dispMin 1.50)"}.get(a, a)
        report(a, lbl)
        if a != "BASE_pooled":
            deltas(a, lbl)
        print()
