# 🔥 Docker Hot Reloading 가이드

> 코드 수정 시 즉시 반영하기

---

## 🎯 Hot Reloading이란?

코드를 수정하면 **Docker 컨테이너를 재시작하지 않고도** 변경사항이 자동으로 반영되는 기능입니다.

---

## ⚡ 빠른 사용법

### 상황별 명령어

| 수정한 파일                             | 명령어                      | 적용 시간 |
| --------------------------------------- | --------------------------- | --------- |
| **Python 코드** (`app.py`, `services/`) | 자동 (개발 모드)            | 즉시      |
| **HTML** (`templates/`)                 | 새로고침만                  | 즉시      |
| **CSS/JS** (`static/`)                  | 새로고침만                  | 즉시      |
| **Config** (`config/`)                  | 자동 (개발 모드)            | 즉시      |
| **requirements.txt**                    | `docker compose up --build` | 2-3분     |
| **Dockerfile**                          | `docker compose up --build` | 2-3분     |
| **.env**                                | `docker compose restart`    | 5초       |

---

## 🔧 설정 확인

### docker compose.yml 확인

```yaml
services:
  chatbot:
    environment:
      - FLASK_ENV=development # ✅ 개발 모드
      - FLASK_DEBUG=True # ✅ 디버그 모드
    volumes:
      - ./app.py:/app/app.py # ✅ 마운트
      - ./services:/app/services # ✅ 마운트
      - ./templates:/app/templates # ✅ 마운트
      - ./static:/app/static # ✅ 마운트
```

**모두 ✅면 Hot Reloading 활성화!**

---

## 📝 실전 예시

### 예시 1: Python 코드 수정

```bash
# 1. Docker 실행 (한 번만)
docker compose up

# 2. services/chatbot_service.py 수정
# (에디터에서 코드 수정)

# 3. 터미널 확인
# * Detected change in '/app/services/chatbot_service.py', reloading
# * Restarting with stat

# 4. 브라우저 새로고침
# ✅ 변경사항 반영됨!
```

### 예시 2: HTML/CSS 수정

```bash
# 1. templates/chat.html 또는 static/css/style.css 수정

# 2. 브라우저 새로고침 (Ctrl+Shift+R 또는 Cmd+Shift+R)
# ✅ 즉시 반영됨!
```

### 예시 3: 패키지 추가

```bash
# 1. requirements.txt에 새 패키지 추가
echo "requests==2.31.0" >> requirements.txt

# 2. 재빌드 필요
docker compose down
docker compose up --build

# ⏱️ 2-3분 소요
```

### 예시 4: 환경변수 변경

```bash
# 1. .env 파일 수정
nano .env

# 2. 컨테이너만 재시작
docker compose restart chatbot

# ⏱️ 5초 소요
```

---

## 🐛 Hot Reloading이 안 될 때

### 1. Flask가 재시작 안 됨

**증상**: 코드 수정해도 반영 안 됨

**해결**:

```bash
# docker compose.yml 확인
environment:
  - FLASK_ENV=development  # ← 이게 development인지 확인
  - FLASK_DEBUG=True       # ← 이게 True인지 확인

# 변경 후 재시작
docker compose restart chatbot
```

### 2. 파일이 마운트 안 됨

**증상**: 파일 수정해도 컨테이너에 반영 안 됨

**해결**:

```bash
# docker compose.yml의 volumes 확인
volumes:
  - ./services:/app/services  # ← 경로가 맞는지 확인

# 확인 방법
docker compose exec chatbot ls -la /app/services
```

### 3. 캐시 문제

**증상**: 브라우저에서 변경사항 안 보임

**해결**:

```bash
# 강력 새로고침
# Chrome/Edge: Ctrl+Shift+R (Windows/Linux) / Cmd+Shift+R (Mac)
# Firefox: Ctrl+F5 (Windows/Linux) / Cmd+Shift+R (Mac)
```

### 4. Syntax Error로 Flask 중단

**증상**: 코드 수정 후 서버가 완전히 멈춤

**해결**:

```bash
# 1. 로그 확인
docker compose logs -f chatbot

# 2. 에러 확인 후 코드 수정

# 3. 저장하면 자동으로 재시작 시도
```

---

## 💡 유용한 명령어 모음

```bash
# 로그 실시간 확인 (Hot Reload 메시지 보기)
docker compose logs -f chatbot

# 컨테이너 재시작 (빠름)
docker compose restart chatbot

# 완전 재시작 (중간 속도)
docker compose down && docker compose up

# 재빌드 (느림, 패키지 변경 시)
docker compose up --build

# 컨테이너 내부 접속 (디버깅)
docker compose exec chatbot bash

# 특정 파일이 마운트되었는지 확인
docker compose exec chatbot cat /app/services/chatbot_service.py
```

---

## 🎯 베스트 프랙티스

### ✅ DO

```bash
# 1. 개발 중에는 개발 모드 유지
FLASK_ENV=development
FLASK_DEBUG=True

# 2. 로그를 항상 켜두기
docker compose logs -f chatbot

# 3. 변경 후 터미널에서 재시작 메시지 확인
# * Restarting with stat

# 4. Python 파일 수정 → 터미널 확인 → 브라우저 새로고침
```

### ❌ DON'T

```bash
# 1. 매번 docker compose up --build 하지 마세요
# (시간 낭비, Python/HTML/CSS는 자동 반영)

# 2. production 모드로 개발하지 마세요
FLASK_ENV=production  # ← Hot Reload 안 됨!

# 3. 변경 후 컨테이너 재시작하지 마세요
# (불필요, 자동으로 reload됨)
```

---

## 🚀 성능 최적화 팁

### 1. Docker Volume 성능 향상 (macOS)

macOS에서 volumes가 느릴 수 있습니다.

**해결책**:

```yaml
# docker compose.yml
volumes:
  - ./services:/app/services:delegated # ← delegated 추가
```

### 2. .dockerignore 최적화

불필요한 파일 제외:

```
__pycache__
*.pyc
.git
.vscode
venv/
```

### 3. 선택적 재시작

전체 재시작 대신:

```bash
# 특정 서비스만 재시작
docker compose restart chatbot

# 전체 재시작 (느림)
docker compose restart  # ← 피하기
```

---

## 📊 개발 vs Production

| 항목            | 개발          | Production   |
| --------------- | ------------- | ------------ |
| **FLASK_ENV**   | `development` | `production` |
| **FLASK_DEBUG** | `True`        | `False`      |
| **Hot Reload**  | ✅ 활성화     | ❌ 비활성화  |
| **에러 표시**   | 상세          | 간단         |
| **성능**        | 느림          | 빠름         |

**배포 전 확인**:

```yaml
# docker compose.yml (production)
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=False
```

---

## 🆘 문제 해결 체크리스트

Hot Reload가 안 될 때 순서대로 확인:

- [ ] `FLASK_ENV=development` 확인
- [ ] `FLASK_DEBUG=True` 확인
- [ ] `volumes` 경로 확인
- [ ] 컨테이너 재시작: `docker compose restart chatbot`
- [ ] 로그 확인: `docker compose logs -f chatbot`
- [ ] 브라우저 캐시 삭제 (Ctrl+Shift+R)
- [ ] 코드 Syntax Error 확인
- [ ] 재빌드: `docker compose up --build`

**여전히 안 되면**:

```bash
# 완전히 초기화
docker compose down -v
docker compose up --build
```

---

## 💡 요약

```bash
# 일반 개발 워크플로우
1. docker compose up         # 한 번만
2. 코드 수정                  # 에디터
3. 터미널 확인               # Restarting 메시지
4. 브라우저 새로고침          # 변경사항 확인

# 패키지 추가 시에만
docker compose up --build

# 환경변수 변경 시에만
docker compose restart chatbot
```

**개발 모드 = 자동 반영! 🎉**
