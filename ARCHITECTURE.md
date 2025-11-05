# 🏗️ 시스템 아키텍처

> 별빛 우체국 챗봇 프로젝트의 전체 구조와 데이터 흐름

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
│  📜 static/js/chatbot.js  - 채팅 UI 로직                         │
│                            (메시지 전송, 렌더링, 버튼 처리)       │
│  📜 static/css/style.css  - 스타일링                             │
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
│  (Business Logic - 핵심 AI 로직)                                  │
├─────────────────────────────────────────────────────────────────┤
│  🧠 services/chatbot_service.py                                  │
│                                                                  │
│  class ChatbotService:                                           │
│    │                                                             │
│    ├── __init__()                                               │
│    │    ├── OpenAI Client 초기화                                │
│    │    ├── ChromaDB 연결 (방별 QA 데이터)                       │
│    │    ├── LangChain Chroma (상담 매뉴얼 벡터 DB)               │
│    │    └── Persona JSON 로드                                   │
│    │                                                             │
│    ├── generate_response(user_message) ⭐ 메인 로직              │
│    │    ├── 1. 세션 관리 (PostOfficeSession)                    │
│    │    ├── 2. 예외 처리 (반복, 편지 요청, 방 변경)              │
│    │    ├── 3. 감정 분석 (LLM 기반)                              │
│    │    ├── 4. RAG 검색 (방별 QA 데이터)                         │
│    │    ├── 5. Persona 검색 (부엉장 스토리)                      │
│    │    ├── 6. 위기 감지 → 상담 매뉴얼 검색 (RAG-D)             │
│    │    ├── 7. 프롬프트 구성                                     │
│    │    ├── 8. LLM 응답 생성                                     │
│    │    ├── 9. 후처리 (의문문 제거, 감정 태그 추가)              │
│    │    └── 10. 세션 저장                                         │
│    │                                                             │
│    ├── _create_embedding(text)                                  │
│    │    └── OpenAI API → 벡터 변환 (캐시 활용)                  │
│    │                                                             │
│    ├── _search_similar(query, room_filter) ⭐ RAG 핵심!        │
│    │    ├── 1. 쿼리 임베딩 생성                                  │
│    │    ├── 2. ChromaDB 검색 (방별 필터링)                       │
│    │    ├── 3. 거리 → 유사도 변환                                │
│    │    ├── 4. 임계값 필터링 (0.72)                              │
│    │    └── 5. Top-K 문서 반환                                   │
│    │                                                             │
│    ├── _search_persona(user_message, context)                  │
│    │    ├── 1. 키워드 매칭 점수 계산                             │
│    │    ├── 2. 직접 질문 감지 → 강제 활성화                      │
│    │    ├── 3. 고득점 강제 활성화 (4점 이상)                     │
│    │    └── 4. Persona 스토리 반환                              │
│    │                                                             │
│    ├── _search_counseling_knowledge(query)                      │
│    │    └── LangChain Chroma 벡터 DB 검색 (위기 모드)           │
│    │                                                             │
│    ├── _analyze_user_emotion(user_message)                      │
│    │    └── LLM 기반 감정 분석 (JOY, SADNESS, ANGER, etc.)      │
│    │                                                             │
│    └── _determine_owl_emotion(...)                               │
│         └── 상황 기반 감정 결정 (의문, 분노, 슬픔, 기쁨, 기본)    │
└──────────────┬────────────┬────────────┬─────────────────────────┘
               │            │            │
               ↓            ↓            ↓
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │   OpenAI     │  │   ChromaDB   │  │ LangChain    │
    │   API        │  │   (Vector    │  │ Chroma       │
    │              │  │   Database)  │  │              │
    │ - Embedding  │  │              │  │ - 상담       │
    │ - GPT-4o-mini│  │ - 방별 QA    │  │   매뉴얼     │
    │ - 감정 분석   │  │   데이터     │  │   벡터 DB    │
    └──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🔄 데이터 흐름 (Request → Response)

### 1️⃣ 사용자 메시지 입력

```
사용자: "후회에 대한 이야기를 하고 싶어"
  ↓
Frontend (chatbot.js)
  ↓
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({
    message: "후회에 대한 이야기를 하고 싶어",
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
    username = request.json.get('username', '방문자')

    # 서비스 호출
    chatbot = get_chatbot_service()
    response = chatbot.generate_response(user_message, username)

    return jsonify(response)
```

### 3️⃣ AI 로직 처리 (핵심)

```
ChatbotService.generate_response()
  ↓
[1단계] 세션 관리
  - 사용자별 세션 로드/생성
  - Phase 상태 확인 (1: 입장, 2: 방 선택, 3: 방 대화, 3.5: 서랍, 4: 편지 생성, 5: 편지 전달)
  - 대화 기록 저장

[2단계] 예외 처리 (우선 처리)
  - 반복 말 감지: 임베딩 유사도 85% 이상 → 대화 전략 조정
  - 편지 조기 요청: "편지줘" 키워드 감지 → 확인 버튼 제공
  - 방 변경 요청: "다른 방으로" 감지 → 재입장 확인 프로세스

[3단계] 감정 분석
  _analyze_user_emotion(user_message)
    → OpenAI GPT-4o-mini API 호출
    → "JOY", "SADNESS", "ANGER", "QUESTION", "BASIC" 중 하나 반환

[4단계] 부엉장 감정 결정
  _determine_owl_emotion(user_message, session, user_emotion)
    → 상황 기반 오버라이드
    → 우선순위: 의문 → 분노 → 슬픔 → 기쁨 → LLM 결과
    → "기본", "기쁨", "슬픔", "분노", "의문" 중 하나 반환

[5단계] RAG 검색 (방별 QA 데이터)
  _search_similar(user_message, room_filter="regret")
    → 쿼리 임베딩 생성 (text-embedding-3-small)
    → ChromaDB.query(query_embedding, where={"room": "regret"})
    → 유사도 계산: similarity = 1.0 / (1.0 + distance)
    → 임계값 필터링 (0.72 이상)
    → Top-K 문서 반환

[6단계] Persona 검색
  _search_persona(user_message, conversation_context)
    → 키워드 매칭 점수 계산
    → 직접 질문 감지 → 강제 활성화
    → 고득점(4점 이상) → 강제 활성화
    → Persona 스토리 및 가이드 반환

[7단계] 위기 감지 및 상담 매뉴얼 검색
  _detect_crisis(user_message)
    → 위기 키워드 감지: "자살", "극단적", "죽고" 등
    → 위기 모드 활성화 시:
      _search_counseling_knowledge(user_message)
        → LangChain Chroma 벡터 DB 검색
        → 상담 매뉴얼 관련 지식 반환 (Top-K: 3)

[8단계] 프롬프트 구성
  system_prompt = """
  당신은 별빛 우체국의 부엉이 우체국장입니다.
  [부엉장 캐릭터 정보]
  [Persona 스토리]
  [RAG 컨텍스트 - 방별 QA 데이터]
  [상담 매뉴얼 지식 - 위기 모드 시]
  [대화 맥락 요약]
  """

[9단계] LLM 응답 생성
  OpenAI.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_message}
    ]
  )
    → 부엉장 스타일의 응답 생성

[10단계] 응답 후처리
  - 의문문 제거 (최소 대화 횟수 충족 시)
  - 긴 문장 분할 (max_length: 120자)
  - 감정 태그 추가 (감정 변화 감지 시)
  - 버튼 추가 (Phase 전환 시)

[11단계] 응답 반환
  {
    "reply": "후회에 대한 이야기를 하고 싶군...",
    "replies": ["후회에 대한 이야기를 하고 싶군...", "그렇군..."],
    "image": "images/chatbot/S_1.png",  # 감정 태그
    "phase": 3,
    "buttons": ["응", "아니"]
  }
```

### 4️⃣ Frontend 렌더링

```
chatbot.js
  ↓
response = await fetch('/api/chat', ...)
  ↓
봇 메시지 DOM 생성
  - 감정 이미지 표시 (image 필드)
  - 버튼 표시 (buttons 필드)
  - Phase 전환 처리
  ↓
채팅 UI에 표시
```

---

## 📂 프로젝트 구조

```
3-character-chat/
│
├── app.py                          # Flask 애플리케이션 (라우팅)
├── services/
│   └── chatbot_service.py          # 핵심 AI 로직 (RAG, 감정, Persona)
├── config/
│   └── chatbot_config.json        # 챗봇 설정 (방 정보, Phase 설정)
├── static/
│   ├── data/
│   │   └── chatbot/
│   │       ├── chardb_text/        # 텍스트 데이터
│   │       │   ├── regret/         # 후회 관련 QA
│   │       │   ├── love/           # 사랑 관련 QA
│   │       │   ├── anxiety/       # 불안 관련 QA
│   │       │   ├── dream/         # 꿈 관련 QA
│   │       │   ├── guides/         # 상담 가이드
│   │       │   ├── owl_character.txt
│   │       │   └── owl_persona.json
│   │       ├── chardb_embedding/   # ChromaDB 벡터 DB (방별 QA)
│   │       ├── counseling_vectordb/ # 상담 매뉴얼 벡터 DB (RAG-D)
│   │       ├── source_pdfs/        # 원본 PDF 파일
│   │       └── sessions/           # 세션 저장소
│   ├── images/
│   │   └── chatbot/                # 부엉장 감정 이미지
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chatbot.js
├── templates/
│   ├── index.html                  # 메인 페이지
│   ├── detail.html                 # 상세 페이지
│   └── chat.html                   # 채팅 페이지
├── tools/
│   └── build_counseling_vectordb.py # 상담 매뉴얼 벡터 DB 구축 스크립트
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── vercel.json                     # Vercel 배포 설정
```

---

## 🧩 핵심 컴포넌트

### 1. ChatbotService (services/chatbot_service.py)

**역할**: 챗봇의 모든 AI 로직 담당

**책임**:

- OpenAI API 관리 (임베딩, LLM, 감정 분석)
- ChromaDB 벡터 검색 (RAG - 방별 QA 데이터)
- LangChain Chroma (상담 매뉴얼 벡터 DB)
- Persona 시스템 관리
- 감정 분석 및 결정
- 세션 관리 및 영속화
- 예외 처리 (반복 말, 편지 요청, 방 변경)
- 응답 생성 파이프라인

**주요 메서드**:

```python
class ChatbotService:
    def __init__(self):
        """초기화: OpenAI, ChromaDB, LangChain 연결"""
    
    def generate_response(self, user_message: str, username: str) -> dict:
        """최종 응답 생성 (통합 파이프라인)"""
    
    def _create_embedding(self, text: str) -> list:
        """텍스트 → 벡터 변환 (캐시 활용)"""
    
    def _search_similar(self, query: str, room_filter: str, 
                       similarity_threshold: float = 0.72) -> list:
        """RAG 검색 (방별 필터링 지원)"""
    
    def _search_persona(self, user_message: str, conversation_context: str) -> dict:
        """Persona 스토리 검색"""
    
    def _search_counseling_knowledge(self, query: str, top_k: int = 3) -> list:
        """상담 매뉴얼 벡터 DB 검색 (RAG-D)"""
    
    def _analyze_user_emotion(self, user_message: str) -> str:
        """LLM 기반 유저 감정 분석"""
    
    def _determine_owl_emotion(self, user_message: str, session, 
                              user_emotion: str) -> str:
        """상황 기반 부엉장 감정 결정"""
    
    def _update_repetition_state(self, session, user_message: str) -> str:
        """반복 말 감지 (의미 기반)"""
    
    def _detect_crisis(self, text: str) -> bool:
        """위기 상황 감지"""
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

### 3. PostOfficeSession (세션 관리)

**역할**: 사용자별 대화 상태 및 기록 관리

**주요 상태**:

- `phase`: 현재 Phase (1: 입장, 2: 방 선택, 3: 방 대화, 3.5: 서랍, 4: 편지 생성, 5: 편지 전달)
- `selected_room`: 선택한 방 (regret, love, anxiety, dream)
- `conversation_history`: 대화 기록
- `summary_text`: 대화 요약 (장기 기억)
- `crisis_mode_active`: 위기 모드 활성화 여부
- `used_persona_stories`: 사용한 Persona 스토리 ID 집합
- `last_emotion`: 마지막 감정 (변화 감지용)

**영속화**: JSON 파일로 저장 (`static/data/chatbot/sessions/`)

### 4. ChromaDB (Vector Database)

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
    "id": "regret_123",
    "embedding": [0.12, -0.34, ..., 0.78],  # 1536차원 (text-embedding-3-small)
    "document": "후회에 대한 이야기...",
    "metadata": {
        "room": "regret",           # 방 필터링용
        "filename": "qa_regret_action.txt",
        "chunk_index": 0,
        "type": "structured"
    }
}
```

**검색 방식**: 
- 방별 필터링: `where={"room": "regret"}`
- 유사도 계산: `similarity = 1.0 / (1.0 + distance)`
- 임계값 필터링: 0.72 이상

### 5. LangChain Chroma (상담 매뉴얼 벡터 DB)

**역할**: 상담 매뉴얼 PDF 파일의 벡터 저장 및 검색

**구조**:

```
static/data/chatbot/counseling_vectordb/
├── chroma.sqlite3
└── [UUID]/
    ├── data_level0.bin
    └── ...
```

**활용**: 위기 모드 활성화 시에만 검색하여 상담 지식 활용

---

## 🔧 기술 스택

### Backend

- **Flask 3.0**: Python 웹 프레임워크
- **OpenAI API**: LLM 및 Embedding
- **ChromaDB**: 벡터 데이터베이스
- **LangChain**: LLM 통합 프레임워크

### Frontend

- **Vanilla JavaScript**: 프레임워크 없이 순수 JS
- **HTML5/CSS3**: 기본 웹 API

### Infrastructure

- **Docker**: 컨테이너화
- **Vercel**: 배포 플랫폼
- **Python 3.11**: 런타임

---

## 🎯 핵심 기능 상세

### 1. 부엉장의 감정 구현

#### 1-1. 유저 감정 분석 (LLM 기반)

**프로세스**:
1. 사용자 메시지를 GPT-4o-mini에 전달
2. 감정 분석 프롬프트로 5가지 카테고리 중 하나 선택
3. 반환: "JOY", "SADNESS", "ANGER", "QUESTION", "BASIC"

**프롬프트 구조**:
```
당신은 감정 분석 전문가입니다.
[유저 메시지]
[감정 카테고리 정의]
→ 단어 하나만 출력 (예: JOY)
```

#### 1-2. 부엉장 감정 결정 (상황 기반)

**우선순위 로직**:
1. **의문 (의문)**: Phase 전환, 확인 대기, 재입장 요청, 질문 표시
2. **분노**: 부엉장에 대한 공격 표현 감지
3. **슬픔**: 위기 모드, 위기 키워드, 슬픔 키워드
4. **기쁨**: Phase 4/5, 긍정적 키워드
5. **LLM 결과 매핑**: 위 규칙에 해당 없으면 LLM 분석 결과 사용

**감정 출력 제어**:
- 동일 감정 유지 시 출력 안 함
- Phase 전환 시점에는 출력 안 함
- 감정 변화 강도가 임계값(1) 이상일 때만 출력
- 위기 모드 첫 진입 시 슬픔 강제 출력

### 2. 부엉장 Persona 구현과 사용

#### 2-1. Persona 데이터 구조

**파일**: `static/data/chatbot/chardb_text/owl_persona.json`

**구조**:
```json
{
  "memory_vault": {
    "love": {
      "stories": {
        "breakup_bluntness": {
          "trigger_keywords": ["이별", "헤어", "차였"],
          "content_short": "짧은 버전 스토리...",
          "content_long": "긴 버전 스토리...",
          "llm_speaking_guidance": "LLM 발화 가이드..."
        }
      }
    }
  }
}
```

#### 2-2. Persona 검색 및 활성화

**검색 프로세스**:
1. 사용자 메시지와 대화 맥락 결합
2. 각 카테고리 → 서브 스토리 순회
3. 트리거 키워드 매칭 점수 계산
4. 최고 점수 스토리 선택

**활성화 조건**:
- 직접 질문 감지: "너는", "부엉", "좋아하" 등 → `used_stories` 무시하고 강제 활성화
- 고득점 매칭: 점수 4점 이상 → 강제 활성화
- 재사용 허용: 점수 3점 이상 → 이미 사용한 스토리도 재사용 허용

**중복 방지**:
- `session.used_persona_stories`에 사용한 스토리 ID 저장
- 일반 매칭 시 중복 제외, 고득점(3점 이상)은 재사용 허용

### 3. 각 방별 질문 데이터 활용

#### 3-1. 데이터 소스 구조

```
static/data/chatbot/chardb_text/
├── regret/          # 후회 관련 QA
│   ├── qa_regret_action.txt
│   ├── qa_regret_dream.txt
│   ├── qa_regret_relation.txt
│   ├── qa_regret_self.txt
│   └── owl_response_regret.txt
├── love/            # 사랑 관련 QA
├── anxiety/         # 불안 관련 QA
├── dream/           # 꿈 관련 QA
└── owl_character.txt
```

#### 3-2. 데이터 로딩 및 임베딩

**프로세스**:
1. 각 방 폴더의 `.txt` 파일 읽기
2. 텍스트 청킹 (최대 900자)
3. OpenAI Embeddings로 임베딩 생성 (`text-embedding-3-small`)
4. ChromaDB에 저장 (메타데이터: `room`, `filename`, `chunk_index`)

**메타데이터 구조**:
```python
{
    "room": "regret",  # 방 이름 (필터링용)
    "filename": "qa_regret_action.txt",
    "chunk_index": 0,
    "type": "structured"
}
```

#### 3-3. RAG 검색 전략

**검색 단계**:
1. 현재 방 우선 검색
   - `room_filter`로 해당 방 데이터만 검색
   - 유사도 임계값: 0.72
   - Top-K: 5개
2. 매칭 없으면 전역 검색
   - 방 필터 없이 전체 검색
   - 유사도 임계값: 0.65 (완화)
3. 거리 → 유사도 변환
   - `similarity = 1.0 / (1.0 + distance)`
4. 임계값 필터링 후 Top-K 반환

### 4. 상담 메뉴얼을 활용한 위기 감지 모드

#### 4-1. 위기 감지 메커니즘

**위기 키워드**:
- 직접 위기: "자살", "극단적", "죽고", "해치", "학대", "폭력", "살고싶지", "위험"
- 위기 완충: 위기 표현 직후 1턴 완충 적용 (`crisis_cooldown`)

**위기 모드 활성화**:
- 위기 키워드 감지 시 `session.crisis_mode_active = True`
- 한 번 활성화되면 편지 전달(Phase 5)까지 유지

#### 4-2. 상담 매뉴얼 벡터 DB (RAG-D)

**구축 과정**:
1. PDF 파일 로드 (`langchain_community.document_loaders.PyPDFLoader`)
2. 텍스트 분할 (`RecursiveCharacterTextSplitter`)
3. 배치 처리 (50개씩)로 임베딩 생성
4. LangChain Chroma에 저장

**검색 조건**:
- 위기 모드 활성화 시 (`session.crisis_mode_active = True`)
- 또는 위기 키워드 포함 시
- 관련 지식 검색 (Top-K: 3)

**활용**:
- 검색된 상담 매뉴얼 청크를 시스템 프롬프트에 포함
- 안전 지침 추가
- 전문 상담 응답 생성

#### 4-3. 위기 모드 회복 및 해제

**회복 감지**:
- 회복 키워드: "괜찮", "나아", "회복", "좀 나은" 등
- 연속 2회 회복 신호 감지 시 위기 모드 해제
- 회복 신호가 없으면 카운터 초기화

**자동 해제**:
- Phase 5 (편지 전달) 시 자동 해제

### 5. 예외 처리

#### 5-1. 사용자 반복 말 감지

**의미 기반 중복 감지**:
1. 최근 3개 사용자 메시지 추출
2. 현재 메시지를 임베딩으로 변환
3. 최근 메시지들과 코사인 유사도 계산
4. 유사도 85% 이상이면 반복으로 간주

**반복 의도 추적**:
- `_normalize_intent_key()`로 의도 키 정규화
- `session.repeated_intent_count`로 반복 횟수 추적
- 반복 감지 시 대화 전략 조정

#### 5-2. 편지 조기 전달 요청 처리

**조기 요청 감지**:
- 키워드: "편지줘", "편지내놔", "그만", "끝" 등
- Phase 3에서 최소 대화 횟수(3회) 미달 시
- Phase 3.5에서 최소 대화 횟수(2회) 미달 시

**확인 프로세스**:
1. `session.awaiting_letter_confirm = True` 설정
2. 확인 메시지: "아직 대화를 마무리하지 못했는데 편지를 먼저 꺼내줄까?"
3. 버튼 제공: "응 편지를 받을래" / "아니, 더 대화할래"
4. 사용자 선택에 따라 처리
   - "편지를 받을래": Phase 5로 이동, 편지 즉시 생성
   - "더 대화할래": 현재 Phase 유지, 대화 계속

#### 5-3. 방 변경 요청 처리

**방 변경 감지**:
- 키워드: "방으로", "다른 방", "바꾸고", "이동", "말고" 등
- `_detect_room_change_request()`로 요청 분석

**처리 케이스**:
1. 구체적 다른 방 지정
   - 예: "사랑의 방 말고 불안의 방으로 가고 싶어"
   - 확인 메시지와 재입장 버튼 제공
2. 현재 방과 같은 방 요청
   - 예: "후회의 방으로 가고 싶어" (이미 후회의 방에 있음)
   - 현재 방 확인 안내
3. 비구체적 요청
   - 예: "다른 방으로 가고 싶어"
   - 확인 메시지와 재입장 버튼 제공

**확인 프로세스**:
1. `session.awaiting_room_change_confirm = True` 설정
2. `session.requested_new_room`에 요청 방 저장
3. 확인 메시지: "우체국에 재입장하면 다른 방으로 다시 갈 수 있긴 한데... 우체국에 재입장하겠나?"
4. 버튼 제공: "응, 우체국에 재입장할래" / "아니, 이 방에서 계속 할래"
5. 사용자 선택에 따라 처리
   - "재입장": 세션 완전 초기화, Phase 1로 복귀
   - "계속": 현재 방 유지, 대화 계속

---

## 📚 추가 학습 자료

- [OpenAI API 공식 문서](https://platform.openai.com/docs)
- [ChromaDB 공식 문서](https://docs.trychroma.com/)
- [LangChain 공식 문서](https://python.langchain.com/)
- [Flask 공식 문서](https://flask.palletsprojects.com/)
