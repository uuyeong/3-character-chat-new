# 🚀 시작하기 가이드

> Fork 후 5분 안에 챗봇 템플릿 실행하기

---

## Quick Start

### 1단계: Fork & Clone

```bash
# 1. GitHub에서 Fork 버튼 클릭
# 2. 로컬로 Clone
git clone https://github.com/YOUR_USERNAME/3-chatbot-project.git
cd 3-chatbot-project
```

### 2단계: 환경변수 설정

**`.env` 파일 생성** (프로젝트 루트에):

```bash
# macOS/Linux
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-later
PORT=5000
EOF

# Windows PowerShell
@"
OPENAI_API_KEY=your_openai_api_key_here
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=dev-secret-key-change-later
PORT=5000
"@ | Out-File -FilePath .env -Encoding utf8
```

**OpenAI API 키 입력**:

1. https://platform.openai.com/api-keys 접속
2. "Create new secret key" 클릭
3. 생성된 키를 `.env` 파일의 `OPENAI_API_KEY`에 입력

### 3단계: Docker 실행

```bash
docker compose up --build
```

### 4단계: 확인

브라우저에서 http://localhost:5001 접속

✅ 기본 템플릿이 정상 작동하면 성공!

**정상 작동 화면:**

<img src="https://www.notion.so/image/attachment%3Aa2870aaf-8d7c-4f0c-ac50-5d713fb72741%3Aimage.png?table=block&id=284219be-4e0b-80e3-9117-ee0850cf3023&spaceId=c18e7d08-d585-4e16-bd89-4e451c2cb079&width=2000&userId=1b37c595-3d33-47d7-90be-4d68c460d992&cache=v2" alt="메인 페이지" width="800">

<img src="https://www.notion.so/image/attachment%3A911aa800-0d00-4f18-8547-626fc850da38%3Aimage.png?table=block&id=284219be-4e0b-8043-a97a-d005b455730f&spaceId=c18e7d08-d585-4e16-bd89-4e451c2cb079&width=2000&userId=1b37c595-3d33-47d7-90be-4d68c460d992&cache=v2" alt="상세 페이지" width="800">

<img src="https://www.notion.so/image/attachment%3Acfde8b88-dbff-4d91-af57-0fbd62cead14%3Aimage.png?table=block&id=284219be-4e0b-80a0-8fd5-ea826e42d0ed&spaceId=c18e7d08-d585-4e16-bd89-4e451c2cb079&width=2000&userId=1b37c595-3d33-47d7-90be-4d68c460d992&cache=v2" alt="채팅 페이지" width="800">

---

## 📚 다음 단계

### 학생 (과제 수행자)

1. **START_HERE.md** 읽기 (5분)
2. **ASSIGNMENT_GUIDE.md** 따라하기 (6-8시간)
   - 설정 파일 작성
   - 텍스트 데이터 준비
   - **AI 로직 구현** ⭐ 핵심!
3. **IMPLEMENTATION_GUIDE.md** 참고 (AI 로직 상세 가이드)
4. 테스트 및 배포

### 교수/TA (관리자)

archive 브랜치에서 다음 문서 확인:

- `WORKFLOW_TEST.md` - 학생 워크플로우 테스트
- `REFACTORING_SUMMARY.md` - 프로젝트 변경 내역

---

## 🐳 Docker 명령어

```bash
# 시작
docker compose up

# 백그라운드 실행
docker compose up -d

# 종료
docker compose down

# 로그 보기
docker compose logs -f

# 컨테이너 내부 접속
docker compose exec chatbot bash

# 재빌드
docker compose up --build
```

---

## 🔧 문제 해결

### Docker가 실행되지 않아요

```bash
# Docker Desktop이 실행 중인지 확인
# macOS: 상단 메뉴바에 Docker 아이콘
# Windows: 시스템 트레이에 Docker 아이콘

# Docker 재시작
docker compose down
docker compose up --build
```

### API 키 오류가 나요

```bash
# .env 파일 확인
cat .env

# API 키가 올바른지 확인
# https://platform.openai.com/api-keys

# Docker 재시작 (환경변수 다시 로드)
docker compose down
docker compose up
```

### 포트가 이미 사용 중이래요

```bash
# 5000번 포트 사용 중인 프로세스 확인
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# docker compose.yml에서 포트 변경
ports:
  - "8080:5000"  # 로컬 8080 → 컨테이너 5000
```

---

## ✅ 체크리스트

Fork 후 확인사항:

- [ ] Git Clone 완료
- [ ] Docker Desktop 설치 및 실행
- [ ] `.env` 파일 생성 및 API 키 입력
- [ ] `docker compose up --build` 성공
- [ ] http://localhost:5000 접속 확인
- [ ] `/health` 엔드포인트 응답 확인 (http://localhost:5000/health)
- [ ] START_HERE.md 읽음
- [ ] ASSIGNMENT_GUIDE.md 확인

모두 체크했다면 과제 시작 준비 완료! 🎉

---

## 📖 문서 가이드

| 문서                        | 읽는 순서 | 소요 시간        |
| --------------------------- | --------- | ---------------- |
| **GETTING_STARTED.md**      | 1️⃣        | 5분              |
| **START_HERE.md**           | 2️⃣        | 10분             |
| **ASSIGNMENT_GUIDE.md**     | 3️⃣        | 전체 과제 가이드 |
| **IMPLEMENTATION_GUIDE.md** | 4️⃣        | AI 로직 구현 시  |
| **DOCKER_GUIDE.md**         | (참고)    | 필요 시          |

---

## 🆘 도움이 필요하면?

1. 가이드 문서 확인 (위 표 참고)
2. 로그 확인 (`docker compose logs -f`)
3. 조원과 상의
4. 교수님/TA에게 질문 (에러 메시지 첨부)

---

**시작 준비 완료! 🚀**

다음: [START_HERE.md](START_HERE.md)로 이동
