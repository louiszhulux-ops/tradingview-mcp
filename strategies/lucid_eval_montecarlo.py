import random
random.seed(23)
# Test A measured on MGC, 11 months, no prop constraints
N,W,GP,GL = 153,26,29948.52,29714.96
P = W/N; AW = GP/W; AL = GL/(N-W)
TPD = N/240.0                      # trades per trading day
print(f"Raw strategy (MGC, unconstrained): {N} trades, win {P:.1%}, "
      f"avg win ${AW:,.0f}, avg loss ${AL:,.0f}, E[trade] ${P*AW-(1-P)*AL:+,.2f}, "
      f"{TPD:.2f} trades/day")

START,TARGET,MLL,DLL,LOCK = 50000.0,3000.0,2000.0,1200.0,50100.0
def draw(k):
    if random.random() < P: return  min(random.expovariate(1/AW), 2385.52)*k
    return -min(random.expovariate(1/AL), 411.48)*k

def sim(k, use_dll=True, days=60, trials=40000):
    passes=fails=cons_fail=0; dlist=[]; worst=0.0
    for _ in range(trials):
        bal=START; floor=START-MLL; locked=False
        daily=[]; dead=False
        for d in range(1,days+1):
            dstart=bal; blocked=False
            nt = 1 if random.random()<TPD else 0
            nt += 1 if random.random()<(TPD-int(TPD)) else 0
            for _t in range(nt):
                if blocked: break
                bal += draw(k)
                if bal <= floor: dead=True; break
                if use_dll and bal-dstart <= -DLL: blocked=True
            if dead: break
            daily.append(bal-dstart)
            worst=min(worst,bal-dstart)
            if not locked:                      # EOD trail
                floor=max(floor,bal-MLL)
                if bal >= START+MLL: floor,locked=LOCK,True
            if bal <= floor: dead=True; break
            if bal >= START+TARGET:
                tot=bal-START; mx=max([x for x in daily if x>0] or [0])
                if tot>0 and mx/tot <= 0.50: passes+=1; dlist.append(d)
                else: cons_fail+=1
                break
        else:
            fails+=1
        if dead: fails+=1
    dlist.sort()
    med = dlist[len(dlist)//2] if dlist else None
    p2 = sum(1 for x in dlist if x<=2)/trials
    p5 = sum(1 for x in dlist if x<=5)/trials
    return passes/trials, cons_fail/trials, fails/trials, med, p2, p5

print(f"\nLucidDaily 50K: +$3,000 target | $2,000 MLL trailing->locks $50,100 | "
      f"$1,200 DLL | 50% consistency\n")
h=f"{'size':>6}{'maxCtr~':>9}{'P(pass)':>10}{'P(consist.fail)':>17}{'P(breach/timeout)':>19}{'med days':>10}{'P(<=2d)':>9}"
print(h); print('-'*len(h))
for k in (1,2,3,5,8,12,20):
    pp,cf,ff,md,p2,p5 = sim(k)
    print(f"{k:>5}x{2*k:>9}{pp:>10.1%}{cf:>17.1%}{ff:>19.1%}{str(md):>10}{p2:>9.1%}")
