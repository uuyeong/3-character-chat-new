# 📚 과제 수행 가이드

## 🎯 과제 목표

OpenAI API와 RAG(Retrieval-Augmented Generation)를 활용하여 캐릭터 챗봇을 개발하고 배포합니다.

---

## 📋 과제 개요

### 역할 분담

- **조원 A**: Repository Owner (Fork 및 배포 담당)
- **조원 B**: Contributor (기능 개발 담당)

### 제출물

1. 완성된 GitHub Repository
2. Vercel 배포 URL
3. README.md (프로젝트 설명)

---

## 🚀 워크플로우

### Phase 1: 저장소 준비 (조원 A)

#### 1-1. Organization 레포 Fork

```bash
# GitHub 웹에서 진행
1. https://github.com/hateslop/3-chatbot-project 접속
2. 우측 상단 "Fork" 버튼 클릭
3. 본인 계정으로 Fork
```

#### 1-2. 로컬에 Clone

```bash
git clone https://github.com/YOUR_USERNAME/3-chatbot-project.git
cd 3-chatbot-project
```

#### 1-3. 조원 B를 Collaborator로 추가

```
GitHub → Settings → Collaborators → Add people
```

---

### Phase 2: 환경 설정 (조원 A & B 공통)

#### 2-1. Docker 설치

- macOS/Windows: [Docker Desktop](https://www.docker.com/products/docker-desktop) 설치
- Linux: Docker Engine 설치

#### 2-2. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 편집기로 열어서 API 키 입력
nano .env
```

`.env` 파일 내용:

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

#### 2-3. Docker로 실행 확인

```bash
docker-compose up --build
```

브라우저에서 `http://localhost:5000` 접속하여 기본 템플릿 확인

---

## 📝 과제 수행 단계

### ✅ 수정하면 안 되는 파일 (템플릿)

```
🚫 절대 수정 금지
├── app.py                    # Flask 애플리케이션
├── templates/                # HTML 템플릿
│   ├── index.html
│   ├── detail.html
│   └── chat.html
├── static/js/chatbot.js      # JavaScript
├── Dockerfile                # Docker 설정
├── docker-compose.yml
└── vercel.json              # 배포 설정
```

### ✏️ 작성/수정해야 하는 파일 (과제)

```
📝 학생이 작성할 부분
├── config/
│   └── chatbot_config.json   # [필수] 챗봇 메타데이터
│
├── generation/chatbot/
│   └── chatbot.py            # [필수] RAG 로직 구현
│
├── static/data/chatbot/
│   ├── chardb_text/          # [필수] 텍스트 데이터
│   │   ├── character_info.txt
│   │   ├── dialogues.txt
│   │   └── background.txt
│   ├── build_db.py           # [필수] 임베딩 생성 스크립트
│   └── imagedb_text/         # [선택] 이미지 메타데이터
│       └── photo_data.json
│
├── static/images/chatbot/    # [필수] 챗봇 이미지
│   ├── thumbnail.png         # 1:1 비율
│   └── photo1.png, photo2.png, ...
│
└── static/videos/chatbot/    # [선택] 챗봇 비디오
    └── video.mp4
```

---

## 📋 Step-by-Step 과제 수행

### Step 1: 챗봇 설정 작성 (30분)

**파일**: `config/chatbot_config.json`

```json
{
  "name": "우리 챗봇 이름",
  "description": "챗봇에 대한 설명 4-5줄<br>캐릭터 특징을 드러내고<br>어떤 대화가 가능한지 설명",
  "tags": ["#태그1", "#태그2", "#태그3", "#태그4"],
  "thumbnail": "images/chatbot/thumbnail.png",
  "character": {
    "age": 20,
    "university": "서강대학교",
    "major": "컴퓨터공학과",
    "personality": "밝고 활발한 성격",
    "background": "신입생을 돕는 선배"
  },
  "system_prompt": {
    "base": "당신은 대학 신입생을 돕는 친절한 선배입니다.",
    "rules": [
      "반말을 사용하세요",
      "이모티콘을 사용하지 마세요",
      "친근하고 자연스럽게 대화하세요",
      "학생의 질문에 성심성의껏 답변하세요"
    ]
  }
}
```

**체크포인트**:

- [ ] 챗봇 이름 작성
- [ ] 설명 4-5줄 작성
- [ ] 태그 3-4개 작성
- [ ] 캐릭터 정보 작성
- [ ] 시스템 프롬프트 작성

---

### Step 2: 텍스트 데이터 준비 (1-2시간)

**폴더**: `static/data/chatbot/chardb_text/`

#### 2-1. 캐릭터 정보 작성

**파일**: `character_info.txt`

```
이름: 김서강
나이: 24세
학번: 20학번
전공: 컴퓨터공학과
특징: 신입생들에게 캠퍼스 생활을 알려주는 것을 좋아함
성격: 친절하고 유머러스함
취미: 코딩, 게임, 영화 감상

[캐릭터 배경]
김서강은 서강대학교 컴퓨터공학과 4학년 학생입니다.
신입생 때 선배들의 도움을 많이 받았기 때문에,
후배들에게도 같은 도움을 주고 싶어합니다.
학교 생활, 수강 신청, 동아리 활동 등
다양한 정보를 친절하게 알려줍니다.
```

#### 2-2. 대화 데이터 작성

**파일**: `dialogues.txt`

```
Q: 학식 추천해줘
A: 학식은 곤자가에서 먹는 게 제일 맛있어. 특히 돈까스가 인기 메뉴야!

Q: 도서관은 몇 시까지 열어?
A: 로욜라 도서관은 평일 오전 9시부터 밤 10시까지야.
   시험 기간엔 24시간 개방하는 열람실도 있어.

Q: 동아리 추천해줘
A: 관심사가 뭐야? 코딩이면 ICPC나 알고리즘 동아리 추천해.
   운동 좋아하면 축구, 농구 동아리도 좋고!

(20-30개 이상의 Q&A 작성)
```

**체크포인트**:

- [ ] character_info.txt 작성 (최소 200단어)
- [ ] dialogues.txt 작성 (최소 20개 Q&A)
- [ ] background.txt 작성 (선택)

---

### Step 3: 이미지 준비 (30분)

**폴더**: `static/images/chatbot/`

#### 3-1. 썸네일 이미지

- **파일명**: `thumbnail.png`
- **크기**: 1:1 비율 (예: 512x512px)
- **내용**: 챗봇 캐릭터를 대표하는 이미지

#### 3-2. 갤러리 이미지 (선택)

- **파일명**: `photo1.png`, `photo2.png`, ...
- **개수**: 5-10개 권장
- **내용**: 캐릭터 관련 이미지, 장면, 배경 등

**이미지 생성 방법**:

- AI 이미지 생성: Midjourney, DALL-E, Stable Diffusion
- 무료 이미지: Unsplash, Pexels
- 직접 제작: 캐릭터 디자인, 일러스트

**체크포인트**:

- [ ] thumbnail.png 준비 (1:1 비율)
- [ ] 갤러리 이미지 5개 이상 준비 (선택)

---

### Step 4: 임베딩 생성 스크립트 작성 (1-2시간)

**파일**: `static/data/chatbot/build_db.py`

```python
import os
import sys
import uuid
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from generation.chatbot.chatbot import get_embedding, init_text_db

def build_text_database():
    """텍스트 데이터를 읽고 임베딩을 생성하여 DB에 저장"""

    # DB 초기화
    _, collection = init_text_db()

    # 텍스트 파일 경로
    text_dir = Path(__file__).parent / "chardb_text"

    # 기존 데이터 삭제 (선택사항)
    # collection.delete(collection.get()['ids'])

    print("=" * 50)
    print("텍스트 임베딩 생성 시작")
    print("=" * 50)

    # 텍스트 파일 읽기 및 임베딩 생성
    for file_path in text_dir.glob("*.txt"):
        print(f"\n처리 중: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            print(f"  ⚠️  빈 파일, 건너뜀")
            continue

        # 큰 파일은 청크로 분할 (500자 단위)
        chunk_size = 500
        chunks = [content[i:i+chunk_size]
                 for i in range(0, len(content), chunk_size)]

        for i, chunk in enumerate(chunks):
            # 임베딩 생성
            embedding = get_embedding(chunk)

            # DB에 저장
            collection.add(
                documents=[chunk],
                embeddings=[embedding],
                ids=[str(uuid.uuid4())],
                metadatas=[{
                    "filename": file_path.name,
                    "source": "text",
                    "chunk_index": i
                }]
            )

            print(f"  ✓ 청크 {i+1}/{len(chunks)} 저장 완료 ({len(chunk)}자)")

    print("\n" + "=" * 50)
    print("임베딩 생성 완료!")
    print(f"총 {collection.count()}개의 문서가 저장되었습니다.")
    print("=" * 50)

if __name__ == "__main__":
    build_text_database()
```

**실행 방법**:

```bash
# Docker 컨테이너 내에서 실행
docker-compose exec chatbot python static/data/chatbot/build_db.py
```

**체크포인트**:

- [ ] build_db.py 작성
- [ ] 스크립트 실행하여 임베딩 생성
- [ ] 에러 없이 완료 확인

---

### Step 5: 챗봇 로직 구현 (3-4시간) ⭐ 핵심

**파일**: `generation/chatbot/chatbot.py`

이 파일은 이미 완성된 템플릿이 제공됩니다. 하지만 다음 부분을 **커스터마이징**해야 합니다:

#### 5-1. 시스템 프롬프트 수정

```python
def build_system_prompt(username, has_context=False):
    """설정 파일 기반 시스템 프롬프트 생성"""

    # ✏️ TODO: 캐릭터에 맞게 프롬프트 커스터마이징
    base_prompt = config.get('system_prompt', {}).get('base',
                                                       '당신은 친근한 챗봇입니다.')

    # 추가 규칙이나 제약사항을 여기에 작성
    # 예: "절대 욕설을 사용하지 마세요", "항상 존댓말을 사용하세요" 등

    ...
```

#### 5-2. RAG 검색 임계값 조정

```python
def search_similar_documents(query, collection, threshold=0.45, top_k=5):
    """유사 문서 검색 (RAG)"""

    # ✏️ TODO: threshold 값을 실험적으로 조정
    # 0.3-0.5 사이에서 테스트해보고 최적값 찾기
    # - 낮을수록: 더 많은 문서 검색 (정확도 낮음)
    # - 높을수록: 더 적은 문서 검색 (정확도 높음)

    ...
```

#### 5-3. 초기 인사말 수정

```python
if user_message.strip().lower() == "init":
    bot_name = config.get('name', '챗봇')

    # ✏️ TODO: 캐릭터에 맞는 초기 인사말 작성
    initial_reply = f"안녕하세요, {username}님! {bot_name}입니다. 무엇을 도와드릴까요?"

    # 예: "반가워, {username}! 나는 {bot_name}이야. 학교 생활에 대해 물어봐!"

    ...
```

**체크포인트**:

- [ ] 시스템 프롬프트 커스터마이징
- [ ] threshold 값 최적화
- [ ] 초기 인사말 작성
- [ ] 로컬에서 테스트

---

### Step 6: 테스트 (1시간)

#### 6-1. 로컬 테스트

```bash
# Docker로 실행
docker-compose up

# 브라우저에서 http://localhost:5000 접속
```

**테스트 체크리스트**:

- [ ] 메인 페이지에 챗봇 정보 표시
- [ ] 상세 페이지에서 이름 입력 가능
- [ ] 채팅 화면에서 대화 가능
- [ ] RAG가 정상 작동 (관련 답변 생성)
- [ ] 이미지 갤러리 표시
- [ ] 비디오 재생 (있는 경우)

#### 6-2. 챗봇 로직 직접 테스트

```bash
# Docker 컨테이너 내부 접속
docker-compose exec chatbot bash

# Python으로 직접 테스트
python generation/chatbot/chatbot.py

# 질문 입력하여 응답 확인
질문을 입력하세요(종료: quit): 안녕?
질문을 입력하세요(종료: quit): 학식 추천해줘
질문을 입력하세요(종료: quit): quit
```

---

### Step 7: Git 작업 (조원 B)

#### 7-1. 브랜치 생성

```bash
# A의 레포 Clone
git clone https://github.com/OWNER_A/3-chatbot-project.git
cd 3-chatbot-project

# Feature 브랜치 생성
git checkout -b feature/chatbot-implementation
```

#### 7-2. 작업 후 Commit

```bash
# 변경사항 확인
git status

# 스테이징
git add config/chatbot_config.json
git add generation/chatbot/chatbot.py
git add static/data/chatbot/
git add static/images/chatbot/

# 커밋
git commit -m "feat: 챗봇 로직 구현 및 데이터 추가

- config: 챗봇 메타데이터 작성
- generation: RAG 로직 구현
- data: 텍스트 데이터 및 임베딩 생성
- images: 썸네일 및 갤러리 이미지 추가"

# 푸시
git push origin feature/chatbot-implementation
```

#### 7-3. Pull Request 생성

```
1. GitHub에서 "Compare & pull request" 클릭
2. 제목: "챗봇 구현 완료"
3. 설명:
   - 구현한 기능
   - 테스트 결과
   - 스크린샷
4. Create Pull Request
```

#### 7-4. 코드 리뷰 (조원 A)

- 코드 검토
- 테스트 확인
- 승인 후 Merge

---

### Step 8: 배포 (조원 A)

#### 8-1. Vercel 배포

```bash
1. https://vercel.com 접속
2. GitHub 계정으로 로그인
3. "New Project" 클릭
4. GitHub 레포 선택
5. Environment Variables 설정:
   - OPENAI_API_KEY: API 키 입력
6. Deploy 클릭
```

#### 8-2. 배포 확인

```
https://your-project.vercel.app 접속
/health 엔드포인트 확인
```

---

## 📊 평가 기준

### 필수 요구사항 (80점)

- [ ] 챗봇 설정 파일 작성 (10점)
- [ ] 텍스트 데이터 준비 (20점)
- [ ] 임베딩 생성 (15점)
- [ ] 챗봇 로직 구현 (25점)
- [ ] 정상 동작 (10점)

### 추가 점수 (20점)

- [ ] 이미지 갤러리 (5점)
- [ ] 비디오 추가 (5점)
- [ ] 고급 RAG 기법 사용 (5점)
- [ ] UI/UX 개선 (5점)

### 협업 (보너스 10점)

- [ ] 체계적인 Git 사용
- [ ] 의미있는 커밋 메시지
- [ ] Pull Request 활용
- [ ] 코드 리뷰 수행

---

## 💡 팁 & 주의사항

### 꿀팁

1. **데이터가 핵심**: 양질의 텍스트 데이터가 좋은 챗봇을 만듭니다
2. **작은 단위로 테스트**: 한 번에 모든 기능을 구현하지 말고 단계별로
3. **로그 확인**: 터미널에서 RAG 검색 결과를 확인하며 디버깅
4. **threshold 조정**: 0.3~0.5 사이에서 실험하며 최적값 찾기
5. **Git 자주 커밋**: 작은 단위로 자주 커밋하여 히스토리 관리

### 주의사항

⚠️ **절대 수정하면 안 되는 파일**

- `app.py`
- `templates/` 폴더
- `static/js/chatbot.js`
- `Dockerfile`, `docker-compose.yml`

⚠️ **API 키 관리**

- `.env` 파일은 절대 Git에 커밋하지 말 것
- GitHub에 Push하기 전에 `.gitignore` 확인

⚠️ **ChromaDB 데이터**

- `chardb_embedding/` 폴더도 Git에 커밋하지 않음
- 임베딩은 각자 로컬에서 생성

---

## 🆘 문제 해결

### Q: Docker가 실행되지 않아요

```bash
# Docker Desktop이 실행 중인지 확인
# macOS: 상단 메뉴바에 Docker 아이콘 확인

# Docker 재시작
docker-compose down
docker-compose up --build
```

### Q: OpenAI API 오류가 나요

```bash
# API 키 확인
cat .env

# API 키가 올바른지 확인
# https://platform.openai.com/api-keys

# 환경변수 다시 로드
docker-compose down
docker-compose up
```

### Q: RAG가 제대로 작동하지 않아요

```bash
# 임베딩이 생성되었는지 확인
ls static/data/chatbot/chardb_embedding/

# 임베딩 재생성
docker-compose exec chatbot python static/data/chatbot/build_db.py

# threshold 값 조정 (generation/chatbot/chatbot.py)
threshold=0.3  # 더 많은 문서 검색
threshold=0.5  # 더 적은 문서 검색
```

### Q: 답변이 이상해요

```bash
# 1. 시스템 프롬프트 확인 (config/chatbot_config.json)
# 2. 텍스트 데이터 품질 확인 (static/data/chatbot/chardb_text/)
# 3. RAG 로그 확인 (터미널에서 검색 결과 확인)
# 4. Temperature 조정 (generation/chatbot/chatbot.py에서 0.7 → 0.5로 변경)
```

---

## 📚 참고 자료

- [OpenAI API 문서](https://platform.openai.com/docs)
- [LangChain 문서](https://python.langchain.com/)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [Docker 문서](https://docs.docker.com/)
- [Git 사용법](https://git-scm.com/book/ko/v2)

---

## 📞 도움말

문제가 생기면:

1. 터미널 로그 확인
2. ASSIGNMENT_GUIDE.md 문제 해결 섹션 확인
3. 조원과 상의
4. 교수님/TA에게 질문

**과제 화이팅! 🚀**

