# 3단계: 부트스트랩으로 "내 진짜 승률이 있을 법한 범위(95%)"를 구한다.
# 실행: python step3_bootstrap.py
# ① 챔피언별 승률 범위와 판정  ② 소나·자이라·룰루끼리 승률 차이 비교
# 결과: data/step3_champions.csv, data/step3_compare.csv

import csv
import random
from itertools import combinations
from pathlib import Path

# ---- 설정 ----
REPEAT = 10_000                      # 가짜 시즌을 몇 번 만들지
LEVEL = 0.95                         # 범위에 담을 비율 (95% 그물)
SEED = 42                            # 난수 시작점. 같으면 매번 같은 결과가 나온다
COMPARE = ["Sona", "Zyra", "Lulu"]   # 서로 비교할 챔피언

HERE = Path(__file__).parent
DATA = HERE / "data"


def load_games():
    """2단계 표를 읽고 다시하기 판은 뺀다."""
    with open(DATA / "my_games.csv", encoding="utf-8") as f:
        return [g for g in csv.DictReader(f) if g["remake"] == "0"]


def middle_range(values):
    """값들을 줄 세우고 양 끝을 잘라 가운데 95%의 처음과 끝을 돌려준다."""
    values = sorted(values)
    cut = int(len(values) * (1 - LEVEL) / 2)   # 한쪽 끝에서 잘라낼 개수 (1만 개면 250개)
    return values[cut], values[len(values) - 1 - cut]


def resample_rate(results, rng):
    """주머니에서 한 판 뽑고 다시 넣기를 판수만큼 해서 가짜 승률 하나를 만든다."""
    fake = rng.choices(results, k=len(results))
    return sum(fake) / len(fake)


def verdict(low, high):
    if low == high:
        return "범위 0: 판단 불가"      # 전승·전패라 다시 뽑아도 똑같이 나옴 (부트스트랩의 약점)
    if low > 0.5:
        return "50% 위"
    if high < 0.5:
        return "50% 아래"
    return "판단 보류"


def champion_table(games):
    """① 챔피언별 판수, 승률, 95% 범위, 판정."""
    rng = random.Random(SEED)
    by_champ = {}
    for g in games:
        by_champ.setdefault(g["champion"], []).append(int(g["win"]))
    by_champ["(전체)"] = [int(g["win"]) for g in games]

    rows = []
    for champ, results in sorted(by_champ.items(), key=lambda kv: -len(kv[1])):
        if champ == "(전체)":
            continue
        rows.append(one_row(champ, results, rng))
    rows.append(one_row("(전체)", by_champ["(전체)"], rng))
    return rows


def one_row(champ, results, rng):
    fakes = [resample_rate(results, rng) for _ in range(REPEAT)]
    low, high = (round(x, 3) for x in middle_range(fakes))
    return {
        "champion": champ,
        "games": len(results),
        "wins": sum(results),
        "win_rate": round(sum(results) / len(results), 3),
        "low": low,
        "high": high,
        "verdict": verdict(low, high),
    }


def compare_table(games):
    """② 두 챔피언의 "승률 차이"를 부트스트랩해서, 차이의 범위가 0을 포함하는지 본다."""
    rng = random.Random(SEED)
    results = {c: [int(g["win"]) for g in games if g["champion"] == c] for c in COMPARE}
    rows = []
    for a, b in combinations(COMPARE, 2):
        diffs = [resample_rate(results[a], rng) - resample_rate(results[b], rng)
                 for _ in range(REPEAT)]
        low, high = middle_range(diffs)
        diff = sum(results[a]) / len(results[a]) - sum(results[b]) / len(results[b])
        rows.append({
            "pair": f"{a} - {b}",
            "diff": round(diff, 3),
            "low": round(low, 3),
            "high": round(high, 3),
            "verdict": "차이 있음" if low > 0 or high < 0 else "판단 보류",
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
    print(f"다시하기 뺀 {len(games)}판으로 분석합니다. (가짜 시즌 {REPEAT}번, {LEVEL:.0%} 범위)\n")

    champs = champion_table(games)
    save(champs, "step3_champions.csv")
    print("① 챔피언별 승률과 범위")
    print(f"{'챔피언':<14}{'판수':>4}  {'승률':>6}   {'범위':^15}  판정")
    for r in champs:
        print(f"{r['champion']:<14}{r['games']:>4}  {pct(r['win_rate'])}   "
              f"{pct(r['low'])} ~ {pct(r['high'])}  {r['verdict']}")

    pairs = compare_table(games)
    save(pairs, "step3_compare.csv")
    print("\n② 챔피언 비교 (앞 챔피언 승률 - 뒤 챔피언 승률)")
    for r in pairs:
        print(f"{r['pair']:<14}차이 {pct(r['diff'])}   범위 {pct(r['low'])} ~ {pct(r['high'])}  {r['verdict']}")

    print("\n저장: data/step3_champions.csv, data/step3_compare.csv")


if __name__ == "__main__":
    main()
