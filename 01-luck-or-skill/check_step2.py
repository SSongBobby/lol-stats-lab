# 2단계 완료 기준 검사. 수집이 끝난 뒤 실행한다.
# 실행: python check_step2.py
# 모든 줄이 PASS면 2단계 완료.

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"

results = []


def check(name, ok):
    results.append(ok)
    print(("PASS" if ok else "FAIL"), name)


ids_file = DATA / "match_ids.json"
csv_file = DATA / "my_games.csv"

check("data/match_ids.json 있음", ids_file.exists())
check("data/my_games.csv 있음", csv_file.exists())

if ids_file.exists() and csv_file.exists():
    ids = json.loads(ids_file.read_text(encoding="utf-8"))
    with open(csv_file, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    check("게임 ID 중복 없음", len(ids) == len(set(ids)))
    check("표의 게임 수 = 게임 ID 수", len(rows) == len(ids))
    check("표에 같은 게임 두 번 없음",
          len({r["match_id"] for r in rows}) == len(rows))
    check("모든 행에 챔피언 이름 있음", all(r["champion"] for r in rows))
    check("모든 행의 승패가 1 또는 0", all(r["win"] in ("1", "0") for r in rows))
    check("모든 게임이 솔로 랭크(420)", all(r["queue_id"] == "420" for r in rows))

    saved = {p.stem for p in (DATA / "matches").glob("*.json")}
    check("모든 게임의 원본 파일 있음", set(ids) <= saved)

    print()
    print("게임 수:", len(rows), "/ 다시하기(remake):",
          sum(r["remake"] == "1" for r in rows))

print()
print("결과:", "전부 통과" if all(results) else "실패 있음")
