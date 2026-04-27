import sys
import os

sys.path.append(os.getcwd())

from app.services.ai_spam_classifier import classify_posts_ai
import json

def test_spam_classification():
    posts = [
        {"title": "안녕하세요, 갑상선 수술 비용 문의드립니다.", "content": "메일로 견적 부탁드려요."},
        {"title": "비아그라 시알리스 파격 세일! 클릭하세요", "content": "최저가 보장 100% 정품"},
        {"title": "[광고] 무직자 대출 당일 승인 가능합니다", "content": "지금 바로 전화주세요 010-1234-5678"},
        {"title": "어제 진료 받았던 환자입니다. 약 복용법 질문있어요.", "content": "식후 30분인가요?"},
    ]
    
    keywords = ["대출", "도박"]
    
    print("Testing Spam Classification (Keyword Fallback)...")
    # We don't set GEMINI_API_KEY so it should fallback to keywords
    results = classify_posts_ai(posts, keywords)
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_spam_classification()
