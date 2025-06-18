import os, subprocess, datetime, pathlib, textwrap
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()                           # .env 값 로드

PLAYLIST_ID = "PLVups02-DZEWWyOMyk4jjGaWJ_0o1N1iO"     # ← 방금 복사한 ID
YT_URL      = f"https://www.youtube.com/playlist?list={PLAYLIST_ID}"
DATE   = datetime.datetime.now().strftime("%Y%m%d")

WORKDIR = pathlib.Path("work")
WORKDIR.mkdir(exist_ok=True)
mp3   = WORKDIR / f"{DATE}.mp3"
txt   = WORKDIR / f"{DATE}.txt"

def cmd(*args): subprocess.check_call(list(args))

def download() -> bool:
    """
    플레이리스트에서
      · 길이 5분↑
      · 전체 공개
    조건을 만족하는 **가장 최근 VOD 1편**만 mp3로 내려받는다.
    조건에 맞는 영상이 없으면 False 반환.
    """
    if mp3.exists():
        return True

    try:
        cmd(
            "yt-dlp",
            "-i",                               # ❶ 에러(멤버십·비공개) 무시하고 다음으로
            "--playlist-end", "10",             #   최근 10편까지만 검사
            "--max-downloads", "1",             # ❷ 첫 성공 1편 받으면 즉시 종료
            "--match-filter",
            (
              "duration > 300 "
              " & availability = 'public'"
            ),
            "--extract-audio", "--audio-format", "mp3",
            "-o", str(mp3),
            YT_URL,
        )
    except subprocess.CalledProcessError as e:
        print("⚠️ yt-dlp 실패:", e)
        return False

    # 성공했는데 mp3가 없으면(= 조건 만족하는 영상 없음) False
    return mp3.exists()

def stt():
    if txt.exists(): return
    cmd("whispercpp", str(mp3), "--model", "small-int8",
        "--language", "ko", "--output-txt")
    mp3.with_suffix(".txt").rename(txt)

def summarize() -> str:
    import re, itertools, collections
    content = txt.read_text(encoding="utf-8")
    # 1) 문장 단위 자르기
    import pysbd; seg=pysbd.Segmenter(lang="ko",clean=False)
    sents = seg.segment(content)[:12]          # 처음 12문장만
    # 2) 숫자 포함 문장 우선 추출
    nums  = [s for s in sents if re.search(r"\d", s)]
    top   = nums[:5] if nums else sents[:5]
    return " ".join(top)

def push_notion(summary):
    client = Client(auth=os.getenv("NOTION_TOKEN"))
    db_id  = os.getenv("NOTION_DB_ID")
    client.pages.create(
        parent={"database_id": db_id},
        properties={
            "Name": {"title":[{"text":{"content":f"{DATE} 한경 LIVE"}}]},
            "Date": {"date":{"start":DATE}}
        },
        children=[{
            "object":"block","type":"paragraph",
            "paragraph":{"rich_text":[{"type":"text",
            "text":{"content":summary}}]}
        }]
    )

if __name__ == "__main__":
    download()
    stt()
    summary = summarize()
    push_notion(summary)
    print("✅ ALL DONE")
