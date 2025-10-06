# 🚀 여기서 시작하세요!

> 이 문서는 프로젝트를 처음 접하는 분들을 위한 간단한 시작 가이드입니다.

---

## 👤 당신은 누구인가요?

### 🎓 학생 (과제 수행자)

➡️ **[ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md)를 읽어주세요**

이 문서에는 다음이 포함되어 있습니다:

- ✅ 과제 수행 완전 가이드
- ✅ Step-by-Step 튜토리얼
- ✅ 코드 작성 예제
- ✅ 체크리스트
- ✅ 문제 해결 가이드

**예상 소요 시간**: 4-6시간

---

### 👨‍🏫 교수님 / TA (과제 관리자)

➡️ **[WORKFLOW_TEST.md](WORKFLOW_TEST.md)를 읽어주세요**

이 문서에는 다음이 포함되어 있습니다:

- ✅ 학생 워크플로우 시뮬레이션
- ✅ 테스트 시나리오
- ✅ 예상 문제점 및 해결책
- ✅ 평가 체크리스트

**예상 소요 시간**: 1-2시간

---

### 🐳 Docker 처음 사용자

➡️ **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)를 읽어주세요**

이 문서에는 다음이 포함되어 있습니다:

- ✅ Docker 소개 및 설치
- ✅ 명령어 레퍼런스
- ✅ 트러블슈팅
- ✅ 60+ 섹션의 완전 가이드

---

## ⚡ 5분 빠른 시작

Docker가 설치되어 있다면:

```bash
# 1. Clone (또는 Fork 후 Clone)
git clone https://github.com/YOUR_USERNAME/3-chatbot-project.git
cd 3-chatbot-project

# 2. 환경변수 설정
cp .env.example .env
nano .env  # OPENAI_API_KEY 입력

# 3. 실행
docker-compose up --build

# 4. 브라우저에서 http://localhost:5000 접속
```

---

## 📋 프로젝트 구조 한눈에 보기

```
3-chatbot-project/
│
├── 📚 가이드 문서
│   ├── START_HERE.md              ⭐ 지금 보고 있는 문서
│   ├── ASSIGNMENT_GUIDE.md        ⭐ 학생용 완전 가이드
│   ├── IMPLEMENTATION_GUIDE.md    ⭐ AI 로직 구현 가이드 (핵심!)
│   ├── WORKFLOW_TEST.md            (교수/TA용)
│   ├── DOCKER_GUIDE.md             (Docker 가이드)
│   └── README.md                   (프로젝트 개요)
│
├── 🔧 수정/작성해야 하는 파일 (✏️ 학생 작업)
│   ├── config/chatbot_config.json        ✏️ 챗봇 설정
│   ├── generation/chatbot/chatbot.py     ✏️ TODO 주석 부분만
│   ├── static/data/chatbot/chardb_text/  ✏️ 텍스트 데이터
│   ├── static/data/chatbot/build_db.py   ✏️ 임베딩 생성
│   ├── static/images/chatbot/            ✏️ 이미지
│   └── static/videos/chatbot/            ✏️ 비디오 (선택)
│
└── 🚫 절대 수정하지 마세요 (템플릿)
    ├── app.py                            🚫 Flask 앱
    ├── templates/                        🚫 HTML
    ├── static/js/chatbot.js              🚫 JavaScript
    ├── Dockerfile                        🚫 Docker 설정
    └── docker-compose.yml                🚫 Docker 설정
```

---

## 🎯 핵심 개념

### 1. 이 프로젝트는 무엇인가요?

OpenAI API와 RAG(지식 기반 검색)를 활용한 캐릭터 챗봇입니다.

### 2. RAG란?

**R**etrieval **A**ugmented **G**eneration

- 미리 준비한 문서에서 관련 정보를 검색
- 검색된 정보를 바탕으로 AI가 답변 생성
- 더 정확하고 맥락에 맞는 답변 가능

### 3. 무엇을 만들어야 하나요?

- 챗봇 캐릭터 설정 (JSON)
- 텍스트 지식 데이터 (TXT)
- 썸네일 이미지
- 챗봇 로직 일부 커스터마이징

### 4. Docker가 왜 필요한가요?

- 모든 팀원이 동일한 환경에서 작업
- Python, Java 등 자동 설치
- "내 컴퓨터에서는 되는데..." 문제 해결

---

## 🎓 학습 목표

이 과제를 통해 다음을 배웁니다:

### AI/ML

- ✅ OpenAI API 사용법
- ✅ RAG (검색 기반 생성) 개념
- ✅ 임베딩과 벡터 데이터베이스
- ✅ 프롬프트 엔지니어링

### 백엔드

- ✅ Flask 웹 프레임워크
- ✅ RESTful API 설계
- ✅ 환경변수 관리

### 프론트엔드

- ✅ Vanilla JavaScript
- ✅ 비동기 통신 (fetch API)
- ✅ DOM 조작

### 개발 도구

- ✅ Docker 컨테이너화
- ✅ Git/GitHub 협업
- ✅ Vercel 배포

---

## ❓ 자주 묻는 질문

### Q: 처음부터 다 코딩해야 하나요?

**A**: 아니요! 템플릿이 거의 완성되어 있습니다.

- 설정 파일 작성 (JSON)
- 텍스트 데이터 작성 (TXT)
- TODO 주석 부분만 코딩 (Python)

### Q: 팀 프로젝트인가요?

**A**: 네, 2인 1조입니다.

- 조원 A: Repository Owner
- 조원 B: Contributor
- Git으로 협업

### Q: 어떤 캐릭터를 만들 수 있나요?

**A**: 자유롭게 선택!

- 대학 선배 챗봇
- 특정 분야 전문가
- 유명인 페르소나
- 창작 캐릭터

### Q: 프로그래밍 경험이 없는데 가능한가요?

**A**: 가능합니다!

- 대부분 설정 파일 작성
- Step-by-Step 가이드 제공
- 예제 코드 제공

### Q: 비용이 드나요?

**A**: OpenAI API 사용료만 발생

- 개발 단계: 약 $1-2
- 무료 크레딧 활용 가능

---

## 🆘 도움이 필요하면?

### 1. 가이드 문서 확인

- [ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md) - 완전 가이드
- [DOCKER_GUIDE.md](DOCKER_GUIDE.md) - Docker 문제 해결

### 2. 로그 확인

```bash
# Docker 로그 보기
docker-compose logs -f
```

### 3. 터미널 에러 메시지 확인

- 에러 메시지를 Google에 검색
- ASSIGNMENT_GUIDE.md의 문제 해결 섹션 참고

### 4. 조원과 상의

- 2인 1조 협업 프로젝트
- 서로 도우며 해결

### 5. 교수님/TA에게 질문

- 위 단계를 모두 시도한 후
- 에러 메시지와 스크린샷 첨부

---

## ✅ 시작하기 전 체크리스트

- [ ] Docker Desktop 설치 완료
- [ ] GitHub 계정 있음
- [ ] OpenAI API 키 발급 완료
- [ ] 텍스트 편집기 준비 (VS Code 권장)
- [ ] Git 기본 명령어 숙지
- [ ] 조원과 역할 분담 완료

모두 체크했다면 ➡️ **[ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md)로 이동!**

---

## 🎉 준비 완료!

이제 [ASSIGNMENT_GUIDE.md](ASSIGNMENT_GUIDE.md)를 열고  
Step 1부터 차근차근 따라하세요!

**과제 화이팅! 🚀**

---

<div align="center">

**Made with ❤️ by HateSlop**

[GitHub](https://github.com/hateslop) | [Documentation](README.md)

</div>
