"""공공데이터포털 API 키가 제대로 잡혔는지 확인하는 스크립트.

키 값 자체는 화면에 출력하지 않고, 앞 4글자와 길이만 보여줍니다.
실행: .venv/bin/python check_api_key.py
"""
import os

from dotenv import load_dotenv

# .env 파일이 있으면 읽어서 환경변수로 올립니다.
# override=False: 터미널에서 이미 지정한 환경변수가 있으면 그것을 우선합니다.
load_dotenv(override=False)

key = os.getenv("DATA_GO_KR_API_KEY", "").strip()

if not key or key.startswith("여기에"):
    print("❌ DATA_GO_KR_API_KEY 가 비어 있어요. .env 파일이나 환경변수에 키를 넣어주세요.")
elif any("가" <= ch <= "힣" for ch in key) or len(key) < 30:
    print(f"❌ 예시 문구 같아요: {key[:4]}**** (길이 {len(key)}자)")
    print("   실제 키는 영문·숫자로 된 긴 문자열이에요. data.go.kr 마이페이지에서 복사해 넣어주세요.")
else:
    print(f"✅ 키를 찾았어요: {key[:4]}**** (길이 {len(key)}자)")
    if "%" in key:
        print("⚠️  '%'가 들어 있어요. Encoding 키 같아요. requests로 호출할 땐 Decoding 키를 쓰세요.")
