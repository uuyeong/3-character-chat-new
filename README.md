# 🤖 캐릭터 챗봇 프로젝트 템플릿

> OpenAI API와 RAG(Retrieval-Augmented Generation)를 활용한 대화형 AI 챗봇 프로젝트 템플릿

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## ⚡ 5분 빠른 시작

```bash
# 1. Fork & Clone
git clone https://github.com/YOUR_USERNAME/3-chatbot-project.git
cd 3-chatbot-project

# 2. .env 파일 생성 및 API 키 입력
cp .env.example .env
nano .env  # OPENAI_API_KEY 입력

# 3. Docker 실행
docker-compose up --build

# 4. http://localhost:5001 접속
```

**상세 가이드**: [GETTING_STARTED.md](GETTING_STARTED.md) ⭐

---

## 📚 문서 가이드

이 프로젝트는 여러 가이드 문서를 제공합니다. 목적에 맞게 선택하세요:

| 문서 | 대상 | 내용 | 읽는 순서 |
|------|------|------|----------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** ⭐ | 👨‍🎓 학생 | 5분 빠른 시작 가이드 | 1️⃣ 필독! |
| **[START_HERE.md](START_HERE.md)** | 👨‍🎓 학생 | 프로젝트 소개 및 FAQ | 2️⃣ |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** ⭐⭐ | 👨‍🎓 학생 | 시스템 아키텍처 (필독!) | 3️⃣ |
| **[ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md)** | 👨‍🎓 학생 | 과제 수행 완전 가이드 | 4️⃣ |
| **[IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)** ⭐ | 👨‍🎓 학생 | AI 로직 구현 상세 가이드 (핵심!) | 5️⃣ |
| **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** | 🐳 모두 | Docker 사용 완전 가이드 | (참고) |

---

## 🎯 프로젝트 개요

### 핵심 기능

- 🤖 OpenAI GPT 기반 대화 생성
- 📚 RAG (Retrieval-Augmented Generation)를 통한 지식 기반 답변
- 💾 ChromaDB를 활용한 임베딩 벡터 저장
- 🧠 LangChain 기반 대화 메모리 관리
- 🔍 KoNLPy를 이용한 한국어 키워드 추출
- 🎨 Vanilla JavaScript 기반 웹 인터페이스
- 🐳 Docker를 통한 환경 일관성 보장

### 기술 스택

- **Backend**: Flask (Python 3.11)
- **AI/ML**: OpenAI API, LangChain, ChromaDB
- **Frontend**: Vanilla JavaScript, HTML, CSS
- **NLP**: KoNLPy (한국어 처리)
- **Deployment**: Docker, Vercel
- **Version Control**: Git, GitHub

---

## 🚀 빠른 시작

### 필수 준비물

- ✅ Docker Desktop (권장) 또는 Python 3.11+
- ✅ OpenAI API 키
- ✅ Git

### 1. 레포지토리 Fork & Clone

```bash
# GitHub에서 Fork 후 Clone
git clone https://github.com/YOUR_USERNAME/3-chatbot-project.git
cd 3-chatbot-project
```

### 2. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 편집기로 열어서 API 키 입력
nano .env
```

`.env` 파일:

```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxx
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
```

### 3-A. Docker로 실행 (강력 권장 ⭐)

```bash
# 빌드 및 실행
docker-compose up --build

# 브라우저에서 접속
open http://localhost:5000
```

**Docker 사용의 장점:**

- ✅ 환경 일관성 100% 보장
- ✅ Java, Python 등 모든 의존성 자동 설치
- ✅ 3개 명령어로 즉시 실행 가능
- 📖 자세한 내용: [DOCKER_GUIDE.md](DOCKER_GUIDE.md)

### 3-B. 로컬 Python으로 실행

<details>
<summary>펼쳐보기 (권장하지 않음)</summary>

```bash
# 1. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Java 설치 (KoNLPy용)
# macOS:
brew install openjdk@11

# Ubuntu:
sudo apt-get install default-jdk

# Windows:
# https://www.oracle.com/java/technologies/downloads/

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 실행
python app.py

# 5. 브라우저에서 http://localhost:5000 접속
```

</details>

---

## 📁 프로젝트 구조

```
3-chatbot-project/
│
├── 📄 과제 수행 가이드
│   ├── ASSIGNMENT_GUIDE.md      ⭐ 학생 필독!
│   ├── WORKFLOW_TEST.md          (교수/TA용)
│   ├── DOCKER_GUIDE.md
│   └── REFACTORING_SUMMARY.md
│
├── 🐳 Docker 설정
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── ⚙️ 환경 설정
│   ├── .env.example              (예제)
│   ├── .env                      (실제, Git에 포함 안됨)
│   ├── .gitignore
│   ├── vercel.json               (Vercel 배포용)
│   └── requirements.txt          (Python 의존성)
│
├── 🔧 설정 파일 (✏️ 수정 필요)
│   └── config/
│       └── chatbot_config.json   ✏️ 챗봇 메타데이터
│
├── 🚀 애플리케이션 (🚫 수정 금지)
│   ├── app.py                    🚫 Flask 앱
│   ├── templates/                🚫 HTML 템플릿
│   │   ├── index.html
│   │   ├── detail.html
│   │   └── chat.html
│   └── static/
│       ├── css/style.css         🚫
│       └── js/chatbot.js         🚫
│
├── 🤖 챗봇 로직 (✏️ 일부 커스터마이징)
│   └── generation/chatbot/
│       └── chatbot.py            ✏️ RAG 로직 (주석 참고)
│
└── 📦 데이터 & 에셋 (✏️ 작성 필요)
    └── static/
        ├── data/chatbot/         ✏️ 텍스트 데이터 & 임베딩
        │   ├── chardb_text/      ✏️ 텍스트 파일 작성
        │   ├── build_db.py       ✏️ 임베딩 생성 스크립트
        │   └── imagedb_text/     (선택)
        ├── images/chatbot/       ✏️ 썸네일 & 갤러리 이미지
        └── videos/chatbot/       (선택) 비디오 파일

✏️ = 학생이 작성/수정해야 하는 파일
🚫 = 절대 수정하면 안 되는 파일 (템플릿)
```

---

## 📝 과제 수행 단계

### 1️⃣ 설정 파일 작성 (30분)

`config/chatbot_config.json`:

```json
{
  "name": "우리 챗봇 이름",
  "description": "챗봇 설명 4-5줄",
  "tags": ["#태그1", "#태그2", "#태그3"],
  "thumbnail": "images/chatbot/thumbnail.png",
  "character": {
    "age": 20,
    "university": "대학교명",
    "major": "전공",
    "personality": "성격",
    "background": "배경 스토리"
  },
  "system_prompt": {
    "base": "당신의 챗봇 페르소나",
    "rules": ["반말을 사용하세요", "이모티콘을 사용하지 마세요"]
  }
}
```

### 2️⃣ 텍스트 데이터 준비 (1-2시간)

`static/data/chatbot/chardb_text/` 폴더에 텍스트 파일 작성:

- `character_info.txt`: 캐릭터 정보
- `dialogues.txt`: 대화 데이터 (Q&A 20개 이상)
- `background.txt`: 배경 스토리 (선택)

### 3️⃣ 이미지 준비 (30분)

`static/images/chatbot/` 폴더에 이미지 추가:

- `thumbnail.png`: 1:1 비율 썸네일
- `photo1.png`, `photo2.png`, ...: 갤러리 이미지 (선택)

### 4️⃣ 임베딩 생성 (15분)

```bash
# build_db.py 스크립트 작성 후 실행
docker-compose exec chatbot python static/data/chatbot/build_db.py
```

### 5️⃣ 챗봇 로직 구현 (3-4시간) ⭐ **핵심!**

`services/chatbot_service.py`에서 7개 메서드 구현:

```python
class ChatbotService:
    def __init__()              # 1. 초기화
    def _load_config()          # 2. 설정 로드
    def _init_chromadb()        # 3. DB 연결
    def _create_embedding()     # 4. 임베딩 생성
    def _search_similar()       # 5. RAG 검색 ⭐ 핵심!
    def _build_prompt()         # 6. 프롬프트 설계
    def generate_response()     # 7. 응답 생성 ⭐⭐ 통합!
```

**상세 가이드**: [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md)

### 6️⃣ 테스트 (30분)

```bash
# 로컬 실행
docker-compose up

# 브라우저에서 http://localhost:5000
# 채팅 테스트
```

### 7️⃣ 배포 (20분)

#### Vercel 배포

```bash
1. https://vercel.com 접속
2. GitHub로 로그인
3. 프로젝트 Import
4. Environment Variables 설정
   - OPENAI_API_KEY 입력
5. Deploy
```

**자세한 단계**: [ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md) 참고

---

## 🧪 테스트

### 헬스체크

```bash
curl http://localhost:5000/health
# 응답: {"status":"ok","chatbot":"챗봇이름"}
```

### 챗봇 직접 테스트

```bash
# Docker 컨테이너 접속
docker-compose exec chatbot bash

# Python 대화형 모드
python generation/chatbot/chatbot.py

# 질문 입력
질문을 입력하세요(종료: quit): 안녕?
질문을 입력하세요(종료: quit): quit
```

---

## 👥 팀 협업 워크플로우

### 조원 A (Repository Owner)

1. Organization 레포 Fork
2. 로컬에 Clone
3. Collaborator 추가 (조원 B)
4. 조원 B의 Pull Request 리뷰
5. Merge 후 배포

### 조원 B (Contributor)

1. 조원 A의 레포 Clone
2. Feature 브랜치 생성
3. 과제 수행
4. Commit & Push
5. Pull Request 생성
6. 코드 리뷰 반영 후 Merge

**자세한 워크플로우**: [ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md#-step-by-step-과제-수행)

---

## 🔧 트러블슈팅

### Q: Docker가 실행되지 않아요

```bash
# Docker Desktop이 실행 중인지 확인
# macOS: 상단 메뉴바에 Docker 아이콘

# Docker 재시작
docker-compose down
docker-compose up --build
```

### Q: OpenAI API 오류

```bash
# .env 파일 확인
cat .env

# API 키가 올바른지 확인
# https://platform.openai.com/api-keys
```

### Q: RAG가 작동하지 않아요

```bash
# 임베딩 파일 확인
ls static/data/chatbot/chardb_embedding/

# 없으면 재생성
docker-compose exec chatbot python static/data/chatbot/build_db.py
```

**더 많은 문제 해결**: [ASSIGNMENT_GUIDE.md#-문제-해결](ASSIGNMENT_GUIDE.md#-문제-해결)

---

## 📚 API 문서

### `/` - 메인 페이지

챗봇 정보 표시

### `/detail` - 상세 페이지

챗봇 소개 및 이름 입력

### `/chat` - 채팅 화면

실시간 대화

### `/api/chat` - 챗봇 API

**Method**: `POST`  
**Body**:

```json
{
  "message": "안녕하세요",
  "username": "사용자"
}
```

**Response**:

```json
{
  "reply": "안녕하세요! 무엇을 도와드릴까요?"
}
```

### `/health` - 헬스체크

**Method**: `GET`  
**Response**:

```json
{
  "status": "ok",
  "chatbot": "챗봇이름"
}
```

---

## 🌟 주요 기능

### 1. RAG (Retrieval-Augmented Generation)

- ChromaDB를 사용한 벡터 데이터베이스
- 텍스트 유사도 기반 문서 검색
- 관련 정보를 활용한 정확한 답변 생성

### 2. 대화 메모리

- LangChain의 ConversationSummaryBufferMemory 사용
- 대화 맥락 유지
- 자연스러운 다회차 대화

### 3. 한국어 처리

- KoNLPy를 이용한 명사 추출
- 키워드 기반 검색 최적화

### 4. 확장성

- 쉬운 설정 변경 (JSON)
- 모듈화된 코드 구조
- Docker를 통한 배포 간소화

---

## 📖 참고 자료

### 공식 문서

- [OpenAI API 문서](https://platform.openai.com/docs)
- [LangChain 문서](https://python.langchain.com/)
- [ChromaDB 문서](https://docs.trychroma.com/)
- [Flask 문서](https://flask.palletsprojects.com/)
- [Docker 문서](https://docs.docker.com/)

### 학습 자료

- [RAG 개념](https://www.pinecone.io/learn/retrieval-augmented-generation/)
- [프롬프트 엔지니어링](https://www.promptingguide.ai/)
- [Git 협업 가이드](https://git-scm.com/book/ko/v2)

---

## 🤝 기여

이 프로젝트는 교육용 템플릿입니다.  
문제를 발견하거나 개선 아이디어가 있다면 Issue나 Pull Request를 생성해주세요.

---

## 📄 라이선스

MIT License

---

## 👨‍💻 제작

**HateSlop Organization**  
OpenAI API와 RAG를 활용한 캐릭터 챗봇 프로젝트

---

## 🎓 교육용 안내

이 프로젝트는 다음을 학습하기 위한 템플릿입니다:

- ✅ OpenAI API 활용
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ 벡터 데이터베이스 (ChromaDB)
- ✅ 프롬프트 엔지니어링
- ✅ Flask 웹 개발
- ✅ Docker 컨테이너화
- ✅ Git/GitHub 협업
- ✅ Vercel 배포

---

<div align="center">

**Made with ❤️ by HateSlop**

[![GitHub](https://img.shields.io/badge/GitHub-HateSlop-black?logo=github)](https://github.com/hateslop)

</div>
