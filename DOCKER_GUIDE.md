# 🐳 Docker 활용 가이드

## Docker를 사용하는 이유

### 1. **환경 일관성 보장**

- 개발자의 로컬 환경(macOS, Windows, Linux)과 관계없이 동일한 환경 제공
- Python 버전, 시스템 패키지, Java 등 모든 의존성 통일
- "내 컴퓨터에서는 되는데..." 문제 완전 해결

### 2. **간편한 설정**

- 복잡한 환경 설정을 `docker compose up` 한 번으로 해결
- KoNLPy를 위한 Java 설치, Python 가상환경 등 자동 처리
- 팀원 간 설정 불일치 없음

### 3. **격리된 환경**

- 프로젝트가 시스템에 영향을 주지 않음
- 여러 프로젝트 동시 작업 가능
- 깨끗한 제거 가능 (`docker compose down`)

---

## 📋 기술 검토 결과

### ✅ Docker 도입의 장점

| 항목           | 기존 방식       | Docker 방식      |
| -------------- | --------------- | ---------------- |
| 환경 설정 시간 | 30분~1시간      | 5분 (처음 1회만) |
| 환경 일관성    | ❌ OS별 차이    | ✅ 완벽히 동일   |
| Java 설치      | 수동 (KoNLPy용) | 자동             |
| 의존성 충돌    | 가능            | 없음 (격리)      |
| 배포           | 복잡            | 간단             |
| 팀 협업        | 환경 문제 빈번  | 문제 없음        |

### ⚠️ Docker 도입의 단점 및 해결책

| 단점           | 영향도 | 해결책                     |
| -------------- | ------ | -------------------------- |
| 학습 곡선      | 중간   | 간단한 명령어만 사용 (3개) |
| 초기 빌드 시간 | 낮음   | 첫 빌드만 5분, 이후 즉시   |
| 디스크 용량    | 낮음   | 약 2GB (Python + Java)     |
| Windows 성능   | 낮음   | WSL2 사용 시 해결          |

### 🎯 결론: **Docker 도입 강력 권장**

특히 다음 경우 Docker가 필수적입니다:

- ✅ 2인 이상 팀 프로젝트
- ✅ Fork한 레포를 여러 사람이 사용
- ✅ Windows, macOS, Linux가 혼재된 팀
- ✅ KoNLPy(Java 의존성)를 사용하는 프로젝트
- ✅ ChromaDB 같은 로컬 DB를 사용하는 경우

---

## 🚀 빠른 시작

### 사전 준비

1. **Docker Desktop 설치**

   - macOS/Windows: [Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop)
   - Linux: Docker Engine 설치

   ```bash
   # Ubuntu
   sudo apt-get update
   sudo apt-get install docker.io docker compose
   ```

2. **환경변수 설정**

   ```bash
   # .env 파일 생성
   cp .env.example .env

   # 편집기로 OPENAI_API_KEY 입력
   nano .env
   ```

### Docker로 실행하기

#### 방법 1: Docker Compose (권장)

```bash
# 1. 빌드 및 실행
docker compose up --build

# 2. 백그라운드 실행
docker compose up -d

# 3. 로그 확인
docker compose logs -f

# 4. 종료
docker compose down
```

#### 방법 2: Docker만 사용

```bash
# 1. 이미지 빌드
docker build -t chatbot-app .

# 2. 컨테이너 실행
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=your_key_here \
  -v $(pwd)/static/data:/app/static/data \
  chatbot-app

# 3. 종료
docker stop chatbot-app
```

---

## 📝 주요 명령어

### 개발 중

```bash
# 앱 시작
docker compose up

# 변경사항 반영 (재빌드)
docker compose up --build

# 로그 보기
docker compose logs -f chatbot

# 컨테이너 상태 확인
docker compose ps

# 컨테이너 내부 접속 (디버깅)
docker compose exec chatbot bash
```

### 유지보수

```bash
# 컨테이너 정지
docker compose stop

# 컨테이너 시작 (재생성 없이)
docker compose start

# 컨테이너 재시작
docker compose restart

# 완전 삭제 (볼륨 포함)
docker compose down -v

# 이미지 삭제
docker rmi chatbot-app
```

### 디버깅

```bash
# 컨테이너 내부에서 Python 실행
docker compose exec chatbot python

# 챗봇 모듈 직접 테스트
docker compose exec chatbot python generation/chatbot/chatbot.py

# 환경변수 확인
docker compose exec chatbot env

# 설치된 패키지 확인
docker compose exec chatbot pip list
```

---

## 🔧 설정 커스터마이징

### 포트 변경

`docker compose.yml`:

```yaml
ports:
  - "8080:5000" # 로컬:8080 → 컨테이너:5000
```

### 환경변수 추가

`docker compose.yml`:

```yaml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY}
  - CUSTOM_VAR=value
```

### 볼륨 추가

`docker compose.yml`:

```yaml
volumes:
  - ./my-folder:/app/my-folder
```

---

## 🔍 트러블슈팅

### Q: 포트가 이미 사용 중이라는 오류

```bash
# 실행 중인 컨테이너 확인
docker ps

# 특정 포트 사용 프로세스 찾기 (macOS/Linux)
lsof -i :5000

# 포트 변경 (docker compose.yml 수정)
ports:
  - "8080:5000"
```

### Q: 빌드가 너무 느림

```bash
# 빌드 캐시 사용
docker compose build --no-cache

# 빌드 중간 출력 확인
docker compose build --progress=plain
```

### Q: ChromaDB 데이터가 사라짐

```bash
# 볼륨 확인
docker volume ls

# 볼륨을 삭제하지 않고 컨테이너만 종료
docker compose down  # (대신 docker compose down -v 사용하지 말것)

# 볼륨 백업
docker run --rm -v chatbot-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/chatbot-data-backup.tar.gz /data
```

### Q: KoNLPy 오류

```bash
# Java 설치 확인
docker compose exec chatbot java -version

# Java 경로 확인
docker compose exec chatbot echo $JAVA_HOME

# 수동 설치 (필요시)
docker compose exec chatbot apt-get update && apt-get install -y default-jdk
```

### Q: 코드 변경이 반영 안 됨

```bash
# 볼륨 마운트 확인
docker compose exec chatbot ls -la /app

# 재빌드
docker compose up --build

# 캐시 없이 재빌드
docker compose build --no-cache
```

---

## 🌐 Vercel vs Docker 비교

| 항목         | Vercel        | Docker (로컬/클라우드) |
| ------------ | ------------- | ---------------------- |
| 배포 속도    | 매우 빠름     | 보통                   |
| 무료 티어    | 제한적        | 무제한 (로컬)          |
| ChromaDB     | ❌ 저장 안 됨 | ✅ 영속성 보장         |
| 커스터마이징 | 제한적        | 자유로움               |
| 디버깅       | 어려움        | 쉬움                   |
| 추천 용도    | 프로덕션 배포 | 개발/테스트            |

### 권장 워크플로우

```
개발: Docker (로컬)
  ↓
테스트: Docker (Docker Hub)
  ↓
배포: Vercel 또는 AWS/GCP (Docker)
```

---

## 📦 프로덕션 배포

### Docker Hub에 푸시

```bash
# 1. Docker Hub 로그인
docker login

# 2. 이미지 태그
docker tag chatbot-app username/chatbot-app:latest

# 3. 푸시
docker push username/chatbot-app:latest
```

### AWS/GCP에서 실행

```bash
# Docker 이미지 pull
docker pull username/chatbot-app:latest

# 실행
docker run -d -p 80:5000 \
  -e OPENAI_API_KEY=your_key \
  --restart always \
  username/chatbot-app:latest
```

---

## ✅ 체크리스트

Docker 환경 설정 시 확인사항:

- [ ] Docker Desktop 설치 및 실행 확인
- [ ] `.env` 파일 생성 및 API 키 입력
- [ ] `docker compose up --build` 성공 확인
- [ ] `http://localhost:5001` 접속 확인
- [ ] `/health` 엔드포인트 응답 확인
- [ ] 채팅 기능 정상 작동 확인
- [ ] 데이터 영속성 확인 (재시작 후)

---

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Flask Docker 배포 가이드](https://flask.palletsprojects.com/en/2.3.x/deploying/docker/)

---

**Made with 🐳 Docker**
