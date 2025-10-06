# 🔧 AI 로직 구현 가이드

> `generation/chatbot/chatbot.py` 구현을 위한 상세 가이드

---

## 📋 개요

이 문서는 `chatbot.py`의 10개 TODO를 단계별로 구현하는 방법을 설명합니다.

**예상 소요 시간**: 3-4시간  
**난이도**: 중급  
**전제 지식**: Python 기초, API 사용 경험

---

## 🎯 전체 구조 이해하기

### 챗봇 동작 흐름

```
1. 사용자 메시지 입력
   ↓
2. RAG 검색 (ChromaDB에서 관련 문서 찾기)
   ↓
3. 시스템 프롬프트 생성 (캐릭터 설정 + RAG 컨텍스트)
   ↓
4. LLM 응답 생성 (OpenAI API 호출)
   ↓
5. 메모리 저장 (대화 기록 유지)
   ↓
6. 응답 반환
```

### 핵심 개념

#### 1. RAG (Retrieval-Augmented Generation)
```
Q: "학식 추천해줘"
   ↓
RAG 검색: "학식은 곤자가가 맛있어" (사전 저장된 정보)
   ↓
LLM: "학식은 곤자가에서 먹는 게 좋아. 돈까스가 특히 인기야!"
```

#### 2. 임베딩 (Embedding)
```
텍스트 → 벡터 변환
"학식 추천" → [0.1, 0.3, -0.2, ..., 0.5]  (3072차원)

유사도 계산:
"학식 추천" [0.1, 0.3, ...] 
    vs
"학식은 곤자가" [0.12, 0.28, ...]
    → 유사도: 0.89 (높음!)
```

#### 3. ChromaDB
```
벡터 데이터베이스
- 임베딩 저장
- 빠른 유사도 검색
- 메타데이터 관리
```

---

## 📝 TODO 1: 라이브러리 임포트

### 필요한 라이브러리

```python
# OpenAI API
from openai import OpenAI

# ChromaDB (벡터 데이터베이스)
import chromadb

# LangChain (LLM 통합 프레임워크)
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

# 한국어 처리
from konlpy.tag import Okt

# 유틸리티
import uuid  # 고유 ID 생성
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

### 각 라이브러리의 역할

| 라이브러리 | 역할 | 사용 이유 |
|---------|------|---------|
| `openai` | OpenAI API 호출 | GPT, 임베딩 생성 |
| `chromadb` | 벡터 DB | 임베딩 저장/검색 (RAG) |
| `langchain` | LLM 통합 | 메모리, 프롬프트 관리 |
| `konlpy` | 한국어 NLP | 키워드 추출 |

---

## 📝 TODO 2: 설정 파일 로드

### 구현 코드

```python
CONFIG_PATH = BASE_DIR / 'config' / 'chatbot_config.json'

try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Warning: config file not found at {CONFIG_PATH}")
    config = {}
```

### 설정 파일 구조

```json
{
  "name": "챗봇 이름",
  "character": {
    "age": 20,
    "university": "대학교",
    "major": "전공"
  },
  "system_prompt": {
    "base": "당신은...",
    "rules": ["반말 사용", "..."]
  }
}
```

---

## 📝 TODO 3: OpenAI API 키 설정

### 구현 코드

```python
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError(
        "OPENAI_API_KEY not found in environment variables. "
        "Please set it in .env file"
    )

client = OpenAI(api_key=api_key)
```

### 테스트

```python
# 간단한 테스트
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "안녕"}],
        max_tokens=10
    )
    print("API 연결 성공:", response.choices[0].message.content)
except Exception as e:
    print("API 오류:", e)
```

---

## 📝 TODO 4: ChromaDB 초기화

### 구현 코드

```python
def init_text_db():
    """텍스트 임베딩 데이터베이스 초기화"""
    
    # 1. 저장 경로 설정
    db_path = BASE_DIR / "static" / "data" / "chatbot" / "chardb_embedding"
    
    # 2. 디렉토리 생성 (없으면)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 3. ChromaDB 클라이언트 생성
    dbclient = chromadb.PersistentClient(path=str(db_path))
    
    # 4. 컬렉션 생성 (이미 있으면 가져오기)
    collection = dbclient.get_or_create_collection(
        name="rag_collection"
    )
    
    print(f"[DB] ChromaDB 초기화 완료: {db_path}")
    print(f"[DB] 저장된 문서 수: {collection.count()}")
    
    return dbclient, collection


# 전역 변수로 초기화 (앱 시작 시 한 번만)
text_dbclient, collection = init_text_db()
```

### ChromaDB 구조

```
chardb_embedding/
├── chroma.sqlite3        # 메타데이터 저장
└── [UUID]/               # 실제 벡터 데이터
    ├── data_level0.bin
    └── ...
```

---

## 📝 TODO 5: 임베딩 생성 함수

### 구현 코드

```python
def get_embedding(text, model="text-embedding-3-large"):
    """텍스트를 임베딩 벡터로 변환"""
    
    try:
        # OpenAI API 호출
        response = client.embeddings.create(
            input=[text],
            model=model
        )
        
        # 임베딩 벡터 반환 (3072차원)
        embedding = response.data[0].embedding
        
        # 로그 출력 (선택)
        print(f"[EMBED] 텍스트: {text[:50]}...")
        print(f"[EMBED] 벡터 차원: {len(embedding)}")
        
        return embedding
        
    except Exception as e:
        print(f"[EMBED] 오류: {e}")
        raise
```

### 모델 비교

| 모델 | 차원 | 성능 | 비용 |
|------|-----|------|-----|
| text-embedding-3-small | 1536 | 보통 | 저렴 |
| text-embedding-3-large | 3072 | 높음 | 비쌈 (권장) |

### 테스트

```python
# 임베딩 생성 테스트
text = "안녕하세요"
embedding = get_embedding(text)
print(f"임베딩 벡터 (처음 5개): {embedding[:5]}")
# 출력: [0.123, -0.456, 0.789, ...]
```

---

## 📝 TODO 6: 한국어 키워드 추출 (선택)

### 구현 코드

```python
okt = Okt()

def extract_nouns_korean(text):
    """한국어 텍스트에서 명사 키워드 추출"""
    
    # 1. 명사 추출
    nouns = okt.nouns(text)
    
    # 2. 불용어 리스트 (의미 없는 단어)
    stopwords = [
        '것', '수', '등', '안', '때', '곳', '중', '들', 
        '거', '제', '간', '내', '나', '점', '게'
    ]
    
    # 3. 필터링 (불용어 제거, 2글자 이상만)
    keywords = [
        noun for noun in nouns 
        if noun not in stopwords and len(noun) > 1
    ]
    
    print(f"[KEYWORD] 원문: {text}")
    print(f"[KEYWORD] 추출: {keywords}")
    
    return keywords
```

### 예시

```python
text = "학식 추천해줘. 어디가 맛있어?"
keywords = extract_nouns_korean(text)
# 출력: ['학식', '추천', '맛']
```

### 왜 필요한가?

```
일반 검색:
"학식 추천해줘" → 임베딩 → 검색 (유사도: 0.65)

키워드 추가:
"학식 추천해줘 + 학식 추천" → 임베딩 → 검색 (유사도: 0.85 ↑)
```

---

## 📝 TODO 7: RAG 문서 검색 (핵심!)

### 구현 코드

```python
def search_similar_documents(query, collection, threshold=0.45, top_k=5):
    """유사 문서 검색 (RAG의 핵심)"""
    
    try:
        # 1. 키워드 추출 (선택, 정확도 향상)
        keywords = extract_nouns_korean(query)
        keyword_text = " ".join(keywords)
        combined = f"{query} {keyword_text}"
        
        print(f"\n[RAG] 질문: {query}")
        print(f"[RAG] 키워드: {keywords}")
        
        # 2. 임베딩 생성
        query_embedding = get_embedding(combined)
        
        # 3. ChromaDB에서 검색
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )
        
        # 4. 결과 확인
        if not results["documents"] or not results["documents"][0]:
            print("[RAG] 검색 결과 없음")
            return None, None, None
        
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        
        # 5. 유사도 계산 및 필터링
        filtered_docs = []
        
        for doc, dist, meta in zip(documents, distances, metadatas):
            # 거리를 유사도로 변환
            similarity = 1 / (1 + dist)
            
            if similarity >= threshold:
                filtered_docs.append((doc, similarity, meta))
                print(f"[RAG] 발견: {doc[:50]}... (유사도: {similarity:.4f})")
        
        # 6. 최고 유사도 문서 반환
        if filtered_docs:
            best_doc = max(filtered_docs, key=lambda x: x[1])
            print(f"[RAG] 선택: 유사도 {best_doc[1]:.4f}")
            return best_doc  # (document, similarity, metadata)
        
        print(f"[RAG] threshold({threshold}) 이상 결과 없음")
        return None, None, None
        
    except Exception as e:
        print(f"[RAG] 검색 오류: {e}")
        return None, None, None
```

### threshold 값 선택

| threshold | 효과 | 사용 시기 |
|-----------|------|---------|
| 0.3-0.35 | 많은 문서 검색 | 데이터가 적을 때 |
| 0.40-0.45 | 균형 (권장) | 일반적인 경우 |
| 0.50-0.60 | 엄격한 검색 | 데이터가 많을 때 |

### 유사도 계산 이해

```
거리 (distance): 벡터 간 거리 (작을수록 유사)
  예: distance = 0.5

유사도 (similarity): 1 / (1 + distance)
  예: similarity = 1 / (1 + 0.5) = 0.67

threshold = 0.45일 때:
  0.67 >= 0.45 → ✅ 통과
```

---

## 📝 TODO 8: LangChain 메모리 및 대화 체인

### 구현 코드

```python
# 1. LLM 초기화
langchain_llm = ChatOpenAI(
    model_name="gpt-4o-mini",
    openai_api_key=api_key,
    temperature=0.7  # 0.3(정확) ~ 1.0(창의적)
)

# 2. 대화 메모리 초기화
memory = ConversationSummaryBufferMemory(
    llm=langchain_llm,
    memory_key="chat_history",
    input_key="input",
    max_token_limit=1000,  # 메모리 크기 제한
    return_messages=True
)

# 3. 프롬프트 템플릿
template = """
{system_prompt}

{chat_history}

사용자: {input}

챗봇:
"""

prompt = PromptTemplate(
    input_variables=["system_prompt", "input", "chat_history"],
    template=template
)

# 4. 대화 체인 생성
conversation_chain = LLMChain(
    llm=langchain_llm,
    prompt=prompt,
    memory=memory,
    verbose=False  # True로 설정하면 디버깅 정보 출력
)
```

### 메모리 동작 방식

```
1차 대화:
  사용자: "안녕?"
  챗봇: "안녕! 뭐 도와줄까?"
  메모리: [사용자: 안녕?, 챗봇: 안녕! 뭐 도와줄까?]

2차 대화:
  사용자: "아까 뭐라고 했어?"
  메모리 참조: "안녕! 뭐 도와줄까?"
  챗봇: "아까 '안녕! 뭐 도와줄까?'라고 했어"
```

---

## 📝 TODO 9: 시스템 프롬프트 생성

### 구현 코드

```python
def build_system_prompt(username, has_context=False):
    """시스템 프롬프트 생성"""
    
    # 1. config에서 기본 프롬프트 가져오기
    base_prompt = config.get('system_prompt', {}).get(
        'base', 
        '당신은 친근한 챗봇입니다.'
    )
    
    rules = config.get('system_prompt', {}).get('rules', [])
    rules_text = '\n'.join(f"- {rule}" for rule in rules)
    
    # 2. 캐릭터 정보 구성
    character = config.get('character', {})
    char_info = f"""
캐릭터 정보:
- 나이: {character.get('age', '알 수 없음')}
- 대학: {character.get('university', '알 수 없음')}
- 전공: {character.get('major', '알 수 없음')}
- 성격: {character.get('personality', '알 수 없음')}
- 배경: {character.get('background', '알 수 없음')}
"""
    
    # 3. RAG 컨텍스트 지시사항
    context_instruction = ""
    if has_context:
        context_instruction = """
[중요] 대화 중에 [참고 정보]가 제공되면, 
이 정보를 적극 활용하여 답변하세요.
단, 자연스럽게 녹여서 말하고, 
"참고 정보에 따르면..."처럼 직접 언급하지 마세요.
"""
    
    # 4. 최종 프롬프트 조합
    system_prompt = f"""
{base_prompt}

{char_info}

대화 규칙:
{rules_text}

{context_instruction}

[사용자 이름: {username}]
"""
    
    return system_prompt
```

### 프롬프트 예시

```
당신은 서강대학교 컴퓨터공학과 4학년 김서강입니다.

캐릭터 정보:
- 나이: 24세
- 대학: 서강대학교
- 전공: 컴퓨터공학과
- 성격: 친절하고 유머러스함
- 배경: 신입생을 돕는 선배

대화 규칙:
- 반말을 사용하세요
- 이모티콘을 사용하지 마세요
- 친근하게 대화하세요

[중요] [참고 정보]가 제공되면 적극 활용하세요.

[사용자 이름: 철수]
```

---

## 📝 TODO 10: 응답 생성 함수 (통합!)

### 전체 구현 코드

```python
def generate_response(user_message, username="사용자"):
    """사용자 메시지에 대한 챗봇 응답 생성"""
    
    print(f"\n{'='*50}")
    print(f"[USER] {username}: {user_message}")
    
    try:
        # ===== 1. 초기 메시지 처리 =====
        if user_message.strip().lower() == "init":
            bot_name = config.get('name', '챗봇')
            
            # 캐릭터에 맞는 인사말 작성
            initial_reply = f"안녕! 나는 {bot_name}이야. 뭐 궁금한 거 있어?"
            
            # 메모리에 저장
            try:
                memory.save_context(
                    {"input": ""},
                    {"output": initial_reply}
                )
            except Exception as e:
                print(f"[MEMORY] 초기화 오류: {e}")
            
            return {
                "reply": initial_reply,
                "image": None
            }
        
        # ===== 2. 메모리 로드 =====
        try:
            memory_variables = memory.load_memory_variables({})
            chat_history = memory_variables.get("chat_history", "")
        except Exception as e:
            print(f"[MEMORY] 로드 오류: {e}")
            chat_history = ""
        
        # ===== 3. RAG 검색 =====
        context, similarity, metadata = search_similar_documents(
            user_message, 
            collection,
            threshold=0.45,
            top_k=5
        )
        
        has_context = context is not None
        
        # ===== 4. 시스템 프롬프트 생성 =====
        system_prompt = build_system_prompt(username, has_context)
        
        # ===== 5. 최종 프롬프트 구성 =====
        if has_context:
            # RAG 컨텍스트 포함
            final_prompt = f"""
{system_prompt}

[참고 정보]
{context}

사용자: {user_message}
"""
        else:
            # RAG 컨텍스트 없음
            final_prompt = f"""
{system_prompt}

사용자: {user_message}
"""
        
        print(f"[PROMPT] RAG 사용: {has_context}")
        
        # ===== 6. LLM 응답 생성 =====
        reply = conversation_chain.predict(
            system_prompt=system_prompt,
            input=user_message
        )
        
        print(f"[BOT] {reply[:100]}...")
        
        # ===== 7. 메모리 저장 =====
        try:
            memory.save_context(
                {"input": user_message},
                {"output": reply}
            )
        except Exception as e:
            print(f"[MEMORY] 저장 오류: {e}")
        
        # ===== 8. 응답 반환 =====
        return {
            "reply": reply,
            "image": None
        }
        
    except Exception as e:
        print(f"[ERROR] 응답 생성 오류: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "reply": "죄송해요. 오류가 발생했어요. 다시 시도해주세요.",
            "image": None
        }
```

---

## 🧪 테스트 방법

### 1. 파일 직접 실행

```bash
docker-compose exec chatbot python generation/chatbot/chatbot.py
```

### 2. 대화 테스트

```
질문을 입력하세요 (종료: quit): 안녕?
[BOT] 안녕! 나는 김서강이야. 뭐 궁금한 거 있어?

질문을 입력하세요 (종료: quit): 학식 추천해줘
[RAG] 검색 중...
[RAG] 발견: 학식은 곤자가가 맛있어...
[BOT] 학식은 곤자가에서 먹는 게 좋아! 돈까스가 특히 인기야.

질문을 입력하세요 (종료: quit): quit
```

### 3. 웹 인터페이스 테스트

```bash
# Docker 실행
docker-compose up

# 브라우저: http://localhost:5000
# 채팅 화면에서 테스트
```

---

## 🐛 디버깅 팁

### 1. 로그 출력 활용

```python
# 각 단계마다 로그 출력
print(f"[DEBUG] 변수 확인: {variable}")
```

### 2. RAG가 작동하지 않을 때

```python
# 임베딩 파일 확인
print(f"문서 개수: {collection.count()}")

# 검색 결과 확인
results = collection.query(...)
print(f"검색 결과: {results}")
```

### 3. 메모리 오류

```python
# verbose=True로 설정
conversation_chain = LLMChain(..., verbose=True)
```

---

## ✅ 완료 체크리스트

- [ ] TODO 1: 라이브러리 임포트 완료
- [ ] TODO 2: 설정 파일 로드 완료
- [ ] TODO 3: OpenAI API 키 설정 완료
- [ ] TODO 4: ChromaDB 초기화 완료
- [ ] TODO 5: 임베딩 생성 함수 완료
- [ ] TODO 6: 키워드 추출 함수 완료 (선택)
- [ ] TODO 7: RAG 검색 함수 완료
- [ ] TODO 8: LangChain 설정 완료
- [ ] TODO 9: 시스템 프롬프트 함수 완료
- [ ] TODO 10: 응답 생성 함수 완료
- [ ] 파일 직접 실행 테스트 통과
- [ ] 웹 인터페이스 테스트 통과

---

## 🎓 학습 포인트

### 구현을 통해 배우는 것

1. **OpenAI API 활용**
   - 임베딩 생성
   - Chat Completion

2. **RAG 구현**
   - 벡터 데이터베이스 (ChromaDB)
   - 유사도 검색
   - 컨텍스트 활용

3. **프롬프트 엔지니어링**
   - 시스템 프롬프트 구성
   - 컨텍스트 통합
   - 페르소나 설정

4. **메모리 관리**
   - LangChain Memory
   - 대화 맥락 유지

5. **한국어 NLP**
   - KoNLPy 활용
   - 키워드 추출

---

## 📚 참고 자료

### 공식 문서
- [OpenAI API 문서](https://platform.openai.com/docs/api-reference)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [LangChain 문서](https://python.langchain.com/docs/get_started/introduction)
- [KoNLPy 문서](https://konlpy.org/ko/latest/)

### 유용한 튜토리얼
- [RAG 튜토리얼](https://python.langchain.com/docs/tutorials/rag/)
- [LangChain 메모리 가이드](https://python.langchain.com/docs/modules/memory/)

---

**구현 완료 후 ASSIGNMENT_GUIDE.md의 다음 단계로 진행하세요!**

