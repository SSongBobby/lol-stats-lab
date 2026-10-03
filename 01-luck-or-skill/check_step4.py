# 4단계 완료 기준 검사. step4_pvalue.py를 실행한 뒤 돌린다.
# 실행: python check_step4.py
# 모든 줄이 PASS면 4단계 완료.

import csv
from math import comb
from pathlib import Path

import step4_pvalue as s4

HERE = Path(__file__).parent
DATA = HERE / "data"

results = []


def check(name, ok):
    results.append(ok)
    print(("PASS" if ok else "FAIL"), name)


def read(name):
    with open(DATA / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def exact_p(wins, n):
    """정답 p-value: 50% 동전 n번에서 나올 수 있는 모든 경우를 직접 세서 구한다 (양쪽)."""
    gap = abs(wins - n / 2)
    hits = sum(comb(n, k) for k in range(n + 1) if abs(k - n / 2) >= gap)
    return hits / 2 ** n


# 정답을 아는 작은 예: 10판 10승이면 정답 p는 2/1024 = 약 0.002
rng = s4.random.Random(s4.SEED)
check("작은 예: 10판 10승의 p가 정답(약 0.002)과 0.002 이내",
      abs(s4.p_vs_half([1] * 10, rng) - exact_p(10, 10)) <= 0.002)

champ_file = DATA / "step4_champions.csv"
pair_file = DATA / "step4_compare.csv"
check("data/step4_champions.csv 있음", champ_file.exists())
check("data/step4_compare.csv 있음", pair_file.exists())

if champ_file.exists() and pair_file.exists():
    champs = read("step4_champions.csv")
    pairs = read("step4_compare.csv")
    games = [g for g in read("my_games.csv") if g["remake"] == "0"]
    each = [c for c in champs if c["champion"] != "(전체)"]

    counts = {}
    for g in games:
        counts[g["champion"]] = counts.get(g["champion"], 0) + 1
    expected = {c for c, n in counts.items() if n >= s4.MIN_GAMES}

    check(f"챔피언 목록 = {s4.MIN_GAMES}판 이상인 챔피언 전부",
          {c["champion"] for c in each} == expected)
    check("(전체) 줄의 판수 = 다시하기 뺀 게임 수",
          [int(c["games"]) for c in champs if c["champion"] == "(전체)"] == [len(games)])
    check("모든 p-value가 0~1 사이",
          all(0 <= float(r["p_value"]) <= 1 for r in champs + pairs))
    check("문턱: 챔피언별 = 0.05 / 챔피언 수",
          all(abs(float(c["threshold"]) - s4.ALPHA / len(each)) < 1e-9 for c in each))
    check("문턱: (전체) = 0.05",
          all(float(c["threshold"]) == s4.ALPHA for c in champs if c["champion"] == "(전체)"))
    check("문턱: 비교 = 0.05 / 3, 비교 3쌍 있음",
          len(pairs) == 3 and all(abs(float(p["threshold"]) - s4.ALPHA / 3) < 1e-9 for p in pairs))
    check("모든 판정이 p와 문턱에 맞음",
          all(r["verdict"] == s4.verdict(float(r["p_value"]), float(r["threshold"]))
              for r in champs + pairs))
    check("흉내 낸 p가 정답 p와 0.01 이내 (모든 챔피언과 전체)",
          all(abs(float(c["p_value"]) - exact_p(int(c["wins"]), int(c["games"]))) <= 0.01
              for c in champs))

    # 같은 설정으로 다시 계산하면 똑같이 나오는지
    again = s4.champion_table(games)
    check("다시 계산해도 결과가 똑같음 (시드 고정)",
          [(r["champion"], str(r["p_value"])) for r in again]
          == [(c["champion"], c["p_value"]) for c in champs])

print()
print("결과:", "전부 통과" if all(results) else "실패 있음")
