"""
✏️ 챗봇 로직 구현 파일 (학생이 직접 작성)

이 파일은 학생이 처음부터 직접 구현해야 합니다.
아래는 기본 구조와 가이드만 제공됩니다.

📝 구현해야 할 기능:
  1. OpenAI API 연동
  2. ChromaDB를 이용한 임베딩 저장/검색 (RAG)
  3. LangChain을 이용한 대화 메모리 관리
  4. 프롬프트 엔지니어링
  5. 한국어 키워드 추출 (KoNLPy)
  6. 응답 생성 로직

💡 참고:
  - ASSIGNMENT_GUIDE.md에 상세한 구현 가이드 있음
  - 필요한 라이브러리는 requirements.txt에 이미 포함됨
  - OpenAI API 키는 .env 파일에서 로드
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# 프로젝트 루트 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

# 환경변수 로드
load_dotenv(dotenv_path=BASE_DIR / ".env")

# ============================================================================
# TODO 1: 필요한 라이브러리 임포트
# ============================================================================
# 힌트:
# - OpenAI API: from openai import OpenAI
# - ChromaDB: import chromadb
# - LangChain: from langchain_community.chat_models import ChatOpenAI
#             from langchain.memory import ConversationSummaryBufferMemory
#             from langchain.chains import LLMChain
#             from langchain.prompts import PromptTemplate
# - KoNLPy: from konlpy.tag import Okt
# - 기타: uuid, warnings 등

# 여기에 임포트 작성


# ============================================================================
# TODO 2: 설정 파일 로드
# ============================================================================
# config/chatbot_config.json 파일을 읽어서 챗봇 설정 로드
# 힌트: json.load() 사용

CONFIG_PATH = BASE_DIR / 'config' / 'chatbot_config.json'

# 여기에 설정 로드 코드 작성
config = {}


# ============================================================================
# TODO 3: OpenAI API 키 설정
# ============================================================================
# .env 파일에서 OPENAI_API_KEY를 읽어서 OpenAI 클라이언트 초기화
# 힌트: os.getenv("OPENAI_API_KEY")

api_key = None  # 여기에 API 키 로드
# client = OpenAI(api_key=api_key)


# ============================================================================
# TODO 4: ChromaDB 초기화 함수 구현
# ============================================================================
# 텍스트 임베딩을 저장할 ChromaDB 초기화
# 
# 힌트:
# 1. chromadb.PersistentClient()로 클라이언트 생성
# 2. get_or_create_collection()로 컬렉션 생성
# 3. 경로: BASE_DIR / "static" / "data" / "chatbot" / "chardb_embedding"

def init_text_db():
    """
    텍스트 임베딩 데이터베이스 초기화
    
    Returns:
        tuple: (dbclient, collection)
    
    구현 단계:
    1. 저장 경로 설정 (static/data/chatbot/chardb_embedding)
    2. 디렉토리가 없으면 생성
    3. PersistentClient 생성
    4. 컬렉션 생성 (이름: "rag_collection")
    5. (dbclient, collection) 반환
    """
    # 여기에 구현
    pass


# 전역 변수로 DB 초기화 (앱 시작 시 한 번만)
# text_dbclient, collection = init_text_db()


# ============================================================================
# TODO 5: 임베딩 생성 함수 구현
# ============================================================================
# OpenAI API를 사용하여 텍스트를 벡터로 변환
#
# 힌트:
# client.embeddings.create(input=[text], model="text-embedding-3-large")

def get_embedding(text, model="text-embedding-3-large"):
    """
    텍스트를 임베딩 벡터로 변환
    
    Args:
        text (str): 변환할 텍스트
        model (str): 사용할 임베딩 모델
    
    Returns:
        list: 임베딩 벡터
    
    구현 단계:
    1. OpenAI API의 embeddings.create() 호출
    2. response.data[0].embedding 반환
    """
    # 여기에 구현
    pass


# ============================================================================
# TODO 6: 한국어 키워드 추출 함수 구현 (선택)
# ============================================================================
# KoNLPy를 사용하여 명사 추출 (RAG 검색 정확도 향상)
#
# 힌트:
# - Okt().nouns(text)로 명사 추출
# - 불용어 제거 (예: "것", "수", "등")
# - 2글자 이상만 선택

# okt = Okt()

def extract_nouns_korean(text):
    """
    한국어 텍스트에서 명사 키워드 추출
    
    Args:
        text (str): 입력 텍스트
    
    Returns:
        list: 추출된 명사 리스트
    
    구현 단계:
    1. Okt().nouns()로 명사 추출
    2. 불용어 필터링
    3. 2글자 이상만 선택
    """
    # 여기에 구현 (선택 사항)
    return []


# ============================================================================
# TODO 7: RAG 문서 검색 함수 구현
# ============================================================================
# ChromaDB에서 유사한 문서를 검색하는 핵심 RAG 로직
#
# 힌트:
# 1. 쿼리 텍스트의 임베딩 생성
# 2. collection.query()로 유사 문서 검색
# 3. 유사도 계산: similarity = 1 / (1 + distance)
# 4. threshold 이상인 문서만 반환

def search_similar_documents(query, collection, threshold=0.45, top_k=5):
    """
    유사 문서 검색 (RAG의 핵심)
    
    Args:
        query (str): 검색 질의
        collection: ChromaDB 컬렉션
        threshold (float): 유사도 임계값 (0.3~0.5 권장)
        top_k (int): 검색할 문서 개수
    
    Returns:
        tuple: (best_document, similarity, metadata) 또는 (None, None, None)
    
    구현 단계:
    1. 쿼리의 임베딩 생성
    2. collection.query()로 검색
    3. 거리를 유사도로 변환: 1 / (1 + distance)
    4. threshold 이상인 문서 필터링
    5. 가장 유사한 문서 반환
    
    💡 팁:
    - extract_nouns_korean()을 사용하면 검색 정확도 향상
    - 로그를 출력하면 디버깅에 도움됨
    """
    try:
        # 여기에 구현
        
        # 1. 임베딩 생성
        # query_embedding = get_embedding(query)
        
        # 2. 검색
        # results = collection.query(
        #     query_embeddings=[query_embedding],
        #     n_results=top_k,
        #     include=["documents", "distances", "metadatas"]
        # )
        
        # 3. 유사도 계산 및 필터링
        # for doc, dist, meta in zip(documents, distances, metadatas):
        #     similarity = 1 / (1 + dist)
        #     if similarity >= threshold:
        #         ...
        
        # 4. 최고 유사도 문서 반환
        
        pass
    except Exception as e:
        print(f"[RAG] 검색 오류: {e}")
        return None, None, None


# ============================================================================
# TODO 8: LangChain 메모리 및 대화 체인 초기화
# ============================================================================
# LangChain을 사용한 대화 메모리 관리
#
# 힌트:
# 1. ChatOpenAI로 LLM 초기화 (model="gpt-4o-mini", temperature=0.7)
# 2. ConversationSummaryBufferMemory로 메모리 생성
# 3. PromptTemplate으로 프롬프트 정의
# 4. LLMChain으로 대화 체인 생성

# 여기에 LangChain 설정 코드 작성
# langchain_llm = ChatOpenAI(...)
# memory = ConversationSummaryBufferMemory(...)
# prompt = PromptTemplate(...)
# conversation_chain = LLMChain(...)


# ============================================================================
# TODO 9: 시스템 프롬프트 생성 함수 구현
# ============================================================================
# config 파일의 설정을 바탕으로 시스템 프롬프트 구성

def build_system_prompt(username, has_context=False):
    """
    시스템 프롬프트 생성
    
    Args:
        username (str): 사용자 이름
        has_context (bool): RAG 컨텍스트 사용 여부
    
    Returns:
        str: 완성된 시스템 프롬프트
    
    구현 단계:
    1. config에서 system_prompt 가져오기
    2. 캐릭터 정보 추가
    3. 대화 규칙 추가
    4. RAG 컨텍스트 사용 여부에 따른 지시사항 추가
    
    예시:
    ```
    당신은 {캐릭터 이름}입니다.
    
    캐릭터 정보:
    - 나이: 20세
    - 대학: 서강대학교
    - 전공: 컴퓨터공학
    
    대화 규칙:
    - 반말을 사용하세요
    - 친근하게 대화하세요
    
    {RAG 컨텍스트 사용 시: 제공된 정보를 활용하여 답변하세요}
    
    [사용자 이름: {username}]
    ```
    """
    # 여기에 구현
    pass


# ============================================================================
# TODO 10: 응답 생성 함수 구현 (핵심!)
# ============================================================================
# 사용자 메시지를 받아서 챗봇 응답을 생성하는 메인 함수

def generate_response(user_message, username="사용자"):
    """
    사용자 메시지에 대한 챗봇 응답 생성
    
    Args:
        user_message (str): 사용자 입력
        username (str): 사용자 이름
    
    Returns:
        dict: {'reply': str, 'image': str or None}
    
    구현 단계:
    
    1. 초기 메시지 처리
       - user_message == "init"이면 인사말 반환
       - config에서 챗봇 이름 가져오기
       - 메모리에 저장
    
    2. RAG 검색
       - search_similar_documents()로 관련 문서 검색
       - 찾으면 has_context=True
    
    3. 시스템 프롬프트 생성
       - build_system_prompt() 호출
       - RAG 컨텍스트 포함 여부 결정
    
    4. LLM 응답 생성
       - conversation_chain.predict() 호출
       - RAG 문서가 있으면 프롬프트에 포함
    
    5. 메모리 저장
       - memory.save_context()로 대화 저장
    
    6. 응답 반환
       - {'reply': 응답텍스트, 'image': None}
    
    💡 팁:
    - 로그를 출력하면 디버깅에 큰 도움됨
    - RAG 컨텍스트를 프롬프트에 명확히 표시
    - 에러 처리 필수
    
    예시 프롬프트 구조:
    ```
    시스템 프롬프트: {build_system_prompt()}
    
    [참고 정보] (RAG 컨텍스트가 있을 때만)
    {검색된 문서 내용}
    
    대화 기록: {memory}
    
    사용자: {user_message}
    
    챗봇:
    ```
    """
    
    print(f"\n{'='*50}")
    print(f"[USER] {username}: {user_message}")
    
    # 여기에 전체 로직 구현
    
    try:
        # 1. 초기 메시지 처리
        if user_message.strip().lower() == "init":
            # 초기 인사말 생성 및 반환
            pass
        
        # 2. RAG 검색
        # context, similarity, metadata = search_similar_documents(...)
        
        # 3. 시스템 프롬프트 생성
        # system_prompt = build_system_prompt(...)
        
        # 4. LLM 응답 생성
        # reply = conversation_chain.predict(...)
        
        # 5. 메모리 저장
        # memory.save_context(...)
        
        # 6. 응답 반환
        return {
            "reply": "구현 필요: generate_response() 함수를 완성하세요",
            "image": None
        }
        
    except Exception as e:
        print(f"[ERROR] 응답 생성 오류: {e}")
        return {
            "reply": "죄송합니다. 오류가 발생했습니다.",
            "image": None
        }


# ============================================================================
# 테스트 코드 (선택)
# ============================================================================
if __name__ == "__main__":
    """
    이 파일을 직접 실행하여 테스트 가능
    
    사용법:
    docker-compose exec chatbot python generation/chatbot/chatbot.py
    """
    print("=" * 50)
    print("챗봇 테스트 모드")
    print("=" * 50)
    
    # 간단한 대화 테스트
    while True:
        user_input = input("\n질문을 입력하세요 (종료: quit): ")
        if user_input.lower() == 'quit':
            break
        
        response = generate_response(user_input, "테스터")
        print(f"\n[BOT] {response['reply']}")
    
    print("\n테스트 종료")