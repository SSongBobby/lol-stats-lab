# 1단계: Riot ID로 내 계정 고유 ID(PUUID)를 조회해 파일로 저장한다.
# 실행: python step1_get_puuid.py
# 외부 라이브러리 없이 Python 기본 기능만 사용한다.

import json
import urllib.parse
import urllib.request
import urllib.error
from getpass import getpass
from pathlib import Path

GAME_NAME = "우주대냥이"
TAG_LINE = "KR1"

api_key = getpass("API 키를 붙여넣고 Enter (화면에 안 보이는 게 정상): ").strip()

url = (
    "https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
    + urllib.parse.quote(GAME_NAME) + "/" + urllib.parse.quote(TAG_LINE)
)
req = urllib.request.Request(url, headers={
    "X-Riot-Token": api_key,
    "User-Agent": "lol-stats-lab/1.0",  # 기본값(Python-urllib)은 Riot 앞단 Cloudflare가 차단함
})

try:
    with urllib.request.urlopen(req) as resp:
        account = json.load(resp)
except urllib.error.HTTPError as e:
    print("실패! 상태 코드:", e.code)
    print("401/403 = 키가 틀렸거나 만료됨, 404 = Riot ID 오타")
    raise SystemExit(1)

# 어느 폴더에서 실행하든 이 파일 옆(01-luck-or-skill)에 저장한다.
with open(Path(__file__).parent / "my_account.json", "w", encoding="utf-8") as f:
    json.dump(account, f, ensure_ascii=False, indent=2)

print("성공!", account["gameName"] + "#" + account["tagLine"])
print("PUUID 길이:", len(account["puuid"]))
print("my_account.json 파일에 저장했습니다.")
