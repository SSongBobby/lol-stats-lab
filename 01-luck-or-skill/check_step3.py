# 3단계 완료 기준 검사. step3_bootstrap.py를 실행한 뒤 돌린다.
# 실행: python check_step3.py
# 모든 줄이 PASS면 3단계 완료.

import csv
from pathlib import Path

import step3_bootstrap as s3

HERE = Path(__file__).parent
DATA = HERE / "data"

results = []


def check(name, ok):
    results.append(ok)
    print(("PASS" if ok else "FAIL"), name)


def read(name):
    with open(DATA / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


champ_file = DATA / "step3_champions.csv"
pair_file = DATA / "step3_compare.csv"
check("data/step3_champions.csv 있음", champ_file.exists())
check("data/step3_compare.csv 있음", pair_file.exists())

if champ_file.exists() and pair_file.exists():
    champs = read("step3_champions.csv")
    pairs = read("step3_compare.csv")
    games = [g for g in read("my_games.csv") if g["remake"] == "0"]

    check("챔피언 판수 합계 = 다시하기 뺀 게임 수",
          sum(int(c["games"]) for c in champs if c["champion"] != "(전체)") == len(games))
    check("(전체) 줄의 판수 = 다시하기 뺀 게임 수",
          [int(c["games"]) for c in champs if c["champion"] == "(전체)"] == [len(games)])
    check("모든 챔피언: 범위 아래 <= 승률 <= 범위 위",
          all(float(c["low"]) <= float(c["win_rate"]) <= float(c["high"]) for c in champs))
    check("모든 챔피언: 판정이 범위와 일치",
          all(c["verdict"] == s3.verdict(float(c["low"]), float(c["high"])) for c in champs))
    check("비교 3쌍 있음", len(pairs) == 3)
    check("모든 비교: 범위 아래 <= 차이 <= 범위 위",
          all(float(p["low"]) <= float(p["diff"]) <= float(p["high"]) for p in pairs))

    # 같은 설정으로 다시 계산하면 똑같이 나오는지
    again = s3.champion_table(games)
    check("다시 계산해도 결과가 똑같음 (시드 고정)",
          [(r["champion"], str(r["low"]), str(r["high"])) for r in again]
          == [(c["champion"], c["low"], c["high"]) for c in champs])

print()
print("결과:", "전부 통과" if all(results) else "실패 있음")
