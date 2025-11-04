# 별빛 우체국

>시간의 경계에서, 별빛 우체국장 부엉과 함께 미래 혹은 과거의 '나'로부터 편지를 받는 심층 스토리텔링 챗봇

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4.24-orange.svg)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 📖 프로젝트 개요

별빛 우체국은 RAG(Retrieval-Augmented Generation) 기반의 감정 분석 및 상담 챗봇입니다. 부엉 우체국장이 사용자의 감정을 이해하고, 방별 주제(후회, 사랑, 불안, 꿈)에 맞는 대화를 제공합니다. 

**핵심 경험**: 대화를 통해 **미래 혹은 과거의 '나'로부터 편지를 받는** 서비스입니다. 대화 내용에 따라 **당신의 상황에 맞는 우표가 붙어있는 편지**를 받게 됩니다. 위기 상황을 감지하면 전문 상담 매뉴얼을 활용한 안전한 응답을 제공합니다.

### 핵심 기능

- 📮 **맞춤형 편지 수신**: 대화 내용을 바탕으로 **미래 혹은 과거의 '나'로부터 편지**를 받습니다
- 🎫 **상황 맞춤 우표**: **당신의 상황에 맞는 우표**가 편지에 붙어 전달됩니다
- 🎭 **감정 기반 대화**: LLM 기반 사용자 감정 분석 및 부엉장 감정 표현
- 🏠 **방별 맞춤 상담**: 후회, 사랑, 불안, 꿈 주제별 전문 데이터 활용
- 🧠 **Persona 시스템**: 상황에 맞는 부엉장의 자기 공개 스토리
- ⚠️ **위기 감지 모드**: 상담 매뉴얼 기반 전문 상담 응답

## 🚀 빠른 시작

### 사전 요구사항

- Docker Desktop 설치 및 실행 중
- OpenAI API 키 발급

### 설치 및 실행

```bash
# 1. 프로젝트 클론
git clone https://github.com/YOUR_USERNAME/3-character-chat.git
cd 3-character-chat

# 2. 환경 변수 설정
cp .env.example .env
# .env 파일에 OPENAI_API_KEY 입력

# 3. Docker 컨테이너 실행
docker compose up --build

# 4. 브라우저에서 접속
# http://localhost:5001
```

## 🏗️ 시스템 아키텍처

### 전체 구조도

```
사용자 메시지 입력
    ↓
Flask API (app.py)
    ↓
ChatbotService (chatbot_service.py)
    ├─→ 감정 분석 (LLM)
    ├─→ RAG 검색 (ChromaDB) - 방별 QA 데이터
    ├─→ Persona 검색 (owl_persona.json)
    ├─→ 위기 감지 → 상담 매뉴얼 검색 (RAG-D)
    └─→ LLM 응답 생성 (GPT-4o-mini)
    ↓
응답 반환 (감정 태그, 이미지, 버튼 포함)
```

### 데이터 흐름

1. **사용자 메시지 입력** → Flask API로 전달
2. **세션 관리** → 사용자별 대화 기록 및 상태 관리
3. **예외 처리** → 반복 말, 편지 요청, 방 변경 등 선행 처리
4. **감정 분석** → LLM 기반 유저 감정 분석 (JOY, SADNESS, ANGER, QUESTION, BASIC)
5. **부엉장 감정 결정** → 상황 기반 감정 오버라이드 (기본, 기쁨, 슬픔, 분노, 의문)
6. **RAG 검색** → 현재 방의 QA 데이터에서 관련 정보 검색
7. **Persona 검색** → 상황에 맞는 부엉장 스토리 검색
8. **위기 감지** → 위기 키워드 감지 시 상담 매뉴얼 검색
9. **프롬프트 구성** → 모든 컨텍스트를 시스템 프롬프트에 통합
10. **LLM 응답 생성** → GPT-4o-mini로 최종 응답 생성
11. **응답 후처리** → 감정 태그, 이미지, 버튼 추가
12. **세션 저장** → 대화 기록 및 상태 영구 저장

## 🛠️ 기술 스택

### Backend
- **Flask 3.0**: RESTful API 서버
- **OpenAI API (gpt-4o-mini)**: 대화 생성 및 감정 분석
- **OpenAI Embeddings (text-embedding-3-small)**: 텍스트 임베딩 생성
- **ChromaDB 0.4.24**: 벡터 데이터베이스 (RAG 검색)
- **LangChain**: 상담 매뉴얼 벡터 DB 관리

### Frontend
- **Vanilla JavaScript**: 프레임워크 없는 순수 JS
- **HTML5/CSS3**: 반응형 웹 UI

### Infrastructure
- **Docker**: 컨테이너화 및 개발 환경 일관성
- **Python 3.11**: 런타임 환경

## 📂 프로젝트 구조

```
3-character-chat/
├── app.py                          # Flask 애플리케이션 (라우팅)
├── services/
│   └── chatbot_service.py          # 핵심 AI 로직 (RAG, 감정, Persona)
├── config/
│   └── chatbot_config.json        # 챗봇 설정 (방 정보, Phase 설정)
├── static/
│   ├── data/
│   │   └── chatbot/
│   │       ├── chardb_text/        # 텍스트 데이터
│   │       │   ├── regret/         # 후회 관련 QA
│   │       │   ├── love/           # 사랑 관련 QA
│   │       │   ├── anxiety/       # 불안 관련 QA
│   │       │   ├── dream/         # 꿈 관련 QA
│   │       │   ├── owl_character.txt
│   │       │   └── owl_persona.json
│   │       ├── chardb_embedding/   # ChromaDB 벡터 DB
│   │       ├── counseling_vectordb/ # 상담 매뉴얼 벡터 DB
│   │       └── sessions/           # 세션 저장소
│   ├── images/
│   │   └── chatbot/                # 부엉장 감정 이미지
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── chatbot.js
├── templates/
│   ├── index.html                  # 메인 페이지
│   ├── detail.html                 # 상세 페이지
│   └── chat.html                   # 채팅 페이지
├── tools/
│   └── build_counseling_vectordb.py # 상담 매뉴얼 벡터 DB 구축 스크립트
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── vercel.json                     # Vercel 배포 설정
```

## 🎯 핵심 기능 상세

### 1. 맞춤형 편지 및 우표 시스템

**편지 수신 경험**
- 대화 내용을 바탕으로 **미래 혹은 과거의 '나'로부터 편지**를 생성합니다
- 사용자의 감정, 고민, 대화 맥락을 종합하여 개인화된 편지 내용을 작성합니다

**상황 맞춤 우표**
- **당신의 상황에 맞는 우표**가 편지에 붙어 전달됩니다
- 각 방(후회, 사랑, 불안, 꿈)에 따라 다른 우표 코드 부여
- 우표는 사용자의 대화 주제와 감정 상태를 반영합니다

### 2. 감정 구현 시스템

부엉장의 감정은 2단계 프로세스로 결정됩니다.

**1단계: LLM 기반 유저 감정 분석**
- GPT-4o-mini를 사용하여 사용자 메시지를 5가지 카테고리로 분류
- 카테고리: JOY, SADNESS, ANGER, QUESTION, BASIC

**2단계: 상황 기반 감정 결정**
- LLM 분석 결과를 상황에 맞게 오버라이드
- 우선순위: 의문 → 분노 → 슬픔 → 기쁨 → LLM 결과
- 감정 변화만 화면에 표시 (중복 방지)

### 3. Persona 시스템

부엉장의 성격과 경험을 담은 스토리를 상황에 맞게 공개합니다.

**데이터 구조**
- `owl_persona.json`: 카테고리별 서브 스토리 저장
- 각 스토리는 트리거 키워드, 내용(short/long), LLM 가이드 포함

**활성화 메커니즘**
- 키워드 매칭 점수 기반 선택
- 직접 질문 시 강제 활성화
- 고득점(4점 이상) 시 재사용 허용

### 4. 방별 질문 데이터 활용

각 방(후회, 사랑, 불안, 꿈)에 맞는 전문 QA 데이터를 RAG 검색으로 활용합니다.

**데이터 로딩**
- 각 방 폴더의 `.txt` 파일을 청킹(최대 900자)
- OpenAI Embeddings로 임베딩 생성
- ChromaDB에 저장 (메타데이터: room, filename, chunk_index)

**검색 전략**
- 현재 방 우선 검색 (유사도 임계값: 0.72)
- 매칭 없으면 전역 검색 (임계값: 0.65로 완화)
- 거리 → 유사도 변환 후 Top-K 반환

### 5. 위기 감지 모드

위기 상황을 감지하면 전문 상담 매뉴얼을 활용한 안전한 응답을 제공합니다.

**위기 감지**
- 키워드 기반 감지: "자살", "극단적", "죽고", "해치" 등
- 위기 모드 활성화 시 세션 플래그 설정

**상담 매뉴얼 활용 (RAG-D)**
- PDF 파일을 청킹하여 별도 벡터 DB 구축
- 위기 키워드 감지 시 관련 지식 검색 (Top-K: 3)
- 시스템 프롬프트에 안전 지침 포함

**회복 감지**
- 회복 키워드 연속 2회 감지 시 위기 모드 해제
- 편지 전달(Phase 5) 시 자동 해제

### 6. 예외 처리

자연스러운 대화 흐름을 유지하기 위한 예외 처리 시스템입니다.

**반복 말 감지**
- 의미 기반 중복 감지 (임베딩 유사도 85% 이상)
- 반복 횟수 추적 및 대화 전략 조정

**편지 조기 전달 요청**
- 최소 대화 횟수 미달 시 확인 프로세스 진행
- 버튼을 통한 사용자 선택 처리

**방 변경 요청**
- 구체적 방 지정, 현재 방 요청, 비구체적 요청 구분
- 재입장 확인 후 세션 초기화 또는 현재 상태 유지

## 📊 주요 구현 사항

### RAG (Retrieval-Augmented Generation)

**검색 파이프라인**
1. 사용자 메시지 임베딩 생성
2. ChromaDB에서 유사도 검색
3. 거리 → 유사도 변환 (similarity = 1.0 / (1.0 + distance))
4. 임계값 필터링 후 Top-K 반환
5. 검색 결과를 시스템 프롬프트에 포함

**최적화**
- 임베딩 캐시 (LRU, 최대 1000개)
- 방별 필터링으로 검색 범위 축소
- 유사도 임계값 조정으로 정확도 향상

### 세션 관리

**세션 상태**
- Phase 관리 (1: 입장, 2: 방 선택, 3: 방 대화, 3.6: 서랍 대화, 4: 편지 생성, 5: 편지 전달)
- 대화 기록 및 요약
- 감정 추적
- Persona 사용 기록

**영속화**
- JSON 파일로 세션 저장 (`static/data/chatbot/sessions/`)
- 서버 재시작 시에도 대화 기록 유지

### 대화 요약

**자동 요약**
- 30개 메시지 증가 시마다 요약 수행
- 최근 60개 사용자 메시지 중심으로 축약
- 누적 요약 방식으로 전체 맥락 유지

## 🔧 개발 가이드

### 로컬 개발 환경

```bash
# Docker 컨테이너 실행
docker compose up --build

# 코드 수정 시 자동 재시작 (Flask 개발 모드)
# volumes 설정으로 실시간 반영
```

### 상담 매뉴얼 벡터 DB 구축

```bash
# PDF 파일을 벡터 DB로 변환
python tools/build_counseling_vectordb.py

# 생성된 DB: static/data/chatbot/counseling_vectordb/
```

### 새로운 라이브러리 추가

1. `requirements.txt`에 패키지 추가
2. Docker 이미지 재빌드: `docker compose up --build`

## 📚 문서

- [ARCHITECTURE.md](ARCHITECTURE.md): 시스템 아키텍처 상세 설명
- [DOCKER-GUIDE.md](DOCKER-GUIDE.md): Docker 개발 환경 가이드
- [RENDER-GUIDE.md](RENDER-GUIDE.md): Render.com 배포 가이드
- [ADVANCED_TOPICS.md](ADVANCED_TOPICS.md): 고급 주제 및 성능 개선

## 🚀 배포

### Vercel 배포

```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel --prod
```

자세한 배포 방법은 [RENDER-GUIDE.md](RENDER-GUIDE.md)를 참고하세요.


## 🚀 성능 개선

### 응답 속도 최적화
- 임베딩 캐시 도입 (60% 속도 개선)
- ChromaDB 쿼리 최적화

### 메모리 사용량 감소
- 대화 요약으로 프롬프트 길이 제한
- 불필요한 라이브러리 제거

## 🤔 회고

### 기술적 성장
- RAG 구현을 통해 벡터 검색의 원리 이해
- 프롬프트 엔지니어링으로 답변 품질 향상
- 감정 분석 및 예외 처리 로직 설계 경험

### 아쉬운 점
- 테스트 코드 부족 (단위 테스트 미구현)
- 멀티모달 기능 미구현 (이미지 검색)
- 성능 모니터링 도구 부재

### 향후 계획
- 단위 테스트 및 통합 테스트 추가
- 이미지 임베딩을 통한 멀티모달 검색
- 대화 품질 평가 메트릭 도입

## 👥 기여자

- [@uuyeong](https://github.com/uuyeong) - Backend (엔지니어)
- [@yunjin-Kim4809](https://github.com/yunjin-Kim4809) - Frontend (엔지니어)

**HateSlop 3기 엔지니어 x 프로듀서 합동 프로젝트**

---

**별빛 우체국에 오신 것을 환영합니다. 부엉장과 함께 대화하며, 미래 혹은 과거의 '나'로부터 당신의 상황에 맞는 우표가 붙은 편지를 받아보세요.** 🌙
