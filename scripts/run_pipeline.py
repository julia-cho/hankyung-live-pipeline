from pathlib import Path
import subprocess
import datetime
import os
import sys

def download():
    """YouTube에서 오디오 다운로드"""
    try:
        # work 디렉토리 생성
        work_dir = Path("work")
        work_dir.mkdir(exist_ok=True)
        
        # 오늘 날짜 파일명
        today = datetime.datetime.now().strftime('%Y%m%d')
        
        url = "https://www.youtube.com/playlist?list=PLVups02-DZEWwYOMyK4jjGaWJ_0o1N1i0"
        command = [
            "yt-dlp",
            "-i",  # 오류 무시하고 진행
            "--playlist-end", "10",  # 최신 10개만 검사
            "--max-downloads", "1",  # 1개만 받음
            "--match-filter", "duration > 300 & availability = 'public'",  # 5분 넘는 공개 영상만
            "--extract-audio",
            "--audio-format", "mp3",
            "-o", f"work/{today}.%(ext)s",  # 확장자 자동 처리
            url
        ]
        
        print("📥 YouTube에서 다운로드 시작...")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ yt-dlp 오류: {result.stderr}")
            return None, None
            
        # 실제 생성된 파일 찾기
        mp3_file = work_dir / f"{today}.mp3"
        if mp3_file.exists():
            print(f"✅ 다운로드 완료: {mp3_file}")
            return mp3_file, work_dir / f"{today}.txt"
        else:
            print("📭 조건에 맞는 영상이 없습니다.")
            return None, None
            
    except FileNotFoundError:
        print("❌ yt-dlp가 설치되지 않았습니다. 설치해주세요:")
        print("pip install yt-dlp")
        return None, None
    except Exception as e:
        print(f"❌ 다운로드 중 오류: {e}")
        return None, None

def stt(mp3_path, text_path):
    """Whisper로 음성을 텍스트로 변환"""
    try:
        import whisper
    except ImportError:
        print("❌ whisper가 설치되지 않았습니다. 설치해주세요:")
        print("pip install openai-whisper")
        return False
        
    try:
        print("🎙 Whisper로 STT 시작...")
        model = whisper.load_model("small")  # small 모델 사용
        result = model.transcribe(str(mp3_path))
        
        # 텍스트 저장
        text_path.write_text(result["text"], encoding='utf-8')
        print("📝 텍스트 추출 완료")
        return True
        
    except Exception as e:
        print(f"❌ STT 중 오류: {e}")
        return False

def summarize(text_path):
    """텍스트 요약 (현재는 간단한 예시)"""
    try:
        if not text_path.exists():
            return "텍스트 파일이 없습니다."
            
        text = text_path.read_text(encoding='utf-8')
        print("📄 요약 생성 중...")
        
        # 간단한 요약 (실제로는 AI API 사용 권장)
        lines = text.split('\n')
        summary_lines = [line.strip() for line in lines if line.strip()][:5]
        summary = '\n'.join(summary_lines)
        
        return summary if summary else text[:300] + "..."
        
    except Exception as e:
        print(f"❌ 요약 중 오류: {e}")
        return "요약 생성에 실패했습니다."

def push_notion(summary):
    """노션에 업로드 (현재는 출력만)"""
    print("🔗 노션 업로드 준비됨")
    print("=" * 50)
    print(summary)
    print("=" * 50)
    
    # 실제 노션 API 연동 시 여기에 구현
    # notion_client.pages.create(...) 등

def main():
    """메인 파이프라인 실행"""
    print("🚀 뉴스 파이프라인 시작")
    
    # 1. 다운로드
    mp3_path, text_path = download()
    if not mp3_path:
        print("📭 오늘은 처리할 영상이 없습니다.")
        return
    
    # 2. STT
    if not stt(mp3_path, text_path):
        print("❌ STT 실패")
        return
    
    # 3. 요약
    summary = summarize(text_path)
    
    # 4. 노션 업로드
    push_notion(summary)
    
    print("✅ 파이프라인 완료!")

if __name__ == "__main__":
    main()
