# 🏗️ 시스템 아키텍처

> 챗봇 프로젝트의 전체 구조와 데이터 흐름

---

## 📊 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                           사용자                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP Request/Response
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Layer                              │
│  (Vanilla JavaScript + HTML/CSS)                                 │
├─────────────────────────────────────────────────────────────────┤
│  📄 templates/                                                   │
│    ├── index.html         - 메인 페이지                          │
│    ├── detail.html        - 상세 페이지                          │
│    └── chat.html          - 채팅 인터페이스                       │
│                                                                  │
│  📜 static/js/                                                   │
│    └── chatbot.js         - 채팅 UI 로직                         │
│                            (메시지 전송, 렌더링)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ POST /api/chat
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Layer                               │
│  (Flask Web Framework)                                           │
├─────────────────────────────────────────────────────────────────┤
│  🎯 app.py                                                       │
│    ├── @app.route('/')              - 메인 페이지               │
│    ├── @app.route('/detail')        - 상세 페이지               │
│    ├── @app.route('/chat')          - 채팅 페이지               │
│    ├── @app.route('/api/chat')      - 챗봇 API ⭐               │
│    └── @app.route('/health')        - 헬스체크                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ get_chatbot_service()
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                               │
│  (Business Logic - 학생 구현 영역)                                │
├─────────────────────────────────────────────────────────────────┤
│  🧠 services/chatbot_service.py                                  │
│                                                                  │
│  class ChatbotService:                                           │
│    │                                                             │
│    ├── __init__()                                               │
│    │    ├── OpenAI Client 초기화                                │
│    │    ├── ChromaDB 연결                                       │
│    │    └── LangChain Memory 설정                               │
│    │                                                             │
│    ├── _create_embedding(text)                                  │
│    │    └── OpenAI API → 벡터 변환                              │
│    │                                                             │
│    ├── _search_similar(query)         ⭐ RAG 핵심!             │
│    │    ├── 1. 쿼리 임베딩 생성                                  │
│    │    ├── 2. ChromaDB 검색                                    │
│    │    ├── 3. 유사도 계산                                       │
│    │    └── 4. 최적 문서 반환                                    │
│    │                                                             │
│    ├── _build_prompt(message, context)                          │
│    │    └── 시스템 프롬프트 + RAG 컨텍스트                       │
│    │                                                             │
│    └── generate_response(user_message)                          │
│         ├── 1. RAG 검색                                          │
│         ├── 2. 프롬프트 구성                                      │
│         ├── 3. LLM API 호출                                      │
│         ├── 4. 메모리 저장                                        │
│         └── 5. 응답 반환                                          │
└──────────────┬────────────┬─────────────────────────────────────┘
               │            │
               ↓            ↓
    ┌──────────────┐  ┌──────────────┐
    │   OpenAI     │  │   ChromaDB   │
    │   API        │  │   (Vector    │
    │              │  │   Database)  │
    │ - Embedding  │  │              │
    │ - GPT-4      │  │ - Text DB    │
    │ - Memory     │  │ - Image DB   │
    └──────────────┘  └──────────────┘
```

---

## 🔄 데이터 흐름 (Request → Response)

### 1️⃣ 사용자 메시지 입력

```
사용자: "학식 추천해줘"
  ↓
Frontend (chatbot.js)
  ↓
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "학식 추천해줘",
    username: "홍길동"
  })
})
```

### 2️⃣ Backend 라우팅

```
Flask (app.py)
  ↓
@app.route('/api/chat', methods=['POST'])
def api_chat():
    # 요청 파싱
    user_message = request.json['message']
    
    # 서비스 호출
    chatbot = get_chatbot_service()
    response = chatbot.generate_response(user_message)
    
    return jsonify(response)
```

### 3️⃣ AI 로직 처리 (핵심!)

```
ChatbotService (chatbot_service.py)
  ↓
[1단계] Embedding 생성
  "학식 추천해줘" 
    → OpenAI API 
    → [0.12, -0.34, ..., 0.78]  (3072차원 벡터)

[2단계] RAG 검색
  query_embedding = [0.12, -0.34, ..., 0.78]
    ↓
  ChromaDB.query(query_embedding)
    ↓
  검색 결과:
    - "학식은 곤자가가 맛있어" (거리: 0.15)
    - "도서관은 10시까지" (거리: 0.98)
    ↓
  유사도 계산:
    - similarity₁ = 1/(1+0.15) = 0.87 ✅ (선택!)
    - similarity₂ = 1/(1+0.98) = 0.50 ❌ (제외)

[3단계] 프롬프트 구성
  system_prompt = """
  당신은 서강대 선배입니다.
  신입생들에게 학교 생활을 알려주세요.
  """
  
  rag_context = """
  [참고 정보]
  학식은 곤자가가 맛있어.
  """
  
  final_prompt = system_prompt + rag_context + user_message

[4단계] LLM API 호출
  OpenAI.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": final_prompt}
    ]
  )
    ↓
  "학식은 곤자가에서 먹는 게 제일 좋아! 돈까스가 특히 인기야 😋"

[5단계] 응답 반환
  {
    "reply": "학식은 곤자가에서...",
    "image": null
  }
```

### 4️⃣ Frontend 렌더링

```
chatbot.js
  ↓
response = await fetch('/api/chat', ...)
  ↓
봇 메시지 DOM 생성
  ↓
채팅 UI에 표시
```

---

## 📂 프로젝트 구조 (MVC 패턴 기반)

```
chatbot-project/
│
├── 🚫 [템플릿 - 수정 금지]
│   │
│   ├── app.py                          # Controller (Flask 라우팅)
│   ├── templates/                      # View (HTML)
│   │   ├── index.html
│   │   ├── detail.html
│   │   └── chat.html
│   ├── static/                         # View Assets
│   │   ├── css/style.css
│   │   └── js/chatbot.js
│   │
│   ├── Dockerfile                      # Docker 설정
│   ├── docker-compose.yml
│   ├── requirements.txt                # Python 패키지
│   └── vercel.json                     # Vercel 배포 설정
│
├── ✏️ [학생 구현 영역]
│   │
│   ├── services/                       # Service Layer (비즈니스 로직)
│   │   ├── __init__.py
│   │   └── chatbot_service.py         # ⭐ 핵심 AI 로직
│   │
│   ├── config/                         # Configuration
│   │   └── chatbot_config.json        # 챗봇 설정
│   │
│   └── static/data/chatbot/            # Data
│       ├── chardb_text/               # 텍스트 데이터
│       ├── chardb_embedding/          # 임베딩 벡터 (자동 생성)
│       ├── images/                    # 이미지 파일
│       └── videos/                    # 비디오 파일 (선택)
│
└── 📚 [문서]
    ├── README.md
    ├── ARCHITECTURE.md                 # 이 문서
    ├── GETTING_STARTED.md
    ├── ASSIGNMENT_GUIDE.md
    ├── IMPLEMENTATION_GUIDE.md
    └── DOCKER_GUIDE.md
```

---

## 🧩 핵심 컴포넌트

### 1. ChatbotService (services/chatbot_service.py)

**역할**: 챗봇의 모든 AI 로직 담당

**책임**:
- OpenAI API 관리
- ChromaDB 벡터 검색 (RAG)
- LangChain 메모리 관리
- 응답 생성 파이프라인

**주요 메서드**:
```python
class ChatbotService:
    def __init__(self):
        """초기화"""
        
    def _create_embedding(self, text: str) -> list:
        """텍스트 → 벡터 변환"""
        
    def _search_similar(self, query: str):
        """RAG 검색 (핵심!)"""
        
    def _build_prompt(self, message: str, context: str):
        """프롬프트 구성"""
        
    def generate_response(self, user_message: str) -> dict:
        """최종 응답 생성 (통합)"""
```

### 2. Flask App (app.py)

**역할**: HTTP 라우팅 및 템플릿 렌더링

**책임**:
- URL 라우팅
- 요청/응답 처리
- 템플릿 렌더링
- 에러 핸들링

**주요 라우트**:
```python
@app.route('/')                    # 메인 페이지
@app.route('/detail')              # 상세 페이지
@app.route('/chat')                # 채팅 페이지
@app.route('/api/chat')            # 챗봇 API
@app.route('/health')              # 헬스체크
```

### 3. ChromaDB (Vector Database)

**역할**: 임베딩 벡터 저장 및 검색

**구조**:
```
static/data/chatbot/chardb_embedding/
├── chroma.sqlite3           # 메타데이터
└── [UUID]/                  # 벡터 인덱스
    ├── data_level0.bin      # HNSW 알고리즘
    ├── header.bin
    └── link_lists.bin
```

**데이터 스키마**:
```python
{
    "id": "1",
    "embedding": [0.12, -0.34, ..., 0.78],  # 3072차원
    "document": "학식은 곤자가가 맛있어",
    "metadata": {
        "type": "qa",
        "keywords": "학식, 추천",
        "filename": "qa.txt"
    }
}
```

---

## 🔧 기술 스택

### Backend
- **Flask 3.0**: Python 웹 프레임워크
- **OpenAI API**: LLM 및 Embedding
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: LLM 통합 프레임워크
- **KoNLPy**: 한국어 자연어 처리

### Frontend
- **Vanilla JavaScript**: 프레임워크 없이 순수 JS
- **HTML5/CSS3**: 기본 웹 기술

### Infrastructure
- **Docker**: 컨테이너화
- **Vercel**: 배포 플랫폼
- **Python 3.11**: 런타임

---

## 🎯 학생 구현 범위

### ✅ 제공되는 것 (템플릿)
- Flask 앱 구조 (app.py)
- HTML/CSS/JS (프론트엔드)
- Docker 설정
- 가이드 문서

### ✏️ 구현해야 하는 것 (핵심!)
1. **ChatbotService 클래스**
   - OpenAI Client 초기화
   - ChromaDB 연결
   - Embedding 생성 함수
   - RAG 검색 알고리즘 ⭐
   - LLM 프롬프트 설계
   - 응답 생성 파이프라인

2. **데이터 준비**
   - 텍스트 데이터 작성
   - 이미지 수집
   - DB 빌드 스크립트

3. **설정 파일**
   - chatbot_config.json
   - .env (API 키)

---

## 🚀 확장 가능성

### 추가 가능한 기능
1. **멀티모달 응답**
   - 이미지 검색 추가
   - 이미지 임베딩 DB 활용

2. **고급 RAG**
   - 재순위(Re-ranking)
   - 하이브리드 검색 (키워드 + 벡터)
   - 문서 청킹 전략

3. **대화 관리**
   - 세션별 메모리
   - 장기 기억 (벡터 DB에 저장)

4. **감정 분석**
   - 사용자 감정 파악
   - 감정에 맞는 응답

5. **다국어 지원**
   - 언어 감지
   - 다국어 임베딩

---

## 📊 성능 고려사항

### Embedding 생성
- **비용**: $0.00013 / 1K 토큰 (text-embedding-3-large)
- **속도**: ~100ms / 요청
- **캐싱**: 동일 쿼리는 캐시 활용 가능

### ChromaDB 검색
- **속도**: ~10ms (1만 벡터 기준)
- **정확도**: HNSW 알고리즘 (99%+)
- **확장성**: 백만 벡터까지 메모리 내 검색

### LLM API
- **비용**: $0.15 / 1M 입력 토큰 (gpt-4o-mini)
- **속도**: ~500ms / 요청
- **컨텍스트**: 최대 128K 토큰

---

## 🔍 디버깅 팁

### 1. Embedding 확인
```python
embedding = chatbot._create_embedding("테스트")
print(f"차원: {len(embedding)}")  # 3072
print(f"첫 5개 값: {embedding[:5]}")
```

### 2. RAG 검색 확인
```python
doc, sim, meta = chatbot._search_similar("학식")
print(f"유사도: {sim:.4f}")
print(f"문서: {doc}")
```

### 3. 프롬프트 확인
```python
prompt = chatbot._build_prompt("안녕", context="...")
print(prompt)
```

### 4. 로그 추가
```python
print(f"[RAG] 검색: {query}")
print(f"[RAG] 결과: {similarity:.4f}")
print(f"[LLM] 호출 중...")
print(f"[LLM] 응답: {reply[:50]}...")
```

---

## 📚 추가 학습 자료

- [OpenAI API 공식 문서](https://platform.openai.com/docs)
- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Flask 공식 문서](https://flask.palletsprojects.com/)

---

**다음 단계**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) 에서 단계별 구현 방법 확인
