# 🧪 워크플로우 테스트 가이드

이 문서는 과제 담당자(교수/TA)가 학생들의 워크플로우를 시뮬레이션하여 테스트하는 가이드입니다.

---

## 🎯 테스트 목적

1. 학생들이 과제를 원활하게 수행할 수 있는지 확인
2. 템플릿과 과제 부분이 명확히 구분되어 있는지 검증
3. 예상되는 문제점 사전 파악

---

## 📋 테스트 시나리오

### 시나리오 1: 조원 A 역할 (Repository Owner)

#### Step 1: Fork 및 Clone

```bash
# 1. GitHub에서 Fork (웹에서 진행)
# 2. 로컬로 Clone
git clone https://github.com/YOUR_TEST_ACCOUNT/3-chatbot-project.git
cd 3-chatbot-project
```

**예상 결과**:
✅ 프로젝트가 정상적으로 Clone됨
✅ 모든 파일이 존재함

**검증 포인트**:

```bash
ls -la
# 확인할 파일:
# - app.py (단일 템플릿)
# - Dockerfile, docker-compose.yml
# - config/chatbot_config.json (예제)
# - generation/chatbot/chatbot.py (완성된 템플릿)
```

#### Step 2: 환경 설정

```bash
# .env 파일 생성
cp .env.example .env

# API 키 입력 (테스트용 키 사용)
nano .env
```

**예상 결과**:
✅ `.env` 파일 생성됨
✅ `.gitignore`에 포함되어 있어 Git에 추적되지 않음

#### Step 3: Docker 실행

```bash
docker-compose up --build
```

**예상 결과**:
✅ 빌드 성공 (첫 실행 시 3-5분 소요)
✅ 서버가 5000번 포트에서 실행
✅ `http://localhost:5000` 접속 가능

**검증 포인트**:

- [ ] 메인 페이지 로드
- [ ] 기본 챗봇 정보 표시
- [ ] 상세 페이지 이동
- [ ] 채팅 화면 접속
- [ ] 초기 인사말 표시

#### Step 4: 기본 기능 테스트

```bash
# 헬스체크
curl http://localhost:5000/health

# 예상 응답:
# {"status":"ok","chatbot":"챗봇 이름"}
```

---

### 시나리오 2: 조원 B 역할 (Contributor)

#### Step 1: Repository Clone

```bash
# A의 레포지토리 Clone
git clone https://github.com/OWNER_A/3-chatbot-project.git
cd 3-chatbot-project
```

#### Step 2: Feature 브랜치 생성

```bash
git checkout -b feature/test-chatbot
```

**예상 결과**:
✅ 새 브랜치 생성됨

#### Step 3: 챗봇 설정 수정

```bash
nano config/chatbot_config.json
```

**수정 내용**:

```json
{
  "name": "테스트 챗봇",
  "description": "이것은 테스트용 챗봇입니다.<br>워크플로우를 검증하기 위한 것입니다.",
  "tags": ["#테스트", "#워크플로우", "#검증"],
  "thumbnail": "images/chatbot/thumbnail.png",
  "character": {
    "age": 25,
    "university": "테스트대학교",
    "major": "소프트웨어학과",
    "personality": "친절하고 정확함",
    "background": "테스트를 도와주는 조교"
  },
  "system_prompt": {
    "base": "당신은 테스트를 돕는 친절한 조교입니다.",
    "rules": ["반말을 사용하세요", "정확하게 답변하세요"]
  }
}
```

#### Step 4: 텍스트 데이터 작성

```bash
# 디렉토리 생성
mkdir -p static/data/chatbot/chardb_text

# 파일 생성
cat > static/data/chatbot/chardb_text/test_data.txt << 'EOF'
테스트 챗봇입니다.
이 챗봇은 워크플로우 테스트를 위해 만들어졌습니다.

Q: 테스트란 무엇인가요?
A: 테스트는 시스템이 정상적으로 작동하는지 확인하는 과정입니다.

Q: 왜 테스트가 중요한가요?
A: 테스트를 통해 버그를 사전에 발견하고 품질을 보장할 수 있습니다.

Q: 좋은 테스트 방법은?
A: 체계적인 계획, 다양한 시나리오, 그리고 자동화가 중요합니다.
EOF
```

#### Step 5: 이미지 준비

```bash
# 테스트용 이미지 디렉토리 생성
mkdir -p static/images/chatbot

# 테스트 이미지 다운로드 또는 복사
# (실제로는 학생이 직접 준비)
```

#### Step 6: 임베딩 생성 스크립트 작성

```bash
cat > static/data/chatbot/build_db.py << 'EOF'
import os
import sys
import uuid
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from generation.chatbot.chatbot import get_embedding, init_text_db

def build_text_database():
    _, collection = init_text_db()
    text_dir = Path(__file__).parent / "chardb_text"

    print("=" * 50)
    print("임베딩 생성 시작")
    print("=" * 50)

    for file_path in text_dir.glob("*.txt"):
        print(f"\n처리 중: {file_path.name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()

        if not content:
            continue

        chunk_size = 500
        chunks = [content[i:i+chunk_size]
                 for i in range(0, len(content), chunk_size)]

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
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
            print(f"  ✓ 청크 {i+1}/{len(chunks)} 완료")

    print("\n" + "=" * 50)
    print(f"완료! {collection.count()}개 문서 저장")
    print("=" * 50)

if __name__ == "__main__":
    build_text_database()
EOF
```

#### Step 7: Docker에서 임베딩 생성

```bash
# Docker 실행
docker-compose up -d

# 임베딩 생성 스크립트 실행
docker-compose exec chatbot python static/data/chatbot/build_db.py
```

**예상 결과**:
✅ 스크립트 실행 성공
✅ 임베딩 파일 생성됨 (`static/data/chatbot/chardb_embedding/`)
✅ 에러 없음

#### Step 8: 테스트

```bash
# 브라우저에서 http://localhost:5000 접속
# 채팅 테스트:
# - "테스트란 무엇인가요?"
# - "왜 테스트가 중요한가요?"
```

**예상 결과**:
✅ RAG가 작동하여 관련 답변 생성
✅ 시스템 프롬프트가 반영된 답변

#### Step 9: Git Commit & Push

```bash
# 변경사항 확인
git status

# 추가
git add config/chatbot_config.json
git add static/data/chatbot/chardb_text/
git add static/data/chatbot/build_db.py
git add static/images/chatbot/

# 커밋
git commit -m "feat: 테스트 챗봇 구현

- config: 테스트 챗봇 설정 추가
- data: 테스트 텍스트 데이터 작성
- images: 테스트 이미지 추가"

# 푸시
git push origin feature/test-chatbot
```

**예상 결과**:
✅ Push 성공
✅ GitHub에서 브랜치 확인 가능

#### Step 10: Pull Request

```
1. GitHub 웹에서 "Compare & pull request"
2. 제목: "테스트 챗봇 구현"
3. 설명 작성
4. Create Pull Request
```

**예상 결과**:
✅ PR 생성 성공
✅ 변경사항 표시

---

### 시나리오 3: 코드 리뷰 및 Merge (조원 A)

#### Step 1: Pull Request 확인

```
GitHub에서 PR 확인
```

#### Step 2: 로컬에서 테스트

```bash
# PR 브랜치 Fetch
git fetch origin feature/test-chatbot

# 브랜치 전환
git checkout feature/test-chatbot

# Docker 재시작
docker-compose down
docker-compose up --build

# 테스트
```

**검증 포인트**:

- [ ] 설정이 올바르게 반영됨
- [ ] 챗봇이 정상 작동
- [ ] RAG가 동작
- [ ] UI에 정보가 올바르게 표시

#### Step 3: 코드 리뷰

```
GitHub에서:
- 코드 검토
- 피드백 작성
- Approve 또는 Request Changes
```

#### Step 4: Merge

```
GitHub에서 "Merge pull request" 클릭
```

**예상 결과**:
✅ Merge 성공
✅ main 브랜치에 변경사항 반영

---

## 🔍 검증 체크리스트

### 프로젝트 구조 검증

- [ ] 템플릿 파일이 명확히 구분됨
- [ ] 과제 파일이 명확히 구분됨
- [ ] README에 명확한 가이드 있음
- [ ] ASSIGNMENT_GUIDE.md 존재
- [ ] 예제 데이터 제공

### Docker 환경 검증

- [ ] `docker-compose up` 성공
- [ ] 빌드 시간 합리적 (5분 이내)
- [ ] 환경변수 정상 로드
- [ ] 볼륨 마운트 정상 작동
- [ ] 헬스체크 정상

### 과제 수행 검증

- [ ] 설정 파일 수정 가능
- [ ] 텍스트 데이터 추가 가능
- [ ] 임베딩 생성 스크립트 작동
- [ ] 이미지 추가 가능
- [ ] RAG 정상 작동

### Git 워크플로우 검증

- [ ] Fork 가능
- [ ] Clone 가능
- [ ] 브랜치 생성 가능
- [ ] Commit & Push 가능
- [ ] Pull Request 생성 가능
- [ ] 코드 리뷰 가능
- [ ] Merge 가능

### 배포 검증

- [ ] Vercel 배포 가능
- [ ] 환경변수 설정 가능
- [ ] 배포 후 정상 작동
- [ ] `/health` 엔드포인트 응답

---

## 🐛 예상 문제점 및 해결책

### 문제 1: Docker 빌드 실패

**원인**: Java 설치 시간이 오래 걸림
**해결책**:

```dockerfile
# Dockerfile에서 캐시 활용
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk && rm -rf /var/lib/apt/lists/*
```

### 문제 2: 임베딩 생성 오류

**원인**: OpenAI API 키가 설정되지 않음
**해결책**:

```bash
# .env 파일 확인
cat .env
# OPENAI_API_KEY가 있는지 확인

# Docker 재시작
docker-compose down
docker-compose up
```

### 문제 3: RAG가 작동하지 않음

**원인**: 임베딩 파일이 생성되지 않음
**해결책**:

```bash
# 임베딩 파일 확인
ls static/data/chatbot/chardb_embedding/

# 없으면 다시 생성
docker-compose exec chatbot python static/data/chatbot/build_db.py
```

### 문제 4: Git Push 실패

**원인**: Collaborator 권한이 없음
**해결책**:

```
GitHub → Settings → Collaborators → Add people
```

### 문제 5: Vercel 배포 실패

**원인**: 환경변수 미설정
**해결책**:

```
Vercel Dashboard → Settings → Environment Variables
OPENAI_API_KEY 추가
```

---

## 📊 테스트 결과 기록

### 테스트 수행일: ****\_\_\_****

#### 시나리오 1: 조원 A (Repository Owner)

- [ ] Fork & Clone
- [ ] 환경 설정
- [ ] Docker 실행
- [ ] 기본 기능 테스트
- **소요 시간**: **\_\_**분
- **문제점**:
- **해결책**:

#### 시나리오 2: 조원 B (Contributor)

- [ ] Clone & 브랜치 생성
- [ ] 설정 파일 수정
- [ ] 데이터 작성
- [ ] 임베딩 생성
- [ ] 테스트
- [ ] Git Push
- [ ] Pull Request
- **소요 시간**: **\_\_**분
- **문제점**:
- **해결책**:

#### 시나리오 3: 코드 리뷰 & Merge

- [ ] PR 확인
- [ ] 로컬 테스트
- [ ] 코드 리뷰
- [ ] Merge
- **소요 시간**: **\_\_**분
- **문제점**:
- **해결책**:

### 전체 평가

- **템플릿 명확성**: ⭐⭐⭐⭐⭐ (5점 만점)
- **가이드 충분성**: ⭐⭐⭐⭐⭐
- **과제 난이도**: ⭐⭐⭐⭐☆ (적절함)
- **워크플로우 원활성**: ⭐⭐⭐⭐⭐

### 개선사항

1.
2.
3.

---

## 📝 학생 피드백 수집

테스트 후 학생들에게 물어볼 질문:

1. 과제 가이드가 명확했나요?
2. 어떤 부분이 가장 어려웠나요?
3. Docker 사용이 도움이 되었나요?
4. Git 워크플로우가 원활했나요?
5. 개선이 필요한 부분은?

---

**테스트 완료 후 이 문서를 업데이트하여 학생들에게 공유하세요!**

