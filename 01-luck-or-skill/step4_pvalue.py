# 4단계: p-value로 "그냥 운이었다면 이런 결과가 얼마나 자주 나올까"를 구한다.
# 실행: python step4_pvalue.py
# ① 챔피언별: 진짜 승률이 50%라고 치고(귀무가설) 내 기록만큼 쏠릴 확률
# ② 소나·자이라·룰루끼리: 두 챔피언 승률이 사실 같다고 치고 이만큼 벌어질 확률
# 결과: data/step4_champions.csv, data/step4_compare.csv

import csv
import random
from itertools import combinations
from pathlib import Path

# ---- 설정 ----
REPEAT = 10_000                      # 50% 동전 시즌, 섞어서 다시 나누기를 각각 몇 번 할지
SEED = 42                            # 난수 시작점. 같으면 매번 같은 결과가 나온다
ALPHA = 0.05                         # 기본 문턱. 운으로 100번 중 5번도 안 나오면 "운 아님"
MIN_GAMES = 5                        # 이보다 적게 한 챔피언은 뺀다
COMPARE = ["Sona", "Zyra", "Lulu"]   # 서로 비교할 챔피언

HERE = Path(__file__).parent
DATA = HERE / "data"


def load_games():
    """2단계 표를 읽고 다시하기 판은 뺀다."""
    with open(DATA / "my_games.csv", encoding="utf-8") as f:
        return [g for g in csv.DictReader(f) if g["remake"] == "0"]


def p_vs_half(results, rng):
    """50% 동전을 판수만큼 던지는 "50% 동전 시즌"을 REPEAT번 만들고,
    내 실제 기록만큼(또는 더) 50%에서 멀어진 경우가 몇 번인지 센다. 위·아래 양쪽 다 센다."""
    n = len(results)
    gap = abs(sum(results) - n / 2)            # 내 기록이 "반타작"에서 몇 판 벗어났나
    hits = 0
    for _ in range(REPEAT):
        fake_wins = sum(rng.random() < 0.5 for _ in range(n))
        if abs(fake_wins - n / 2) >= gap:
            hits += 1
    return hits / REPEAT


def p_same_rate(a, b, rng):
    """두 챔피언 기록을 한 통에 섞고 무작위로 다시 나누기를 REPEAT번 해서,
    실제 승률 차이만큼(또는 더) 벌어진 경우가 몇 번인지 센다. 양쪽 다 센다."""
    real = abs(sum(a) / len(a) - sum(b) / len(b))
    pool = a + b
    hits = 0
    for _ in range(REPEAT):
        rng.shuffle(pool)
        fake_a, fake_b = pool[:len(a)], pool[len(a):]
        if abs(sum(fake_a) / len(fake_a) - sum(fake_b) / len(fake_b)) >= real - 1e-12:
            hits += 1
    return hits / REPEAT


def verdict(p, threshold):
    return "운으로 보기 어려움" if p < threshold else "판단 보류"


def champion_table(games):
    """① 챔피언별(MIN_GAMES판 이상)과 전체의 p-value와 판정."""
    rng = random.Random(SEED)
    by_champ = {}
    for g in games:
        by_champ.setdefault(g["champion"], []).append(int(g["win"]))
    kept = sorted(((c, r) for c, r in by_champ.items() if len(r) >= MIN_GAMES),
                  key=lambda kv: -len(kv[1]))
    threshold = ALPHA / len(kept)              # 여러 개를 동시에 보니 문턱을 그만큼 높인다

    rows = [one_row(c, r, threshold, rng) for c, r in kept]
    rows.append(one_row("(전체)", [int(g["win"]) for g in games], ALPHA, rng))
    return rows


def one_row(champ, results, threshold, rng):
    p = p_vs_half(results, rng)
    return {
        "champion": champ,
        "games": len(results),
        "wins": sum(results),
        "win_rate": round(sum(results) / len(results), 3),
        "p_value": round(p, 4),
        "threshold": threshold,
        "verdict": verdict(p, threshold),
    }


def compare_table(games):
    """② 두 챔피언씩 묶어 p-value와 판정."""
    rng = random.Random(SEED)
    results = {c: [int(g["win"]) for g in games if g["champion"] == c] for c in COMPARE}
    pairs = list(combinations(COMPARE, 2))
    threshold = ALPHA / len(pairs)
    rows = []
    for a, b in pairs:
        p = p_same_rate(results[a], results[b], rng)
        diff = sum(results[a]) / len(results[a]) - sum(results[b]) / len(results[b])
        rows.append({
            "pair": f"{a} - {b}",
            "diff": round(diff, 3),
            "p_value": round(p, 4),
            "threshold": threshold,
            "verdict": verdict(p, threshold),
        })
    return rows


def save(rows, name):
    with open(DATA / name, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def pct(x):
    return f"{x * 100:5.1f}%"


def main():
    games = load_games()
    print(f"다시하기 뺀 {len(games)}판으로 분석합니다. (50% 동전 시즌 {REPEAT}번, {MIN_GAMES}판 미만 챔피언 제외)\n")

    champs = champion_table(games)
    save(champs, "step4_champions.csv")
    print("① 챔피언별: 진짜 승률이 50%라면 이만큼 쏠릴 확률")
    print(f"{'챔피언':<14}{'판수':>4}  {'승률':>6}  {'p-value':>8}  {'문턱':>7}  판정")
    for r in champs:
        print(f"{r['champion']:<14}{r['games']:>4}  {pct(r['win_rate'])}  {r['p_value']:>8.4f}  "
              f"{r['threshold']:>7.4f}  {r['verdict']}")

    pairs = compare_table(games)
    save(pairs, "step4_compare.csv")
    print("\n② 챔피언 비교: 두 챔피언 승률이 사실 같다면 이만큼 벌어질 확률")
    for r in pairs:
        print(f"{r['pair']:<14}차이 {pct(r['diff'])}  p {r['p_value']:.4f}  "
              f"문턱 {r['threshold']:.4f}  {r['verdict']}")

    print("\n저장: data/step4_champions.csv, data/step4_compare.csv")


if __name__ == "__main__":
    main()
