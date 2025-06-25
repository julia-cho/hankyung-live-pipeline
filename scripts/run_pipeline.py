from pathlib import Path
import subprocess
import whisper
import datetime

# 오늘 날짜 mp3 경로 지정
today = datetime.datetime.now().strftime('%Y%m%d')
mp3 = Path(f"work/{today}.mp3")
text = Path(f"work/{today}.txt")

def download():
    try:
        url = "https://www.youtube.com/playlist?list=PLVups02-DZEWwYOMyK4jjGaWJ_0o1N1i0"
        command = [
            "yt-dlp",
            "-i",  # 오류 무시하고 진행
            "--playlist-end", "10",  # 최신 10개만 검사
            "--max-downloads", "1",  # 1개만 받음
            "--match-filter", "duration > 300 & availability = 'public'",  # 5분 넘는 공개 영상만
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", str(mp3),
            url
        ]
        subprocess.check_call(command)
        return mp3.exists()
    except subprocess.CalledProcessError:
        return False

def stt():
    print("🎙 Whisper로 STT 시작")
    model = whisper.load_model("small")  # small-fast 추천
    result = model.transcribe(str(mp3))
    text.write_text(result["text"])
    print("📝 텍스트 추출 완료")

def summarize():
    print("📄 요약하는 기능은 여기에 작성!")
    return text.read_text()[:300] + "..."  # 예시 요약

def push_notion(summary):
    print("🔗 노션에 업로드하는 코드가 여기에 들어감")
    print(summary)

if __name__ == "__main__":
    if download():
        stt()
        summary = summarize()
        push_notion(summary)
        print("✅ 파이프라인 완료")
    else:
        print("📭 오늘은 전체공개 5분 이상 VOD가 없어 건너뜁니다!")
