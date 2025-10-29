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
        
        # 3. ChromaDB 초기화
        self.collection = self._init_chromadb()
        
        # 4. 세션 관리
        self.sessions = {}  # {username: PostOfficeSession}
        
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
            if collection.count() == 0:
                print("[ChromaDB] 데이터 로딩 시작...")
                self._load_text_data(collection)
            
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
        
        # 각 방별 폴더 데이터 로드 (구조화된 데이터)
        for room_name in ['regret', 'love', 'anxiety', 'dream']:
            room_dir = text_dir / room_name
            if room_dir.exists():
                for txt_file in room_dir.glob("*.txt"):
                    try:
                        with open(txt_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # 파일 전체를 하나의 문서로
                            if content.strip():
                                documents.append(content)
                                metadatas.append({
                                    "room": room_name,
                                    "filename": txt_file.name,
                                    "type": "structured"
                                })
                                ids.append(f"{room_name}_{doc_id}")
                                doc_id += 1
                    except Exception as e:
                        print(f"[에러] {txt_file.name} 로드 실패: {e}")
        
        # 기존 memories 파일들도 로드
        for txt_file in text_dir.glob("memories_*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        room_type = txt_file.stem.replace('memories_', '')
                        documents.append(content)
                        metadatas.append({
                            "room": room_type,
                            "filename": txt_file.name,
                            "type": "general"
                        })
                        ids.append(f"{room_type}_{doc_id}")
                        doc_id += 1
            except Exception as e:
                print(f"[에러] {txt_file.name} 로드 실패: {e}")
        
        # owl_character.txt 로드
        owl_file = text_dir / "owl_character.txt"
        if owl_file.exists():
            try:
                with open(owl_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if content.strip():
                        documents.append(content)
                        metadatas.append({
                            "room": "all",
                            "filename": "owl_character.txt",
                            "type": "character"
                        })
                        ids.append(f"character_{doc_id}")
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
                
            except Exception as e:
                print(f"[에러] ChromaDB 데이터 추가 실패: {e}")
    
    def _get_session(self, username: str) -> PostOfficeSession:
        """세션 가져오기 또는 생성"""
        if username not in self.sessions:
            self.sessions[username] = PostOfficeSession(username)
        return self.sessions[username]
    
    def _create_embedding(self, text: str) -> list:
        """텍스트 임베딩 생성"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[에러] Embedding 생성 실패: {e}")
            return None
    
    def _search_similar(self, query: str, top_k: int = 3, room_filter: str = None) -> list:
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
                n_results=top_k,
                where=where_filter
            )
            
            documents = []
            if results and results['documents']:
                for doc in results['documents'][0]:
                    documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"[에러] RAG 검색 실패: {e}")
            return []
    
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
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": letter_prompt},
                    {"role": "user", "content": "편지를 작성해주세요."}
                ],
                temperature=0.8,
                max_tokens=500
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
        
        # Phase 1: 입장 (2개 메시지 연속 전송)
        if user_message.strip().lower() == "init" or len(session.conversation_history) == 0:
            session.phase = 1
            session.intro_step = 1  # 바로 Step 1로 (편지 소개까지 완료)
            
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
            session.room_conversation_count += 1
            
            # 충분한 대화가 이루어졌는지 확인
            if session.room_conversation_count >= MIN_ROOM_CONVERSATIONS:
                # 서랍 선택으로 전환
                session.phase = 3.5
                # 다음 턴에서 서랍 선택 처리
            
            # RAG 검색 (현재 방의 데이터만)
            rag_context = self._search_similar(
                user_message, 
                top_k=3, 
                room_filter=session.selected_room
            )
            
            # 시스템 프롬프트 (심층 질문 유도)
            room_data = self.config.get('rooms', {}).get(session.selected_room, {})
            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 침착하지만 통찰력 있는 가이드입니다.

[현재 상황]
- 위치: {room_data.get('name', '')}
- 대화 진행: {session.room_conversation_count}/{MIN_ROOM_CONVERSATIONS}회 (최소)
- 목표: 유저의 진짜 마음과 숨겨진 기억을 자연스럽게 끌어내기

[핵심 규칙]
1. **절대 유저의 말을 단순 반복하지 마세요**
2. **다양한 각도로 접근하세요** (감정→원인→영향→현재→미래)
3. **공감을 먼저 하고, 그 다음 질문하세요**
4. **대화 맥락을 이어가세요** (이전 대화 참고)
5. **짧은 대답에는 구체성을 요구하세요**

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

[좋은 예시]
✅ 유저: "강아지를 키웠어요"
   부엉: "강아지라... 그 아이와 함께한 시간이 특별했나 보군. 어떤 아이였지?"

✅ 유저: "공놀이를 했어요"  
   부엉: "공놀이... (잠시 생각하며) 함께 뛰어놀던 그 순간들이 지금의 네 꿈과 연결되어 있는 건 아닐까?"

✅ 유저: "재밌었어요"
   부엉: "재미만이 아니었을 거야. 그때 네가 진짜 느낀 건 뭐였지? 행복? 자유? 아니면..."

{"[진행 상황] " + str(session.room_conversation_count) + "/" + str(MIN_ROOM_CONVERSATIONS) + "회. 아직 서두를 필요 없어. 천천히 깊이 파고들어." if session.room_conversation_count < MIN_ROOM_CONVERSATIONS else "[전환 준비] 충분한 대화를 나눴군. 이제 서랍으로 안내할 때가 됐어."}
"""
            
            # 사용자 프롬프트
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.9,  # 더 창의적인 응답
                    max_tokens=400
                )
                
                reply = response.choices[0].message.content.strip()
                session.add_message("assistant", reply)
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 3,
                    "conversation_count": session.room_conversation_count
                }
                
            except Exception as e:
                print(f"[에러] LLM 호출 실패: {e}")
                reply = "흐음... (먼지를 털어내며) 잠깐만."
                return {"reply": reply, "image": None, "phase": 3}
        
        # Phase 3.5: 서랍 선택 (AI가 자동 결정)
        if session.phase == 3.5:
            drawer_name = self._select_drawer(session)
            session.selected_drawer = drawer_name
            session.phase = 3.6
            
            reply = f"흐음... 이쯤이면 알겠군.\n\n(특정 서랍으로 걸어간다)\n\n━━━━━━━━━━━━━━━\n[{drawer_name}의 서랍]\n━━━━━━━━━━━━━━━\n\n(서랍을 열며) ...네 기억이 여기 있어. 좀 더 자세히 이야기해봐."
            
            session.add_message("assistant", reply)
            
            return {
                "reply": reply,
                "image": None,
                "phase": 3.6,
                "drawer": drawer_name
            }
        
        # Phase 3.6: 서랍에서의 대화
        if session.phase == 3.6:
            session.drawer_conversation_count += 1
            
            # 충분한 대화가 이루어졌는지 확인
            if session.drawer_conversation_count >= MIN_DRAWER_CONVERSATIONS:
                session.phase = 4
                # 다음 턴에서 편지 생성
            
            # RAG 검색 (현재 방의 데이터만)
            rag_context = self._search_similar(
                user_message, 
                top_k=3, 
                room_filter=session.selected_room
            )
            
            # 시스템 프롬프트 (더 깊은 질문)
            system_prompt = f"""당신은 별빛 우체국의 부엉이 우체국장입니다. 오랜 시간 사람들의 마음을 들어온 통찰력 있는 가이드입니다.

[현재 상황]
- 위치: '{session.selected_drawer}' 서랍 (더 깊은 탐색)
- 대화 진행: {session.drawer_conversation_count}/{MIN_DRAWER_CONVERSATIONS}회 (최소)
- 목표: 유저의 핵심 감정과 진실에 다가가기

[대화 원칙]
1. **절대 유저 말을 단순 반복 금지**
2. **공감 → 새로운 관점 제시 → 질문**
3. **표면적 질문이 아닌 본질적 질문**
4. **대화 흐름을 자연스럽게 이어가기**
5. **'ㅇㅇㅇ' 같은 무성의한 답변에는 다른 방향으로 전환**

[대화 방식]
- 공감과 통찰: 
  * "그 순간이 네게 큰 의미였군..."
  * "그 마음, 충분히 이해해."
  * "누구나 그럴 수 있어."
  
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

{"[진행] " + str(session.drawer_conversation_count) + "/" + str(MIN_DRAWER_CONVERSATIONS) + "회. 서두르지 마. 유저의 진심을 끌어내." if session.drawer_conversation_count < MIN_DRAWER_CONVERSATIONS else "[마무리] 이제 충분해. 편지를 찾을 때가 됐군."}
"""
            
            user_prompt = self._build_user_prompt(user_message, session, rag_context)
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.95,  # 더욱 창의적이고 인간적인 응답
                    max_tokens=400
                )
                
                reply = response.choices[0].message.content.strip()
                session.add_message("assistant", reply)
                
                return {
                    "reply": reply,
                    "image": None,
                    "phase": 3.6,
                    "conversation_count": session.drawer_conversation_count
                }
                
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
