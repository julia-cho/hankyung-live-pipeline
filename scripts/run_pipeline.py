import os, subprocess, datetime, pathlib, textwrap
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()                           # .env 값 로드

CHANNEL_ID = "UCAVdqlngIAxHtwlCA2hjv3A"
YT_URL     = f"https://www.youtube.com/channel/{CHANNEL_ID}/streams"
DATE   = datetime.datetime.now().strftime("%Y%m%d")

WORKDIR = pathlib.Path("work")
WORKDIR.mkdir(exist_ok=True)
mp3   = WORKDIR / f"{DATE}.mp3"
txt   = WORKDIR / f"{DATE}.txt"

def cmd(*args): subprocess.check_call(list(args))

def download():
    if mp3.exists():
        return True

    cmd(
        "yt-dlp",
        "--dateafter", "now-2day",        # 이틀 이내 (VOD 업로드 지연 여유)
        "--playlist-end", "1",            # 최신 1편만
        "--match-filter", "duration > 600",
        "--extract-audio", "--audio-format", "mp3",
        "-o", str(mp3),
        YT_URL
    )
    return True

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
