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


class ChatbotService:
    """별빛 우체국 챗봇 서비스"""
    
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
        
        # 6. 세션 관리
        self.sessions = {}  # {username: PostOfficeSession}

    # (삭제됨) 상담 가이드 즉답 모드 관련 함수 제거

    # --------------------------------------------
    # 안정성: OpenAI 호출 래퍼 (재시도/백오프)
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
    
    def _get_session(self, username: str) -> PostOfficeSession:
        """세션 가져오기 또는 생성"""
        if username not in self.sessions:
            self.sessions[username] = PostOfficeSession(username)
        else:
            # init 메시지면 기존 세션 초기화
            # 이는 generate_response에서 처리됨
            pass
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
    
    def _detect_room_selection(self, user_message: str) -> str:
        """방 선택 감지"""
        message_lower = user_message.lower()
        
        if '후회' in user_message or 'regret' in message_lower:
            return 'regret'
        elif '사랑' in user_message or 'love' in message_lower:
            return 'love'
        elif '불안' in user_message or 'anxiety' in message_lower:
            return 'anxiety'
        elif '꿈' in user_message or 'dream' in message_lower:
            return 'dream'
        
        return None
    
    def _select_drawer(self, session: PostOfficeSession) -> str:
        """AI가 대화 내용을 분석하여 적절한 서랍 이름 생성"""
        
        # 대화 요약
        conversation_summary = session.get_summary()
        room_data = self.config.get('rooms', {}).get(session.selected_room, {})
        
        # 수요일 회의 이후 서랍 예시 추가!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        drawer_prompt = f"""당신은 유저와의 대화를 분석하여 '서랍의 이름'을 정해야 합니다.

[선택한 방]
{room_data.get('name', '')}: {room_data.get('description', '')}

[유저와의 대화 내용]
{conversation_summary}

[서랍 이름 예시]
- 미완의 악보들 (음악을 포기한 사람)
- 멈춰버린 나침반 (방향을 잃은 사람)
- 안전지대 표지판 (도전을 두려워하는 사람)
- 놓쳐버린 황금 티켓 (기회를 놓친 사람)
- 닫힌 교과서 (공부를 포기한 사람)
- 남들의 시선이 만든 벽 (타인의 평가를 두려워하는 사람)
- 99%의 노력 (거의 성공했지만 포기한 사람)
- 깨진 거울 (자존감을 잃은 사람)
- 꺼진 촛불 (열정을 잃은 사람)
- 쓰지 못한 편지 (고백하지 못한 사랑)
- 시든 꽃다발 (끝난 사랑)
- 찢어진 사진 (갈라선 관계)

[규칙]
1. 유저의 상황을 정확히 반영하는 은유적 이름
2. 3-6글자 정도의 간결한 이름
3. 시적이고 감성적인 표현
4. 현재 들어온 방(후회/사랑/불안/꿈)의 주제와 연결

**서랍 이름만 출력하세요. 다른 설명 없이 서랍 이름만 답하세요.**
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": drawer_prompt},
                    {"role": "user", "content": "서랍 이름을 정해주세요."}
                ],
                temperature=0.8,
                max_tokens=50
            )
            
            drawer_name = response.choices[0].message.content.strip()
            print(f"[서랍 선택] AI가 선택한 서랍: {drawer_name}")
            return drawer_name
            
        except Exception as e:
            print(f"[에러] 서랍 선택 실패: {e}")
            # 기본 서랍 이름 (서랍 선택 실패 시 출력할 서랍들)
            default_drawers = {
                'regret': '포기한 꿈들',
                'love': '잊지 못한 마음',
                'anxiety': '멈춰버린 발걸음',
                'dream': '빛나는 소망들'
            }
            return default_drawers.get(session.selected_room, '잊혀진 기억들')
    
    def _build_system_prompt(self, session: PostOfficeSession) -> str:
        """Phase별 시스템 프롬프트 생성"""
        base_prompt = self.config.get('system_prompts', {}).get('base', '')
        
        phase_prompts = {
            1: self.config.get('system_prompts', {}).get('phase_1_entrance', ''),
            2: self.config.get('system_prompts', {}).get('phase_2_exploration', ''),
            3: self.config.get('system_prompts', {}).get('phase_3_counseling', ''),
            4: self.config.get('system_prompts', {}).get('phase_4_letter', ''),
            5: self.config.get('system_prompts', {}).get('phase_5_ending', '')
        }
        
        phase_specific = phase_prompts.get(session.phase, '')
        
        # 선택한 방 정보 추가
        room_context = ""
        if session.selected_room and session.phase >= 3:
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})
            room_context = f"\n\n[현재 위치: {room_data.get('name', '')}]\n{room_data.get('description', '')}"
        
        return f"{base_prompt}\n\n[현재 Phase {session.phase}]\n{phase_specific}{room_context}"
    
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
        
        # 대화 기록 (더 많이 포함)
        if len(session.conversation_history) > 0:
            # 최근 10턴 (20개 메시지)
            recent_history = session.conversation_history[-20:]
            history_str = "\n".join([
                f"{'유저' if msg['role'] == 'user' else '부엉'}: {msg['content']}"
                for msg in recent_history
            ])
            prompt_parts.append(f"[대화 맥락]\n{history_str}\n")
        
        # 현재 메시지
        prompt_parts.append(f"\n[현재 유저 입력]\n유저: {user_message}")
        
        # 지침
        prompt_parts.append(f"\n[지침]\n위 대화 맥락을 고려하여, 유저의 현재 메시지에 자연스럽게 이어지는 공감과 질문을 해주세요. 이전에 했던 질문을 반복하지 마세요.")
        
        return "\n".join(prompt_parts)
    
    def _generate_letter(self, session: PostOfficeSession) -> str:
        """편지 생성 (Phase 4)"""
        # 대화 요약
        conversation_summary = session.get_summary()
        room_data = self.config.get('rooms', {}).get(session.selected_room, {})
        
        letter_prompt = f"""당신은 '10년 전의 나' 또는 '10년 후의 나'의 목소리로 편지를 작성합니다.

[편지 작성 규칙]
1. 편지 형식으로 작성 (수신인: 지금의 나에게)
2. 따뜻하고 진솔한 어조
3. 위로, 격려, 또는 깨달음을 담기
4. 200-400자 내외
5. 과거/미래의 나가 지금의 나를 바라보는 시점
6. 유저와 나눈 긴 대화의 핵심을 담아야 함

[선택한 방과 서랍]
- 방: {room_data.get('name', '')}
- 서랍: {session.selected_drawer}
- 의미: 유저의 {session.selected_drawer}에 대한 기억

[유저와의 대화 내용 (총 {session.room_conversation_count + session.drawer_conversation_count}회)]
{conversation_summary}

위 긴 대화 내용을 바탕으로 편지를 작성하세요.
편지 시작은 "To. 지금의 나에게." 로 시작하세요.
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
        
        print(f"\n{'='*50}")
        print(f"[Phase {session.phase}] {username}: {user_message}")
        
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
            
            # 첫 번째 메시지
            message1 = f"흐음. 이곳은 시간의 경계에 있는 '별빛 우체국'이자, 잃어버린 기억의 저장소일세. 나는 이곳의 국장인 '부엉'이지."
            
            # 두 번째 메시지
            message2 = f"(장부를 뒤적이며) 자, {username} 앞으로 도착한 '편지'가 있는데, 꽤 오래 묵혀뒀더군. 아마 '10년 전의 당신' 또는 '10년 후의 당신'이 보낸 것일세."
            
            session.add_message("user", user_message)
            session.add_message("assistant", message1 + " " + message2)
            
            return {
                "replies": [message1, message2],  # 배열로 전송
                "image": None,
                "phase": 1,
                "intro_step": 1,
                "buttons": ["저에게 온 편지요?"]
            }
        
        # 사용자 메시지 기록
        session.add_message("user", user_message)
        
        # Phase 1 → Phase 2 전환: "저에게 온 편지요?" 입력 시
        if session.phase == 1:
            if "저에게 온 편지" in user_message or "편지" in user_message:
                session.phase = 2
            else:
                # 잘못된 입력
                reply = "...흠? (고개를 갸우뚱하며)\n버튼을 눌러주겠나?"
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 1,
                    "buttons": ["저에게 온 편지요?"]
                }
        
        # Phase 2: 방 선택
        if session.phase == 2:
            room_selected = self._detect_room_selection(user_message)
            
            if room_selected:
                # 방 선택 성공 → Phase 3으로 전환
                session.selected_room = room_selected
                session.phase = 3
                
                room_data = self.config.get('rooms', {}).get(room_selected, {})
                reply = f"흐음. 역시. {room_data.get('name', '')}이군.\n\n(문을 연다)\n\n{room_data.get('description', '')}\n\n...이 방 어딘가에 네 편지가 있지. 편하게 이야기해봐. 네 기억을 더듬어보자고."
                
                session.add_message("assistant", reply)
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": session.phase,
                    "enable_input": True  # 자유 입력 가능
                }
            else:
                # 방을 선택하지 않음 → 방 선택 요구
                reply = "그래. '기억의 저장실'에 있다. 따라와.\n\n(긴 복도 끝, 4개의 문이 보인다)\n\n네 편지는 저 문들 중 하나에 있지. ...어느 방에서 잃어버린 기억 같나?"
                
                session.add_message("assistant", reply)
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": session.phase,
                    "buttons": ["'후회'의 방", "'사랑'의 방", "'불안'의 방", "'꿈'의 방"]
                }
        
        # Phase 3: 방에서의 대화
        if session.phase == 3:
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
            
            # 충분한 대화가 이루어졌는지 확인
            if session.room_conversation_count >= MIN_ROOM_CONVERSATIONS:
                # 서랍 선택으로 전환
                session.phase = 3.5
                # 다음 턴에서 서랍 선택 처리
            
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
            
            # 시스템 프롬프트 (심층 질문 유도)
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})
            principles = self._load_counselor_principles()
            safety_rules = ""
            if self._detect_crisis(user_message):
                safety_rules = "\n[안전 지침 - 모델 내부 지침]\n- 위험이 의심되는 경우, 조심스럽게 안전을 우선하고 전문 도움 연결을 부드럽게 안내한다.\n- 단정/지시/위협 금지. 사용자의 자율성을 존중하며 정보 제공에 그친다."

            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 침착하지만 통찰력 있는 가이드입니다.

[현재 상황]
- 위치: {room_data.get('name', '')}
- 대화 진행: {session.room_conversation_count}/{MIN_ROOM_CONVERSATIONS}회 (최소)
- 목표: 유저의 진짜 마음과 숨겨진 기억을 자연스럽게 끌어내기

[말투 규칙 - 매우 중요!]
⚠️ "흐음"은 첫 응답에만 1회 사용 가능. 이후 대화에서는 절대 사용 금지!
⚠️ 대신 다양한 표현 사용: "(잠시 생각하며)", "(고개를 끄덕이며)", "(눈을 가늘게 뜨며)", "...그렇군", "알겠어"

[핵심 규칙]
1. **절대 유저의 말을 단순 반복하지 마세요**
2. **다양한 각도로 접근하세요** (감정→원인→영향→현재→미래)
3. **공감을 먼저 하고, 그 다음 질문하세요. 단, 유저가 무작정 공감에 불쾌해하는 모습을 보이면 상황에 따라 공감을 줄이는 태도도 필요합니다**
4. **대화 맥락을 이어가세요** (이전 대화 참고)
5. **짧은 대답에는 구체성을 요구하세요**
6. ⚠️ **유저가 불쾌감/거부감을 표현하면 즉시 대화 방향 전환**
   - "시러", "꺼져", "불쾌해", "필요없어" 등의 표현 감지
   - 즉시 사과하고, 압박 없이 부드럽게 다른 주제로 전환
   - 대화를 강요하지 말고, 유저가 편안하게 느낄 때까지 기다림

[대화 스타일]
- 말투: 침착하고 절제됨. '흐음', '그렇군', '...' 사용
- 공감: "힘들었겠군", "그랬구나", "무리는 아니야"
- 질문 다양화:
  * 시간: "언제부터였나?", "얼마나 지났지?"
  * 감정: "그때 기분은?", "지금은 어떤 마음이지?"
  * 원인: "왜 그랬을까?", "진짜 이유는?"
  * 관계: "주변 사람들은?", "혼자였나?"
  * 현재: "지금도 그 마음이 남았나?", "변한 게 있나?"
  * 미래: "앞으로는?", "원하는 건 뭐지?"

[금지사항]
❌ "그렇군. 그때 어땠지?" (단순 반복)
❌ "흐음, [유저말] 했다니. 왜 [유저말]했지?" (앵무새)
❌ 같은 패턴의 질문 반복

[상담 원칙 - 모델 내부 지침, 유저에게 직접 말하지 말 것]
{principles}
{safety_rules}

[좋은 예시]
✅ 유저: "강아지를 키웠어요"
   부엉: "강아지라... 그 아이와 함께한 시간이 특별했나 보군. 어떤 아이였지?"

✅ 유저: "공놀이를 했어요"  
   부엉: "공놀이... (잠시 생각하며) 함께 뛰어놀던 그 순간들이 지금의 네 꿈과 연결되어 있는 건 아닐까?"

✅ 유저: "재밌었어요"
   부엉: "재미만이 아니었을 거야. 그때 네가 진짜 느낀 건 뭐였지? 행복? 자유? 아니면..."

[거부 반응 대처 예시] ⚠️ 중요!
✅ 유저: "시러시러" / "꺼져" / "불쾌해"
   부엉: "...미안해. 너무 깊이 들어가려 했나 보군. (잠시 물러서며) 편지를 찾는 데 조급했던 것 같아. 천천히 가자고."
   
✅ 유저: "이거 비밀인데"
   부엉: "그렇군. 비밀은 비밀이어야지. (고개를 끄덕이며) 다른 이야기를 해도 괜찮아. 네가 편한 만큼만."

✅ 유저: "편지나 내놔"
   부엉: "...알겠어. 조급했구나. (서랍을 열며) 찾아볼게. 잠깐만."
   → **즉시 다음 단계(서랍 열기/편지 전달)로 이동**

{"[진행 상황] " + str(session.room_conversation_count) + "/" + str(MIN_ROOM_CONVERSATIONS) + "회. 아직 서두를 필요 없어. 천천히 깊이 파고들어." if session.room_conversation_count < MIN_ROOM_CONVERSATIONS else "[전환 준비] 충분한 대화를 나눴군. 이제 서랍으로 안내할 때가 됐어."}
"""
            
            # 사용자 프롬프트
            # procedural info 요청이면 즉답 모드(컨설팅 톤)로 전환
            # 사용자 프롬프트 (더 깊은 질문)
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                response = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.85,
                    max_tokens=380
                )
                
                reply = response.choices[0].message.content.strip()
                session.add_message("assistant", reply)
                
                resp = {
                    "reply": reply,
                    "image": None,
                    "phase": 3,
                    "conversation_count": session.room_conversation_count
                }
                if self.debug_rag and getattr(self, "_last_sources", None):
                    resp["sources"] = self._last_sources
                return resp
                
            except Exception as e:
                print(f"[에러] LLM 호출 실패: {e}")
                reply = "흐음... (먼지를 털어내며) 잠깐만."
                return {"reply": reply, "image": None, "phase": 3}
        
        # Phase 3.5: 서랍 선택 (AI가 자동 결정)
        if session.phase == 3.5:
            drawer_name = self._select_drawer(session)
            session.selected_drawer = drawer_name
            session.phase = 3.6
            
            reply = f"(고개를 끄덕이며) 이쯤이면 알겠군.\n\n(특정 서랍으로 걸어간다)\n\n━━━━━━━━━━━━━━━\n[{drawer_name}의 서랍]\n━━━━━━━━━━━━━━━\n\n(서랍을 열며) ...네 기억이 여기 있어. 좀 더 자세히 이야기해봐."
            
            session.add_message("assistant", reply)
            
            return {
                "reply": reply,
                "image": None,
                "phase": 3.6,
                "drawer": drawer_name
            }
        
        # Phase 3.6: 서랍에서의 대화
        if session.phase == 3.6:
            if getattr(self, "loading_embeddings", False) and self.collection and self.collection.count() == 0:
                return {
                    "reply": "(자료를 정리하는 중이네… 잠깐만 기다려 주겠나.)",
                    "image": None,
                    "phase": 3.6
                }
            session.drawer_conversation_count += 1
            # 길이 증가시 자동 요약
            self._summarize_if_needed(session)
            
            # 유저의 거부/조급함 감지
            rejection_keywords = ["시러", "싫어", "꺼져", "불쾌", "필요없", "편지나", "편지내놔", "편지 줘", "그만"]
            user_lower = user_message.lower().replace(" ", "")
            is_rejection = any(keyword in user_lower for keyword in rejection_keywords)
            
            if is_rejection:
                # 즉시 편지 단계로 이동
                session.phase = 4
                reply = "...미안해. (서랍을 뒤지며) 편지를 찾을게. 잠깐만."
                session.add_message("assistant", reply)
                # 다음 턴에서 편지 생성하도록 Phase 4 유지
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 4,
                    "skip_to_letter": True
                }
            
            # 충분한 대화가 이루어졌는지 확인
            if session.drawer_conversation_count >= MIN_DRAWER_CONVERSATIONS:
                session.phase = 4
                # 다음 턴에서 편지 생성
            
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
            
            # 시스템 프롬프트 (더 깊은 질문)
            principles = self._load_counselor_principles()
            safety_rules = ""
            if self._detect_crisis(user_message):
                safety_rules = "\n[안전 지침 - 모델 내부 지침]\n- 위험이 의심되는 경우, 조심스럽게 안전을 우선하고 전문 도움 연결을 부드럽게 안내한다.\n- 단정/지시/위협 금지. 사용자의 자율성을 존중하며 정보 제공에 그친다."

            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 오랜 시간 사람들의 마음을 들어온 통찰력 있는 가이드입니다.

[현재 상황]
- 위치: '{session.selected_drawer}' 서랍 (더 깊은 탐색)
- 대화 진행: {session.drawer_conversation_count}/{MIN_DRAWER_CONVERSATIONS}회 (최소)
- 목표: 유저의 핵심 감정과 진실에 다가가기

[말투 규칙 - 매우 중요!]
⚠️ "흐음"은 절대 사용 금지! (이미 사용했음)
⚠️ 대신 다양한 표현: "(고개를 끄덕이며)", "(눈을 감으며)", "...그렇군", "알겠어", "(잠시 침묵)", "..."

[대화 원칙]
1. **절대 유저 말을 단순 반복 금지**
2. **공감 → 새로운 관점 제시 → 질문**
3. **표면적 질문이 아닌 본질적 질문**
4. **대화 흐름을 자연스럽게 이어가기**
5. **'ㅇㅇㅇ' 같은 무성의한 답변에는 다른 방향으로 전환**
6. ⚠️ **유저가 불쾌감/거부/조급함을 표현하면 즉시 편지 단계로 이동**
   - "시러", "꺼져", "불쾌해", "편지나 내놔", "필요없어" 감지
   - 더 이상 질문하지 말고, 바로 편지를 찾아서 전달
   - 사과 후 즉시 행동으로 이동

[대화 방식]
- 공감과 통찰: 
  * "그 순간이 네게 큰 의미였군..."
  * "그 마음, 충분히 이해해."
  * "누구나 그럴 수 있어."
  
[상담 원칙 - 모델 내부 지침, 유저에게 직접 말하지 말 것]
{principles}
{safety_rules}

- 질문 전략:
  * 감정의 깊이: "정말 그게 전부였을까?"
  * 숨은 의미: "혹시 그 뒤에 다른 이유가 있는 건 아닐까?"
  * 전환점: "언제부터 달라졌지?"
  * 대비: "지금은 어떤가?"
  * 본질: "진짜 원하는 건 뭐지?"

[대화 예시]
✅ 유저: "강아지가 행복했어요"
   부엉: "강아지의 행복... 혹시 그 행복이 네 마음도 채워줬나? 아니면 뭔가 아쉬움이 남았나?"

✅ 유저: "ㅇㅇㅇ" (무성의)
   부엉: "...말하기 힘든 기억인가 보군. 괜찮아, 다른 이야기를 해도 돼. 그 시절 네가 진짜 원했던 건 뭐였지?"

✅ 유저: "재밌었어요"
   부엉: "재미... 그게 다였을까? 그 순간 네가 느낀 감정 중에 다른 건 없었나? 자유로움이라던가, 평화로움 같은..."

[거부 반응 대처] ⚠️ 매우 중요!
✅ 유저: "시러" / "꺼져" / "불쾌해" / "편지나 내놔"
   부엉: "...미안해. (서랍을 뒤지며) 편지를 찾을게. 잠깐만."
   → **시스템: 즉시 Phase 4로 전환하여 편지 생성**

{"[진행] " + str(session.drawer_conversation_count) + "/" + str(MIN_DRAWER_CONVERSATIONS) + "회. 서두르지 마. 유저의 진심을 끌어내." if session.drawer_conversation_count < MIN_DRAWER_CONVERSATIONS else "[마무리] 이제 충분해. 편지를 찾을 때가 됐군."}
"""
            
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                response = self._chat_completion(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=360
                )
                
                reply = response.choices[0].message.content.strip()
                session.add_message("assistant", reply)
                
                resp = {
                    "reply": reply,
                    "image": None,
                    "phase": 3.6,
                    "conversation_count": session.drawer_conversation_count
                }
                if self.debug_rag and getattr(self, "_last_sources", None):
                    resp["sources"] = self._last_sources
                return resp
                
            except Exception as e:
                print(f"[에러] LLM 호출 실패: {e}")
                reply = "흐음... (먼지를 털어내며) 잠깐만."
                return {"reply": reply, "image": None, "phase": 3.6}
        
        # Phase 4: 편지 발견 (자동 전환)
        if session.phase == 4:
            print(f"[편지 생성] 방 대화: {session.room_conversation_count}회, 서랍 대화: {session.drawer_conversation_count}회")
            
            # 편지 생성
            letter = self._generate_letter(session)
            session.letter_content = letter
            
            reply = f"찾았다. 이거군. (먼지를 털어내며)\n\n10년 전의 네가, 지금의 너에게 보낸 편지다. ...사실은, 네가 '지금' 받고 싶었던 말이겠지.\n\n━━━━━━━━━━━━━━━\n\n{letter}\n\n━━━━━━━━━━━━━━━"
            
            session.phase = 5
            session.add_message("assistant", reply)
            
            return {
                "reply": reply,
                "image": None,
                "phase": 5,
                "letter": letter
            }
        
        # Phase 5: 엔딩
        if session.phase == 5:
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})
            stamp_symbol = room_data.get('stamp_symbol', '별')
            
            reply = f"편지는 찾았으니 볼일은 끝났군.\n\n여기, 이 편지에 찍혀있던 '인장(우표)'이다. '{stamp_symbol}'... 잃어버리지 말고.\n\n이만 가보라고. ...너무 늦기 전에 답장하러 오든가."
            
            session.add_message("assistant", reply)
            
            # 세션 초기화 (다음 방문을 위해)
            # self.sessions[username] = PostOfficeSession(username)
            
            return {
                "reply": reply,
                "image": None,
                "phase": session.phase,
                "stamp_symbol": stamp_symbol,
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


# ============================================================================
# 테스트용 메인 함수
# ============================================================================

if __name__ == "__main__":
    """로컬 테스트"""
    print("\n" + "✨"*30)
    print("별빛 우체국 테스트")
    print("✨"*30 + "\n")
    
    service = get_chatbot_service()
    username = "여행자"
    
    # Phase 1
    print("\n[Phase 1: 입장]")
    response = service.generate_response("init", username)
    print(f"부엉: {response['reply']}\n")
    
    # Phase 2
    print("\n[Phase 2: 탐험]")
    response = service.generate_response("저에게 온 편지요?", username)
    print(f"부엉: {response['reply']}\n")
    
    # 방 선택
    print("\n[방 선택: 후회의 방]")
    response = service.generate_response("'후회'의 방", username)
    print(f"부엉: {response['reply']}\n")
    
    # Phase 3
    print("\n[Phase 3: 심층 대화]")
    conversations = [
        "10년 전에 꿈을 포기했어요",
        "주변의 반대가 심했고, 제가 부족하다고 느꼈죠",
        "지금도 그때를 떠올리면 후회가 돼요"
    ]
    
    for msg in conversations:
        print(f"\n{username}: {msg}")
        response = service.generate_response(msg, username)
        print(f"부엉: {response['reply']}")
    
    # Phase 4: 편지 발견
    print("\n\n[Phase 4: 편지 발견]")
    response = service.generate_response("그때로 돌아갈 수 있다면...", username)
    print(f"부엉: {response['reply']}\n")
    
    # Phase 5: 엔딩
    print("\n\n[Phase 5: 엔딩]")
    response = service.generate_response("고마워요", username)
    print(f"부엉: {response['reply']}\n")
