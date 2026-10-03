# 2단계: 2026 시즌 솔로 랭크 게임을 전부 받아서 저장하고, 내 기록만 뽑아 표로 만든다.
# 실행: python step2_collect_matches.py
# 다시 실행해도 이미 받은 게임은 건너뛴다 (중간에 끊겨도 이어서 받음).

import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path

# ---- 설정 ----
SEASON_START = "2026-01-08"  # 2026 랭크 시즌 시작일 (한국 시간 0시 기준)
QUEUE_SOLO_RANK = 420       # Riot이 정한 솔로 랭크 번호
WAIT_SECONDS = 1.3          # 개발 키 제한(2분에 100번)을 넘지 않게 요청 사이에 쉬는 시간

HERE = Path(__file__).parent
DATA = HERE / "data"
MATCH_DIR = DATA / "matches"
API = "https://asia.api.riotgames.com"


def season_start_epoch():
    # 한국 시간 0시 = 전날 UTC 15시
    day = datetime.strptime(SEASON_START, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(day.timestamp()) - 9 * 3600


def load_api_key():
    """레포 맨 위 riot.key 파일에서 키를 읽는다. 파일이 없거나 비어 있으면 직접 묻는다.
    riot.key는 .gitignore의 *.key 규칙 때문에 GitHub에 올라가지 않는다."""
    key_file = HERE.parent / "riot.key"
    if key_file.exists():
        key = key_file.read_text(encoding="utf-8").strip()
        if key.startswith("RGAPI-"):
            return key
        print("riot.key 내용이 RGAPI-로 시작하지 않아서 직접 입력받습니다.")
    return getpass("API 키를 붙여넣고 Enter (화면에 안 보이는 게 정상): ").strip()


def get_json(path, api_key):
    """Riot 서버에 요청을 보내고 답을 받아온다. 너무 자주 물어서 거절(429)되면 기다렸다 다시 한다."""
    req = urllib.request.Request(
        API + path,
        headers={"X-Riot-Token": api_key, "User-Agent": "lol-stats-lab/1.0"},
    )
    while True:
        try:
            with urllib.request.urlopen(req) as resp:
                time.sleep(WAIT_SECONDS)
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = int(e.headers.get("Retry-After", "10"))
                print(f"  요청이 너무 많아 {wait}초 기다립니다...")
                time.sleep(wait)
                continue
            print("실패! 상태 코드:", e.code, "/ 요청:", path.split("?")[0])
            print("401/403 = 키가 틀렸거나 만료됨")
            raise SystemExit(1)


def fetch_match_ids(puuid, api_key):
    """시즌 시작 이후 솔로 랭크 게임 ID를 100개씩 끝까지 받아온다."""
    ids = []
    start = 0
    while True:
        query = urllib.parse.urlencode({
            "queue": QUEUE_SOLO_RANK,
            "startTime": season_start_epoch(),
            "start": start,
            "count": 100,
        })
        page = get_json(f"/lol/match/v5/matches/by-puuid/{puuid}/ids?{query}", api_key)
        ids += page
        print(f"  게임 ID {len(ids)}개 받음")
        if len(page) < 100:
            return ids
        start += 100


def my_row(match, puuid):
    """게임 원본에서 내 줄만 뽑아 표 한 줄로 만든다."""
    info = match["info"]
    me = next(p for p in info["participants"] if p["puuid"] == puuid)
    return {
        "match_id": match["metadata"]["matchId"],
        "date": datetime.fromtimestamp(info["gameStartTimestamp"] / 1000).strftime("%Y-%m-%d"),
        "queue_id": info["queueId"],
        "patch": ".".join(info["gameVersion"].split(".")[:2]),
        "champion": me["championName"],
        "win": int(me["win"]),
        "remake": int(me.get("gameEndedInEarlySurrender", False)),
        "minutes": round(info["gameDuration"] / 60, 1),
    }


def build_table(ids, puuid):
    rows = []
    for match_id in ids:
        match = json.loads((MATCH_DIR / f"{match_id}.json").read_text(encoding="utf-8"))
        rows.append(my_row(match, puuid))
    with open(DATA / "my_games.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else ["match_id"])
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main():
    account = json.loads((HERE / "my_account.json").read_text(encoding="utf-8"))
    puuid = account["puuid"]
    api_key = load_api_key()

    MATCH_DIR.mkdir(parents=True, exist_ok=True)

    print("1) 게임 ID 목록 받는 중")
    ids = fetch_match_ids(puuid, api_key)
    (DATA / "match_ids.json").write_text(json.dumps(ids, indent=2), encoding="utf-8")

    todo = [m for m in ids if not (MATCH_DIR / f"{m}.json").exists()]
    print(f"2) 게임 상세 받는 중: 새로 {len(todo)}개 (이미 있는 {len(ids) - len(todo)}개는 건너뜀)")
    for i, match_id in enumerate(todo, 1):
        match = get_json(f"/lol/match/v5/matches/{match_id}", api_key)
        (MATCH_DIR / f"{match_id}.json").write_text(json.dumps(match), encoding="utf-8")
        if i % 10 == 0 or i == len(todo):
            print(f"  {i}/{len(todo)}")

    print("3) 내 기록만 뽑아 표 만드는 중")
    rows = build_table(ids, puuid)
    print(f"완료! 게임 {len(rows)}판 → data/my_games.csv")


if __name__ == "__main__":
    main()
