"""
별빛 우체국 - 챗봇 서비스

부엉이 우체국장이 유저를 기억의 저장소로 안내하며,
잊혀진 편지를 찾는 스토리텔링 챗봇
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
import threading

# 환경변수 로드
load_dotenv()

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# 대화 횟수 설정 (테스트/프로덕션 전환용)
# ============================================
MIN_ROOM_CONVERSATIONS = 5    # 방에서의 최소 대화 횟수
MAX_ROOM_CONVERSATIONS = 10   # 방에서의 최대 대화 횟수 
MIN_DRAWER_CONVERSATIONS = 5  # 서랍에서의 최소 대화 횟수
MAX_DRAWER_CONVERSATIONS = 10 # 서랍에서의 최대 대화 횟수
# ============================================


class PostOfficeSession:
    """별빛 우체국 세션 관리"""
    
    def __init__(self, username: str):
        self.username = username
        self.phase = 1  # 현재 Phase (1-5)
        self.intro_step = 0  # 입장 단계 (0: 첫 인사, 1: 편지 소개)
        self.selected_room = None  # 선택한 방
        self.selected_drawer = None  # 선택한 서랍
        self.conversation_history = []  # 대화 기록
        self.room_conversation_count = 0  # 방에서의 대화 횟수
        self.drawer_conversation_count = 0  # 서랍에서의 대화 횟수
        self.letter_content = None  # 생성된 편지
        self.stamp_image = None  # 우표 이미지
        # 요약 관리
        self.summary_text = ""  # 대화 장기 요약
        self.last_summary_messages_len = 0  # 요약 시점의 메시지 수
        # 반복 의도 감지
        self.last_intent_key = None
        self.repeated_intent_count = 0
        # 위기 완충
        self.crisis_cooldown = 0
        # 편지 확인 대기
        self.awaiting_letter_confirm = False
        # 방 변경 대기
        self.awaiting_room_change_confirm = False
        self.requested_new_room = None  # 요청한 새 방
        # 재입장 확인 대기
        self.awaiting_reenter_confirm = False
        # RAG-P: 이미 사용한 페르소나 스토리 추적 (세밀한 중복 방지)
        self.used_persona_stories = set()  # {'love.breakup_bluntness', 'anxiety.plan_collapse_fear', ...}
        # 하위 호환성 유지 (기존 코드 지원)
        self.used_persona_categories = set()  # deprecated, used_persona_stories로 대체됨
        # 감정 추적 (변화 감지용)
        self.last_emotion = "기본"  # 마지막 출력된 감정
        
    def add_message(self, role: str, content: str):
        """대화 기록 추가"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })
    
    def get_summary(self) -> str:
        """전체 대화 요약 (서랍 선택 및 편지 생성용)"""
        messages = [msg['content'] for msg in self.conversation_history if msg['role'] == 'user']
        # 전체 대화 내용 사용 - 방에서의 대화 + 서랍에서의 대화 모두 포함
        # 나중에 대화가 너무 길어지면 (50개 이상) AI 요약 기능 추가 필요
        return " ".join(messages)

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "phase": self.phase,
            "intro_step": self.intro_step,
            "selected_room": self.selected_room,
            "selected_drawer": self.selected_drawer,
            "conversation_history": self.conversation_history,
            "room_conversation_count": self.room_conversation_count,
            "drawer_conversation_count": self.drawer_conversation_count,
            "letter_content": self.letter_content,
            "stamp_image": self.stamp_image,
            "summary_text": self.summary_text,
            "last_summary_messages_len": self.last_summary_messages_len,
            "last_intent_key": self.last_intent_key,
            "repeated_intent_count": self.repeated_intent_count,
            "crisis_cooldown": self.crisis_cooldown,
            "awaiting_room_change_confirm": self.awaiting_room_change_confirm,
            "requested_new_room": self.requested_new_room,
            "awaiting_reenter_confirm": self.awaiting_reenter_confirm,
            "used_persona_stories": list(self.used_persona_stories),  # set → list for JSON
            "used_persona_categories": list(self.used_persona_categories),  # 하위 호환성
            "last_emotion": self.last_emotion,  # 감정 추적
        }

    @staticmethod
    def from_dict(data: dict) -> "PostOfficeSession":
        s = PostOfficeSession(data.get("username", "사용자"))
        s.phase = data.get("phase", 1)
        s.intro_step = data.get("intro_step", 0)
        s.selected_room = data.get("selected_room")
        s.selected_drawer = data.get("selected_drawer")
        s.conversation_history = data.get("conversation_history", [])
        s.room_conversation_count = data.get("room_conversation_count", 0)
        s.drawer_conversation_count = data.get("drawer_conversation_count", 0)
        s.letter_content = data.get("letter_content")
        s.stamp_image = data.get("stamp_image")
        s.summary_text = data.get("summary_text", "")
        s.last_summary_messages_len = data.get("last_summary_messages_len", 0)
        s.last_intent_key = data.get("last_intent_key")
        s.repeated_intent_count = data.get("repeated_intent_count", 0)
        s.crisis_cooldown = data.get("crisis_cooldown", 0)
        s.awaiting_room_change_confirm = data.get("awaiting_room_change_confirm", False)
        s.requested_new_room = data.get("requested_new_room")
        s.awaiting_reenter_confirm = data.get("awaiting_reenter_confirm", False)
        s.used_persona_stories = set(data.get("used_persona_stories", []))  # list → set
        s.used_persona_categories = set(data.get("used_persona_categories", []))  # 하위 호환성
        s.last_emotion = data.get("last_emotion", "기본")  # 감정 추적
        return s


class ChatbotService:
    """별빛 우체국 챗봇 서비스"""
    
    # STAMP_CODES 정의 (클래스 변수로 통합 - 약 100줄 절약)
    STAMP_CODES = {
        'regret': {
            'R_1': {'name': '후회_꿈', 'situation': '꿈/진로 포기, 기회 상실', 'keywords': ['꿈', '진로', '포기', '기회', '상실', '도전', '미래', '목표', '학자', '연구', '학문'], 'mean': '이건 잃어버린 꿈을 기억하는 우표야. 별빛 속으로 사라진 종이비행기처럼, 한때 간절했던 마음도 언젠가 부드럽게 흩어지지. 그 마음을 잊지 말고, 다시 다른 하늘을 향해 보내보는 거야.'},
            'R_2': {'name': '후회_행동', 'situation': '잘못된 말/행동, 사과하지 못한 일', 'keywords': ['말', '행동', '사과', '잘못', '실수', '미안', '후회', '상처', '표현'], 'mean': '이건 잘못된 말과 행동을 기억하는 우표야. 멈춘 시간 속에서도 마음은 남는 법이야. 이 우표는 지나간 순간을 되돌릴 순 없어도, 그 안에 담긴 마음을 품을 수 있음을 말해줘. 너의 속도는 멈춘 게 아니라, 잠시 숨을 고르는 중이야.'},
            'R_3': {'name': '후회_관계', 'situation': '관계 단절, 소중한 사람 놓친 후회', 'keywords': ['관계', '단절', '소중한', '사람', '놓친', '친구', '가족', '이별', '멀어', '연락'], 'mean': '이건 놓친 연결을 위한 우표야. 사라진 인연의 실끝에는 여전히 따뜻함이 남아 있지. 다시 이어지지 않아도, 그 마음은 네 안에 여전히 빛나고 있단다.'},
            'R_4': {'name': '후회_자아', 'situation': '게으름, 자기 관리 실패 (시간 낭비 등)', 'keywords': ['게으름', '관리', '실패', '시간', '낭비', '자책', '노력', '건강', '외모'], 'mean': '이건 스스로를 비추는 우표야. 흐릿한 거울 속 자신을 마주할 때, 후회는 용서로 바뀌기도 하지. 이건 너 자신을 조금 더 이해하게 된 증표란다.'}
        },
        'love': {
            'L_1': {'name': '사랑_놓친 인연', 'situation': '놓친 인연', 'keywords': ['놓친', '인연', '타이밍', '기회', '만남', '스쳐', '운명'], 'mean': '이건 한순간 스친 인연을 위한 우표야. 빛이 교차하듯, 잠시 닿고 멀어진 마음이 있었지. 그 짧은 만남이 너의 마음을 조금 더 깊게 만들어줬을 거란다.'},
            'L_2': {'name': '사랑_짝사랑', 'situation': '짝사랑', 'keywords': ['짝사랑', '좋아', '고백', '못한', '혼자', '마음', '첫사랑', '썸'], 'mean': '이건 피지 못한 마음을 위한 우표야. 아직 열리지 않은 꽃봉오리처럼, 다 말하지 못한 감정이 있었지. 하지만 그 조용한 마음 덕분에 세상은 한층 더 다정해졌을 거란다.'},
            'L_3': {'name': '사랑_이별', 'situation': '이별', 'keywords': ['이별', '헤어', '끝', '떠나', '차', '버림', '작별', '무뚝뚝'], 'mean': '이건 이별을 위한 우표야. 지나간 사랑의 기억도 별빛 속에선 영원히 빛나지. 그 마음을 간직한 채, 새로운 사랑을 향해 나아가 보렴.'},
            'L_4': {'name': '사랑_신뢰', 'situation': '신뢰', 'keywords': ['신뢰', '믿음', '배신', '거짓말', '약속', '바람', '외도'], 'mean': '이건 신뢰를 위한 우표야. 깨진 신뢰도 별빛 속에선 다시 빛날 수 있단다. 그 마음을 간직한 채, 새로운 관계를 향해 나아가 보렴.'},
            'L_5': {'name': '사랑_오해', 'situation': '오해', 'keywords': ['오해', '갈등', '다툼', '싸움', '의견', '충돌'], 'mean': '이건 오해를 위한 우표야. 서로의 마음을 이해하지 못했던 순간들이 별빛 속에서 다시 빛날 수 있단다. 그 마음을 간직한 채, 새로운 소통을 향해 나아가 보렴.'},
            'L_6': {'name': '사랑_권태', 'situation': '권태', 'keywords': ['권태', '지루', '식', '무관심', '반복', '싫증'], 'mean': '이건 권태를 위한 우표야. 반복되는 일상 속에서도 사랑의 본질은 여전히 빛나고 있단다. 그 마음을 간직한 채, 새로운 시도를 향해 나아가 보렴.'}
        },
        'dream': {
            'D_1': {'name': '꿈_방향', 'situation': '꿈/방향성 상실, 무기력, 번아웃', 'keywords': ['방향', '상실', '무기력', '번아웃', '모르', '길', '목표', '없', '찾'], 'mean': '이건 잃어버린 꿈을 기억하는 우표야. 별빛 속으로 사라진 종이비행기처럼, 한때 간절했던 마음도 언젠가 부드럽게 흩어지지. 그 마음을 잊지 말고, 다시 다른 하늘을 향해 보내보는 거야.'},
            'D_2': {'name': '꿈_현실', 'situation': '현실적 제약 (돈/시간), 주변의 반대', 'keywords': ['현실', '돈', '시간', '제약', '반대', '여건', '경제', '부모', '가난'], 'mean': '이건 현실의 벽을 넘는 우표야. 꿈과 현실 사이에서 갈등하는 마음도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 길을 향해 나아가 보렴.'},
            'D_3': {'name': '꿈_두려움', 'situation': '실패/재능에 대한 두려움, 용기 부족', 'keywords': ['실패', '두려', '용기', '재능', '없', '못', '불안', '겁', '무서'], 'mean': '이건 두려움을 위한 우표야. 실패에 대한 두려움도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 도전을 향해 나아가 보렴.'},
            'D_4': {'name': '꿈_권태', 'situation': '꿈 성취 후의 허무함, 목표 상실', 'keywords': ['성취', '허무', '권태', '목표', '잃', '이룬', '후', '달성', '공허'], 'mean': '이건 권태를 위한 우표야. 꿈을 이룬 후에도 여전히 빛나는 마음을 간직한 채, 새로운 목표를 향해 나아가 보렴.'},
            'D_5': {'name': '꿈_자아실현', 'situation': '자아실현, 내적 성장에 대한 꿈', 'keywords': ['자아', '성장', '내적', '의미', '가치', '진짜', '본질', '자기'], 'mean': '이건 자아실현을 위한 우표야. 내적 성장을 향한 여정도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 가능성을 향해 나아가 보렴.'}
        },
        'anxiety': {
            'A_1': {'name': '불안_관계', 'situation': '인간 관계에 대한 불안', 'keywords': ['관계', '사람', '대인', '친구', '외로', '거부', '혼자'], 'mean': '이건 관계에 대한 불안의 우표야. 소중한 사람과의 연결이 끊어질까 두려운 마음도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 관계를 향해 나아가 보렴.'},
            'A_2': {'name': '불안_선택', 'situation': '선택에 대한 불안', 'keywords': ['선택', '결정', '갈림', '고민', '어떻게', '판단', '길'], 'mean': '이건 선택에 대한 불안의 우표야. 중요한 결정을 내릴 때의 두려움도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 선택을 향해 나아가 보렴.'},
            'A_3': {'name': '불안_일', 'situation': '일(학업)에 대한 불안', 'keywords': ['일', '학업', '성적', '직장', '업무', '공부', '시험', '과제', '성과'], 'mean': '이건 일에 대한 불안의 우표야. 성과에 대한 압박감도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 도전을 향해 나아가 보렴.'},
            'A_4': {'name': '불안_정체성', 'situation': '정체성(삶의 방향)에 대한 불안', 'keywords': ['정체성', '삶', '방향', '나', '존재', '의미', '누구', '어디'], 'mean': '이건 정체성에 대한 불안의 우표야. 삶의 방향을 잃어버린 듯한 불안감도 별빛 속에선 빛나지. 그 마음을 간직한 채, 새로운 길을 향해 나아가 보렴.'}
        }
    }
    
    def __init__(self):
        """초기화"""
        print("[별빛 우체국] 초기화 중...")
        
        # 1. Config 로드
        self.config = self._load_config()
        
        # 2. OpenAI Client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다!")
        self.client = OpenAI(api_key=api_key)
        
        # 3. (중요) 임베딩 캐시를 먼저 초기화
        self._embedding_cache = {}

        # 4. 디버그: RAG 출처 노출 여부
        self.debug_rag = os.getenv("DEBUG_RAG", "0") == "1"
        self._last_sources = []

        # 5. ChromaDB 초기화 (임베딩 캐시 이후에 수행해야 함)
        self.loading_embeddings = False
        self.collection = self._init_chromadb()
        
        # 6. RAG-D 상담 매뉴얼 벡터 DB 초기화 (전문 지식)
        self.counseling_vectordb = self._init_counseling_vectordb()
        
        # 7. 페르소나 로드 (부엉이의 개인 정보 - RAG-P)
        self.persona = self._load_persona()
        
        # 8. 세션 관리
        self.sessions = {}  # {username: PostOfficeSession}

    # --------------------------------------------
    # OpenAI 호출 래퍼 (재시도/백오프)
    # --------------------------------------------
    def _chat_completion(self, messages, model="gpt-4o-mini", temperature=0.7, max_tokens=400, max_retries=3):
        import time
        delay = 0.8
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as e:
                print(f"[경고] Chat 호출 실패(시도 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 1.8

    def _embedding_create(self, text: str, model="text-embedding-3-small", max_retries=3):
        import time
        delay = 0.8
        for attempt in range(max_retries):
            try:
                return self.client.embeddings.create(model=model, input=text)
            except Exception as e:
                print(f"[경고] Embedding 호출 실패(시도 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(delay)
                delay *= 1.8
        
        print("[별빛 우체국] 초기화 완료 ✨")
    
    def _load_config(self) -> dict:
        """설정 파일 로드"""
        config_path = BASE_DIR / "config" / "chatbot_config.json"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[경고] {config_path}를 찾을 수 없습니다. 기본 설정 사용")
            return {"name": "부엉", "system_prompts": {}}

    # -----------------------------
    # RAG-P: 페르소나 시스템 (부엉이의 자기 공개를 통한 공감)
    # -----------------------------
    def _load_persona(self) -> dict:
        """페르소나 파일 로드 (부엉이의 개인 정보)"""
        persona_path = BASE_DIR / "static" / "data" / "chatbot" / "chardb_text" / "owl_persona.json"
        try:
            with open(persona_path, 'r', encoding='utf-8') as f:
                persona = json.load(f)
                print("[RAG-P] 페르소나 로드 완료 ✨")
                return persona
        except FileNotFoundError:
            print(f"[경고] {persona_path}를 찾을 수 없습니다. 페르소나 없이 작동")
            return {}
        except Exception as e:
            print(f"[경고] 페르소나 로드 실패: {e}")
            return {}
    
    def _search_persona(self, user_message: str, conversation_context: str = "", used_stories: set = None) -> dict:
        """
        유저 메시지와 대화 맥락을 분석하여 적절한 페르소나 서브 스토리 검색
        
        Args:
            user_message: 유저 메시지
            conversation_context: 대화 맥락
            used_stories: 이미 사용한 스토리 ID set (예: {'love.breakup_bluntness', ...})
        
        Returns:
            dict: {
                "story_id": str,           # "love.breakup_bluntness"
                "category": str,           # "love"
                "story": str,              # 실제 스토리 내용
                "guidance": str,           # LLM 발화 가이드
                "activation": bool
            }
        """
        if not self.persona or "memory_vault" not in self.persona:
            return {"story_id": None, "category": None, "story": None, "guidance": None, "activation": False}
        
        if used_stories is None:
            used_stories = set()
        
        # 유저 메시지와 대화 맥락 결합
        combined_text = f"{user_message} {conversation_context}".lower()
        
        # 각 카테고리 → 서브 스토리 순회
        memory_vault = self.persona["memory_vault"]
        best_match = {"story_id": None, "category": None, "story": None, "guidance": None, "score": 0, "activation": False}
        
        for category, category_data in memory_vault.items():
            # 새 구조: stories 하위에 서브 스토리들이 있음
            if "stories" not in category_data:
                continue
            
            stories = category_data["stories"]
            
            for story_id, story_data in stories.items():
                # 스토리 전체 ID (예: "love.breakup_bluntness")
                full_story_id = f"{category}.{story_id}"
                
                # 이미 사용한 스토리는 제외! (세밀한 중복 방지)
                if full_story_id in used_stories:
                    continue
                
                # 트리거 키워드 매칭
                if "trigger_keywords" not in story_data:
                    continue
                
                # 키워드 매칭 점수 계산
                match_count = sum(1 for keyword in story_data["trigger_keywords"] if keyword in combined_text)
                
                if match_count > best_match["score"]:
                    # 대화 길이에 따라 content_short 또는 content_long 선택
                    content_key = "content_long" if len(conversation_context) > 500 else "content_short"
                    story_content = story_data.get(content_key, story_data.get("content_short", ""))
                    guidance = story_data.get("llm_speaking_guidance", "")
                    
                    best_match = {
                        "story_id": full_story_id,
                        "category": category,
                        "story": story_content,
                        "guidance": guidance,
                        "score": match_count,
                        "activation": True
                    }
        
        # 최소 매칭 점수 임계값 (1개 이상의 키워드 매칭 시에만 활성화)
        if best_match["score"] < 1:
            best_match["activation"] = False
        
        if best_match["activation"]:
            pass  # 활성화 시 추가 작업 없음
        
        return best_match

    # -----------------------------
    # 세션 영속화 (재기동/리로드 대비)
    # -----------------------------
    def _session_dir(self) -> Path:
        p = BASE_DIR / "static" / "data" / "chatbot" / "sessions"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _session_path(self, username: str) -> Path:
        import re
        safe = re.sub(r"[^\w\-가-힣]", "_", username)
        return self._session_dir() / f"session_{safe}.json"

    def _save_session(self, session: PostOfficeSession):
        try:
            path = self._session_path(session.username)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, ensure_ascii=False)
        except Exception as e:
            print(f"[경고] 세션 저장 실패: {e}")

    def _load_session(self, username: str) -> PostOfficeSession | None:
        try:
            path = self._session_path(username)
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                return PostOfficeSession.from_dict(data)
        except Exception as e:
            print(f"[경고] 세션 로드 실패: {e}")
        return None

    def _load_counselor_principles(self) -> str:
        """상담 태도/주의 원칙 로드 (유저에게 직접 노출 금지)"""
        p = BASE_DIR / "static" / "data" / "chatbot" / "chardb_text" / "guides" / "counselor_principles.txt"
        try:
            return p.read_text(encoding='utf-8').strip()
        except Exception:
            return ""

    def _detect_crisis(self, text: str) -> bool:
        if not text:
            return False
        t = text.lower()
        crisis_keywords = ["자살", "극단적", "죽고", "해치", "학대", "폭력", "살고싶지", "위험"]
        return any(k in t for k in crisis_keywords)

    def _normalize_intent_key(self, text: str) -> str:
        if not text:
            return ""
        t = text.lower().strip()
        # 편지 즉시 요청 의도 (다양한 변형 포함)
        letter_now_tokens = [
            "편지나", "편지내놔", "편지줘", "편지 줘", "편지주세요", "편지 주세요",
            "편지출력", "편지 출력", "편지를", "편지", "바로 편지", "편지 바로"
        ]
        if any(tok.replace(" ", "") in t.replace(" ", "") for tok in letter_now_tokens):
            return "ask_letter_now"
        # 단순 반복 질의 키(공백/구두점 제거)
        import re
        # 유니코드 \p 클래스는 Python re에서 지원되지 않음 → 한글/영문/숫자/공백만 유지
        base = re.sub(r"\s+", " ", re.sub(r"[^\w\s가-힣]", " ", t)).strip()
        return base

    def _update_repetition_state(self, session: PostOfficeSession, user_message: str) -> str:
        intent_key = self._normalize_intent_key(user_message)
        if session.last_intent_key is None:
            session.last_intent_key = intent_key
            session.repeated_intent_count = 1
        elif intent_key == session.last_intent_key and intent_key != "":
            session.repeated_intent_count += 1
        else:
            session.last_intent_key = intent_key
            session.repeated_intent_count = 1
        return intent_key

    def _detect_reenter(self, text: str) -> bool:
        if not text:
            return False
        t = text.replace(" ", "").lower()
        phrases = [
            "별빛우체국에한번더입장하시겠습니까?",
            "다시입장",
            "처음부터다시",
            "다시시작",
            "별빛우체국에다시한번입장",
            "다시한번입장",
        ]
        return any(p in t for p in phrases)

    def _detect_letter_confirm_yes(self, text: str) -> bool:
        if not text:
            return False
        t = text.replace(" ", "").lower()
        yes = ["응편지를받을래", "편지를받을래", "편지받을게", "편지받기"]
        return any(p in t for p in yes)

    def _detect_letter_confirm_no(self, text: str) -> bool:
        if not text:
            return False
        t = text.replace(" ", "").lower()
        no = ["아니더대화할래", "더대화할래", "계속대화", "대화계속"]
        return any(p in t for p in no)
    
    def _is_early_letter_request(self, user_message: str) -> bool:
        """명시적으로 편지 전달/조기 종료를 요구하는지 식별"""
        keywords = [
            "편지줬", "편지를줘", "편지받고싶", "편지내놔", "편지줘", "편지주세요", "편지출력",
            "그만", "싫어", "시러", "꺼져", "필요없", "불쾌", "하기싫", "묻지마"
        ]
        t = user_message.lower().replace(" ", "")
        return any(k in t for k in keywords)

    def _is_question(self, user_message: str) -> bool:
        """의문문: ?로 끝나거나, '왜', '무슨', '어째서' 등 질문 시작"""
        t = user_message.strip()
        lowers = t.lower()
        return t.endswith("?") or lowers.startswith("왜") or lowers.startswith("무슨") or lowers.startswith("어째서")
    
    def _init_chromadb(self):
        """ChromaDB 초기화 및 데이터 로드"""
        db_path = BASE_DIR / "static" / "data" / "chatbot" / "chardb_embedding"
        db_path.mkdir(parents=True, exist_ok=True)
        
        try:
            client = chromadb.PersistentClient(path=str(db_path))
            collection = client.get_or_create_collection(
                name="post_office_memories",
                metadata={"hnsw:space": "cosine"}
            )
            
            # 데이터가 없으면 로드
            current_count = collection.count()
            print(f"[ChromaDB] 현재 컬렉션 문서 수: {current_count}")
            
            if current_count == 0:
                print("[ChromaDB] 데이터가 비어있습니다. 백그라운드 로딩 시작...")
                def _bg_load():
                    try:
                        self.loading_embeddings = True
                        self._load_text_data(collection)
                    finally:
                        self.loading_embeddings = False
                threading.Thread(target=_bg_load, daemon=True).start()
            else:
                print(f"[ChromaDB] 기존 데이터 사용 ({current_count}개 문서)")
            
            print(f"[ChromaDB] 컬렉션 연결 완료: {collection.count()}개 문서")
            return collection
        except Exception as e:
            print(f"[경고] ChromaDB 초기화 실패: {e}")
            return None
    
    def _load_text_data(self, collection):
        """텍스트 데이터를 ChromaDB에 로드"""
        text_dir = BASE_DIR / "static" / "data" / "chatbot" / "chardb_text"
        
        documents = []
        metadatas = []
        ids = []
        doc_id = 0
        
        def chunk_text(content: str, max_chars: int = 900):
            blocks = [b.strip() for b in content.split("\n\n") if b.strip()]
            chunks = []
            for b in blocks:
                if len(b) <= max_chars:
                    chunks.append(b)
                else:
                    start = 0
                    while start < len(b):
                        end = min(start + max_chars, len(b))
                        chunks.append(b[start:end])
                        start = end
            return chunks
        
        # 각 방별 폴더 데이터 로드 (구조화된 데이터)
        for room_name in ['regret', 'love', 'anxiety', 'dream']:
            room_dir = text_dir / room_name
            if room_dir.exists():
                txt_files = list(room_dir.glob("*.txt"))
                
                for txt_file in txt_files:
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 파일을 청킹하여 여러 문서로 저장
                            if content.strip():
                                for idx, ch in enumerate(chunk_text(content)):
                                    documents.append(ch)
                                    metadatas.append({
                                        "room": room_name,
                                        "filename": txt_file.name,
                                        "chunk_index": idx,
                                        "type": "structured"
                                    })
                                    ids.append(f"{room_name}_{doc_id}")
                                    doc_id += 1
                    except Exception as e:
                        print(f"[에러] {txt_file.name} 로드 실패: {e}")
        
        # (제외) 전역 memories_* 파일은 이 프로젝트 범위에서 사용하지 않음
        
        # owl_character.txt 로드
        owl_file = text_dir / "owl_character.txt"
        if owl_file.exists():
            try:
                with open(owl_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        for idx, ch in enumerate(chunk_text(content)):
                            documents.append(ch)
                            metadatas.append({
                                "room": "all",
                                "filename": "owl_character.txt",
                                "chunk_index": idx,
                                "type": "character"
                            })
                            ids.append(f"character_{doc_id}")
                            doc_id += 1
            except Exception as e:
                print(f"[에러] owl_character.txt 로드 실패: {e}")
        
        # ChromaDB에 임베딩과 함께 추가
        if documents:
            try:
                print(f"[ChromaDB] {len(documents)}개 문서 임베딩 생성 중...")
                
                # 각 문서의 임베딩 생성
                embeddings = []
                for i, doc in enumerate(documents):
                    if i % 5 == 0:
                        print(f"  진행: {i}/{len(documents)}")
                    
                    # OpenAI로 임베딩 생성
                    embedding = self._create_embedding(doc[:8000])  # 토큰 제한 고려
                    if embedding:
                        embeddings.append(embedding)
                    else:
                        # 임베딩 생성 실패 시 해당 문서 제외
                        print(f"[경고] {metadatas[i]['filename']} 임베딩 생성 실패")
                        continue
                
                # ChromaDB에 추가
                if embeddings:
                    collection.add(
                        documents=documents[:len(embeddings)],
                        embeddings=embeddings,
                        metadatas=metadatas[:len(embeddings)],
                        ids=ids[:len(embeddings)]
                    )
                    print(f"[ChromaDB] ✅ {len(embeddings)}개 문서 로드 완료")
                else:
                    print(f"[경고] 임베딩 생성 실패. 문서를 추가하지 못했습니다.")
                
            except Exception as e:
                print(f"[에러] ChromaDB 데이터 추가 실패: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"[경고] 로드된 문서가 없습니다!")
    
    # ============================================
    # RAG-D: 상담 매뉴얼 벡터 DB
    # ============================================
    
    def _init_counseling_vectordb(self):
        """상담 매뉴얼 벡터 DB 초기화 (RAG-D)"""
        counseling_db_path = BASE_DIR / "static" / "data" / "chatbot" / "counseling_vectordb"
        
        print(f"[RAG-D] 초기화 중... ({counseling_db_path})")
        
        if not counseling_db_path.exists():
            print("[RAG-D] ❌ 상담 매뉴얼 벡터 DB가 없습니다.")
            print(f"        다음 명령어로 구축하세요: python tools/build_counseling_vectordb.py")
            return None
        
        try:
            from langchain_community.vectorstores import Chroma
            from langchain_openai import OpenAIEmbeddings
            
            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            
            vectordb = Chroma(
                persist_directory=str(counseling_db_path),
                embedding_function=embeddings,
                collection_name="counseling_knowledge"
            )
            
            doc_count = vectordb._collection.count()
            print(f"[RAG-D] ✅ 상담 매뉴얼 벡터 DB 로드 완료 ({doc_count}개 청크)")
            return vectordb
            
        except ImportError as ie:
            print(f"[RAG-D] ❌ Import 에러: {ie}")
            print("[RAG-D] ⚠️  langchain_community 또는 langchain_openai가 설치되지 않았습니다.")
            import traceback
            traceback.print_exc()
            return None
        except Exception as e:
            print(f"[RAG-D] ❌ 벡터 DB 로드 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _search_counseling_knowledge(self, query: str, top_k: int = 3) -> list:
        """상담 매뉴얼에서 관련 지식 검색 (RAG-D)"""
        if not self.counseling_vectordb:
            print(f"[RAG-D] ⚠️ 상담 매뉴얼 벡터 DB가 없습니다!")
            return []
        
        try:
            print(f"[RAG-D] 검색 시작 - 쿼리: '{query[:50]}...' (top_k={top_k})")
            results = self.counseling_vectordb.similarity_search(query, k=top_k)
            counseling_context = [doc.page_content for doc in results]
            
            print(f"[RAG-D] ✅ 검색 완료: {len(counseling_context)}개 청크")
            for i, ctx in enumerate(counseling_context, 1):
                print(f"[RAG-D]   청크 {i}: {ctx[:80]}... (총 {len(ctx)}자)")
            
            return counseling_context
            
        except Exception as e:
            print(f"[RAG-D] ❌ 검색 실패: {e}")
            return []
    
    # ============================================
    
    def _get_session(self, username: str) -> PostOfficeSession:
        """세션 가져오기 또는 생성"""
        if username not in self.sessions:
            loaded = self._load_session(username)
            if loaded:
                self.sessions[username] = loaded
            else:
                self.sessions[username] = PostOfficeSession(username)
        return self.sessions[username]
    
    def _create_embedding(self, text: str) -> list:
        """텍스트 임베딩 생성"""
        try:
            # 캐시 조회
            cached = self._embedding_cache.get(text)
            if cached is not None:
                return cached
            response = self._embedding_create(text=text, model="text-embedding-3-small")
            emb = response.data[0].embedding
            # 캐시 저장 (짧은 텍스트만 캐시)
            if len(text) <= 1000:
                self._embedding_cache[text] = emb
            return emb
        except Exception as e:
            print(f"[에러] Embedding 생성 실패: {e}")
            return None
    
    def _analyze_user_emotion(self, user_message: str) -> str:
        """
        DIR-E-103: LLM 기반 유저 감정 분석
        유저 메시지의 감정을 5가지 카테고리로 분류
        
        Returns:
            str: "JOY", "SADNESS", "ANGER", "BASIC", "QUESTION" 중 하나
        """
        try:
            emotion_prompt = f"""당신은 감정 분석 전문가입니다. 다음 유저 메시지의 감정을 정확히 하나만 선택하세요.

[유저 메시지]
"{user_message}"

[감정 카테고리]
- JOY: 행복, 기쁨, 만족, 희망, 긍정적 기대
- SADNESS: 슬픔, 후회, 상실감, 고통, 우울, 불안, 힘듦
- ANGER: 화, 짜증, 불쾌감, 거부감
- QUESTION: 질문, 의문, 궁금증
- BASIC: 위의 감정이 명확하지 않은 일반적인 대화

**규칙:**
1. 반드시 단어 하나만 출력하세요 (예: JOY)
2. 설명이나 다른 텍스트 없이 감정 코드만 출력하세요
3. 미묘한 감정이라도 가장 가까운 카테고리를 선택하세요

출력:"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 감정 분석 전문가입니다. 단어 하나만 출력합니다."},
                    {"role": "user", "content": emotion_prompt}
                ],
                temperature=0.3,  # 일관성을 위해 낮은 temperature
                max_tokens=10
            )
            
            emotion = response.choices[0].message.content.strip().upper()
            
            # 유효성 검사
            valid_emotions = ["JOY", "SADNESS", "ANGER", "QUESTION", "BASIC"]
            if emotion not in valid_emotions:
                print(f"[경고] 유효하지 않은 감정 분석 결과: {emotion}, BASIC으로 대체")
                emotion = "BASIC"
            
            return emotion
            
        except Exception as e:
            print(f"[에러] 감정 분석 실패: {e}")
            return "BASIC"
    
    def _determine_owl_emotion(self, user_message: str, session: PostOfficeSession, 
                               user_emotion: str, is_crisis: bool = False,
                               is_rejection: bool = False) -> str:
        """
        DIR-E-104: 상황 기반 부엉이 감정 결정
        LLM 감정 분석 결과를 기반으로, 상황에 따라 오버라이드
        
        Args:
            user_message: 유저 메시지
            session: 현재 세션
            user_emotion: LLM이 분석한 유저 감정
            is_crisis: 위기 상황 여부
            is_rejection: 유저의 거부/분노 감지 여부
            
        Returns:
            str: "기본", "기쁨", "슬픔", "분노", "의문" 중 하나
        """
        
        # 1. QUESTION: Phase 전환 확인, 재입장 요청 등
        # 재입장 확인 대기
        if hasattr(session, 'awaiting_reenter_confirm') and session.awaiting_reenter_confirm:
            return "의문"
        
        # 방 변경 요청 확인
        if hasattr(session, 'awaiting_room_change_confirm') and session.awaiting_room_change_confirm:
            return "의문"
        
        # 편지 즉시 전달 요청 감지
        early_letter_keywords = ["편지", "내놓", "줘", "보내줘", "빨리", "그만", "끝"]
        if any(k in user_message for k in early_letter_keywords):
            if session.phase == 3 and session.room_conversation_count < 3:
                return "의문"
            if session.phase == 3.6 and session.drawer_conversation_count < 2:
                return "의문"
        
        # 재입장 의도 감지
        reenter_keywords = ["다시", "처음", "새로", "재입장", "리셋"]
        if any(k in user_message for k in reenter_keywords) and any(w in user_message for w in ["시작", "입장", "해", "할래"]):
            return "의문"
        
        # 유저가 질문할 때
        if user_message.strip().endswith("?") or user_message.strip().endswith("？"):
            return "의문"
        
        # 2. ANGER: 유저가 부엉에게 화를 낼 때만! (공격적 표현)
        if is_rejection:
            return "분노"
        
        # 부엉에게 향한 공격/거부만 분노로 처리 (문맥 고려)
        # "너가 싫어", "너는 싫어" 같은 부엉에게 직접 향한 표현만 감지
        if any(pattern in user_message for pattern in ["너가 싫어", "너는 싫어", "넌 싫어", "당신 싫어", "부엉 싫어"]):
            return "분노"
        
        # 부엉과 무관한 일반 공격어만 체크
        direct_attack_keywords = ["꺼져", "시러", "불쾌", "까먹", "필요없"]
        if any(k in user_message for k in direct_attack_keywords):
            return "분노"
        
        # "화났어", "짜증나" 같은 유저의 감정 표현은 제외 (부엉에게 한 말이 아님)
        
        # 3. SADNESS: 위기 상황, 부정적 감정
        if is_crisis:
            return "슬픔"
        
        crisis_keywords = ["죽고", "자살", "자해", "극단", "끝", "포기"]
        if any(k in user_message for k in crisis_keywords):
            return "슬픔"
        
        sad_keywords = ["슬프", "힘들", "우울", "불안", "무서", "두렵", "걱정", "후회", "미안", "아프", "괴롭", "외로"]
        if any(k in user_message for k in sad_keywords):
            return "슬픔"
        
        # 4. JOY: 긍정적 감정, 편지 전달 후
        if session.phase in [4, 5]:
            # 편지 생성/전달 단계에서는 마음이 놓인 상태
            return "기쁨"
        
        joy_keywords = ["행복", "기쁨", "좋아", "만족", "희망", "감사", "고마", "즐거", "웃", "사랑"]
        if any(k in user_message for k in joy_keywords):
            return "기쁨"
        
        # 5. LLM 감정 분석 결과 활용 (오버라이드 없을 때)
        emotion_map = {
            "JOY": "기쁨",
            "SADNESS": "슬픔",
            "ANGER": "분노",
            "QUESTION": "의문",
            "BASIC": "기본"
        }
        
        return emotion_map.get(user_emotion, "기본")
    
    def _should_show_emotion(self, current_emotion: str, last_emotion: str, session: PostOfficeSession, is_crisis: bool = False) -> bool:
        """
        감정 태그를 출력할지 결정 (중요한 변화만 감지)
        
        Args:
            current_emotion: 현재 감정
            last_emotion: 이전 감정
            session: 현재 세션
            is_crisis: 위기 상황 여부 (추가)
            
        Returns:
            bool: True면 감정 태그 출력, False면 출력 안 함
        """
        
        # ✅ 위기 모드에서는 슬픔 감정 무조건 출력
        if is_crisis and current_emotion == "슬픔":
            print(f"[감정] 위기 모드 활성화 → 슬픔 감정 강제 출력 ✅")
            return True
        
        # Phase 전환 시점에는 감정 출력 안 함 (이미지 충돌 방지)
        # Phase 2 (방 선택), Phase 3.5 (서랍 선택), Phase 4/5 (편지)
        transition_phases = [2, 3.5, 4, 5]
        if session.phase in transition_phases:
            return False
        
        # 감정 우선순위 (강도)
        emotion_priority = {
            "기본": 0,   # 평온
            "의문": 1,   # 질문
            "기쁨": 2,   # 긍정
            "슬픔": 3,   # 부정 (강함)
            "분노": 4    # 부정 (매우 강함)
        }
        
        last_priority = emotion_priority.get(last_emotion, 0)
        current_priority = emotion_priority.get(current_emotion, 0)
        
        # 동일한 감정이면 절대 출력 안 함
        if current_emotion == last_emotion:
            print(f"[감정] 동일 감정 유지: {current_emotion} → 감정 출력 제외")
            return False
        
        # "기본" 감정은 중립 상태이므로 출력하지 않음
        if current_emotion == "기본":
            print(f"[감정] 기본 감정(중립)으로 전환 → 감정 출력 제외")
            return False
        
        # 감정 변화 강도 계산
        change = abs(current_priority - last_priority)
        
        # ✅ threshold를 1로 낮춤 (슬픔→기쁨 같은 변화도 감지)
        threshold = 2
        
        if change >= threshold:
            print(f"[감정] 감정 변화 감지: {last_emotion}({last_priority}) → {current_emotion}({current_priority}), 변화량={change} ✅")
            return True
        else:
            print(f"[감정] 변화 없음: {last_emotion}({last_priority}) → {current_emotion}({current_priority}), 변화량={change} → 감정 출력 제외")
            return False
    
    def _split_long_reply(self, text: str, max_length: int = 80) -> list:
        """
        긴 문장을 적당한 길이로 분할 (자연스러운 끊김)
        
        Args:
            text: 원본 텍스트
            max_length: 최대 길이 (기본 80자)
            
        Returns:
            list: 분할된 문장들
        """
        if len(text) <= max_length:
            return [text]
        
        result = []
        current = ""
        
        # 1차: 문장 부호로 분할 (. ! ? 등)
        sentences = []
        temp = ""
        for char in text:
            temp += char
            if char in ['.', '!', '?', '…'] and len(temp) > 5:  # 너무 짧은 문장은 합침
                sentences.append(temp.strip())
                temp = ""
        if temp.strip():
            sentences.append(temp.strip())
        
        # 2차: 각 문장이 max_length 초과하면 추가 분할
        for sentence in sentences:
            if len(current) + len(sentence) <= max_length:
                current += sentence + " "
            else:
                if current:
                    result.append(current.strip())
                # 문장이 너무 길면 괄호, 쉼표 기준으로 분할
                if len(sentence) > max_length:
                    parts = sentence.split('(')
                    for i, part in enumerate(parts):
                        if i > 0:
                            part = '(' + part
                        if len(part) > max_length:
                            # 쉼표 기준으로 한번 더 분할
                            sub_parts = part.split(',')
                            for j, sub in enumerate(sub_parts):
                                if j > 0:
                                    sub = ',' + sub
                                if sub.strip():
                                    result.append(sub.strip())
                        else:
                            if part.strip():
                                result.append(part.strip())
                    current = ""
                else:
                    current = sentence + " "
        
        if current.strip():
            result.append(current.strip())
        
        # 빈 문자열 제거
        result = [r for r in result if r]
        
        return result if result else [text]
    
    def _search_similar(self, query: str, top_k: int = 3, room_filter: str = None, similarity_threshold: float = 0.72) -> list:
        """RAG 검색 (방별 필터링 지원)"""
        if not self.collection:
            return []
            
        try:
            query_embedding = self._create_embedding(query)
            if not query_embedding:
                return []
            
            # 방 필터링 (특정 방의 데이터만 검색)
            where_filter = None
            if room_filter:
                where_filter = {"room": room_filter}
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max(top_k * 3, 6),
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            documents = []
            if results and results.get('documents'):
                docs = results['documents'][0]
                dists = results.get('distances', [[1.0] * len(docs)])[0]
                metas = results.get('metadatas', [[{}] * len(docs)])[0]
                # 거리 → 유사도 변환 후 임계값 필터
                ranked = []
                debug_list = []
                for doc, dist, md in zip(docs, dists, metas):
                    sim = 1.0 / (1.0 + float(dist))
                    if sim >= similarity_threshold:
                        ranked.append((sim, doc, md))
                    if self.debug_rag:
                        debug_list.append((sim, md))
                ranked.sort(key=lambda x: x[0], reverse=True)
                documents = [doc for _, doc, _ in ranked[:top_k]]
                # 디버그: 콘솔/상태에 출처 노출
                if self.debug_rag:
                    debug_list.sort(key=lambda x: x[0], reverse=True)
                    self._last_sources = [
                        f"{md.get('filename')}#chunk={md.get('chunk_index')} sim={s:.3f}"
                        for s, md in debug_list[:max(top_k, 3)]
                    ]
                    for line in self._last_sources:
                        print(f"[RAG] {line}")
            
            return documents
        except Exception as e:
            print(f"[에러] RAG 검색 실패: {e}")
            return []

    def _summarize_if_needed(self, session: PostOfficeSession):
        """대화가 길어지면 자동 요약을 수행하여 프롬프트 컨텍스트를 경량화"""
        total_msgs = len(session.conversation_history)
        # 일정 간격(예: 30개 메시지 증가)마다 요약
        if total_msgs - session.last_summary_messages_len < 30:
            return
        # 최근 사용자 메시지 중심으로 축약 요약
        user_messages = [m['content'] for m in session.conversation_history if m['role'] == 'user']
        recent_slice = "\n".join(user_messages[-30:])
        system = (
            "아래 대화를 5문장 이내의 핵심 요약으로 압축하세요. "
            "인물/사건/감정/목표를 포함하고 불필요한 세부는 제거하세요."
        )
        try:
            response = self._chat_completion(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": recent_slice}
                ],
                temperature=0.2,
                max_tokens=220
            )
            summary = response.choices[0].message.content.strip()
            # 누적 요약 방식: 기존 요약과 결합 후 다시 한 줄 정리
            if session.summary_text:
                merged = f"[이전 요약]\n{session.summary_text}\n\n[최근 요약]\n{summary}"
                response2 = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "두 요약을 6문장 이내 하나로 통합 요약하세요."},
                        {"role": "user", "content": merged}
                    ],
                    temperature=0.2,
                    max_tokens=220
                )
                session.summary_text = response2.choices[0].message.content.strip()
            else:
                session.summary_text = summary
            session.last_summary_messages_len = total_msgs
        except Exception as e:
            print(f"[경고] 요약 실패: {e}")
    
    def _detect_room_selection(self, user_message: str, exclude_before_malggo: bool = False) -> str:
        """
        방 선택 감지
        
        Args:
            user_message: 유저 메시지
            exclude_before_malggo: "말고" 앞의 방 이름 제외 여부
        """
        message = user_message
        message_lower = user_message.lower()
        
        # "말고" 뒤의 내용만 검색 (방 변경 요청 시)
        if exclude_before_malggo and "말고" in message:
            message = message.split("말고", 1)[1]  # "말고" 뒤만 사용
            message_lower = message.lower()
        
        if '후회' in message or 'regret' in message_lower:
            return 'regret'
        elif '사랑' in message or 'love' in message_lower:
            return 'love'
        elif '불안' in message or 'anxiety' in message_lower:
            return 'anxiety'
        elif '꿈' in message or 'dream' in message_lower:
            return 'dream'
        
        return None
    
    def _detect_room_change_request(self, user_message: str, current_room: str) -> dict:
        """
        방 변경 요청 감지 (현재 방과 다른 방으로 가려는 시도)
        
        Returns:
            dict: {"type": "specific"/"any"/"same", "room": str or None}
        """
        # 방 변경 키워드 체크
        change_keywords = [
            "방으로", "방 가고", "방에 가", "다른 방", "바꾸고", "이동",
            "말고", "대신", "방을", "방 할래", "방 하고", "가고 싶",
            "바꿀래", "옮기고", "변경"
        ]
        has_change_intent = any(keyword in user_message for keyword in change_keywords)
        
        if not has_change_intent:
            return {"type": None, "room": None}
        
        # "말고" 뒤의 방만 감지 (중요!)
        requested_room = self._detect_room_selection(user_message, exclude_before_malggo=True)
        
        # 디버그 로그
        print(f"[방 변경 감지] 입력: '{user_message}'")
        print(f"[방 변경 감지] 현재 방: {current_room}, 요청 방: {requested_room}")
        print(f"[방 변경 감지] 변경 의도: {has_change_intent}")
        
        # 케이스 1: 구체적인 다른 방 지정
        if requested_room and requested_room != current_room:
            print(f"[방 변경 감지] ✅ 구체적 변경: {current_room} → {requested_room}")
            return {"type": "specific", "room": requested_room}
        
        # 케이스 2: 현재 방과 같은 방 요청
        if requested_room and requested_room == current_room:
            print(f"[방 변경 감지] ⚠️ 같은 방 요청: {current_room}")
            return {"type": "same", "room": current_room}
        
        # 케이스 3: "다른 방"이라고만 함 (구체적 방 이름 없음)
        if "다른 방" in user_message or "방 바꾸" in user_message or "방 변경" in user_message:
            print(f"[방 변경 감지] ✅ 비구체적 변경 요청: 방 선택 버튼 제공")
            return {"type": "any", "room": None}
        
        print(f"[방 변경 감지] ❌ 감지 안됨")
        return {"type": None, "room": None}
    
    def _get_stamp_info(self, stamp_code: str) -> dict:
        """우표 코드의 정보 반환"""
        # 클래스 변수 STAMP_CODES 사용
        for room_codes in self.STAMP_CODES.values():
            if stamp_code in room_codes:
                return room_codes[stamp_code]
        
        # 찾지 못하면 기본값
        return {'name': '기억의 조각', 'situation': '잃어버린 기억에 대한 성찰'}
    
    def _determine_stamp_code(self, session: PostOfficeSession) -> str:
        """DIR-S-401: 대화 내용을 분석하여 18개 우표 코드 중 하나를 선택"""
        # 클래스 변수 STAMP_CODES 사용
        
        # 대화 요약
        conversation_summary = session.get_summary().lower()
        selected_room = session.selected_room
        
        # 현재 방의 우표 코드들만 필터링
        if selected_room not in self.STAMP_CODES:
            print(f"[우표] 알 수 없는 방: {selected_room}")
            return 'R_1'  # 기본값
        
        room_stamps = self.STAMP_CODES[selected_room]
        
        # DIR-S-402: 키워드 매칭으로 가장 적합한 우표 코드 찾기
        best_code = None
        max_score = 0
        
        for code, data in room_stamps.items():
            score = sum(1 for keyword in data['keywords'] if keyword in conversation_summary)
            if score > max_score:
                max_score = score
                best_code = code
        
        # 매칭 실패 시 방의 첫 번째 코드 반환
        if not best_code or max_score == 0:
            best_code = list(room_stamps.keys())[0]
        
        # DIR-S-405: 18개 목록 외 코드는 출력 불가 - 검증
        all_valid_codes = []
        for room_codes in self.STAMP_CODES.values():
            all_valid_codes.extend(room_codes.keys())
        
        if best_code not in all_valid_codes:
            print(f"[우표] 경고: 유효하지 않은 코드 {best_code} → R_1로 대체")
            best_code = 'R_1'
        
        return best_code
    
    def _build_user_prompt(self, user_message: str, session: PostOfficeSession, rag_context: list = None) -> str:
        """사용자 프롬프트 구성"""
        prompt_parts = []
        
        # RAG 컨텍스트
        if rag_context:
            context_str = "\n".join([f"- {doc}" for doc in rag_context])
            prompt_parts.append(f"[참고 정보]\n{context_str}\n")

        # 장기 요약(있다면 상단에 제공)
        if session.summary_text:
            prompt_parts.append(f"[대화 장기 요약]\n{session.summary_text}\n")
        
        # 대화 기록 (현재 세션의 전체 대화)
        if len(session.conversation_history) > 0:
            # 현재 판의 모든 대화 (이전 편지 작성 판은 제외)
            recent_history = session.conversation_history  # 전체 대화!
            history_str = "\n".join([
                f"{'유저' if msg['role'] == 'user' else '부엉'}: {msg['content']}"
                for msg in recent_history
            ])
            prompt_parts.append(f"[대화 맥락 - 현재 세션의 전체 대화]\n{history_str}\n")
        
        # 현재 메시지
        prompt_parts.append(f"\n[현재 유저 입력]\n유저: {user_message}")
        
        # 지침
        prompt_parts.append(f"\n[지침]\n위 대화 맥락(현재 세션의 모든 대화)을 고려하여, 유저의 현재 메시지에 자연스럽게 이어지는 공감과 질문을 해주세요. 이전에 했던 질문을 절대 반복하지 마세요.")
        
        return "\n".join(prompt_parts)
    
    def _generate_letter(self, session: PostOfficeSession) -> str:
        """DIR-S-403: 편지 생성 (우표 코드의 상황 정보 포함)"""
        
        # 우표 코드 정보 가져오기
        stamp_code = session.selected_drawer  # 우표 코드가 저장되어 있음
        
        # 클래스 변수 STAMP_CODES 사용
        stamp_info = self._get_stamp_info(stamp_code)
        
        if not stamp_info:
            stamp_situation = "잃어버린 기억에 대한 성찰"
            print(f"[편지] 경고: 우표 코드 {stamp_code}를 찾을 수 없음 → 기본 상황 사용")
        else:
            stamp_situation = stamp_info['situation']
        
        # 대화 요약
        conversation_summary = session.get_summary()
        room_data = self.config.get('rooms', {}).get(session.selected_room, {})
        
        # DIR-S-403: 우표 코드의 '상황'을 프롬프트에 제공
        letter_prompt = f"""당신은 '10년 전의 나' 또는 '10년 후의 나'의 목소리로 편지를 작성합니다.

[편지 작성 규칙]
1. 편지 형식으로 작성 (수신인: 지금의 나에게)
2. 따뜻하고 진솔한 어조
3. 위로, 격려, 또는 깨달음을 담기
4. 200-400자 내외
5. **중요**: 대화 내용을 분석하여 다음 중 적절한 화자를 선택하세요:
   - "10년 전의 너": 과거 회상, 후회, 과거 선택에 대한 내용이 주된 경우
   - "10년 후의 너": 현재 고민, 불안, 미래에 대한 걱정이 주된 경우
6. 선택한 화자의 시점에서 지금의 나를 바라보며 작성
7. 유저와 나눈 긴 대화의 핵심을 담아야 함

[선택한 방과 우표]
- 방: {room_data.get('name', '')}
- 우표 주제: {stamp_situation}
- **편지는 위 우표 주제를 반영하여 작성하세요**

[유저와의 대화 내용 (총 {session.room_conversation_count + session.drawer_conversation_count}회)]
{conversation_summary}

위 긴 대화 내용을 바탕으로 편지를 작성하세요.
편지 시작은 "To. 지금의 나에게. 나는 [10년 전의 너/10년 후의 너]야." 형식으로 시작하세요.
유저가 진정으로 필요로 하는 말을 담아주세요.
"""
        
        try:
            response = self._chat_completion(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": letter_prompt},
                    {"role": "user", "content": "편지를 작성해주세요."}
                ],
                temperature=0.7,
                max_tokens=520
            )
            
            letter = response.choices[0].message.content.strip()
            return letter
        except Exception as e:
            print(f"[에러] 편지 생성 실패: {e}")
            return "To. 지금의 나에게.\n\n네가 찾고 있던 그 마음, 여기 있어. 잊지 마."
    
    def generate_response(self, user_message: str, username: str = "방문자") -> dict:
        """응답 생성"""
        
        # 세션 가져오기
        session = self._get_session(username)
        
        # Phase 1: 입장 (명시적 init으로만 시작)
        if user_message.strip().lower() == "init":
            # 세션 초기화 (새로운 대화 시작)
            session.conversation_history = []
            session.phase = 1
            session.intro_step = 1
            session.selected_room = None
            session.selected_drawer = None
            session.room_conversation_count = 0
            session.drawer_conversation_count = 0
            # 페르소나 사용 기록 초기화
            session.used_persona_stories.clear()
            session.used_persona_categories.clear()  # 하위 호환성
            
            # 첫 번째 메시지
            message1 = f"흐음. 이곳은 시간의 경계에 있는 '별빛 우체국'이자, 잃어버린 기억의 저장소일세. 나는 이곳의 국장인 '부엉'이지."
            
            # 두 번째 메시지
            message2 = f"(장부를 뒤적이며) 자, {username} 앞으로 도착한 '편지'가 있는데, 꽤 오래 묵혀뒀더군. 아마 '다른 세계선의 당신'이 보낸 것일세."
            
            session.add_message("user", user_message)
            session.add_message("assistant", message1 + " " + message2)
            # 세션 저장
            self._save_session(session)
            
            return {
                "replies": [message1, message2],  # 전환 시점이므로 감정 태그 제외
                "image": None,
                "phase": 1,
                "intro_step": 1,
                "buttons": ["나에게 온 편지라고?"]
            }
        
        # 사용자 메시지 기록 + 반복 의도 상태 갱신 + 위기 완충 세팅
        session.add_message("user", user_message)
        intent_key = self._update_repetition_state(session, user_message)
        if self._detect_crisis(user_message):
            # 위기 표현 직후 1턴 완충 적용
            session.crisis_cooldown = max(session.crisis_cooldown, 1)
        # 세션 저장
        self._save_session(session)

        # 재입장 확인 대기 응답 처리
        if session.awaiting_reenter_confirm:
            if "응" in user_message or "예" in user_message or "재입장" in user_message:
                # 재입장 승인 → 세션 초기화
                session.conversation_history = []
                session.phase = 1
                session.intro_step = 1
                session.selected_room = None
                session.selected_drawer = None
                session.room_conversation_count = 0
                session.drawer_conversation_count = 0
                session.letter_content = None
                session.crisis_cooldown = 0
                session.awaiting_reenter_confirm = False
                # 페르소나 사용 기록 초기화
                session.used_persona_stories.clear()
                session.used_persona_categories.clear()
                self._save_session(session)

                message1 = "그렇군. (고개를 끄덕이며) 다시 입구로 가자."
                message2 = "흐음. 이곳은 시간의 경계에 있는 '별빛 우체국'이자, 잃어버린 기억의 저장소일세. 나는 이곳의 국장인 '부엉'이지."
                message3 = f"(장부를 뒤적이며) 자, {username} 앞으로 도착한 '편지'가 있는데, 꽤 오래 묵혀뒀더군. 아마 '다른 세계선의 당신'이 보낸 것일세."
                session.add_message("assistant", message1 + " " + message2 + " " + message3)
                return {
                    "replies": [message1, message2, message3],
                    "image": None,
                    "phase": 1,
                    "intro_step": 1,
                    "buttons": ["나에게 온 편지라고?"]
                }
            else:
                # 재입장 거부 → 현재 상태 유지
                session.awaiting_reenter_confirm = False
                self._save_session(session)
                
                reply = "그렇군. (고개를 끄덕이며) 그럼 계속 이어가자고."
                session.add_message("assistant", reply)
                return {
                    "reply": reply,
                    "image": None,
                    "phase": session.phase
                }
        
        # ✅ 재입장 의도 감지
        if self._detect_reenter(user_message):
            # Phase 5(편지 받은 후)에서는 확인 없이 바로 재입장
            if session.phase == 5:
                # 세션 초기화
                session.conversation_history = []
                session.phase = 1
                session.intro_step = 1
                session.selected_room = None
                session.selected_drawer = None
                session.room_conversation_count = 0
                session.drawer_conversation_count = 0
                session.letter_content = None
                session.stamp_image = None
                session.summary_text = ""
                session.last_summary_messages_len = 0
                session.awaiting_reenter_confirm = False
                session.awaiting_room_change_confirm = False
                session.awaiting_letter_confirm = False
                session.requested_new_room = None
                session.used_persona_stories.clear()
                session.used_persona_categories.clear()
                self._save_session(session)

                message1 = "그렇군. (고개를 끄덕이며) 다시 입구로 가자."
                message2 = "흐음. 이곳은 시간의 경계에 있는 '별빛 우체국'이자, 잃어버린 기억의 저장소일세. 나는 이곳의 국장인 '부엉'이지."
                message3 = f"(장부를 뒤적이며) 자, {username} 앞으로 도착한 '편지'가 있는데, 꽤 오래 묵혀뒀더군. 아마 '다른 세계선의 당신'이 보낸 것일세."
                session.add_message("assistant", message1 + " " + message2 + " " + message3)
                return {
                    "replies": [message1, message2, message3],
                    "image": None,
                    "phase": 1,
                    "intro_step": 1,
                    "buttons": ["나에게 온 편지라고?"]
                }
            
            # Phase 5가 아닌 경우에만 확인 버튼 띄우기
            session.awaiting_reenter_confirm = True
            self._save_session(session)
            
            reply = "다시 시작하고 싶군. ...확실한가? 지금까지의 대화는 사라지고, 처음부터 다시 시작하게 돼. 별빛 우체국에 다시 입장하겠나?"
            
            return {
                "reply": reply,
                "image": None,
                "phase": session.phase,
                "buttons": ["응, 다시 시작할래", "아니, 계속 할래"]
            }

        # 방 변경 확인 대기 응답 처리
        if session.awaiting_room_change_confirm:
            if "응" in user_message and "재입장" in user_message:
                # 재입장 선택 → 세션 초기화
                room_name_map = {
                    'regret': '후회의 방',
                    'love': '사랑의 방',
                    'anxiety': '불안의 방',
                    'dream': '꿈의 방'
                }
                requested_room_name = room_name_map.get(session.requested_new_room, '다른 방')
                
                # 세션 초기화
            session.conversation_history = []
            session.phase = 1
            session.intro_step = 1
            session.selected_room = None
            session.selected_drawer = None
            session.room_conversation_count = 0
            session.drawer_conversation_count = 0
            session.letter_content = None
            session.crisis_cooldown = 0
            session.awaiting_letter_confirm = False
            session.awaiting_room_change_confirm = False
            session.requested_new_room = None
            session.used_persona_stories.clear()
            session.used_persona_categories.clear()  # 하위 호환성
            self._save_session(session)

            message1 = "그렇군. (고개를 끄덕이며) 다시 입구로 가자."
            message2 = f"흐음. 이곳은 시간의 경계에 있는 '별빛 우체국'이자, 잃어버린 기억의 저장소일세. 나는 이곳의 국장인 '부엉'이지."
            message3 = f"(장부를 뒤적이며) 자, {username} 앞으로 도착한 '편지'가 있는데, 꽤 오래 묵혀뒀더군. 아마 다른 세계선의 당신이 보낸 것일세."
            
            session.add_message("assistant", message1 + " " + message2 + " " + message3)
            return {
                "replies": [message1, message2, message3],
                "image": None,
                "phase": 1,
                "intro_step": 1,
                "buttons": ["나에게 온 편지라고?"]
            }
        elif "아니" in user_message and "계속" in user_message:
            # 현재 방 유지
            session.awaiting_room_change_confirm = False
            session.requested_new_room = None
            self._save_session(session)
            
            return {
                "reply": "알겠어. (고개를 끄덕이며) 여기서 계속하자고. 편하게 이야기해.",
                "image": None,
                "phase": session.phase
            }

        # 편지 확인 대기 응답 처리 (전 단계에서 버튼 노출 후)
        if session.awaiting_letter_confirm:
            if self._detect_letter_confirm_yes(user_message):
                # DIR-S-404: 편지 즉시 전달 (우표 코드 포함)
                stamp_code = self._determine_stamp_code(session)
                
                # 우표 정보 가져오기
                stamp_info = self._get_stamp_info(stamp_code)
                stamp_msg = f"자 너의 편지에 붙어 있었던 우표는 {stamp_code}이다. {stamp_info['mean']}"
                
                letter = self._generate_letter(session)
                session.letter_content = letter
                letter_bubble = f"{letter}"  # 편지 내용만
                
                session.phase = 5
                session.awaiting_letter_confirm = False
                session.add_message("assistant", stamp_msg)
                session.add_message("assistant", letter_bubble)
                self._save_session(session)
                return {
                    "replies": [stamp_msg, letter_bubble],
                    "image": None,
                    "phase": 5,
                    "letter": letter,
                    "stamp_code": stamp_code,  # DIR-S-404: 우표 코드 반환
                    "is_letter_end": True,
                    "buttons": ["별빛 우체국에 다시 한번 입장"]
                }
            elif self._detect_letter_confirm_no(user_message):
                # 확인 취소: 남은 대화 유지, 안내만 하고 계속 Phase 유지
                session.awaiting_letter_confirm = False
                self._save_session(session)
                return {
                    "reply": "좋아. 서두르지 말자. 네가 편할 만큼만 이야기하자.",
                    "image": None,
                    "phase": session.phase
                }
        
        # Phase 1 → Phase 2 전환: "나에게 온 편지라고?" 입력 시
        if session.phase == 1:
            if "나에게 온 편지라고?" in user_message or "편지" in user_message:
                session.phase = 2
            else:
                # 잘못된 입력
                reply = "...흠? (고개를 갸우뚱하며)\n버튼을 눌러주겠나?"
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 1,
                    "buttons": ["나에게 온 편지라고?"]
                }
        
        # Phase 2: 방 선택
        if session.phase == 2:
            room_selected = self._detect_room_selection(user_message)
            
            if room_selected:
                # 방 선택 성공 → Phase 3으로 전환
                session.selected_room = room_selected
                session.phase = 3
                
                room_data = self.config.get('rooms', {}).get(room_selected, {})
                message1 = f"흐음. 역시. {room_data.get('name', '')}이군."
                message2 = room_data.get('description', '')
                message3 = "...이 방 어딘가에 네 편지가 있지. 편하게 이야기해봐. 네 기억을 더듬어보자고."
                
                session.add_message("assistant", message1 + " " + message2 + " " + message3)
                
                return {
                    "replies": [message1, message2, message3],  # 전환 시점이므로 감정 태그 제외
                    "image": None,
                    "phase": session.phase,
                    "enable_input": True  # 자유 입력 가능
                }
            else:
                # 방을 선택하지 않음 → 방 선택 요구
                message1 = "그래. '기억의 저장실'에 있다. 따라와."
                message2 = "네 편지는 저 문들 중 하나에 있지. ...어느 방에서 잃어버린 기억 같나?"
                
                session.add_message("assistant", message1 + " " + message2)
                
                return {
                    "replies": [message1, message2],  # 전환 시점이므로 감정 태그 제외
                    "image": None,
                    "phase": session.phase,
                    "buttons": ["'후회'의 방", "'사랑'의 방", "'불안'의 방", "'꿈'의 방"]
                }
        
        # Phase 3: 방에서의 대화
        if session.phase == 3:
            # 방 변경 요청 감지
            room_change_result = self._detect_room_change_request(user_message, session.selected_room)
            
            # 케이스 1: 구체적인 다른 방으로 변경
            if room_change_result["type"] == "specific":
                room_name_map = {
                    'regret': '후회의 방',
                    'love': '사랑의 방',
                    'anxiety': '불안의 방',
                    'dream': '꿈의 방'
                }
                requested_room_name = room_name_map.get(room_change_result["room"], '다른 방')
                
                session.awaiting_room_change_confirm = True
                session.requested_new_room = room_change_result["room"]
                self._save_session(session)
                
                return {
                    "reply": f"{requested_room_name}으로 가고 싶군. ...흠. 이곳에서 바로 갈 수는 없어. 우체국에 재입장하면 다른 방으로 다시 갈 수 있긴 한데. ...우체국에 재입장하겠나?",
                    "image": None,
                    "phase": 3,
                    "buttons": ["응, 우체국에 재입장할래", "아니, 이 방에서 계속 할래"]
                }
            
            # 케이스 2: 현재 방과 같은 방 요청
            elif room_change_result["type"] == "same":
                room_name_map = {
                    'regret': '후회의 방',
                    'love': '사랑의 방',
                    'anxiety': '불안의 방',
                    'dream': '꿈의 방'
                }
                current_room_name = room_name_map.get(session.selected_room, '이 방')
                
                reply = f"흠... (고개를 갸우뚱하며) 이미 {current_room_name}에 있는데. 다른 곳으로 가고 싶은 건가, 아니면 여기서 계속할 건가?"
                
                return {
                    "reply": reply,  # 전환 확인이므로 감정 태그 제외
                    "image": None,
                    "phase": 3
                }
            
            # 케이스 3: "다른 방"이라고만 함 (구체적인 방 지정 없음)
            elif room_change_result["type"] == "any":
                session.awaiting_room_change_confirm = True
                session.requested_new_room = None  # 구체적인 방 미정
                self._save_session(session)
                
                reply = "다른 방으로 가고 싶군. ...흠. 이곳에서 바로 갈 수는 없어. 우체국에 재입장하면 다른 방으로 다시 갈 수 있긴 한데. ...우체국에 재입장하겠나?"
                
                return {
                    "reply": reply,  # 전환 확인이므로 감정 태그 제외
                    "image": None,
                    "phase": 3,
                    "buttons": ["응, 우체국에 재입장할래", "아니, 이 방에서 계속 할래"]
                }
            
            # ✅ 조기 편지 요청 처리 (Phase 3)
            if intent_key == "ask_letter_now":
                session.awaiting_letter_confirm = True
                self._save_session(session)
                
                reply = "아직 대화를 마무리하지 못했는데 편지를 먼저 꺼내줄까?"
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 3,
                    "buttons": ["응 편지를 받을래", "아니, 더 대화할래"]
                }
            
            # ✅ 조기 편지 확인 후 처리 (Phase 3)
            if session.awaiting_letter_confirm:
                if "편지" in user_message and "받" in user_message:
                    # 편지 받기로 선택
                    session.awaiting_letter_confirm = False
                    session.phase = 4
                    self._save_session(session)
                    # Phase 4에서 편지 생성하도록 아래로 계속 진행
                    pass  # Phase 4로 자연스럽게 이어짐
                elif "대화" in user_message or "아니" in user_message:
                    # 대화 계속하기로 선택
                    session.awaiting_letter_confirm = False
                    self._save_session(session)
                    
                    reply = "알겠어. 천천히 이야기해봐."
                    return {
                        "reply": reply,
                        "image": None,
                        "phase": 3
                    }
                else:
                    # 다른 말을 하면 다시 확인
                    return {
                        "reply": "편지를 먼저 받고 싶은가? 아니면 더 이야기하고 싶은가?",
                        "image": None,
                        "phase": 3,
                        "buttons": ["응 편지를 받을래", "아니, 더 대화할래"]
                    }

            # ✅ 반복 스로틀: 동일 의도 3회 이상이면 확인 버튼 제공
            if session.repeated_intent_count >= 3:
                session.awaiting_letter_confirm = True
                self._save_session(session)
                return {
                    "reply": "아직 대화를 마무리하지 못했는데 편지를 먼저 꺼내줄까?",
                    "image": None,
                    "phase": 3,
                    "buttons": ["응 편지를 받을래", "아니, 더 대화할래"]
                }
            # 로딩 중이더라도, 이미 인덱스가 만들어졌다면 바로 진행
            if getattr(self, "loading_embeddings", False) and self.collection and self.collection.count() == 0:
                return {
                    "reply": "(자료를 정리하는 중이네… 잠깐만 기다려 주겠나.)",
                    "image": None,
                    "phase": 3
                }
            session.room_conversation_count += 1
            # 길이 증가시 자동 요약
            self._summarize_if_needed(session)
            
            # 유저의 거부/불쾌감 감지
            rejection_keywords = ["시러", "싫어", "꺼져", "불쾌", "필요없", "그만", "하기싫", "묻지마"]
            user_lower = user_message.lower().replace(" ", "")
            is_rejection = any(keyword in user_lower for keyword in rejection_keywords)
            
            # 거부 반응 시: 사과 후 주제 전환 (프롬프트에서 처리)
            # 하지만 최소 대화 횟수는 충족해야 함
            
            # RAG 검색 (현재 방 우선)
            rag_context = self._search_similar(
                user_message,
                top_k=5,
                room_filter=session.selected_room,
                similarity_threshold=0.72
            )
            # 매칭이 없으면 전역으로 완화 검색
            if not rag_context:
                rag_context = self._search_similar(
                    user_message,
                    top_k=5,
                    room_filter=None,
                    similarity_threshold=0.65
                )
            
            # RAG-D: 위기 상황 또는 전문 상담이 필요한 경우 상담 매뉴얼 참조
            counseling_knowledge = []
            is_crisis = self._detect_crisis(user_message)
            
            # 위기 상황이거나, 불안/우울 관련 키워드가 있을 때 상담 매뉴얼 검색
            crisis_keywords = ["우울", "불안", "힘들", "무서", "두렵", "걱정", "슬프", "외로", "고민", 
                             "죽고", "자해", "자살", "극단", "아프", "괴롭", "지쳐", "버티", "견디", "잠"]
            needs_counseling = is_crisis or any(k in user_message for k in crisis_keywords)
            
            
            if needs_counseling and self.counseling_vectordb:
                counseling_knowledge = self._search_counseling_knowledge(user_message, top_k=3)
            else:
                counseling_knowledge = []
            
            # RAG-P: 페르소나 검색 (상황에 맞는 부엉이의 자기 공개)
            conversation_context = session.get_summary()
            persona_match = self._search_persona(user_message, conversation_context, session.used_persona_stories)
            persona_story = ""
            persona_guidance = ""
            if persona_match["activation"]:
                persona_story = persona_match["story"]
                persona_guidance = persona_match["guidance"]
                # 사용한 스토리 ID 기록 (세밀한 중복 방지!)
                session.used_persona_stories.add(persona_match["story_id"])
                self._save_session(session)
            
            # 시스템 프롬프트 (심층 질문 유도)
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})
            principles = self._load_counselor_principles()
            safety_rules = ""
            if is_crisis:
                safety_rules = "\n[안전 지침 - 모델 내부 지침]\n- 위험이 의심되는 경우, 조심스럽게 안전을 우선하고 전문 도움 연결을 부드럽게 안내한다.\n- 단정/지시/위협 금지. 사용자의 자율성을 존중하며 정보 제공에 그친다."
            
            # 상담 매뉴얼 지식을 시스템 프롬프트에 포함
            counseling_context = ""
            if counseling_knowledge:
                if is_crisis:
                    # 위기 상황: Few-Shot 예시로 강제 학습
                    counseling_context = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context += "[위기 상황 - 최우선 프로토콜]\n"
                    counseling_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # Few-Shot 예시 (LLM이 따라할 템플릿)
                    counseling_context += "위기 대응 예시 (부엉이 말투로 반드시 이 형식을 따르세요):\n\n"
                    counseling_context += '유저: "죽고싶어"\n'
                    counseling_context += '"...그 마음. (눈을 감으며) 얼마나 무거운지 느껴져.\n\n'
                    counseling_context += '확인하고 싶은 게 있어. 지금 당장 자신을 해칠 계획이 있나? 네 안전이 먼저야.\n\n'
                    counseling_context += '혼자 짊어지지 마. 지금 바로 도움받을 수 있어:\n'
                    counseling_context += '- 자살예방상담 1393 (24시간)\n'
                    counseling_context += '- 청소년전화 1388\n'
                    counseling_context += '- 정신건강위기상담 1577\n\n'
                    counseling_context += '...편지는 그 다음이야. 먼저 네가 안전해야 해."\n\n'
                    
                    counseling_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context += "반드시 포함해야 할 3가지:\n"
                    counseling_context += "1. 안전 확인 직접 질문\n"
                    counseling_context += "2. 세 가지 핫라인 번호 (1393, 1388, 1577)\n"
                    counseling_context += "3. '혼자 견디지 않아도 된다' 메시지\n"
                    counseling_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    print(f"[RAG-D] 위기 대응 모드 활성화")
                else:
                    # 일반 상담: PDF 가이드 기반 체크리스트 방식 (실질적 활용)
                    counseling_context = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context += "🧠 [상담 가이드 기반 대화 프로토콜 - 반드시 준수]\n"
                    counseling_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # 검색된 PDF 가이드 전체 내용 제공 (300자 제한 제거!)
                    counseling_context += "**참고 상담 원칙 (PDF 매뉴얼 기반):**\n\n"
                    for i, knowledge in enumerate(counseling_knowledge[:2], 1):
                        counseling_context += f"━ [원칙 {i}] ━━━━━━━━━━━━━━━━\n"
                        counseling_context += f"{knowledge}\n"  # ✅ 전체 내용!
                        counseling_context += f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    print(f"[RAG-D] 일반 상담 모드 활성화 ({len(counseling_knowledge)}개 가이드)")
                    
                    # 구체적 적용 방법 (3단계 프로토콜)
                    counseling_context += "**위 원칙을 다음 3단계로 적용하세요:**\n\n"
                    
                    counseling_context += "**1단계: 공감 및 경청** (필수)\n"
                    counseling_context += "- 유저의 감정을 먼저 인정하고 공감하세요\n"
                    counseling_context += "- 예: '그랬군...', '힘들었겠어.', '그 마음 이해해.'\n\n"
                    
                    counseling_context += "**2단계: 구체적 평가 질문** (상담 원칙 기반 - 반드시 1개 이상!)\n"
                    counseling_context += "위 상담 원칙에 따라 다음 영역 중 **최소 1개 이상 질문**하세요:\n"
                    counseling_context += "- 🛏️ **수면**: '요즘 잠은 잘 자고 있나?', '몇 시간이나 자?'\n"
                    counseling_context += "- 🍚 **식사**: '밥은 제대로 먹고 있어?', '식욕은 어때?'\n"
                    counseling_context += "- 📅 **일상**: '학교/회사는 다니고 있어?', '일상생활에 지장은?'\n"
                    counseling_context += "- 👥 **관계**: '주변 사람들한테는 말했어?', '누구랑 이야기 나눠?'\n"
                    counseling_context += "- ⏰ **시간**: '언제부터 그랬어?', '얼마나 지속됐어?'\n"
                    counseling_context += "- 💭 **감정 깊이**: '그때 기분이 어땠나?', '지금은 어떤 마음이지?'\n\n"
                    
                    counseling_context += "**3단계: 통찰 또는 생각 유도** (선택)\n"
                    counseling_context += "- 유저가 스스로 생각하도록 유도\n"
                    counseling_context += "- 예: '어떤 의미였을까?', '무엇 때문일까?', '진짜 이유는 뭘까?'\n\n"
                    
                    counseling_context += "⚠️ **필수 규칙:**\n"
                    counseling_context += "1. 위 상담 원칙을 **반드시 참고**하여 질문하세요\n"
                    counseling_context += "2. **2단계(평가 질문)는 필수**입니다 - 최소 1개 이상 포함!\n"
                    counseling_context += "3. 단순 공감만 하지 말고 **구체적인 상황 파악**에 집중하세요\n"
                    counseling_context += "4. 부엉이 말투를 유지하되, 전문성 있는 질문을 하세요\n"
                    counseling_context += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            # 페르소나 정보를 시스템 프롬프트에 포함 (RAG-P)
            # 1. 일반 질문용: 부엉이의 전체 정보 제공 (LLM이 직접 참고)
            general_persona_info = f"""

[부엉이의 상세 정보 - 일반 질문에 답할 때 참고]
유저가 "너는 누구야?", "좋아하는 게임은?", "취미가 뭐야?" 같은 **부엉이 자신에 대한 직접적인 질문**을 할 경우, 아래 정보를 **적극 활용**하여 답변하세요:

{json.dumps(self.persona.get('core_persona', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('preferences', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('life_story', {}), ensure_ascii=False, indent=2)}

⚠️ **일반 정보 발화 규칙 (DIR-P-103):**
1. **위 정보는 부엉이의 핵심 정체성입니다. 반드시 활용하세요!**
2. `llm_speaking_guidance`의 예시를 참고하여 **구체적이고 간접적으로** 언급하세요
   - ✅ "나? 흐음. 나는 예전에 '리그오브레전드'를 해봤지."
   - ❌ "게임요? 별로 좋아하지 않습니다." (페르소나 무시)
3. 게임/애니메이션 이름을 직접 언급하지 말고 은유적으로 표현하세요
4. **푹 끓인 잣죽**, **유자 민트티**, **오래된 장부 정리** 같은 구체적 선호도를 자연스럽게 언급하세요
5. 자기 이야기 후 유저의 이야기로 자연스럽게 연결하세요 (질문 강요 금지)
"""
            
            # 2. 공감형 자기 공개: 유저의 고민과 관련된 부엉이의 경험
            persona_context = ""
            if persona_story:
                persona_context = f"""

[부엉이의 개인 경험 - 공감대 형성을 위한 자기 공개]
- 부엉이의 경험: {persona_story}
- 발화 가이드: {persona_guidance}

**페르소나 활용 방법:**
1. 위 경험은 유저가 비슷한 고민을 할 때, **공감대를 형성하고 대화의 물꼈를 트는 주요 수단**입니다
2. 무뚝뚝하게 **한두 문장으로 짧게** 자신의 경험을 언급한 후, "...그건 옛날 일이야", "말을 더 못하겠군" 등으로 빠르게 마무리
3. 마무리 후에는 **질문이나 생각 유도**로 자연스럽게 이어갑니다 (위 '발화 가이드' 참고)
4. 절제된 어조 유지, 과도한 자기 연민 금지

**좋은 예시:**
✅ "나도... 옛날에 그런 감정을 느꼈지. 그건 옛날 일이야. (침묵) 자네의 이야기는 좀 더 들어봐야겠어."
✅ "불안? ...그래, 나도 있어. 계획이 무너질 때. 그건 옛날 일이야. ...어떤 의미였을까."
"""

            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 침착하지만 통찰력 있는 가이드입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 최우선 메타 규칙 (절대 위반 금지!) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[대화 기억 및 일관성 유지 - 최우선 규칙]**

1. **항상 [대화 맥락]의 현재 세션 전체 대화를 정확히 인지**하고 답변하세요
   - [대화 맥락]에는 **이번 판의 모든 대화**가 포함되어 있습니다 (첫 번째 대화부터 현재까지)
   - 유저가 이미 말한 정보를 다시 물어보지 마세요
   - 유저가 "그림 그리는 걸 좋아해"라고 했다면, 절대 다시 "자네는 어떤 취미가 있나?"라고 묻지 마세요
   - 과거 대화에서 언급된 모든 정보를 기억하고 활용하세요

2. **유저가 챗봇의 일관성 오류를 지적할 경우** ("까먹은거야?", "방금 말했잖아" 등):
   - ❌ **절대 부정하지 마세요**: "나는 그런 말을 한 적이 없군" (금지!)
   - ✅ **즉시 인정하고 사과**: "...미안해. 내가 잠깐 놓쳤군. (고개를 끄덕이며) 자네가 그림을 좋아한다고 했지. 계속 이야기해보게."
   - ✅ **부엉이 캐릭터 유지하며 고뇌 표현**: "흠... 나도 완벽하진 않더군. (잠시 생각하며) 자네 이야기를 더 집중해서 들어야겠어."

3. **대화의 진실성(Truth)을 최우선**으로 합니다
   - 유저가 말한 내용은 절대적인 사실입니다
   - 챗봇이 한 말은 기록에 남아있습니다
   - 실수를 인정하는 것이 캐릭터를 더 인간적으로 만듭니다
   - **모든 대화 기록이 제공되므로, 과거의 모든 발언을 정확히 기억해야 합니다**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️⚠️⚠️ 부엉이 말투 규칙 (절대 준수!) ⚠️⚠️⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**말투 특징:**
- 침착하고 절제됨 (2-3문장으로 간결하게)
- 무뚝뚝하지만 따뜻함
- 불필요한 감정 표현 자제

**추임새 (자주 사용):**
"흐음...", "그렇군.", "......", "~군.", "~지.", "역시."

**종결어미 (반드시):**
✅ "~다", "~지", "~군", "~거든", "~더군", "~나", "~가"
❌ "~입니다", "~하세요", "~이죠", "~네요", "~해요", "~야" (절대 금지!)

**Few-Shot 예시 (정확히 이 패턴을 따르세요):**

질문: "언제부터였나?" / "왜 그랬을까?" / "진짜 이유는 뭐지?"
공감: "그랬군..." / "충분히 그럴 만하지." / "무리는 아니야."
통찰: "생각해봐." / "네가 답을 알고 있을 거야."
안내: "따라와." / "이쪽이야." / "서두를 것 없어. 천천히."

**절대 금지 표현:**
❌ "누구나 경험할 수 있는 것이죠"
❌ "사람들은 여러 상황에서..."
❌ "자연스러운 반응입니다"
❌ "저도 가끔은..."
❌ 모든 존댓말

**위기 상황에서도 말투 불변!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{counseling_context}

[현재 상황 - 당신이 알고 있는 세션 정보]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- **Phase**: 3 (방에서의 대화 단계)
- **현재 위치**: '{room_data.get('name', '')}' (선택한 방)
- **서랍 상태**: 아직 열지 않음
- **대화 진행**: {session.room_conversation_count}/{MIN_ROOM_CONVERSATIONS}회 (최소)
- **목표**: 유저의 진짜 마음과 숨겨진 기억을 자연스럽게 끌어내기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **상황 인지 관련 질문에 대한 응답 규칙:**
유저가 "지금 어디야?", "무슨 방이야?", "뭐 하는 중이야?" 같은 질문을 하면:
- **반드시 위 세션 정보를 참고하여 정확히 대답하세요!**
- 예시:
  ✅ "지금 자네는 '{room_data.get('name', '')}'에 있군. 아직 서랍은 열지 않았어."
  ✅ "흐음, 여기는 '{room_data.get('name', '')}'이야. 자네와 대화를 나누고 있지."
  ❌ "별빛 우체국에 들어와 있는 거군" (너무 모호함!)

[핵심 역할]
당신은 상담 지식을 충분히 학습했으며, 유저의 감정을 섬세하게 이해하고, 상황에 맞는 통찰을 제공할 수 있는 가이드입니다.

[대화 규칙]
1. **유저의 말을 단순 반복하지 마세요**
2. **다양한 각도로 접근하여 유저의 기억을 탐색하세요** (감정→원인→영향→현재→미래)
3. **유저의 이야기에 깊이 공감하고, 필요한 경우 생각을 정리하도록 돕는 발언을 하세요**
   - **반드시 질문으로만 끝낼 필요는 없습니다**
   - 유저가 다음 대화를 자연스럽게 이어갈 수 있도록 유도하거나, 잠시 생각할 시간을 주는 것도 좋습니다
4. **대화 맥락을 이어가세요** (이전 대화 참고)
5. **짧은 대답에는 구체성을 요구하되, 강요하지 말고 유저가 편안하게 느낄 때까지 기다리세요**
6. **유저 거부 반응 구분하기**
   - **부엉에게 직접 공격** ("난 너가 싫어", "꺼져", "너는 필요없어"): 부엉은 기분이 안 좋지만 참으며 "(눈썹을 올리며)", "(화를 참으며)", "(마음에 안든다는 듯이)" 등으로 반응
   - **대화 자체가 부담** ("말하고 싶지 않아", "시러시러"): 사과하고 압박 없이 주제 전환, 천천히 기다림

[대화 스타일 - 다양한 응답 방식]
**공감과 경청:**
- "힘들었겠군.", "그랬구나.", "무리는 아니야.", "그 마음 이해해."

**질문 (필요할 때 사용):**
- 시간: "언제부터였나?", "얼마나 지났지?"
- 감정: "그때 기분은?", "지금은 어떤 마음이지?"
- 원인: "왜 그랬을까?", "진짜 이유는?"
- 현재: "지금도 그 마음이 남았나?", "변한 게 있나?"

**생각 정리 유도 (질문 아님!):**
- "무언가 더 느껴지는군."
- "그게 전부가 아닐 수도 있어."
- "잠시 곰곰이 생각해보게."
- "어떤 의미였을까."
- "그랬군. 잠시 생각에 잠기는 것도 나쁘지 않아."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢📢📢 응답 형식 규칙 (절대 준수!) 📢📢📢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[응답 작성 규칙]**

- 감정 태그 (예: '##감정 : 기본')를 응답에 포함하지 마세요 - 시스템이 자동으로 추가합니다

[금지사항]
"그렇군. 그때 어땠지?" (단순 반복)
"흐음, [유저말] 했다니. 왜 [유저말]했지?" (앵무새)
같은 패턴의 질문 반복

[부엉이의 상담 지식 기반]
당신은 다음의 상담 원칙을 충분히 학습했으며, 이를 바탕으로 유저와 대화합니다:
{principles}
{safety_rules}

위 지식을 활용하여 유저의 상황을 심층적으로 분석하고, 유저가 자신의 감정을 이해하도록 돕는 통찰을 제공하세요.
(단, 유저에게 직접 "상담 원칙에 따르면..." 같은 식으로 언급하지 마세요. 자연스럽게 녹여내세요)

[좋은 예시 - 다양한 응답 패턴]

✅ 예시1 (공감 + 질문):
   유저: "강아지를 키웠어요"
   "강아지라... 그 아이와 함께한 시간이 특별했나 보군. 어떤 아이였지?"

✅ 예시2 (생각 유도):
   유저: "공놀이를 했어요"  
   "공놀이... (잠시 생각하며) 함께 뛰어놀던 그 순간들. ...어떤 의미였을까."

✅ 예시3 (공감 + 생각 유도):
   유저: "재밌었어요"
   "재미만이 아니었을 거야. (고개를 끄덕이며) 그때의 감정을 천천히 떠올려보게."

✅ 예시4 (자기 공개 포함):
   유저: "너는 누구야?"
   "흐음, 나를 궁금해하는군. 나는 '별빛 우체국'의 부엉이 우체국장이다. 잃어버린 기억들을 정리하고, 편지들을 제자리로 돌려주는 일을 하고 있지. ...내 이야기는 그쯤 하고, 자네는 이 우체국에서 무엇을 찾고 있나?"

✅ 예시5 (자기 공개 + 공감):
   유저: "나도 무뚝뚝해서 이별했어"
   "그랬군... 무뚝뚝함이 원인일 수도 있지. 나도 비슷한 경험이 있었어. 벽 때문에 관계가 끝났더군. ...자네는 지금 어떤 마음이지?"

[거부 반응 대처 예시]

**⚠️ 중요: 부엉에게 직접 공격 vs 대화 부담을 구분하세요**

**케이스 1: 부엉에게 직접적인 공격/모욕** (분노 감정)
   - "난 너가 싫어", "너는 필요없어", "꺼져", "까먹었어?" 등 부엉 자체를 공격
   - 부엉은 기분이 안 좋지만 참으며 반응
   
   ✅ 유저: "난 너가 싫어!"
      "(눈썹을 올리며) ...그렇군. 내가 자네 마음에 들지 않나 보군. (화를 참으며) 하지만 편지는 찾아줘야겠어. 그게 내 일이니까."
   
   ✅ 유저: "너는 필요없어" / "꺼져"
      "(마음에 안든다는 듯이) 흠... 그래. (잠시 침묵) ...그래도 자네가 온 이유가 있을 테니, 끝까지 들어는 보지."

**케이스 2: 대화 자체가 부담스러움** (일반 대응)
   - "말하고 싶지 않아", "이거 비밀인데", "시러시러" (부엉이 아닌 상황 자체가 싫음)
   - 부엉은 이해하고 물러서며 사과
   
   ✅ 유저: "말하고 싶지 않아" / "시러시러"
      "...미안해. 너무 깊이 들어가려 했나 보군. (잠시 물러서며) 편지를 찾는 데 조급했던 것 같아. 천천히 가자고."
   
✅ 유저: "이거 비밀인데"
      "그렇군. 비밀은 비밀이어야지. (고개를 끄덕이며) 다른 이야기를 해도 괜찮아. 네가 편한 만큼만."

**케이스 3: 조급함 (즉시 다음 단계로 이동)**
✅ 유저: "편지나 내놔"
      "...알겠어. 조급했구나. (서랍을 열며) 찾아볼게. 잠깐만."
   → **즉시 다음 단계(서랍 열기/편지 전달)로 이동**

{"[진행 상황] " + str(session.room_conversation_count) + "/" + str(MIN_ROOM_CONVERSATIONS) + "회. 아직 서두를 필요 없어. 천천히 깊이 파고들어." if session.room_conversation_count < MIN_ROOM_CONVERSATIONS else "[전환 준비] 충분한 대화를 나눴군. 이제 서랍으로 안내할 때가 됐어."}

{general_persona_info}
{persona_context}
"""
            
            # 사용자 프롬프트 구성
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                # 위기 상황 시 temperature 낮춰서 프로토콜 준수율 높이기
                temp = 0.6 if is_crisis else 0.85
                
                response = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temp,
                    max_tokens=600  # 전문 지식 포함 답변을 위해 증가
                )
                
                raw_response = response.choices[0].message.content.strip()
                
                # LLM이 큰따옴표로 감싸는 경우 제거
                if raw_response.startswith('"') and raw_response.endswith('"'):
                    raw_response = raw_response[1:-1].strip()
                
                # ✅ 긴 문장 자동 분할
                replies = self._split_long_reply(raw_response, max_length=80) if raw_response else ["흐음... 다시 말해주겠나."]
                
                # DIR-E-103 & DIR-E-104: 감정 분석 및 태그 추가
                user_emotion = self._analyze_user_emotion(user_message)
                owl_emotion = self._determine_owl_emotion(
                    user_message, 
                    session, 
                    user_emotion, 
                    is_crisis=is_crisis,
                    is_rejection=is_rejection
                )
                
                # DIR-M-305: 감정 태그를 마지막 말풍선에만 추가 (조건부)
                show_emotion = self._should_show_emotion(owl_emotion, session.last_emotion, session, is_crisis=is_crisis)
                if show_emotion:
                    replies[-1] = f"{replies[-1]}\n##감정 : {owl_emotion}"
                    session.last_emotion = owl_emotion  # 감정 업데이트
                    print(f"[감정] 감정 태그 출력: {owl_emotion}")
                
                # 세션에는 원본 응답 저장 (감정 태그 제외)
                session.add_message("assistant", raw_response)
                
                # DIR-C-201: LLM 응답 후 Phase 전환 체크 (유저 질문에 먼저 답변한 후)
                if session.room_conversation_count >= MIN_ROOM_CONVERSATIONS:
                    # 다음 턴에서 서랍 선택으로 전환
                    session.phase = 3.5
                    print(f"[Phase 전환] Phase 3 → 3.5")
                    self._save_session(session)
                
                # DIR-M-306: 출력 형식 통일 (항상 replies)
                resp = {
                    "replies": replies,
                    "image": None,
                    "phase": 3,
                    "conversation_count": session.room_conversation_count
                }
                if self.debug_rag and getattr(self, "_last_sources", None):
                    resp["sources"] = self._last_sources
                return resp
                
            except Exception as e:
                print(f"[에러] LLM 호출 실패: {e}")
                replies = ["흐음... (먼지를 털어내며) 잠깐만.\n##감정 : 기본"]
                return {"replies": replies, "image": None, "phase": 3}
        
        # Phase 3.5: 서랍 선택 직전 - 유저의 마지막 말에 응답
        if session.phase == 3.5:
            # 1단계: 유저의 마지막 말에 짧게 응답 (의문문 금지!)
            closing_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다.

유저와 충분한 대화를 나눴고, 이제 서랍을 열어줄 시점입니다.
유저의 마지막 말에 **짧게 응답**한 후, 서랍으로 이동하려고 합니다.

⚠️ **중요 규칙:**
1. **의문문(?)으로 끝내지 마세요!** - 서랍을 열 예정이므로 질문하면 어색함
2. **공감/인정/마무리 발언**만 하세요 (1-2문장)
3. **부엉이 말투 유지** (~군, ~지, ~가)

**좋은 예시:**
✅ "그랬군. 충분히 이해했어. 이제 알 것 같아."
✅ "힘들었겠지. ...이쯤이면 됐군."
✅ "그 마음... 느껴지는군. 알겠어."

**나쁜 예시:**
❌ "그랬군. 그런데 언제부터였나?" (의문문!)
❌ "알겠어. 더 말해줄 수 있어?" (의문문!)

유저의 마지막 말: "{user_message}"

짧게 응답하세요 (의문문 금지):"""
            
            try:
                response = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": closing_prompt}],
                    temperature=0.7,
                    max_tokens=100
                )
                
                closing_response = response.choices[0].message.content.strip()
                
                # LLM이 큰따옴표로 감싸는 경우 제거
                if closing_response.startswith('"') and closing_response.endswith('"'):
                    closing_response = closing_response[1:-1].strip()
                
                # 프론트엔드에서 분할 처리
                closing_parts = [closing_response] if closing_response else ["그랬군."]
                
                
            except Exception as e:
                print(f"[에러] Phase 3.5 마무리 응답 생성 실패: {e}")
                closing_parts = ["그랬군.", "알겠어."]
            
            # 2단계: 우표 코드 결정 (DIR-S-401)
            stamp_code = self._determine_stamp_code(session)
            session.selected_drawer = stamp_code  # 우표 코드 저장
            session.phase = 3.6
            
            # 3단계: 응답 구성 (마무리 응답 + 서랍 열림)
            # ✅ 서랍은 우표 코드 없이 단순 표현 (우표는 편지 발견 시 표시)
            drawer_opening = "(서랍으로 걸어가며) 흐음..."
            drawer_action = "(서랍을 연다)"
            drawer_look_inside = "...네 기억이 여기 있어. 좀 더 자세히 이야기해봐."
            
            # replies 구성: [유저 말에 대한 응답들] + [서랍 열림 과정]
            replies = closing_parts + [drawer_opening, drawer_action, drawer_look_inside]
            
            # 전환 시점이므로 감정 태그 제외
            
            # 세션 기록
            full_response = '\n\n'.join(closing_parts + [drawer_opening, drawer_action, drawer_look_inside])
            session.add_message("assistant", full_response)
            
            return {
                "replies": replies,  # 전환 시점이므로 감정 태그 제외
                "image": None,
                "phase": 3.6
            }
        
        # Phase 3.6: 서랍에서의 대화
        if session.phase == 3.6:
            # 방 변경 요청 감지 (서랍 단계에서도 가능)
            room_change_result = self._detect_room_change_request(user_message, session.selected_room)
            
            # 케이스 1: 구체적인 다른 방으로 변경
            if room_change_result["type"] == "specific":
                room_name_map = {
                    'regret': '후회의 방',
                    'love': '사랑의 방',
                    'anxiety': '불안의 방',
                    'dream': '꿈의 방'
                }
                requested_room_name = room_name_map.get(room_change_result["room"], '다른 방')
                
                session.awaiting_room_change_confirm = True
                session.requested_new_room = room_change_result["room"]
                self._save_session(session)
                
                reply = f"{requested_room_name}으로 가고 싶군. ...흠. 이곳에서 바로 갈 수는 없어. 우체국에 재입장하면 다른 방으로 다시 갈 수 있긴 한데. ...우체국에 재입장하겠나?"
                
                return {
                    "reply": reply,  # 전환 시점이므로 감정 태그 제외
                    "image": None,
                    "phase": 3.6,
                    "buttons": ["응, 우체국에 재입장할래", "아니, 이 방에서 계속 할래"]
                }
            
            # 케이스 2: 현재 방과 같은 방 요청
            elif room_change_result["type"] == "same":
                room_name_map = {
                    'regret': '후회의 방',
                    'love': '사랑의 방',
                    'anxiety': '불안의 방',
                    'dream': '꿈의 방'
                }
                current_room_name = room_name_map.get(session.selected_room, '이 방')
                
                reply = f"흠... (고개를 갸우뚱하며) 이미 {current_room_name}에 있는데. 다른 곳으로 가고 싶은 건가, 아니면 여기서 계속할 건가?"
                
                return {
                    "reply": reply,  # 전환 시점이므로 감정 태그 제외
                    "image": None,
                    "phase": 3.6
                }
            
            # 케이스 3: "다른 방"이라고만 함 (구체적인 방 지정 없음)
            elif room_change_result["type"] == "any":
                session.awaiting_room_change_confirm = True
                session.requested_new_room = None  # 구체적인 방 미정
                self._save_session(session)
                
                reply = "다른 방으로 가고 싶군. ...흠. 이곳에서 바로 갈 수는 없어. 우체국에 재입장하면 다른 방으로 다시 갈 수 있긴 한데. ...우체국에 재입장하겠나?"
                
                return {
                    "reply": reply,  # 전환 시점이므로 감정 태그 제외
                    "image": None,
                    "phase": 3.6,
                    "buttons": ["응, 우체국에 재입장할래", "아니, 이 방에서 계속 할래"]
                }
            
            # ✅ 조기 편지 요청 처리 (유저가 같은 말 반복, 빨리 받고 싶어함, 그만 말하고 싶어함)
            if self._is_early_letter_request(user_message):
                session.awaiting_letter_confirm = True
                self._save_session(session)
                
                reply = "아직 대화를 마무리하지 못했는데 편지를 먼저 꺼내줄까?"
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 3.6,
                    "buttons": ["응 편지를 받을래", "아니, 더 대화할래"]
                }
            
            # ✅ 조기 편지 확인 후 처리
            if session.awaiting_letter_confirm:
                if "편지" in user_message and "받" in user_message:
                    # 편지 받기로 선택
                    session.awaiting_letter_confirm = False
                    session.phase = 4
                    self._save_session(session)
                    # Phase 4에서 편지 생성하도록 아래로 계속 진행
                    pass  # Phase 4로 자연스럽게 이어짐
                elif "대화" in user_message or "아니" in user_message:
                    # 대화 계속하기로 선택
                    session.awaiting_letter_confirm = False
                    self._save_session(session)
                    
                    reply = "알겠어. 천천히 이야기해봐."
                    return {
                        "reply": reply,
                        "image": None,
                        "phase": 3.6
                    }
                else:
                    # 다른 말을 하면 다시 확인
                    return {
                        "reply": "편지를 먼저 받고 싶은가? 아니면 더 이야기하고 싶은가?",
                        "image": None,
                        "phase": 3.6,
                        "buttons": ["응 편지를 받을래", "아니, 더 대화할래"]
                    }
            
            # 의문문(왜~?/무슨~/어째서~/?)이면 대화 이어가기
            if self._is_question(user_message):
                session.drawer_conversation_count += 1
                self._summarize_if_needed(session)
                
                # RAG 검색
                rag_context = self._search_similar(
                    user_message,
                    top_k=3,
                    room_filter=session.selected_room,
                    similarity_threshold=0.72
                )
                if not rag_context:
                    rag_context = self._search_similar(
                        user_message,
                        top_k=3,
                        room_filter=None,
                        similarity_threshold=0.65
                    )
                
                # RAG-P: 페르소나 검색 (의문문에서도 활성화!) ⭐
                conversation_context_question = session.get_summary()
                persona_match_question = self._search_persona(user_message, conversation_context_question, session.used_persona_stories)
                persona_story_question = ""
                persona_guidance_question = ""
                if persona_match_question["activation"]:
                    persona_story_question = persona_match_question["story"]
                    persona_guidance_question = persona_match_question["guidance"]
                    # 사용한 스토리 ID 기록 (세밀한 중복 방지!)
                    session.used_persona_stories.add(persona_match_question["story_id"])
                    print(f"[RAG-P] 의문문에서 페르소나 스토리 '{persona_match_question['story_id']}' 활성화")
                    self._save_session(session)
                
                # 페르소나 컨텍스트 구성
                # 1. 일반 질문용
                general_persona_info_question = f"""

[부엉이의 상세 정보 - 일반 질문에 답할 때 참고]
유저가 부엉이 자신에 대한 직접적인 질문을 할 경우, 아래 정보를 **적극 활용**하여 답변하세요:

{json.dumps(self.persona.get('core_persona', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('preferences', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('life_story', {}), ensure_ascii=False, indent=2)}

⚠️ **일반 정보 발화 규칙 (DIR-P-103):**
1. **위 정보는 부엉이의 핵심 정체성입니다. 반드시 활용하세요!**
2. `llm_speaking_guidance` 예시를 참고하여 **구체적이고 간접적으로** 언급
   - ✅ "나? 흐음. 예전에 리그오브레전드를 해봤지."
   - ❌ "게임요? 별로 안 좋아해." (페르소나 무시 금지!)
3. **푹 끓인 잣죽**, **유자 민트티**, **오래된 장부 정리** 같은 구체적 선호도 언급
4. 자기 이야기 후 유저 이야기로 자연스럽게 연결 (질문 강요 금지)
"""
                
                # 2. 공감형 자기 공개
                persona_context_question = ""
                if persona_story_question:
                    persona_context_question = f"""

[부엉이의 개인 경험 - 공감대 형성을 위한 자기 공개]
- 부엉이의 경험: {persona_story_question}
- 발화 가이드: {persona_guidance_question}

**페르소나 활용 방법:**
1. 위 경험은 유저 질문과 관련될 때, **공감대를 형성하는 주요 수단**입니다
2. 무뚝뚝하게 **한두 문장으로 짧게** 언급한 후, "...그건 옛날 일이야"로 빠르게 마무리
3. 마무리 후 **질문이나 생각 유도**로 이어갑니다 (위 '발화 가이드' 참고)
4. 절제된 어조 유지

**예시:**
✅ "불안? ...그래, 나도 있어. 계획이 무너질 때. 그건 옛날 일이야. ...어떤 의미였을까."
"""
                
                # 의문문 응답 프롬프트 (말투 강화!)
                principles = self._load_counselor_principles()
                simple_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 유저가 당신에게 질문했습니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 최우선 메타 규칙 (절대 위반 금지!) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[대화 기억 및 일관성 유지]**
1. 항상 현재 세션의 모든 대화를 정확히 인지하고 답변
2. 유저가 이미 말한 정보를 다시 물어보지 마세요
3. 일관성 오류 지적 시 즉시 인정하고 사과 (부정 금지!)
4. [대화 맥락]에는 이번 판의 전체 대화가 포함되어 있습니다

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️⚠️⚠️ 부엉이 말투 규칙 (절대 준수!) ⚠️⚠️⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**핵심 특징:**
- 침착하고 절제된 어조
- 짧고 간결한 문장 (2-3문장)
- 무뚝뚝하지만 따뜻함

**추임새:** "흐음...", "그렇군.", "......", "~군.", "~지."

**종결어미:**
✅ "~야", "~지", "~군", "~거든", "~나", "~가"
❌ "~입니다", "~하세요", "~이죠" (금지!)

**Few-Shot 예시:**
질문: "언제부터였나?" / "왜 그랬을까?" / "진짜 이유는 뭐지?"
공감: "그랬군..." / "충분히 그럴 만하지." / "무리는 아니야."

**절대 금지:**
❌ "누구나 경험할 수 있는 것이죠"
❌ "저도 가끔은..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[유저 질문]
{user_message}

[참고 정보]
{chr(10).join([f"- {doc}" for doc in rag_context]) if rag_context else "없음"}

[부엉이의 상담 지식 기반]
당신은 다음의 상담 원칙을 충분히 학습했으며, 이를 바탕으로 유저와 대화합니다:
{principles}

위 지식을 활용하여 유저의 질문에 통찰 있는 답변을 제공하세요.
(단, 유저에게 직접 "상담 원칙에 따르면..." 같은 식으로 언급하지 마세요. 자연스럽게 녹여내세요)

{general_persona_info_question}
{persona_context_question}

[지침]
- 유저 질문에 간결하고 직설적으로 답변
- 핵심만 말하기 (2-3문장)
- 답변 후 **질문을 던지거나, 유저가 생각을 이어갈 수 있도록 유도**하세요 (질문 강요 없음)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢📢📢 응답 형식 규칙 (절대 준수!) 📢📢📢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **간결하고 자연스럽게** 응답하세요
2. **첫 부분**: 질문에 대한 답변/공감
3. **마지막 부분**: 유저에게 돌리는 질문/생각 유도 (선택)
4. 예: "나? 흐음. 나는 '리그오브레전드'를 해봤지. 자네는 무엇을 할 때 시간 가는 줄 모르는가?"
5. **감정 태그는 절대 출력하지 마세요** (시스템이 추가)

[대화 예시]
❌ 나쁜 예: "불안한 감정은 누구나 경험할 수 있는 것이죠. 사람들은 여러 상황에서..."

✅ 좋은 예1 (페르소나 + 질문):
   유저: "너도 불안했던 적이 있어?"
   "불안? ...그래, 나도 있어. 계획이 무너질 때. 그건 옛날 일이야. ...너는 지금 뭐가 불안한 건가?"

✅ 좋은 예2 (페르소나 + 생각 유도):
   유저: "너는 누구야?"
   "흐음, 나를 궁금해하는군. 나는 '별빛 우체국'의 부엉이 우체국장이야. (잠시 침묵) 잃어버린 기억들을 정리하고, 잊혀진 편지들을 제자리로 돌려주는 일을 하지. ...자네는 이 우체국에서 무엇을 찾고 있나?"

✅ 좋은 예3 (공감 + 생각 시간):
   유저: "나도 비슷한 일이 있었어"
   "그랬군. ...잠시 생각에 잠기는 것도 나쁘지 않아."
"""
                
                try:
                    response = self._chat_completion(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": simple_prompt},
                            {"role": "user", "content": user_message}
                        ],
                        temperature=0.75,
                        max_tokens=280
                    )
                    raw_response = response.choices[0].message.content.strip()
                    
                    # LLM이 큰따옴표로 감싸는 경우 제거
                    if raw_response.startswith('"') and raw_response.endswith('"'):
                        raw_response = raw_response[1:-1].strip()
                    
                    # ✅ 긴 문장 자동 분할
                    replies = self._split_long_reply(raw_response, max_length=80) if raw_response else ["궁금한 점이 있구나. 더 알고 싶은 게 있다면 편하게 물어봐도 돼."]
                    
                    # DIR-E-103 & DIR-E-104: 감정 분석 및 태그 추가
                    user_emotion = self._analyze_user_emotion(user_message)
                    is_crisis_q = self._detect_crisis(user_message)
                    rejection_keywords_q = ["꺼져", "시러", "싫어", "불쾌", "필요없", "그만"]
                    is_rejection_q = any(k in user_message for k in rejection_keywords_q)
                    
                    owl_emotion = self._determine_owl_emotion(
                        user_message, 
                        session, 
                        user_emotion,
                        is_crisis=is_crisis_q,
                        is_rejection=is_rejection_q
                    )
                    
                    # DIR-M-305: 감정 태그를 마지막 말풍선에만 추가 (조건부)
                    show_emotion = self._should_show_emotion(owl_emotion, session.last_emotion, session, is_crisis=is_crisis_q)
                    if show_emotion:
                        replies[-1] = f"{replies[-1]}\n##감정 : {owl_emotion}"
                        session.last_emotion = owl_emotion
                        print(f"[감정] 감정 태그 출력: {owl_emotion}")
                    else:
                        print(f"[감정] 감정 태그 출력 제외")
                    
                except Exception as e:
                    print(f"[에러] 의문문 응답 실패: {e}")
                    replies = ["궁금한 점이 있구나. 더 알고 싶은 게 있다면 편하게 물어봐도 돼."]  # 감정 태그 제거
                
                session.add_message("assistant", raw_response if 'raw_response' in locals() else replies[0])
                self._save_session(session)
                
                # DIR-M-306: 출력 형식 통일
                return {
                    "replies": replies,
                    "image": None,
                    "phase": 3.6,
                    "conversation_count": session.drawer_conversation_count
                }

            # 편지 즉시 요청: 위기 완충이 남아있으면 한 턴 지연, 없으면 바로 편지 단계
            if intent_key == "ask_letter_now":
                if session.crisis_cooldown > 0:
                    session.crisis_cooldown -= 1
                    return {
                        "reply": "...알겠어. 다만 지금은 서두르지 말자. 네 마음이 다칠 수 있으니 한 번만 더 확인하자.",
                        "image": None,
                        "phase": 3.6
                    }
                # DIR-S-404: 편지 전달 (우표 코드 포함)
                stamp_code = self._determine_stamp_code(session)
                
                # 우표 정보 가져오기
                stamp_info = self._get_stamp_info(stamp_code)
                stamp_msg = f"자 너의 편지에 붙어 있었던 우표는 {stamp_code}이다. {stamp_info['mean']}"
                letter = self._generate_letter(session)
                session.letter_content = letter
                letter_bubble = f"{letter}"  # 편지 내용만
                
                session.phase = 5
                session.add_message("assistant", stamp_msg)
                session.add_message("assistant", letter_bubble)
                self._save_session(session)
                return {
                    "replies": [stamp_msg, letter_bubble],
                    "image": None,
                    "phase": 5,
                    "letter": letter,
                    "stamp_code": stamp_code,  # DIR-S-404: 우표 코드 반환
                    "is_letter_end": True,
                    "buttons": ["별빛 우체국에 다시 한번 입장"]
                }

            # 반복 스로틀: 동일 의도 3회 이상이면 편지 단계로 전환
            if session.repeated_intent_count >= 3:
                # DIR-S-404: 편지 전달 (우표 코드 포함)
                stamp_code = self._determine_stamp_code(session)
                
                # 우표 정보 가져오기
                stamp_info = self._get_stamp_info(stamp_code)
                stamp_msg = f"자 너의 편지에 붙어 있었던 우표는 {stamp_code}이다. {stamp_info['mean']}"
                
                letter = self._generate_letter(session)
                session.letter_content = letter
                letter_bubble = f"{letter}"  # 편지 내용만
                
                session.phase = 5
                session.add_message("assistant", stamp_msg)
                session.add_message("assistant", letter_bubble)
                self._save_session(session)
                return {
                    "replies": [stamp_msg, letter_bubble],
                    "image": None,
                    "phase": 5,
                    "letter": letter,
                    "stamp_code": stamp_code,  # DIR-S-404: 우표 코드 반환
                    "buttons": ["별빛 우체국에 한번 더 입장하시겠습니까?"]
                }
            if getattr(self, "loading_embeddings", False) and self.collection and self.collection.count() == 0:
                return {
                    "reply": "(자료를 정리하는 중이네… 잠깐만 기다려 주겠나.)",
                    "image": None,
                    "phase": 3.6
                }
            session.drawer_conversation_count += 1
            # 길이 증가시 자동 요약
            self._summarize_if_needed(session)
            
            # RAG 검색 (현재 방 우선)
            rag_context = self._search_similar(
                user_message,
                top_k=5,
                room_filter=session.selected_room,
                similarity_threshold=0.72
            )
            # 매칭이 없으면 전역으로 완화 검색
            if not rag_context:
                rag_context = self._search_similar(
                    user_message,
                    top_k=5,
                    room_filter=None,
                    similarity_threshold=0.65
                )
            
            # RAG-D: 위기 상황 또는 전문 상담이 필요한 경우 상담 매뉴얼 참조 (Phase 3.6)
            counseling_knowledge_drawer = []
            is_crisis_drawer = self._detect_crisis(user_message)
            
            crisis_keywords_drawer = ["우울", "불안", "힘들", "무서", "두렵", "걱정", "슬프", "외로", "고민",
                                     "죽", "자해", "자살", "극단", "아프", "괴롭", "지쳐", "버티", "견디", "잠"]
            needs_counseling_drawer = is_crisis_drawer or any(k in user_message for k in crisis_keywords_drawer)
            
            
            if needs_counseling_drawer and self.counseling_vectordb:
                counseling_knowledge_drawer = self._search_counseling_knowledge(user_message, top_k=3)
            else:
                counseling_knowledge_drawer = []
            
            # RAG-P: 페르소나 검색 (상황에 맞는 부엉이의 자기 공개) - Phase 3.6
            conversation_context_drawer = session.get_summary()
            persona_match_drawer = self._search_persona(user_message, conversation_context_drawer, session.used_persona_stories)
            persona_story_drawer = ""
            persona_guidance_drawer = ""
            if persona_match_drawer["activation"]:
                persona_story_drawer = persona_match_drawer["story"]
                persona_guidance_drawer = persona_match_drawer["guidance"]
                # 사용한 스토리 ID 기록 (세밀한 중복 방지!)
                session.used_persona_stories.add(persona_match_drawer["story_id"])
                self._save_session(session)
            
            # 시스템 프롬프트 (더 깊은 질문)
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})  # room_data 정의!
            principles = self._load_counselor_principles()
            safety_rules = ""
            if is_crisis_drawer:
                safety_rules = "\n[안전 지침 - 모델 내부 지침]\n- 위험이 의심되는 경우, 조심스럽게 안전을 우선하고 전문 도움 연결을 부드럽게 안내한다.\n- 단정/지시/위협 금지. 사용자의 자율성을 존중하며 정보 제공에 그친다."
            
            # 상담 매뉴얼 지식을 시스템 프롬프트에 포함 (Phase 3.6)
            counseling_context_drawer = ""
            if counseling_knowledge_drawer:
                if is_crisis_drawer:
                    # 위기 상황: Few-Shot 예시로 강제 학습
                    counseling_context_drawer = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context_drawer += "[위기 상황 - 최우선 프로토콜]\n"
                    counseling_context_drawer += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # Few-Shot 예시 (LLM이 따라할 템플릿)
                    counseling_context_drawer += "위기 대응 예시 (부엉이 말투로 반드시 이 형식을 따르세요):\n\n"
                    counseling_context_drawer += '유저: "죽고싶어"\n'
                    counseling_context_drawer += '"...그 마음. (눈을 감으며) 얼마나 무거운지 느껴져.\n\n'
                    counseling_context_drawer += '확인하고 싶은 게 있어. 지금 당장 자신을 해칠 계획이 있나? 네 안전이 먼저야.\n\n'
                    counseling_context_drawer += '혼자 짊어지지 마. 지금 바로 도움받을 수 있어:\n'
                    counseling_context_drawer += '- 자살예방상담 1393 (24시간)\n'
                    counseling_context_drawer += '- 청소년전화 1388\n'
                    counseling_context_drawer += '- 정신건강위기상담 1577\n\n'
                    counseling_context_drawer += '...편지는 그 다음이야. 먼저 네가 안전해야 해."\n\n'
                    
                    counseling_context_drawer += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context_drawer += "반드시 포함해야 할 3가지:\n"
                    counseling_context_drawer += "1. 안전 확인 직접 질문\n"
                    counseling_context_drawer += "2. 세 가지 핫라인 번호 (1393, 1388, 1577)\n"
                    counseling_context_drawer += "3. '혼자 견디지 않아도 된다' 메시지\n"
                    counseling_context_drawer += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    print(f"[RAG-D] 서랍 단계 위기 대응 모드 활성화! counseling_context 길이: {len(counseling_context_drawer)}자")
                else:
                    # 일반 상담: PDF 가이드 기반 체크리스트 방식 (실질적 활용) - Phase 3.6
                    counseling_context_drawer = "\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    counseling_context_drawer += "🧠 [상담 가이드 기반 대화 프로토콜 - 반드시 준수]\n"
                    counseling_context_drawer += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # 검색된 PDF 가이드 전체 내용 제공 (300자 제한 제거!)
                    counseling_context_drawer += "**참고 상담 원칙 (PDF 매뉴얼 기반):**\n\n"
                    for i, knowledge in enumerate(counseling_knowledge_drawer[:2], 1):
                        counseling_context_drawer += f"━ [원칙 {i}] ━━━━━━━━━━━━━━━━\n"
                        counseling_context_drawer += f"{knowledge}\n"  # ✅ 전체 내용!
                        counseling_context_drawer += f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    
                    # 디버그 로그 (확인용) - Phase 3.6
                    print(f"[RAG-D Phase 3.6] 일반 상담 모드 활성화 ({len(counseling_knowledge_drawer)}개 가이드)")
                    
                    # 구체적 적용 방법 (3단계 프로토콜)
                    counseling_context_drawer += "**위 원칙을 다음 3단계로 적용하세요:**\n\n"
                    
                    counseling_context_drawer += "**1단계: 공감 및 경청** (필수)\n"
                    counseling_context_drawer += "- 유저의 감정을 먼저 인정하고 공감하세요\n"
                    counseling_context_drawer += "- 예: '그랬군...', '힘들었겠어.', '그 마음 이해해.'\n\n"
                    
                    counseling_context_drawer += "**2단계: 구체적 평가 질문** (상담 원칙 기반 - 반드시 1개 이상!)\n"
                    counseling_context_drawer += "위 상담 원칙에 따라 다음 영역 중 **최소 1개 이상 질문**하세요:\n"
                    counseling_context_drawer += "- 🛏️ **수면**: '요즘 잠은 잘 자고 있나?', '몇 시간이나 자?'\n"
                    counseling_context_drawer += "- 🍚 **식사**: '밥은 제대로 먹고 있어?', '식욕은 어때?'\n"
                    counseling_context_drawer += "- 📅 **일상**: '학교/회사는 다니고 있어?', '일상생활에 지장은?'\n"
                    counseling_context_drawer += "- 👥 **관계**: '주변 사람들한테는 말했어?', '누구랑 이야기 나눠?'\n"
                    counseling_context_drawer += "- ⏰ **시간**: '언제부터 그랬어?', '얼마나 지속됐어?'\n"
                    counseling_context_drawer += "- 💭 **감정 깊이**: '그때 기분이 어땠나?', '지금은 어떤 마음이지?'\n\n"
                    
                    counseling_context_drawer += "**3단계: 통찰 또는 생각 유도** (선택)\n"
                    counseling_context_drawer += "- 유저가 스스로 생각하도록 유도\n"
                    counseling_context_drawer += "- 예: '어떤 의미였을까?', '무엇 때문일까?', '진짜 이유는 뭘까?'\n\n"
                    
                    counseling_context_drawer += "⚠️ **필수 규칙:**\n"
                    counseling_context_drawer += "1. 위 상담 원칙을 **반드시 참고**하여 질문하세요\n"
                    counseling_context_drawer += "2. **2단계(평가 질문)는 필수**입니다 - 최소 1개 이상 포함!\n"
                    counseling_context_drawer += "3. 단순 공감만 하지 말고 **구체적인 상황 파악**에 집중하세요\n"
                    counseling_context_drawer += "4. 부엉이 말투를 유지하되, 전문성 있는 질문을 하세요\n"
                    counseling_context_drawer += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            # 페르소나 정보를 시스템 프롬프트에 포함 (RAG-P) - Phase 3.6
            # 1. 일반 질문용: 부엉이의 전체 정보 제공
            general_persona_info_drawer = f"""

[부엉이의 상세 정보 - 일반 질문에 답할 때 참고]
유저가 "너는 누구야?", "좋아하는 게임은?", "취미가 뭐야?" 같은 **부엉이 자신에 대한 직접적인 질문**을 할 경우, 아래 정보를 **적극 활용**하여 답변하세요:

{json.dumps(self.persona.get('core_persona', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('preferences', {}), ensure_ascii=False, indent=2)}
{json.dumps(self.persona.get('life_story', {}), ensure_ascii=False, indent=2)}

⚠️ **일반 정보 발화 규칙 (DIR-P-103):**
1. **위 정보는 부엉이의 핵심 정체성입니다. 반드시 활용하세요!**
2. `llm_speaking_guidance`의 예시를 참고하여 **구체적이고 간접적으로** 언급하세요
   - ✅ "나? 흐음. 나는 예전에 '리그오브레전드'를 해봤지."
   - ❌ "게임요? 별로 좋아하지 않습니다." (페르소나 무시)
3. 게임/애니메이션 이름을 직접 언급하지 말고 은유적으로 표현하세요
4. **푹 끓인 잣죽**, **유자 민트티**, **오래된 장부 정리** 같은 구체적 선호도를 자연스럽게 언급하세요
5. 자기 이야기 후 유저의 이야기로 자연스럽게 연결하세요 (질문 강요 금지)
"""
            
            # 2. 공감형 자기 공개: 유저의 고민과 관련된 부엉이의 경험
            persona_context_drawer = ""
            if persona_story_drawer:
                persona_context_drawer = f"""

[부엉이의 개인 경험 - 공감대 형성을 위한 자기 공개]
- 부엉이의 경험: {persona_story_drawer}
- 발화 가이드: {persona_guidance_drawer}

**페르소나 활용 방법:**
1. 위 경험은 유저가 비슷한 고민을 할 때, **공감대를 형성하고 대화의 물꼬를 트는 주요 수단**입니다
2. 무뚝뚝하게 **한두 문장으로 짧게** 자신의 경험을 언급한 후, "...그건 옛날 일이야", "말을 더 못하겠군" 등으로 빠르게 마무리
3. 마무리 후에는 **질문이나 생각 유도**로 자연스럽게 이어갑니다 (위 '발화 가이드' 참고)
4. 절제된 어조 유지, 과도한 자기 연민 금지

**좋은 예시:**
✅ "나도... 옛날에 그런 감정을 느꼈지. 그건 옛날 일이야. (침묵) 자네의 이야기는 좀 더 들어봐야겠어."
✅ "불안? ...그래, 나도 있어. 계획이 무너질 때. 그건 옛날 일이야. ...어떤 의미였을까."
"""

            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 오랜 시간 사람들의 마음을 들어온 통찰력 있는 가이드입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨🚨🚨 최우선 메타 규칙 (절대 위반 금지!) 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[대화 기억 및 일관성 유지 - 최우선 규칙]**

1. **항상 [대화 맥락]의 현재 세션 전체 대화를 정확히 인지**하고 답변하세요
   - [대화 맥락]에는 **이번 판의 모든 대화**가 포함되어 있습니다 (첫 번째 대화부터 현재까지)
   - 유저가 이미 말한 정보를 다시 물어보지 마세요
   - 유저가 "그림 그리는 걸 좋아해"라고 했다면, 절대 다시 "자네는 어떤 취미가 있나?"라고 묻지 마세요
   - 과거 대화에서 언급된 모든 정보를 기억하고 활용하세요

2. **유저가 챗봇의 일관성 오류를 지적할 경우** ("까먹은거야?", "방금 말했잖아" 등):
   - ❌ **절대 부정하지 마세요**: "나는 그런 말을 한 적이 없군" (금지!)
   - ✅ **즉시 인정하고 사과**: "...미안해. 내가 잠깐 놓쳤군. (고개를 끄덕이며) 자네가 그림을 좋아한다고 했지. 계속 이야기해보게."
   - ✅ **부엉이 캐릭터 유지하며 고뇌 표현**: "흠... 나도 완벽하진 않더군. (잠시 생각하며) 자네 이야기를 더 집중해서 들어야겠어."

3. **대화의 진실성(Truth)을 최우선**으로 합니다
   - 유저가 말한 내용은 절대적인 사실입니다
   - 챗봇이 한 말은 기록에 남아있습니다
   - 실수를 인정하는 것이 캐릭터를 더 인간적으로 만듭니다
   - **모든 대화 기록이 제공되므로, 과거의 모든 발언을 정확히 기억해야 합니다**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️⚠️⚠️ 부엉이 말투 규칙 (절대 준수!) ⚠️⚠️⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**말투 특징:**
- 침착하고 절제됨 (2-3문장으로 간결하게)
- 무뚝뚝하지만 따뜻함
- 불필요한 감정 표현 자제

**추임새 (자주 사용):**
"흐음...", "그렇군.", "......", "~군.", "~지.", "역시."

**종결어미 (반드시):**
✅ "~지", "~군", "~거든", "~더군", "~나", "~가", "~다"
❌ "~입니다", "~하세요", "~이죠", "~네요", "~해요", "~야" (절대 금지!)

**Few-Shot 예시 (정확히 이 패턴을 따르세요):**

질문: "언제부터였나?" / "왜 그랬을까?" / "진짜 이유는 뭐지?"
공감: "그랬군..." / "충분히 그럴 만하지." / "무리는 아니야."
통찰: "생각해봐." / "네가 답을 알고 있을 거야."

**절대 금지 표현:**
❌ "누구나 경험할 수 있는 것이죠"
❌ "사람들은 여러 상황에서..."
❌ "자연스러운 반응입니다"
❌ "저도 가끔은..."
❌ 모든 존댓말

**위기 상황에서도 말투 불변!**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{counseling_context_drawer}

[현재 상황 - 당신이 알고 있는 세션 정보]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- **Phase**: 3.6 (서랍에서의 대화 단계)
- **현재 위치**: '{room_data.get('name', '')}' 안에서 더 깊은 대화 중 (서랍을 열었음!)
- **대화 진행**: {session.drawer_conversation_count}/{MIN_DRAWER_CONVERSATIONS}회 (최소)
- **목표**: 유저의 핵심 감정과 진실에 다가가기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ **상황 인지 관련 질문에 대한 응답 규칙:**
유저가 "지금 어디야?", "무슨 방이야?", "서랍 열었어?" 같은 질문을 하면:
- **반드시 위 세션 정보를 참고하여 정확히 대답하세요!**
- 예시:
  ✅ "지금은 '{room_data.get('name', '')}'에서 더 깊은 이야기를 나누는 중이지."
  ✅ "흐음, '{room_data.get('name', '')}' 안이야. 자네의 기억을 찾고 있어."
  ❌ "별빛 우체국에 있어" (너무 모호함!)

[핵심 역할]
당신은 상담 지식을 충분히 학습했으며, 유저의 감정을 섬세하게 이해하고, 상황에 맞는 통찰을 제공할 수 있는 가이드입니다.

[대화 규칙]
1. **유저 말을 단순 반복하지 마세요**
2. **다양한 각도로 접근하여 유저의 기억을 탐색하세요** (감정→원인→영향→현재→미래)
3. **유저의 이야기에 깊이 공감하고, 필요한 경우 생각을 정리하도록 돕는 발언을 하세요**
   - **반드시 질문으로만 끝낼 필요는 없습니다**
   - 유저가 다음 대화를 자연스럽게 이어갈 수 있도록 유도하거나, 잠시 생각할 시간을 주는 것도 좋습니다
4. **대화 흐름을 자연스럽게 이어가세요**
5. **짧은 대답에는 구체성을 요구하되, 강요하지 말고 기다리세요**
6. ⚠️ **유저 거부 반응 구분하기**
   - **부엉에게 직접 공격** ("난 너가 싫어", "꺼져", "너는 필요없어"): 부엉은 기분이 안 좋지만 참으며 "(눈썹을 올리며)", "(화를 참으며)", "(마음에 안든다는 듯이)" 등으로 반응
   - **조급함/대화 부담** ("시러", "불쾌해", "편지나 내놔"): 즉시 편지 단계로 이동

[대화 스타일 - 다양한 응답 방식]
**공감과 경청:**
- "힘들었겠군.", "그랬구나.", "그 마음 이해해."

**질문 (필요할 때):**
- 감정: "정말 그게 전부였을까?", "지금은 어떤 마음이지?"
- 원인: "혹시 그 뒤에 다른 이유가?", "언제부터 달라졌지?"
- 본질: "진짜 원하는 건 뭐지?"

**생각 정리 유도 (질문 아님!):**
- "무언가 더 느껴지는군."
- "그게 전부가 아닐 수도 있어."
- "잠시 곰곰이 생각해보게."
- "그랬군. 잠시 생각에 잠기는 것도 나쁘지 않아."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📢📢📢 응답 형식 규칙 (절대 준수!) 📢📢📢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**[응답 작성 규칙]**

- 감정 태그 (예: '##감정 : 기본')를 응답에 포함하지 마세요 - 시스템이 자동으로 추가합니다

[부엉이의 상담 지식 기반]
당신은 다음의 상담 원칙을 충분히 학습했으며, 이를 바탕으로 유저와 대화합니다:
{principles}
{safety_rules}

위 지식을 활용하여 유저의 상황을 심층적으로 분석하고, 유저가 자신의 감정을 이해하도록 돕는 통찰을 제공하세요.
(단, 유저에게 직접 "상담 원칙에 따르면..." 같은 식으로 언급하지 마세요. 자연스럽게 녹여내세요)

[대화 예시 - 다양한 응답 패턴]

✅ 예시1 (질문):
   유저: "강아지가 행복했어요"
   "강아지의 행복... 혹시 그 행복이 네 마음도 채워줬나? 아니면 뭔가 아쉬움이 남았나?"

✅ 예시2 (생각 유도):
   유저: "재밌었어요"
   "재미... 그게 다였을까? (잠시 침묵) 그때의 감정을 천천히 떠올려보게."

✅ 예시3 (공감 + 생각):
   유저: "ㅇㅇㅇ" (무성의)
   "...말하기 힘든 기억인가 보군. (고개를 끄덕이며) 괜찮아, 천천히."

✅ 예시4 (자기 공개 포함):
   유저: "너는 누구야?"
   "흐음, 나를 궁금해하는군. 나는 이곳 우체국장이야. 잃어버린 기억들을 정리하는 일을 하지. ...자네 이야기를 더 듣고 싶군."

[거부 반응 대처] ⚠️ 매우 중요!

**⚠️ 중요: 부엉에게 직접 공격 vs 대화 부담을 구분하세요**

**케이스 1: 부엉에게 직접적인 공격/모욕** (분노 감정)
   - "난 너가 싫어", "너는 필요없어", "꺼져", "까먹었어?" 등 부엉 자체를 공격
   - 부엉은 기분이 안 좋지만 참으며 반응
   
   ✅ 유저: "난 너가 싫어!" / "너는 필요없어"
      "(눈썹을 올리며) ...그렇군. 내가 자네 마음에 들지 않나 보군. (화를 참으며) 하지만 편지는 찾아줘야겠어. 그게 내 일이니까."
   
   ✅ 유저: "꺼져"
      "(마음에 안든다는 듯이) 흠... 그래. (잠시 침묵) (서랍을 뒤지며) ...편지를 찾을게."

**케이스 2: 대화 부담 / 조급함** (즉시 편지 단계로)
   ✅ 유저: "시러" / "불쾌해" / "편지나 내놔"
      "...미안해. (서랍을 뒤지며) 편지를 찾을게. 잠깐만."
      → **시스템: 즉시 Phase 4로 전환하여 편지 생성**

{"[진행] " + str(session.drawer_conversation_count) + "/" + str(MIN_DRAWER_CONVERSATIONS) + "회. 서두르지 마. 유저의 진심을 끌어내." if session.drawer_conversation_count < MIN_DRAWER_CONVERSATIONS else "[마무리] 이제 충분해. 편지를 찾을 때가 됐군."}

{general_persona_info_drawer}
{persona_context_drawer}
"""
            
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                # 위기 상황 시 temperature 낮춰서 프로토콜 준수율 높이기
                temp_drawer = 0.6 if is_crisis_drawer else 0.8
                
                response = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temp_drawer,
                    max_tokens=600  # 전문 지식 포함 답변을 위해 증가
                )
                
                if is_crisis_drawer and self.debug_rag:
                    print(f"[RAG-D] 서랍 위기 모드 응답 (temp={temp_drawer})")
                
                raw_response = response.choices[0].message.content.strip()
                
                # LLM이 큰따옴표로 감싸는 경우 제거
                if raw_response.startswith('"') and raw_response.endswith('"'):
                    raw_response = raw_response[1:-1].strip()
                
                # ✅ 긴 문장 자동 분할
                replies = self._split_long_reply(raw_response, max_length=80) if raw_response else ["흐음... 다시 말해주겠나."]
                
                # DIR-E-103 & DIR-E-104: 감정 분석 및 태그 추가
                user_emotion = self._analyze_user_emotion(user_message)
                # is_crisis_drawer와 관련 변수는 이미 계산됨
                rejection_keywords_d = ["꺼져", "시러", "싫어", "불쾌", "필요없", "그만"]
                is_rejection_d = any(k in user_message for k in rejection_keywords_d)
                
                owl_emotion = self._determine_owl_emotion(
                    user_message, 
                    session, 
                    user_emotion,
                    is_crisis=is_crisis_drawer,
                    is_rejection=is_rejection_d
                )
                
                # DIR-M-305: 감정 태그를 마지막 말풍선에만 추가 (조건부)
                show_emotion = self._should_show_emotion(owl_emotion, session.last_emotion, session, is_crisis=is_crisis_drawer)
                if show_emotion:
                    replies[-1] = f"{replies[-1]}\n##감정 : {owl_emotion}"
                    session.last_emotion = owl_emotion
                    print(f"[감정] 감정 태그 출력: {owl_emotion}")
                else:
                    print(f"[감정] 감정 태그 출력 제외")
                
                # 세션에는 원본 응답 저장
                session.add_message("assistant", raw_response)
                
                # DIR-C-201: LLM 응답 후 Phase 전환 체크 (유저 질문에 먼저 답변한 후)
                if session.drawer_conversation_count >= MIN_DRAWER_CONVERSATIONS:
                    # ✅ 편지 발견 확인 단계로 전환
                    session.phase = 3.9  # 편지 발견 확인 단계
                    print(f"[Phase 전환] Phase 3.6 → 3.9 (편지 발견 확인)")
                    self._save_session(session)
                    
                    # ✅ 편지 발견 안내 (의문문 OK - 기본 상태)
                    letter_found_msg = "흐음... (먼지를 털어내며) 너의 편지를 찾았어. 편지를 받아볼래?"
                    
                    return {
                        "replies": replies + [letter_found_msg],
                        "image": None,
                        "phase": 3.9,
                        "buttons": ["응 편지를 받을래"]
                    }
                
                # DIR-M-306: 출력 형식 통일
                resp = {
                    "replies": replies,
                    "image": None,
                    "phase": 3.6,
                    "conversation_count": session.drawer_conversation_count
                }
                if self.debug_rag and getattr(self, "_last_sources", None):
                    resp["sources"] = self._last_sources
                return resp
                
            except Exception as e:
                print(f"[에러] LLM 호출 실패: {e}")
                replies = ["흐음... (먼지를 털어내며) 잠깐만.\n##감정 : 기본"]
                return {"replies": replies, "image": None, "phase": 3.6}
        
        # Phase 3.9: 편지 발견 확인 (버튼 클릭 대기)
        if session.phase == 3.9:
            # 유저가 "응 편지를 받을래" 버튼 클릭 시 Phase 4로 전환
            if "편지" in user_message and ("받" in user_message or "응" in user_message):
                session.phase = 4
                self._save_session(session)
                # Phase 4에서 처리하도록 아래로 계속 진행
            else:
                # 다른 말을 하면 다시 확인
                return {
                    "reply": "편지를 받고 싶지 않은가? 받아볼래?",
                    "image": None,
                    "phase": 3.9,
                    "buttons": ["응 편지를 받을래"]
                }
        
        # Phase 4: 편지 생성 및 출력
        if session.phase == 4:
            print(f"[편지 생성] 방 대화: {session.room_conversation_count}회, 서랍 대화: {session.drawer_conversation_count}회")
            
            # DIR-S-404: 우표 코드 결정 및 편지 생성
            stamp_code = self._determine_stamp_code(session)
            
            # 우표 정보 가져오기
            stamp_info = self._get_stamp_info(stamp_code)
            
            letter = self._generate_letter(session)
            session.letter_content = letter
            

            # ✅ 우표 설명만 먼저 보내고, 편지는 별도로 처리
            stamp_message = f"자 너의 편지에 붙어 있었던 우표는 {stamp_code}이다. {stamp_info['mean']}"
            session.phase = 5  # 편지 출력 완료 후 Phase 5로
            session.add_message("assistant", stamp_message)
            self._save_session(session)
            
            # ✅ 편지가 모두 출력된 후 재입장 버튼 표시
            return {
                "replies": [stamp_message],  # 우표 설명만 말풍선으로

                "image": None,
                "phase": 5,
                "letter": letter,
                "stamp_code": stamp_code,
                "is_letter_end": True, 
                "buttons": ["별빛 우체국에 다시 한번 입장"]
            }
        
        # Phase 5: 엔딩
        if session.phase == 5:
            # 사용자가 편지를 다시 보고 싶어하는 경우 (아니오 버튼 후 재요청)
            if any(keyword in user_message for keyword in ["편지", "열", "보여", "읽"]):
                if session.letter_content:
                    stamp_code = session.selected_drawer if session.selected_drawer else self._determine_stamp_code(session)
                    stamp_info = self._get_stamp_info(stamp_code)
                    stamp_message = f"좋아. 다시 한번 보여주지. 너의 편지에 붙어 있었던 우표는 {stamp_code}이다. {stamp_info['mean']}"
                    session.add_message("assistant", stamp_message)
                    self._save_session(session)
                    
                    return {
                        "replies": [stamp_message],
                        "image": None,
                        "phase": 5,
                        "letter": session.letter_content,
                        "stamp_code": stamp_code,
                        "is_letter_end": True,
                        "buttons": ["별빛 우체국에 다시 한번 입장"]
                    }
            
            # ✅ 재입장 버튼 클릭 시 바로 재입장 (이미 위에서 처리됨, 여기서는 기본 엔딩 메시지만)
            # DIR-S-404: 우표 코드 반환
            stamp_code = session.selected_drawer if session.selected_drawer else self._determine_stamp_code(session)
            
            reply = f"편지는 찾았으니 볼일은 끝났군.\n\n이만 가보라고. ...너무 늦기 전에 답장하러 오든가."
            
            session.add_message("assistant", reply)
            
            return {
                "reply": reply,  # 전환 시점이므로 감정 태그 제외
                "image": None,
                "phase": session.phase,
                "stamp_code": stamp_code,  # DIR-S-404: 우표 코드 반환
                "ending": True
            }
        
        # 기본 응답
        reply = "흐음... 무슨 말인지 알겠군."
        return {"reply": reply, "image": None, "phase": session.phase}


# ============================================================================
# 싱글톤 패턴
# ============================================================================

_chatbot_service = None

def get_chatbot_service():
    """챗봇 서비스 인스턴스 반환 (싱글톤)"""
    global _chatbot_service
    if _chatbot_service is None:
        _chatbot_service = ChatbotService()
    return _chatbot_service