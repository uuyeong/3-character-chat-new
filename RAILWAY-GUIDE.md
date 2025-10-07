## 🚀 Railway 배포 가이드

> Docker로 로컬 개발은 끝났는데, 이걸 어떻게 친구들에게 보여주거나 포트폴리오로 활용할 수 있을까요?
>
> 이 문서는 여러분이 Docker 환경에서 개발한 챗봇 프로젝트를 **Railway CLI**를 사용하여 누구나 사용할 수 있는 배포환경을 구성하겠습니다.

---

### 🤔 Railway, 왜 사용해야 할까요?

- **Docker 네이티브 지원:** 로컬에서 사용한 Dockerfile을 그대로 배포할 수 있습니다. 추가 설정이 거의 필요 없습니다.
- **ChromaDB + LangChain 완벽 지원:** Serverless 제약 없이 Vector Database와 메모리를 자유롭게 사용할 수 있습니다.
- **비용 효율:** 개인 프로젝트나 소규모 트래픽은 무료 플랜(500MB 메모리)으로 충분히 운영 가능합니다.
- **간편한 CLI:** Vercel만큼 쉬운 명령어로 배포할 수 있습니다.
- **자동 빌드:** GitHub에 푸시하면 자동으로 재배포됩니다.

---

### 🔧 배포 환경 구축을 위한 준비물

배포를 시작하기 전에 다음 3가지를 확인해주세요.

- [ ] **로컬에서 완벽히 동작하는 프로젝트:** `DOCKER-GUIDE.md`를 따라 로컬(`http://localhost:5001`)에서 챗봇이 완벽하게 동작하는 것을 확인해야 합니다.
- [ ] **Railway 계정:** [Railway 홈페이지](https://railway.app/)에서 GitHub 계정으로 가입하는 것을 권장합니다.
- [ ] **Node.js 및 npm:** Railway CLI는 `npm`(Node Package Manager)을 통해 설치됩니다. [Node.js 공식 사이트](https://nodejs.org/)에서 LTS 버전을 설치하세요.

---

### 🚀 Railway CLI를 이용한 단계별 배포 가이드

#### 1단계: Railway CLI 설치

터미널을 열고 아래 명령어를 입력하여 Railway CLI를 전역(`global`)으로 설치합니다.

```bash
npm install -g @railway/cli
```

설치가 완료되면, 버전을 확인하여 정상적으로 설치되었는지 검증합니다.

```bash
railway --version
```

#### 2단계: Railway 로그인

아래 명령어를 실행하면, 브라우저를 통해 Railway 계정으로 로그인하라는 안내가 나타납니다.

```bash
railway login
```

> GitHub 계정 연동을 통해 로그인을 완료하세요. 브라우저에서 인증이 완료되면 터미널로 자동 복귀됩니다.

#### 3단계: 프로젝트 초기화

프로젝트 폴더 최상위 경로에서 아래 명령어를 실행하세요.

```bash
railway init
```

Railway CLI가 다음과 같이 물어봅니다:

- **"What is your project name?"** → 원하는 프로젝트 이름 입력 (예: `sogang-chatbot`)
- **"Environment"** → `production` 선택 (기본값)

프로젝트가 생성되면 Railway 대시보드에서도 확인할 수 있습니다.

#### 4단계: 첫 배포 (서비스 생성)

⚠️ **중요:** Railway v3부터는 환경 변수를 설정하기 전에 먼저 배포를 해야 합니다!

```bash
railway up --detach
```

> `--detach` 옵션을 사용하면 백그라운드에서 배포되어 바로 다음 단계로 진행할 수 있습니다.

이 시점에서는 OpenAI API 키가 없어서 챗봇이 완전히 작동하지 않지만, **서비스가 생성**되므로 다음 단계에서 환경 변수를 설정할 수 있습니다.

#### 5단계: 환경 변수 설정

이제 OpenAI API 키를 설정합니다.

**방법 1: 웹 대시보드로 설정 (가장 쉬움, 권장!)**

```bash
railway open
```

브라우저가 자동으로 열리면:

1. 본인의 서비스 클릭 (프로젝트 이름이 표시됨)
2. `Variables` 탭 선택
3. `New Variable` 버튼 클릭
4. Name: `OPENAI_API_KEY`, Value: `sk-your-api-key` 입력
5. `Add` 버튼 클릭
6. **자동으로 재배포됩니다!**

**방법 2: CLI로 설정**

```bash
railway variables --set "OPENAI_API_KEY=sk-your-actual-api-key-here"
railway variables --set "FLASK_ENV=production"
```

> `sk-`로 시작하는 **본인의 OpenAI API 키**를 그대로 입력하세요.

환경 변수 설정 후 재배포:

```bash
railway up --detach
```

환경 변수가 제대로 설정되었는지 확인:

```bash
railway variables
```

#### 6단계: 배포 상태 확인

배포가 완료될 때까지 기다립니다 (약 2-5분).

Railway가 자동으로:

1. 프로젝트의 `Dockerfile`을 감지
2. Docker 이미지 빌드
3. 컨테이너 실행
4. 공개 URL 생성

배포가 완료되면 터미널에 배포 상태가 표시됩니다.

#### 7단계: 도메인 확인 및 접속

배포가 완료되면 서비스의 URL을 확인합니다:

```bash
railway domain
```

또는 Railway 웹 대시보드(https://railway.app/dashboard)에서:

1. 본인의 프로젝트 클릭
2. `Settings` 탭 → `Domains` 섹션
3. `Generate Domain` 버튼 클릭 (아직 없다면)

생성된 URL (예: `https://your-project.up.railway.app`)을 웹 브라우저에서 열어 챗봇이 정상 작동하는지 확인하세요!

---

### 🔄 코드 변경 후 재배포

코드를 수정한 후 다시 배포하려면:

```bash
railway up
```

단, 한 번만 실행하면 됩니다!

**더 편한 방법 (자동 배포):**

Railway 대시보드에서 GitHub 저장소를 연결하면, `git push`만 해도 자동으로 재배포됩니다:

1. Railway 대시보드 → 프로젝트 선택
2. `Settings` → `Connect to GitHub Repository`
3. 저장소 선택 및 연결

이제 `git push`할 때마다 자동 배포됩니다! 🎉

---

### 💡 로컬 Docker vs Railway Docker: 무엇이 같고 다를까?

이 프로젝트의 **큰 장점**은 **로컬과 배포 환경이 완전히 동일**하다는 것입니다!

| 항목            | 로컬 환경 (Docker Desktop) | Railway 환경     |
| --------------- | -------------------------- | ---------------- |
| **기반 기술**   | Docker                     | Docker           |
| **Dockerfile**  | 동일한 파일 사용           | 동일한 파일 사용 |
| **Python 버전** | 3.11                       | 3.11             |
| **의존성**      | requirements.txt           | requirements.txt |
| **ChromaDB**    | ✅ 작동                    | ✅ 작동          |
| **LangChain**   | ✅ 작동                    | ✅ 작동          |
| **차이점**      | 로컬 파일 시스템           | Railway 스토리지 |

**핵심:** 로컬에서 완벽히 동작한다면, Railway에서도 동일하게 동작합니다!

---

### 📊 Railway vs Vercel 비교

| 항목           | Railway                 | Vercel                    |
| -------------- | ----------------------- | ------------------------- |
| **배포 방식**  | Docker 컨테이너         | Serverless Function       |
| **ChromaDB**   | ✅ 완벽 지원            | ❌ 용량 초과 (250MB 제한) |
| **LangChain**  | ✅ 완벽 지원            | ⚠️ 제한적                 |
| **메모리**     | 500MB (무료 플랜)       | 250MB (무료 플랜)         |
| **빌드 시간**  | 약간 느림 (Docker 빌드) | 빠름                      |
| **학습 목적**  | ✅ 교육용 최적          | ⚠️ 경량 앱 전용           |
| **CLI 명령어** | `railway up`            | `vercel --prod`           |

---

### 🛠️ 주요 Railway CLI 명령어 모음

```bash
# 로그인
railway login

# 프로젝트 초기화
railway init

# 환경 변수 설정
railway variables --set "KEY=value"

# 여러 환경 변수 한번에 설정
railway variables --set "KEY1=value1" --set "KEY2=value2"

# 환경 변수 확인
railway variables

# 배포
railway up

# 로그 확인 (실시간)
railway logs

# 도메인 확인
railway domain

# Railway 대시보드 열기
railway open
```

---

### 🐛 Troubleshooting

#### **문제 1: 빌드가 실패해요**

**증상:** `railway up` 실행 시 빌드 에러

**해결 방법:**

1. `requirements.txt`에 오타가 없는지 확인
2. Railway 대시보드에서 빌드 로그 확인:
   ```bash
   railway logs
   ```
3. 로컬에서 Docker 빌드 테스트:
   ```bash
   docker compose build
   ```

#### **문제 2: 배포는 성공했는데 500 에러가 발생해요**

**증상:** 사이트에 접속하면 `Internal Server Error`

**해결 방법:**

1. 환경 변수 확인:

   ```bash
   railway variables
   ```

   `OPENAI_API_KEY`가 제대로 설정되었는지 확인

2. 실시간 로그 확인:

   ```bash
   railway logs
   ```

3. ChromaDB 데이터 확인:
   - `static/data/chatbot/chardb_embedding/` 폴더가 있는지 확인
   - 데이터가 제대로 커밋되었는지 확인

#### **문제 3: ChromaDB 데이터가 사라져요**

**증상:** 재배포 후 Vector DB 데이터가 초기화됨

**원인:** Railway의 컨테이너는 재시작 시 파일 시스템이 초기화됩니다.

**해결 방법:**

**방법 1: 임베딩 데이터를 Git에 포함 (권장)**

```bash
# .gitignore에서 ChromaDB 데이터 제외하지 않기
git add static/data/chatbot/chardb_embedding/
git commit -m "Add ChromaDB embeddings"
git push
```

**방법 2: Railway Volume 사용 (고급)**
Railway 대시보드에서 Persistent Volume을 연결할 수 있습니다.

#### **문제 4: 이미지나 CSS가 안 보여요**

**증상:** 웹사이트는 뜨는데 스타일이 깨짐

**해결 방법:**

1. `static/` 폴더가 Git에 포함되었는지 확인
2. Flask 라우팅 확인 (`app.py`의 static 경로)
3. Railway 로그에서 404 에러 확인

#### **문제 5: "No Dockerfile found" 에러**

**증상:** Railway가 Dockerfile을 찾지 못함

**해결 방법:**

```bash
# 프로젝트 루트에서 확인
ls -la Dockerfile

# 있다면 다시 배포
railway up
```

#### **문제 6: "Your account is on a limited plan" 메시지**

**증상:** `railway up` 실행 시 limited plan 메시지

**원인:** Railway 무료 플랜은 매월 제한된 크레딧을 제공합니다.

**해결 방법:**

**확인 1: 현재 사용량 체크**

```bash
railway open
```

대시보드에서 `Account` → `Usage` 탭에서 현재 사용량 확인

**확인 2: 무료 크레딧 받기**

- Railway는 신규 가입 시 $5 무료 크레딧 제공
- GitHub 학생 계정이 있다면 추가 크레딧 가능
- [railway.app/account/plans](https://railway.app/account/plans) 에서 확인

**임시 해결:**

- 기존 사용하지 않는 프로젝트 삭제
- 또는 Hobby Plan($5/월) 고려

**대안:** Render.com 무료 플랜 사용 (Docker 지원, 무제한)

#### **문제 7: "No service linked" 에러**

**증상:** `railway variables` 실행 시 서비스가 링크되지 않았다는 메시지

**해결 방법:**

먼저 `railway up`으로 배포하여 서비스를 생성한 후 환경 변수를 설정하세요:

```bash
# 1. 먼저 배포 (서비스 생성)
railway up --detach

# 2. 그 다음 환경 변수 설정
railway variables --set "OPENAI_API_KEY=sk-xxx"
```

또는 웹 대시보드에서 설정:

```bash
railway open
```

---

### 🎓 추가 학습: Railway의 작동 원리

Railway는 다음과 같은 순서로 배포를 진행합니다:

1. **소스 코드 업로드**

   - `railway up` 실행 시 현재 폴더의 모든 파일 업로드
   - `.gitignore`에 있는 파일은 제외

2. **Dockerfile 감지**

   - 프로젝트 루트에서 `Dockerfile` 자동 검색
   - 발견되면 Docker 빌드 프로세스 시작

3. **Docker 이미지 빌드**

   ```dockerfile
   # Dockerfile의 각 단계 실행
   FROM python:3.11-slim
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD ["python", "app.py"]
   ```

4. **컨테이너 실행**

   - 환경 변수 주입
   - 포트 자동 매핑 (Flask의 5000 포트 → 공개 URL)

5. **도메인 연결**
   - `*.up.railway.app` 형태의 공개 URL 생성

---

### 🚀 배포 완료 체크리스트

배포가 성공적으로 완료되었는지 확인하세요:

- [ ] Railway CLI 설치 완료
- [ ] `railway login` 성공
- [ ] `railway init`로 프로젝트 생성
- [ ] `OPENAI_API_KEY` 환경 변수 설정
- [ ] `railway up` 배포 성공
- [ ] 공개 URL에서 챗봇 정상 작동
- [ ] 챗봇과 대화 테스트 (RAG 기능 확인)
- [ ] 이미지/CSS 정상 로드 확인

---

### 📚 참고 자료

- [Railway 공식 문서](https://docs.railway.app/)
- [Railway CLI 가이드](https://docs.railway.app/develop/cli)
- [Docker 공식 문서](https://docs.docker.com/)
- [Flask 배포 가이드](https://flask.palletsprojects.com/en/3.0.x/deploying/)

---

### 💬 도움이 필요하신가요?

- **Railway Discord:** https://discord.gg/railway
- **프로젝트 이슈:** GitHub Issues 탭 활용
- **헤이트슬롭 커뮤니티:** 학회 Discord 채널에서 질문하기

---

**축하합니다! 🎉**

여러분의 챗봇이 이제 전 세계 어디서든 접속 가능한 서비스가 되었습니다!
포트폴리오에 추가하고, 친구들에게 자랑해보세요! 🚀
