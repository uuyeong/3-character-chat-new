# 🔧 AI 로직 구현 가이드

> `services/chatbot_service.py` 구현을 위한 실전 가이드

---

## 📋 개요

이 문서는 `ChatbotService` 클래스의 핵심 메서드를 구현하는 방법을 안내합니다.

**파일 위치**: `services/chatbot_service.py`  
**예상 소요 시간**: 3-4시간  
**난이도**: 중급  
**전제 지식**: Python 기초, API 사용 경험

---

## 🎯 구현 순서

```
1. __init__         : 초기화 (30분)
   ↓
2. _load_config     : 설정 로드 (10분)
   ↓
3. _init_chromadb   : DB 연결 (20분)
   ↓
4. _create_embedding: 임베딩 생성 (15분)
   ↓
5. _search_similar  : RAG 검색 ⭐ (60분)
   ↓
6. _build_prompt    : 프롬프트 설계 (30분)
   ↓
7. generate_response: 전체 통합 ⭐⭐ (60분)
```

---

## 📚 사전 학습: 핵심 개념

### 1. Embedding (임베딩)

**개념**: 텍스트를 숫자 벡터로 변환

```python
# Before
text = "학식 추천해줘"

# After (Embedding)
vector = [0.12, -0.34, 0.56, ..., 0.78]  # 3072차원
```

**왜 필요한가?**
- 컴퓨터는 텍스트를 직접 비교 못함
- 벡터로 변환하면 수학적 유사도 계산 가능
- 의미가 비슷하면 벡터도 비슷함!

```python
"학식 추천" → [0.1, 0.3, ...]
"밥 추천"   → [0.11, 0.29, ...]  # 유사함!
"날씨"      → [-0.5, 0.8, ...]  # 다름!
```

### 2. RAG (Retrieval-Augmented Generation)

**개념**: 검색 + 생성

```
질문: "학식 추천해줘"
  ↓
[1. 검색] ChromaDB에서 관련 문서 찾기
  "학식은 곤자가가 맛있어"
  ↓
[2. 생성] LLM에게 검색 결과와 함께 질문
  LLM: "학식은 곤자가에서 먹는 게 좋아!"
```

**왜 필요한가?**
- LLM만 쓰면: 환각(hallucination) 발생
- RAG 쓰면: 정확한 정보 기반 답변

### 3. 유사도 계산

**Distance → Similarity 변환**:

```python
# ChromaDB는 거리(distance)를 반환
distance = 0.15  # 작을수록 유사

# 우리는 유사도(similarity)로 변환
similarity = 1 / (1 + distance)
# similarity = 1 / (1 + 0.15) = 0.87

# 해석:
# similarity 0.9 이상: 거의 같음
# similarity 0.7-0.9: 매우 유사
# similarity 0.5-0.7: 관련 있음
# similarity 0.5 미만: 별로 관련 없음
```

---

## 🛠️ 단계별 구현

### Step 1: 초기화 (__init__)

**목표**: 필요한 모든 구성 요소 초기화

```python
def __init__(self):
    print("[ChatbotService] 초기화 중...")
    
    # 1. Config 로드
    self.config = self._load_config()
    
    # 2. OpenAI Client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다")
    
    from openai import OpenAI
    self.client = OpenAI(api_key=api_key)
    
    # 3. ChromaDB
    self.collection = self._init_chromadb()
    
    # 4. LangChain Memory (선택)
    from langchain_community.chat_models import ChatOpenAI
    from langchain.memory import ConversationSummaryBufferMemory
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    self.memory = ConversationSummaryBufferMemory(
        llm=llm,
        max_token_limit=500,
        return_messages=True
    )
    
    print("[ChatbotService] 초기화 완료")
```

**필요한 import**:
```python
import os
from openai import OpenAI
import chromadb
from langchain_community.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
```

---

### Step 2: 설정 로드 (_load_config)

**목표**: JSON 파일에서 챗봇 설정 읽기

```python
def _load_config(self):
    config_path = BASE_DIR / 'config' / 'chatbot_config.json'
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[WARNING] config 파일 없음, 기본값 사용")
        return {
            'name': '챗봇',
            'system_prompt': {
                'base': '당신은 친절한 챗봇입니다.',
                'rules': []
            }
        }
```

---

### Step 3: ChromaDB 초기화 (_init_chromadb)

**목표**: 벡터 데이터베이스 연결

```python
def _init_chromadb(self):
    import chromadb
    
    # DB 경로
    db_path = BASE_DIR / "static/data/chatbot/chardb_embedding"
    
    # 디렉토리 생성 (없으면)
    db_path.mkdir(parents=True, exist_ok=True)
    
    # Client 생성
    client = chromadb.PersistentClient(path=str(db_path))
    
    # Collection 가져오기 (없으면 생성)
    collection = client.get_or_create_collection(
        name="rag_collection",
        metadata={"description": "RAG를 위한 텍스트 임베딩"}
    )
    
    print(f"[ChromaDB] 컬렉션 연결 완료 (문서 수: {collection.count()})")
    
    return collection
```

**주의**: 처음 실행 시 컬렉션이 비어있을 수 있습니다. 텍스트 데이터를 먼저 임베딩해야 합니다!

---

### Step 4: 임베딩 생성 (_create_embedding)

**목표**: 텍스트 → 벡터 변환

```python
def _create_embedding(self, text: str) -> list:
    try:
        response = self.client.embeddings.create(
            input=[text],
            model="text-embedding-3-large"
        )
        
        embedding = response.data[0].embedding
        
        print(f"[Embedding] 생성 완료 (차원: {len(embedding)})")
        
        return embedding
        
    except Exception as e:
        print(f"[ERROR] Embedding 생성 실패: {e}")
        raise
```

**테스트**:
```python
embedding = chatbot._create_embedding("안녕하세요")
print(len(embedding))  # 3072
print(embedding[:5])   # [0.12, -0.34, ...]
```

---

### Step 5: RAG 검색 (_search_similar) ⭐ 핵심!

**목표**: 유사 문서 찾기

```python
def _search_similar(self, query: str, threshold: float = 0.45, top_k: int = 5):
    print(f"\n[RAG] 검색 시작: '{query}'")
    
    try:
        # 1. 쿼리 임베딩 생성
        query_embedding = self._create_embedding(query)
        
        # 2. ChromaDB 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )
        
        # 3. 결과 확인
        if not results["documents"] or not results["documents"][0]:
            print("[RAG] 검색 결과 없음")
            return None, None, None
        
        documents = results["documents"][0]
        distances = results["distances"][0]
        metadatas = results["metadatas"][0]
        
        # 4. 유사도 계산 및 필터링
        best_doc = None
        best_similarity = 0
        best_meta = None
        
        for doc, dist, meta in zip(documents, distances, metadatas):
            # 거리 → 유사도 변환
            similarity = 1 / (1 + dist)
            
            print(f"[RAG] 문서: {doc[:50]}... | 유사도: {similarity:.4f}")
            
            # Threshold 체크
            if similarity >= threshold and similarity > best_similarity:
                best_doc = doc
                best_similarity = similarity
                best_meta = meta
        
        # 5. 결과 반환
        if best_doc:
            print(f"[RAG] ✅ 선택: 유사도 {best_similarity:.4f}")
            return best_doc, best_similarity, best_meta
        else:
            print(f"[RAG] ❌ Threshold({threshold}) 이상 없음")
            return None, None, None
            
    except Exception as e:
        print(f"[ERROR] RAG 검색 실패: {e}")
        return None, None, None
```

**Threshold 선택 가이드**:
- `0.3`: 매우 느슨 (많은 결과)
- `0.45`: **추천** (적절한 균형)
- `0.6`: 엄격 (정확한 매칭만)
- `0.8`: 매우 엄격 (거의 동일한 것만)

---

### Step 6: 프롬프트 구성 (_build_prompt)

**목표**: LLM에 보낼 최종 프롬프트 생성

```python
def _build_prompt(self, user_message: str, context: str = None, username: str = "사용자"):
    # 1. 시스템 프롬프트
    system_prompt = self.config.get('system_prompt', {}).get('base', '')
    rules = self.config.get('system_prompt', {}).get('rules', [])
    
    prompt = system_prompt
    
    # 2. 규칙 추가
    if rules:
        prompt += "\n\n[대화 규칙]\n"
        for rule in rules:
            prompt += f"- {rule}\n"
    
    # 3. RAG 컨텍스트 (있으면)
    if context:
        prompt += f"\n\n[참고 정보]\n{context}\n"
    
    # 4. 사용자 메시지
    prompt += f"\n\n{username}: {user_message}\n"
    
    return prompt
```

**예시 출력**:
```
당신은 서강대 선배입니다.
신입생들에게 학교 생활을 알려주세요.

[대화 규칙]
- 친근하게 반말로 대화하세요
- 구체적인 정보를 제공하세요

[참고 정보]
학식은 곤자가가 맛있어. 돈까스가 인기야.

사용자: 학식 추천해줘
```

---

### Step 7: 응답 생성 (generate_response) ⭐⭐ 통합!

**목표**: 모든 단계를 통합하여 최종 응답 생성

```python
def generate_response(self, user_message: str, username: str = "사용자") -> dict:
    print(f"\n{'='*60}")
    print(f"[USER] {username}: {user_message}")
    
    try:
        # 1. 초기 메시지 처리
        if user_message.strip().lower() == "init":
            bot_name = self.config.get('name', '챗봇')
            greeting = f"안녕! 나는 {bot_name}이야. 뭐 궁금한 거 있어?"
            
            # 메모리 저장
            self.memory.save_context(
                {"input": ""},
                {"output": greeting}
            )
            
            return {'reply': greeting, 'image': None}
        
        # 2. RAG 검색
        context, similarity, metadata = self._search_similar(
            query=user_message,
            threshold=0.45,
            top_k=5
        )
        
        has_context = (context is not None)
        
        # 3. 프롬프트 구성
        prompt = self._build_prompt(
            user_message=user_message,
            context=context,
            username=username
        )
        
        # 4. LLM API 호출
        print(f"[LLM] API 호출 중...")
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.config.get('system_prompt', {}).get('base', '')},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        reply = response.choices[0].message.content
        
        print(f"[LLM] 응답 완료: {reply[:50]}...")
        
        # 5. 메모리 저장
        self.memory.save_context(
            {"input": user_message},
            {"output": reply}
        )
        
        # 6. 응답 반환
        print(f"{'='*60}\n")
        
        return {
            'reply': reply,
            'image': None  # TODO: 이미지 검색 로직 추가 가능
        }
        
    except Exception as e:
        print(f"[ERROR] 응답 생성 실패: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'reply': "죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.",
            'image': None
        }
```

---

## 🧪 테스트 방법

### 1. 로컬 테스트

```bash
# 파일 직접 실행
python services/chatbot_service.py
```

### 2. Docker 테스트

```bash
docker-compose up
# http://localhost:5001 접속
```

### 3. 디버깅 로그 확인

```python
# chatbot_service.py에서 로그 추가
print(f"[DEBUG] Embedding: {embedding[:3]}...")
print(f"[DEBUG] Similarity: {similarity:.4f}")
print(f"[DEBUG] Context: {context}")
```

---

## 💡 확장 아이디어

### 1. 이미지 검색 추가

```python
def _search_similar_image(self, query: str):
    # 이미지 임베딩 DB에서 검색
    # 유사한 이미지 경로 반환
    pass
```

### 2. 한국어 키워드 추출

```python
def _extract_keywords(self, text: str):
    from konlpy.tag import Okt
    okt = Okt()
    nouns = okt.nouns(text)
    return nouns
```

### 3. 감정 분석

```python
def _analyze_emotion(self, text: str):
    # 사용자 감정 파악
    # 감정에 맞는 응답 생성
    pass
```

---

## 🐛 자주 발생하는 오류

### 1. "OPENAI_API_KEY not found"

**원인**: `.env` 파일이 없거나 API 키가 없음  
**해결**:
```bash
cp .env.example .env
# .env 파일에 API 키 입력
```

### 2. "Collection not found"

**원인**: ChromaDB에 데이터가 없음  
**해결**: 텍스트 데이터를 먼저 임베딩해야 함 (별도 스크립트 필요)

### 3. "Rate limit exceeded"

**원인**: OpenAI API 호출 제한 초과  
**해결**: 
- API 키 확인
- 요청 속도 줄이기
- 상위 플랜 구매

---

## 📊 성능 최적화

### 1. Embedding 캐싱

```python
# 동일한 쿼리는 캐싱
self.embedding_cache = {}

def _create_embedding(self, text: str):
    if text in self.embedding_cache:
        return self.embedding_cache[text]
    
    embedding = ...  # OpenAI API 호출
    self.embedding_cache[text] = embedding
    return embedding
```

### 2. Batch Processing

```python
# 여러 텍스트 한 번에 임베딩
texts = ["안녕", "학식", "도서관"]
embeddings = self.client.embeddings.create(
    input=texts,
    model="text-embedding-3-large"
)
```

---

## 🎓 다음 단계

1. ✅ `chatbot_service.py` 구현 완료
2. 텍스트 데이터 준비 및 임베딩
3. Docker로 테스트
4. Vercel 배포

**참고 문서**:
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 구조
- [ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md) - 전체 워크플로우
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker 사용법