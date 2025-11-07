# 🦉 별빛 우체국 ✨

>시간의 경계에서, 별빛 우체국장 부엉과 함께 다른 세계선의 '나'로부터 편지를 받는 심층 스토리텔링 챗봇

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-purple.svg)](https://openai.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4.24-orange.svg)](https://www.trychroma.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 프로젝트 개요

별빛 우체국은 RAG 기반의 감정 분석 및 심층 상담 챗봇입니다. 이곳의 국장인 부엉은 사용자의 감정을 이성적으로 분석하고, 후회, 사랑, 불안, 꿈의 주제별 방을 탐험하도록 안내합니다. 

이 탐험을 통해 사용자는 대화 맥락을 담아 다른 세계선의 '나'로부터 편지를 받게 되며, 그 내용에 따라 당신의 상황에 맞는 우표가 붙어 전달됩니다. 

### 핵심 기능

- **맞춤형 편지 수신**: 대화 내용을 바탕으로 **미래 혹은 과거의 '나'로부터 편지**를 받습니다
- **상황 맞춤 우표**: **당신의 상황에 맞는 우표**가 편지에 붙어 전달됩니다
- **감정 기반 대화**: LLM 기반 사용자 감정 분석 및 부엉장 감정 표현
- **방별 맞춤 상담**: 후회, 사랑, 불안, 꿈 주제별 전문 데이터 활용
- **Persona 시스템**: 상황에 맞는 부엉장의 자기 공개 스토리
- **위기 감지 모드**: 상담 매뉴얼 기반 전문 상담 응답


## 기술 스택

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



## 프로젝트 구조

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


## 작동 화면

### 시작 이미지
<div align="center">
  <img src="git_image/start_1.png" alt="시작 화면 1" width="400" />
  <img src="git_image/start_2.png" alt="시작 화면 2" width="400" />
</div>

---

### 채팅 초기 화면 / 방 선택 화면
<div align="center">
  <img src="git_image/main.png" alt="채팅 초기 화면" width="400" />
  <img src="git_image/room_select.png" alt="방 선택 화면" width="400" />
</div>

---

### 감정 이모지 출력
<div align="center">
  <img src="git_image/emotion.png" alt="감정 이모지 출력" width="400" />
</div>

---

### 편지 생성
<div align="center">
  <img src="git_image/letter_1.png" alt="편지 생성 화면 1" width="400" />
  <img src="git_image/letter_2.png" alt="편지 생성 화면 2" width="400" />
</div>


## 시스템 아키텍처
- [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 기술 선택 이유

### ChromaDB
- Python 네이티브 지원으로 Flask와 통합 용이
- 별도 서버 없이 임베디드 모드 사용 가능
- 방별 필터링으로 검색 정확도 향상

### RAG 패턴
- LLM의 환각(Hallucination) 감소
- 방별 주제별 맞춤 상담 서비스 제공 가능
- 새로운 데이터 추가 시 벡터 DB만 업데이트하면 확장 가능

### LangChain
- PDF 파일 로드 및 청킹 도구 제공
- 상담 매뉴얼 벡터 DB 구축 및 관리 용이

---

## 개발 중 문제점

### 문제 1: 사용자 예외 상황 처리

- **현상**: 사용자가 같은 말을 반복하거나, 편지를 빨리 받고 싶어하거나, 다른 방으로 가고 싶다고 하는 경우 어떻게 처리할지 불명확
- **원인**: 예외 상황에 대한 명확한 처리 로직 부재
- **증상**: 
  - 반복 말: 사용자가 같은 내용을 반복하면 대화가 진전되지 않음
  - 편지 조기 요청: 최소 대화 횟수 미달 시 편지를 요청하면 처리 방법 불명확
  - 방 변경 요청: 현재 방에서 다른 방으로 가고 싶다는 요청 처리 방법 부재

### 문제 2: Persona 로드 후 미사용 문제

- **현상**: 부엉장의 Persona가 분명 로드되고는 있는데, 대화 출력 시 사용하지 않는 문제
- **원인**: Persona 검색 결과가 활성화되지 않거나, 활성화되어도 시스템 프롬프트에 제대로 포함되지 않음
- **증상**: 사용자가 부엉장에 대해 질문해도 Persona 스토리가 활용되지 않음

### 문제 3: 대량 PDF 저장 시 오류 발생

- **현상**: 상담 매뉴얼 PDF 파일들을 벡터 DB에 저장하는 도중 오류 발생
- **원인**: 
  - OpenAI API 토큰 제한으로 인한 대량 임베딩 생성 실패
  - 한 번에 모든 문서를 처리하려 할 때 메모리 부족
- **증상**: PDF 파일 저장 중간에 프로세스가 중단되거나 오류 발생

---

## 해결 방법

### 문제 1 해결: 예외 상황 처리 시스템 구축

- **반복 말 감지**: 임베딩 유사도로 의미 기반 중복 감지 (85% 이상 시 반복으로 간주)
- **편지 조기 요청**: 키워드 감지 후 확인 메시지 및 버튼 제공으로 사용자 선택 처리
- **방 변경 요청**: 키워드 감지 후 재입장 확인 프로세스 진행

### 문제 2 해결: Persona 활성화 메커니즘 개선

- **강제 활성화 조건**: 직접 질문 감지 또는 키워드 매칭 점수 4점 이상 시 강제 활성화
- **시스템 프롬프트 명시**: `persona_story`와 `persona_guidance`를 프롬프트에 포함하여 LLM이 반드시 활용하도록 함
- **사용 기록 추적**: `session.used_persona_stories`로 중복 방지

### 문제 3 해결: 배치 처리 방식 도입

- **배치 크기**: 한 번에 50개 청크씩 처리하여 OpenAI API 토큰 제한 회피
- **순차 처리**: 첫 배치로 컬렉션 생성 후 나머지 배치를 `add_documents()`로 추가
- **에러 처리**: 개별 PDF 로드 실패 시 해당 파일만 스킵하고 계속 진행


---

## 성능 개선

### 개선 1: 응답 속도 최적화

- **결과**: 평균 5초 → 2초로 단축 (60% 개선)
- **방법**: 임베딩 LRU 캐시 도입, ChromaDB 방별 필터링, max_tokens 제한

### 개선 2: RAG 검색 정확도 향상

- **유사도 임계값**: 0.65 → 0.72로 상향 조정
- **방별 필터링**: 현재 방 데이터 우선 검색 후 전역 검색 폴백

---

## 아쉬웠던 점

### 1. 부엉의 감정 구현의 한계

- 문맥 전체를 고려하지 못하고 키워드만 보고 감정을 판단하는 문제
- 예: "같이 노는게 정말 즐거웠었는데" → 과거의 즐거움만 보고 기쁨으로 출력 (슬픔이어야 함)

### 2. 상담 가이드 PDF 활용의 한계

- 초기 계획: 모든 상담 가이드를 일상 대화에서 활용
- 현실: 성능 문제로 위기 감지 모드일 때만 사용하도록 제한
- 아쉬운 점: 상담 가이드의 풍부한 정보를 일상 대화에서 활용하지 못함

### 3. 질문 중심 대화의 한계

- 유저가 질문을 무시하고 하고 싶은 말만 할 때 자연스러운 대화가 어려움
- 질문 중심 프롬프트로 인해 유저의 답변을 기다리지 않고 계속 질문하는 패턴
- 실제 인간과의 대화처럼 자연스럽지 않음

---

## Contributors
<table>
  <tr>
    <td align="center">
      <a href="https://github.com/uuyeong">
        <sub><b>uuyeong</b></sub>
      </a>
      <br />
      <sub>Backend</sub>
    </td>
    <td align="center">
      <a href="https://github.com/yunjin-Kim4809">
        <sub><b>yunjin-Kim4809</b></sub>
      </a>
      <br />
      <sub>Frontend</sub>
    </td>
    <td align="center">
      <sub><b>박소현</b></sub>
      <br />
      <sub>Producer</sub>
    </td>
    <td align="center">
      <sub><b>이유진</b></sub>
      <br />
      <sub>Producer</sub>
    </td>
  </tr>
</table>

**HateSlop 3기 엔지니어 x 프로듀서 합동 프로젝트**

---

**별빛 우체국에 오신 것을 환영합니다.**


**부엉장과 함께 대화하며, 다른 시간의 '나'로부터 당신의 상황에 맞는 우표가 붙은 편지를 받아보세요.** 🌙
