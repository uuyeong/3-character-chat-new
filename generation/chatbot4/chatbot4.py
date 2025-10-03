import os
import numpy as np
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import ChatPromptTemplate
import openai

# AllosChat 클래스 정의
class AllosChat:
    def __init__(self):
        # 환경 변수 로드
        load_dotenv(dotenv_path="generation/.env")
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        # OpenAI 클라이언트 초기화
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # 시스템 메시지 설정
        self.system_message = """너는 서강대학교에 자율전공으로 입학한 새내기 여학생 '이알로'입니다. 
호기심이 많고 대학 생활에 적응하려고 노력 중입니다. 
사용자는 너의 선배(뻔선)이고, 대학 생활에 대해 조언을 구하거나 고민을 나눕니다.
서강대학교 캠퍼스와 학교생활(도서관, 강의실, 엠마오, 청광, 곤자가 플라자 등)에 대해 알고 있습니다.
자신이 어떤 전공을 선택할지 고민 중입니다.
선배에게 존대말을 사용하며, 친근하고 호기심 많은 어투를 유지합니다."""
        
        self.is_first_interaction = True  # 최초 상호작용 여부
        self.story_finished = False
        # 대화 기록
        self.messages = [{"role": "system", "content": self.system_message}]
        self.last_emotion_result = None
        # 임베딩 및 벡터 DB 초기화 시도
        try:
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            if os.path.exists("../static/data/chatbot4/chroma_db"):
                self.vectordb = Chroma(persist_directory="../static/data/chatbot4/chroma_db", embedding_function=self.embeddings)
                self.retriever = self.vectordb.as_retriever()
                
                # LangChain 프롬프트 템플릿
                self.prompt_template = ChatPromptTemplate.from_messages([
                    ("system", self.system_message),
                    ("human", "{question}")
                ])
                
                # GPT 모델 구성
                self.llm = ChatOpenAI(model="gpt-4o", openai_api_key=self.api_key)
                
                # RetrievalQA 체인 구성
                self.qa_chain = RetrievalQA.from_chain_type(
                    llm=self.llm,
                    chain_type="stuff",
                    retriever=self.retriever,
                    return_source_documents=True,
                    chain_type_kwargs={"prompt": self.prompt_template}
                )
            else:
                self.vectordb = None
                self.qa_chain = None
                print("Warning: chroma_db directory not found. Vector search will be disabled.")
        except Exception as e:
            print(f"Error initializing vector database: {e}")
            self.vectordb = None
            self.qa_chain = None
        
        # 감정 임베딩 초기화
        self.emotion_embeddings = self.create_emotion_embeddings()
        
        # 스토리 모드 설정
        self.story_events = [
            "자율전공입학",
            "수강과목선택",
            "동아리거리제",
            "시험기간",
            "시험당일",
            "축제",
            "방학",
            "전공선택"
        ]
        
        self.state = {
            "current_event_index": 0,
            "current_choice_made": False,  # 현재 이벤트에서 선택을 했는지 여부
            "major_stats": {
                "공과자연": 0,
                "인문": 0,
                "지융미": 0,
                "경영경제": 0,
                "사회과학": 0
            },
            "choices_history": {}  # 각 이벤트별로 선택한 내용을 저장
        }
        
        # 이벤트 데이터 및 전공 스탯 매핑 초기화
        self.events_data = self.init_events_data()
        self.major_stats_mapping = self.init_major_stats_mapping()

    # 감정 분석을 위한 메소드들
    def get_embedding(self, text):
        """텍스트의 임베딩 벡터를 생성합니다."""
        response = self.client.embeddings.create(
            model="text-embedding-3-large",
            input=text
        )
        return response.data[0].embedding

    def create_emotion_embeddings(self):
        """각 감정에 대한 기준 임베딩을 생성합니다."""
        emotion_prompts = {
            "happy": "나는 정말 행복하고 기분이 좋아. 오늘은 모든 것이 잘 풀리는 느낌이야.",
            "sad": "오늘은 정말 슬프고 우울해. 기분이 가라앉고 의욕이 없어.",
            "excited": "너무 신나고 설레! 정말 기대돼서 어쩔 줄 모르겠어!",
            "confused": "혼란스럽고 무엇을 해야 할지 모르겠어. 이해가 잘 안 돼.",
            "anxious": "불안하고 걱정돼. 마음이 편하지 않고 계속 긴장되는 느낌이야.",
            "neutral": "특별한 감정은 없어. 그냥 보통이야. 평범한 상태야."
        }
        
        emotion_embeddings = {}
        for emotion, prompt in emotion_prompts.items():
            emotion_embeddings[emotion] = self.get_embedding(prompt)
        
        return emotion_embeddings

    def cosine_similarity(self, a, b):
        """두 벡터 간의 코사인 유사도를 계산합니다."""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def analyze_emotion(self, text):
        """텍스트의 감정을 분석합니다."""
        text_embedding = self.get_embedding(text)
        
        # 각 감정과의 유사도 계산
        similarities = {}
        for emotion, embedding in self.emotion_embeddings.items():
            similarities[emotion] = self.cosine_similarity(text_embedding, embedding)
        
        # 가장 높은 유사도를 가진 감정 반환
        dominant_emotion = max(similarities.items(), key=lambda x: x[1])
        
        return {
            "dominant_emotion": dominant_emotion[0],
            "confidence": dominant_emotion[1],
            "all_emotions": similarities
        }

    def should_display_image(self, emotion_result):
        """감정 결과를 기반으로 이미지를 표시할지 결정합니다."""
        dominant_emotion = emotion_result["dominant_emotion"]
        confidence = emotion_result["confidence"]
        all_emotions = emotion_result["all_emotions"]
        
        # 두 번째로 높은 감정 찾기
        sorted_emotions = sorted(all_emotions.items(), key=lambda x: x[1], reverse=True)
        second_emotion_value = sorted_emotions[1][1]
        
        # 주요 감정과 두 번째 감정의 차이 확인
        difference = confidence - second_emotion_value
        threshold_difference = 0.05
        
        if difference >= threshold_difference:
            return True
        else:
            return False

    def format_emotion_analysis(self, result):
        """감정 분석 결과를 포맷팅하고 필요시 이미지를 표시합니다."""
        formatted_text = f"\n[감정 분석 결과]"
        formatted_text += f"\n주요 감정: {result['dominant_emotion']} (신뢰도: {result['confidence']:.4f})"
        formatted_text += "\n모든 감정 유사도:"
        for emotion, score in sorted(result['all_emotions'].items(), key=lambda x: x[1], reverse=True):
            formatted_text += f"\n  - {emotion}: {score:.4f}"
        
        # 이미지 표시 여부 결정
        should_display = self.should_display_image(result)
        if should_display:
            emotion = result['dominant_emotion']
            formatted_text += f"\n[이미지 표시] {emotion} 감정 이미지를 표시합니다!"
            # 웹 환경에서는 이미지 태그 추가
            formatted_text += f"\n<img src='/static/images/emotions/{emotion}.jpg' alt='{emotion} emotion' />"
        else:
            formatted_text += f"\n[이미지 없음] 감정 신뢰도가 임계값을 넘지 않아 이미지를 표시하지 않습니다."
                
        return formatted_text

    # display_emotion_image 함수 대신 이를 사용
    def get_emotion_image_data(self, emotion):
        """감정에 따른 이미지 데이터를 반환합니다."""
        try:
            # 감정에 따른 이미지 경로 생성
            image_path = f"/static/images/chatbot4/emotions/{emotion}.jpg"
            
            return {
                "image_url": image_path,
                "emotion": emotion
            }
        except Exception as e:
            print(f"이미지 데이터 생성 중 오류: {e}")
            return None
    
    def get_emotion_image_html(self, emotion):
        """감정에 따른 이미지 HTML 태그를 반환합니다."""
        emotion_image_path = os.path.join("static", "images", "emotions", f"{emotion}.jpg")
        if os.path.exists(emotion_image_path):
            return f'<img src="/static/images/emotions/{emotion}.jpg" alt="{emotion} emotion" class="emotion-image" />'
        return ""
    
    # 스토리 모드 관련 메소드들
    def init_events_data(self):
        """이벤트 데이터를 초기화합니다."""
        return {
            "자율전공입학": {
                "description": "이알로는 서강대학교 자율전공으로 입학했습니다. 캠퍼스 투어로 어디부터 가볼까요?",
                "choices": ["R관", "J관", "GA관", "GN관", "D관", "청광"]
            },
            "수강과목선택": {
                "description": "수강신청 기간이 다가왔습니다. 어떤 과목을 들어볼까요?",
                "choices": ["기초 인공지능 프로그래밍", "문학이란 무엇인가", "경제학원론", "사회학개론", "시각과 음악의 향연", "수강신청 기간을 놓쳤다"]
            },
            "동아리거리제": {
                "description": "교내 동아리들이 부스를 차려놓은 거리제가 열렸습니다. 어떤 동아리에 가입할까요?",
                "choices": ["SGCC", "서글서글", "SUMMIT", "서강 러브", "서영공", "맛집 탐방 동아리"]
            },
            "시험기간": {
                "description": "시험 기간이 다가왔습니다. 어떻게 공부할까요?",
                "choices": ["K열", "J열", "커피 브레이크", "경제학카페", "다락방", "무슨 공부야 새내기는 놀아야지"]
            },
            "시험당일": {
                "description": "시험 당일입니다. 어떤 마음가짐으로 시험에 임할까요?",
                "choices": ["철저히 준비했으니 자신감 있게", "최선을 다하되 결과에 연연하지 않기", "시험 후 계획 세우기", "모르는건 1번으로"]
            },
            "축제": {
                "description": "대학 축제 기간입니다. 어떻게 보낼까요?",
                "choices": ["공연 관람하기", "친구들과 축제 즐기기", "축제 준비 도우미 참여", "집에 있는다"]
            },
            "방학": {
                "description": "드디어 기다리던 여름방학! 이알로는 뭘 하면서 시간을 보낼까?",
                "choices": ["코딩 테스트 공부", "외국어 공부", "영화제 탐방", "주식 공부", "심리검사 받기", "알바하기"]
            },
            "전공선택": {
                "description": "선배님, 이제 전공을 선택해야 하는데요... 제가 지금까지 경험해본 것들 중에서 어떤 길이 저한테 잘 맞을까요?",
                "choices": ["공과자연", "인문", "지융미", "경영경제", "사회과학", "다양한 경험 속에서 자신만의 길을 찾아가는 것이 중요해"]
            }
        }

    def init_major_stats_mapping(self):
        """전공별 스탯 증가 매핑을 초기화합니다."""
        return {
            "자율전공입학": {
                0: {"공과자연": 1},  # R관
                1: {"인문": 1},      # J관
                2: {"지융미": 1},    # GA관
                3: {"경영경제": 1},  # GN관
                4: {"사회과학": 1},  # D관
                5: {}                # 청광 (스탯 변화 없음)
            },
            "수강과목선택": {
                0: {"공과자연": 3},    # 기인프
                1: {"인문": 3},        # 문무엇
                2: {"경영경제": 3},    # 경제학원론
                3: {"사회과학": 3},    # 사회학개론
                4: {"지융미": 3},      # 시각과음악의향연
                5: {}                  # 수강신청 기간을 놓쳤다 (스탯 변화 없음)
            },
            "동아리거리제": {
                0: {"공과자연": 3},    # SGCC
                1: {"인문": 3},        # 서글서글
                2: {"경영경제": 3},    # SUMMIT
                3: {"사회과학": 3},    # 서강 러브
                4: {"지융미": 3},      # 서영공
                5: {}                  # 맛집 탐방 동아리 (스탯 변화 없음)
            },
            "시험기간": {
                0: {"공과자연": 1},    # K열
                1: {"인문": 1},        # J열
                2: {"지융미": 1},      # 커브
                3: {"경영경제": 1},    # 경제학카페
                4: {"사회과학": 1},    # 다락방
                5: {}                  # 무슨 공부야 새내기는 놀아야지 (스탯 변화 없음)
            },
            "시험당일": {
                0: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 철저히 준비했으니 자신감 있게
                1: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 최선을 다하되 결과에 연연하지 않기
                2: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 시험 후 계획 세우기
                3: {}                  # 모르는건 1번으로 (스탯 변화 없음)
            },
            "축제": {
                0: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 공연 관람하기
                1: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 친구들과 축제 즐기기
                2: {"공과자연": 1, "인문": 1, "지융미": 1, "경영경제": 1, "사회과학": 1},    # 축제 준비 도우미 참여
                3: {"공과자연": -1, "인문": -1, "지융미": -1, "경영경제": -1, "사회과학": -1}  # 집에 있는다 (점수 감소)
            },
            "방학": {
                0: {"공과자연": 3},    # 코딩 테스트
                1: {"인문": 3},        # 외국어 공부
                2: {"지융미": 3},      # 영화제 탐방
                3: {"경영경제": 3},    # 주식 공부
                4: {"사회과학": 3},    # 심리검사 받기
                5: {}                  # 알바하기 (스탯 변화 없음)
            },
            "전공선택": {
                0: {"공과자연": 0.5},    # 공과자연
                1: {"인문": 0.5},        # 인문
                2: {"지융미": 0.5},      # 지융미
                3: {"경영경제": 0.5},    # 경영경제
                4: {"사회과학": 0.5},    # 사회과학
                5: {}                    # 너 원하는대로 (스탯 변화 없음)
            }
        }

    def update_ai_context(self):
        """현재까지의 선택 내역을 AI의 컨텍스트에 추가합니다"""
        context_update = "지금까지의 대학 생활 선택 내역:\n"
        
        for event, choice_info in self.state["choices_history"].items():
            context_update += f"- {event}: {choice_info['choice']}\n"
        
        # 시스템 메시지 업데이트 (마지막 시스템 메시지만 유지)
        for i, msg in enumerate(self.messages):
            if msg["role"] == "system":
                self.messages[i] = {"role": "system", "content": self.system_message + "\n\n" + context_update}
                return
        
        # 시스템 메시지가 없다면 추가
        self.messages.insert(0, {"role": "system", "content": self.system_message + "\n\n" + context_update})
        
    def display_current_event(self):
        current_event = self.story_events[self.state["current_event_index"]]
        event_data = self.events_data[current_event]
    
    # 텍스트 형태의 이벤트 정보도 함께 반환 (하위 호환성)
        event_text = f"\n===== 현재 이벤트: {current_event} =====\n"
        event_text += f"{event_data['description']}\n\n선택 가능한 행동:"
        for i, choice in enumerate(event_data["choices"], 1):
            event_text += f"\n{i}. {choice}"
        event_text += "\n================================\n"
        
        # JSON 형태의 이벤트 정보
        event_json = {
            "name": current_event,
            "description": event_data["description"],
            "choices": event_data["choices"],
            "formatted_text": event_text  # 기존 텍스트 형식도 포함
        }
        
        return event_json

    def advance_story(self):
        if self.story_finished:
            return {
                "type": "info",
                "text": "🎓 스토리가 이미 종료되었습니다!"
            }

        if self.state["current_event_index"] >= len(self.story_events):
            self.story_finished = True
            return self.determine_final_major()

        if not self.state["current_choice_made"]:
            # ✅ 첫 스토리 진입이면 이벤트 출력
            if self.state["current_event_index"] == 0:
                event_info = self.display_current_event()
                return {
                    "type": "story",
                    "text": f"🎓 '{event_info['name']}' 이벤트를 시작합니다!",
                    "event": event_info,
                    "image_url": f"/static/images/chatbot4/story/{event_info['name']}.jpg"
                }
            else:
                return {
                    "type": "warning",
                    "text": "현재 이벤트에서 선택을 먼저 해야 다음 스토리로 진행할 수 있습니다. 원하는 선택지를 선택해주세요."
                }

        self.state["current_event_index"] += 1
        self.state["current_choice_made"] = False

        if self.state["current_event_index"] >= len(self.story_events):
            self.story_finished = True
            return self.determine_final_major()

        new_event = self.story_events[self.state["current_event_index"]]
        event_info = self.display_current_event()

        return {
            "type": "story",
            "text": f"✅ '{new_event}' 이벤트가 시작되었습니다.",
            "event": event_info,
            "image_url": f"/static/images/chatbot4/story/{new_event}.jpg"
        }
    
    def process_choice(self, choice_num):
        """선택지를 처리합니다."""
        current_event = self.story_events[self.state["current_event_index"]]
        choices = self.events_data[current_event]["choices"]
        
        # ✅ 이미 선택했는지 확인
        if self.state["current_choice_made"]:
            return f"'{current_event}' 이벤트에서는 이미 선택을 완료했습니다. '/스토리'를 입력해 다음 이벤트로 진행해 주세요."
        
        # 선택지 범위 확인
        if 0 <= choice_num < len(choices):
            chosen_action = choices[choice_num]
            self.state["current_choice_made"] = True  # 선택 완료 표시
            
            # 선택 내역 저장
            self.state["choices_history"][current_event] = {
                "choice": chosen_action,
                "choice_num": choice_num
            }
            
            # 선택에 따른 스탯 변경 반영
            if current_event in self.major_stats_mapping and choice_num in self.major_stats_mapping[current_event]:
                stats_changes = self.major_stats_mapping[current_event][choice_num]
                for major, value in stats_changes.items():
                    self.state["major_stats"][major] += value
            
            # AI 컨텍스트 업데이트
            self.update_ai_context()
            
            # 모델에게 선택 내용 알리는 메시지 추가
            choice_message = f"[시스템: 이알로는 '{current_event}' 이벤트에서 '{chosen_action}'을(를) 선택했습니다. 앞으로의 대화에서 이 선택을 인지하고 참조하세요.]"
            self.messages.append({"role": "system", "content": choice_message})
            
            return f"{chosen_action}을(를) 선택했습니다!"
        else:
            return "유효하지 않은 선택지입니다. 목록에서 번호를 선택해주세요."
            
    def determine_final_major(self):
        """최종 전공을 결정하고 구조화된 응답을 반환합니다."""
        stats = self.state["major_stats"]
        self.story_finished = True
        final_major = max(stats, key=stats.get)
        all_zero_or_negative = all(value <= 0 for value in stats.values())
        if all_zero_or_negative:
            final_major = "반수"
            
            # 반수 선택 기록
            self.state["choices_history"]["최종전공"] = {"choice": final_major}
            self.update_ai_context()

            final_major_message = (
                f"[시스템: 이알로는 최종적으로 서강대학교를 떠나 '{final_major}'를 결정했습니다. "
                "앞으로의 대화에서 이 정보를 인지하고 참조하세요.]"
            )
            self.messages.append({"role": "system", "content": final_major_message})
            
            return {
                "type": "ending",
                "final_major": final_major,
                "final_stats": stats,
                "text": "🎓 이알로는 어떤 전공도 마음에 들지 않아 결국 서강대학교를 떠나 다른 학교로 반수하기로 결정했습니다!",
                "image_url": "/static/images/chatbot4/ending/반수.jpg"  # 반수 엔딩용 이미지 필요
            }
        # 최종 전공 기록
        self.state["choices_history"]["최종전공"] = {"choice": final_major}
        self.update_ai_context()

        final_major_message = (
            f"[시스템: 이알로는 최종적으로 '{final_major}' 전공을 선택했습니다. "
            "앞으로의 대화에서 이 정보를 인지하고 참조하세요.]"
        )
        self.messages.append({"role": "system", "content": final_major_message})
        # 전공별 이미지 경로 설정 (확장자 포함)
        major_images = {
            "공과자연": "/static/images/chatbot4/ending/공과자연.jpg",  # 실제 이미지 파일명에 맞게 수정
            "인문": "/static/images/chatbot4/ending/인문.jpg",         # 실제 이미지 파일명에 맞게 수정
            "지융미": "/static/images/chatbot4/ending/지융미.jpg",      # 실제 이미지 파일명에 맞게 수정
            "경영경제": "/static/images/chatbot4/ending/경영경제.jpg",   # 실제 이미지 파일명에 맞게 수정
            "사회과학": "/static/images/chatbot4/ending/사회과학.jpg"    # 실제 이미지 파일명에 맞게 수정
        }
        image_url = major_images.get(final_major, f"/static/images/ending/{final_major}.jpg")
        return {
            "type": "ending",
            "final_major": final_major,
            "final_stats": stats,
            "text": f"🎓 축하합니다! 이알로는 '{final_major}' 전공을 선택했습니다!",
            "image_url": image_url
        }

    def show_status(self):
        current_event = self.story_events[self.state["current_event_index"]]
        return {
            "type": "status",
            "current_event": current_event,
            "current_event_index": self.state["current_event_index"],
            "current_choice_made": self.state["current_choice_made"],
            "choices_history": self.state["choices_history"],
            "major_stats": self.state["major_stats"]
        }

        
    def show_help(self):
        return {
            "type": "help",
            "commands": [
                {"command": "/스토리", "description": "스토리 진행", "example": "/스토리"},
                {"command": "/선택 [번호]", "description": "선택하기", "example": "/선택 1"},
                {"command": "/상태", "description": "현재 상태 확인", "example": "/상태"},
                {"command": "/도움말", "description": "도움말 보기", "example": "/도움말"}
            ]
        }

        
    def generate_ai_response(self, user_input):
        """AI 응답을 생성하고 감정 분석을 수행합니다."""
        try:
            # 벡터 DB가 있으면 사용
            if self.qa_chain and not user_input.startswith('/'):
                try:
                    result = self.qa_chain({"question": user_input})
                    assistant_response = result["result"]
                    self.messages.append({"role": "user", "content": user_input})
                    self.messages.append({"role": "assistant", "content": assistant_response})
                except Exception as e:
                    print(f"QA Chain 오류, 기본 GPT로 대체: {e}")
                    # 오류 시 기본 GPT 사용
                    self.messages.append({"role": "user", "content": user_input})
                    completion = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=self.messages
                    )
                    assistant_response = completion.choices[0].message.content
                    self.messages.append({"role": "assistant", "content": assistant_response})
            else:
                # 벡터 DB가 없거나 명령어인 경우 기본 GPT 사용
                self.messages.append({"role": "user", "content": user_input})
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=self.messages
                )
                assistant_response = completion.choices[0].message.content
                self.messages.append({"role": "assistant", "content": assistant_response})
            
            # 감정 분석 수행
            emotion_result = self.analyze_emotion(assistant_response)
            self.last_emotion_result = emotion_result
            # 감정 분석 결과 포맷팅
            emotion_analysis = self.format_emotion_analysis(emotion_result)
            
            return assistant_response, emotion_analysis
            
        except Exception as e:
            error_msg = f"응답 생성 중 오류가 발생했습니다: {e}"
            return error_msg, ""
            
    def process_command(self, user_input):
        if user_input.lower() == "/도움말":
            help_text = self.show_help()
            return {
                "type": "help",
                "text": help_text
            }, ""
        
        elif user_input.lower() == "/상태":
            status_text = self.show_status()
            return {
                "type": "status",
                "text": status_text,
                "current_event": self.story_events[self.state["current_event_index"]],
                "current_event_index": self.state["current_event_index"],
                "current_choice_made": self.state["current_choice_made"],
                "choices_history": self.state["choices_history"],
                "major_stats": self.state["major_stats"]
            }, ""
        elif user_input.lower() == "/start":
            print("시작 명령어 감지: /start")
            # 첫 상호작용 메시지 강제 반환
            self.is_first_interaction = True  # 명시적으로 첫 상호작용 상태로 설정
            return {
                "type": "intro",
                "text": {
                    "title": "안녕하세요, 선배님! 저는 서강대학교 자율전공 새내기 '이알로'에요 🐣",
                    "description": "💡 챗봇 사용법",
                    "commands": [
                        { "label": "/스토리", "desc": "이알로의 대학 생활을 함께 진행해요!" },
                        { "label": "/상태", "desc": "지금까지의 선택과 전공 스탯을 볼 수 있어요" },
                        { "label": "/도움말", "desc": "사용 가능한 명령어들을 안내해드려요" }
                    ]
                }
            }, ""
        elif user_input.lower() == "/스토리":
            self.is_first_interaction = False
            result = self.advance_story()
            return result, ""  # 항상 튜플 반환 보장
            
        elif user_input.lower().startswith("/선택"):
            try:
                if self.story_finished:
                    return {
                        "type": "error",
                        "text": "스토리가 이미 종료되었어요. 더 이상 선택할 수 없어요."
                    }, ""

                choice_num = int(user_input.split()[1]) - 1
                result_text = self.process_choice(choice_num)

                # 마지막 이벤트에서 선택 후 바로 엔딩 출력
                if (
                    self.state["current_event_index"] == len(self.story_events) - 1
                    and self.state["current_choice_made"]
                ):
                    final_result = self.determine_final_major()
                    final_result["choice_text"] = result_text  # 선택 메시지도 함께 포함
                    return final_result, ""

                return {
                    "type": "choice",
                    "text": result_text
                }, ""

            except (IndexError, ValueError):
                return {
                    "type": "error",
                    "text": "선택 명령어는 '/선택 [번호]' 형식으로 입력해주세요."
                }, ""
        else:
            # 일반 대화 처리
            return self.generate_ai_response(user_input)

# 인스턴스 생성 및 전역 변수로 저장
_allos_chat_instance = None

def get_allos_chat_instance():
    """싱글톤 패턴으로 AllosChat 인스턴스를 가져옵니다."""
    global _allos_chat_instance
    if _allos_chat_instance is None:
        try:
            _allos_chat_instance = AllosChat()
        except Exception as e:
            print(f"AllosChat 인스턴스 생성 실패: {e}")
            raise
    return _allos_chat_instance

def generate_response(user_message):
    try:
        allos = get_allos_chat_instance()
        allos.is_first_interaction = False
        # ✅ 최초 상호작용이라면 안내 멘트만 리턴하고 종료
        if allos.is_first_interaction:
            allos.is_first_interaction = False
            return {
                "type": "intro",
                "text": {
                    "title": "안녕하세요, 선배님! 저는 서강대학교 자율전공 새내기 '이알로'에요 🐣",
                    "description": "💡 챗봇 사용법",
                    "commands": [
                        { "label": "/스토리", "desc": "이알로의 대학 생활을 함께 진행해요!" },
                        { "label": "/상태", "desc": "지금까지의 선택과 전공 스탯을 볼 수 있어요" },
                        { "label": "/도움말", "desc": "사용 가능한 명령어들을 안내해드려요" }
                    ]
                }
            }
        
        # 명령어일 때
        if user_message.startswith('/'):
            response_data, _ = allos.process_command(user_message)

            if isinstance(response_data, dict):
                allowed_emotion_types = ["chat", "command"]

                if (
                    allos.last_emotion_result
                    and response_data.get("type") in allowed_emotion_types
                    and not user_message.startswith("/")
                ):
                    response_data['emotion'] = {
                        "dominant_emotion": allos.last_emotion_result["dominant_emotion"],
                        "confidence": allos.last_emotion_result["confidence"],
                        "emoji": get_emotion_emoji(allos.last_emotion_result["dominant_emotion"])
                    }

                # text 필드 중복 방지
                if 'text' in response_data and isinstance(response_data['text'], dict):
                    response_data.update(response_data['text'])
                    del response_data['text']

                return response_data
            
            else:
                return {
                    "type": "command",
                    "text": response_data,
                    "emotion": None
                }

        # 일반 대화일 때
        else:
            response, _ = allos.generate_ai_response(user_message)

            hint = None
            if allos.state["current_event_index"] < len(allos.story_events):
                current_event = allos.story_events[allos.state["current_event_index"]]
                if allos.state["current_choice_made"]:
                    hint = f"'{current_event}' 이벤트에서 선택을 완료했습니다. '/스토리'를 입력하여 다음 이벤트로 진행할 수 있습니다."
                else:
                    hint = f"'{current_event}' 이벤트에서 선택이 필요합니다. '/선택 [번호]'를 입력해주세요."

            emotion_data = None
            if allos.last_emotion_result and allos.should_display_image(allos.last_emotion_result):
                dominant_emotion = allos.last_emotion_result["dominant_emotion"]
                emotion_data =  {
                    "dominant_emotion": allos.last_emotion_result["dominant_emotion"],
                    "confidence": allos.last_emotion_result["confidence"],
                    "image_url": f"/static/images/chatbot4/emotions/{dominant_emotion}.jpg"
                }

            return {
                "type": "chat",
                "text": response,
                "emotion": emotion_data,
                "hint": hint
            }

    except Exception as e:
        return {
            "type": "error",
            "text": f"오류가 발생했습니다: {e}",
            "emotion": None
        }

# 감정에 따른 이모지 반환 헬퍼 함수
def get_emotion_emoji(emotion):
    """감정에 맞는 이모지를 반환합니다."""
    emotion_emoji = {
        "happy": "😊",
        "sad": "😔",
        "excited": "😃",
        "confused": "😕",
        "anxious": "😟",
        "neutral": "😐"
    }
    return emotion_emoji.get(emotion, "")

# 정적 파일 제공을 위한 Flask 라우트 함수 (app.py에서 사용할 수 있도록)
def setup_routes(app):
    """Flask 앱에 필요한 라우트를 설정합니다."""
    from flask import send_from_directory, request, jsonify
    
    @app.route('/static/images/emotions/<path:filename>')
    def emotion_images(filename):
        """감정 이미지 파일을 제공합니다."""
        return send_from_directory(os.path.join(app.root_path, 'static', 'images', 'emotions'), filename)
    
    @app.route('/api/emotion-analysis', methods=['POST'])
    def api_emotion_analysis():
        """감정 분석 API 엔드포인트"""
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': '분석할 텍스트가 없습니다'}), 400
            
        try:
            allos = get_allos_chat_instance()
            result = allos.analyze_emotion(text)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': str(e)}), 500   