# 🔧 리팩토링 가이드

## 📌 현재 상태

### 파일 크기
- `chatbot_service.py`: 1890줄 (❌ 너무 큼)
- 모든 로직이 하나의 파일에 집중

### 문제점
1. **유지보수 어려움**: 특정 기능 찾기 힘듦
2. **테스트 어려움**: 단위 테스트 불가능
3. **협업 어려움**: 동시 수정 시 충돌
4. **가독성**: 스크롤 지옥

---

## ✅ 리팩토링 완료 모듈

### 1. `session_manager.py` (240줄)
```python
from services.session_manager import PostOfficeSession, SessionPersistence

# 사용 예시
session = PostOfficeSession("유저")
persistence = SessionPersistence(BASE_DIR)
persistence.save(session)
```

### 2. `rag_manager.py` (200줄)
```python
from services.rag_manager import RAGManager

# 사용 예시
rag = RAGManager(BASE_DIR, openai_client, cache, debug=True)
rag.init_counseling_vectordb()
results = rag.search_counseling("불안해요", top_k=3)
```

### 3. `counseling_utils.py` (100줄)
```python
from services.counseling_utils import detect_crisis, detect_counseling_need

# 사용 예시
if detect_crisis("죽고싶어"):
    # 위기 대응
```

### 4. `prompt_builder.py` (100줄)
```python
from services.prompt_builder import build_counseling_context, build_user_prompt

# 사용 예시
context = build_counseling_context(knowledge, is_crisis=True)
user_prompt = build_user_prompt("죽고싶어", session, rag_results)
```

---

## 🎯 목표 구조

### Before (현재)
```
chatbot_service.py (1890줄)
├── PostOfficeSession 클래스 (100줄)
├── RAG 초기화 (200줄)
├── RAG 검색 (150줄)
├── 프롬프트 생성 (300줄)
├── Phase 처리 (1000줄)
└── 유틸리티 (140줄)
```

### After (목표)
```
chatbot_service.py (500줄) ⭐
├── import 모듈들
├── ChatbotService.__init__
├── generate_response (Phase 라우팅만)
└── 핵심 비즈니스 로직

session_manager.py (240줄)
rag_manager.py (200줄)
prompt_builder.py (100줄)
counseling_utils.py (100줄)
```

**총 줄 수는 비슷하지만 구조화됨!**

---

## 🚀 마이그레이션 계획 (3단계)

### Phase 1: 모듈 검증 (현재 완료 ✅)
- [x] 모듈 파일 생성
- [ ] import 테스트
- [ ] 기본 동작 확인

### Phase 2: 점진적 교체
- [ ] `chatbot_service.py`에서 새 모듈 import
- [ ] 한 번에 하나씩 교체
- [ ] 각 단계마다 테스트

### Phase 3: 정리
- [ ] 중복 코드 제거
- [ ] 문서화
- [ ] 최종 테스트

---

## 🔧 빠른 적용 (10분)

현재 작동하는 코드를 유지하면서 import만 추가:

```python
# chatbot_service.py 상단에 추가
from .session_manager import PostOfficeSession, SessionPersistence
from .rag_manager import RAGManager
from .counseling_utils import (
    detect_crisis, detect_counseling_need,
    normalize_intent_key, detect_reenter
)
from .prompt_builder import build_counseling_context

# 점진적으로 기존 함수를 새 모듈로 교체
```

---

## ⚠️ 주의사항

### 지금은 리팩토링하지 마세요!

**이유**:
1. RAG-D 구현이 방금 완성됨
2. 위기 대응이 작동 중
3. 배포 전 안정성 확보 우선

### 리팩토링 적기

- ✅ 배포 후
- ✅ 충분한 테스트 후
- ✅ 기능 추가가 필요할 때

---

## 📚 참고: 현재 chatbot_service.py 구조

```
Line 1-107: PostOfficeSession 클래스
Line 110-141: ChatbotService.__init__
Line 145-175: OpenAI 래퍼 함수
Line 178-230: Config & 세션 관리
Line 233-280: 유틸리티 (위기 감지 등)
Line 309-450: ChromaDB 초기화
Line 452-616: RAG 검색 함수들
Line 620-870: _get_session, 임베딩, 검색
Line 873-1450: Phase 처리 로직
Line 1450-1850: generate_response (핵심)
```

---

## 🎯 다음 단계 제안

### 지금 할 일
1. ✅ 현재 구현 테스트
2. ✅ 배포 준비
3. ✅ 사용자 피드백 수집

### 나중에 할 일 (배포 후)
1. 리팩토링 적용
2. 단위 테스트 작성
3. 성능 최적화

---

**현재는 작동하는 코드를 유지하고, 배포 후 리팩토링을 진행하는 것을 추천합니다!**

계속 리팩토링을 진행하시겠습니까, 아니면 배포 준비로 넘어가시겠습니까? 🚀
