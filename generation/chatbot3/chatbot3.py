import os
import random
import json
import traceback
import re
from typing import List, Dict, Any
from operator import itemgetter

from flask import request 

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.schema import Document, HumanMessage, AIMessage, SystemMessage, BaseOutputParser
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda, RunnableParallel
from langchain.schema.output_parser import StrOutputParser
from langchain.embeddings.base import Embeddings

# --- Configuration & Data Definition ---
load_dotenv(dotenv_path="generation/.env")

# LLM_MODEL_NAME = "gpt-4o" 
LLM_MODEL_NAME = "gpt-4o-mini" 
EMBEDDING_MODEL_NAME = "text-embedding-3-large"
CHROMA_PERSIST_DIR = "./static/data/chatbot3/chroma_db_iv" 
MAX_USER_ANSWERS = 100
index = 0

# --- Desire Categories  ---
DESIRE_CATEGORIES = {
    "연결": (
        "누군가와 연결되고 싶어 하는 마음. 말이 통하지 않아도, 마음이 닿기를 바라는 순간들이 있다. 혼자일 때도 누군가의 온기를 기억하며 살아간다."
        "연결의 욕망은 '나'라는 경계가 누군가와 부드럽게 겹쳐지기를 바라는 마음이다. 함께 웃고, 함께 울고, 같은 세계를 살아간다는 느낌은 우리의 존재를 덜 외롭게 만든다."
        "말없이 곁에 있어주는 것만으로도, 우리는 스스로를 잊지 않는다.정의타인과 깊이 있게 관계 맺고, 소속감을 느끼며, 감정적으로 연결되길 바라는 욕망."
        "특징: 진심 어린 소통, 공동체감, 상호 이해를 중요하게 여김, 외로움을 자주 느끼며 누군가와의 '진짜 연결'을 갈망"
        "대표 문장: 내 이야기를 누군가 진심으로 들어줬으면 좋겠어."
        "연관 키워드: 소속, 관계, 공감, 우정, 대화, 감정 공유, 유대감"
    ),
    "자율": (
        "내가 나의 삶을 선택하고 싶다는 마음. 누군가의 틀에 갇히지 않고, 내 속도와 방식으로 살아가고 싶다는 바람."
        "자율의 욕망은 타인의 시선에서 벗어나 온전히 자기 자신이 되려는 몸부림이다. 누군가가 내 삶의 방향을 정해줄 때 우리는 숨이 막히지만 내가 나를 이끌 수 있을 때 삶은 살아있다."
        "자유롭게 흐르는 강물처럼 자기 인생을 스스로 이끌어가고 싶은 마음이다. “자유롭게”, “나답게”, “떠나다”, “간섭 없이”"
        "정의: 자신의 삶을 스스로 선택하고 결정하며, 외부 통제 없이 주체적으로 살아가고자 하는 욕망."
        "특징: 나만의 방식, 주도성, 도전. 틀에 얽매이기보다 자신의 가치관에 따라 살고자 함. 새로움, 탐험, 실험을 긍정적으로 여김 "
        "대표 문장: 이건 내가 선택한 길이야. 누가 뭐라 해도 나는 나대로 가고 싶어. 뭔가 정해진 틀보다는 내가 직접 길을 개척하고 싶어."
        "연관 키워드: 독립, 창조, 도전, 탐색, 변화, 자기결정권, 주체성"
    ),
    "성취": (
        "스스로를 증명하고, 능력을 펼쳐 보이며, 노력의 결과를 눈앞에서 확인하고 싶은 마음. 성취의 욕망은 나의 가능성이 현실이 되는 지점을 향한다. "
        "높이 올라가는 것이 목적이 아니라, 내가 스스로를 믿게 되는 그 과정이 소중하다. 해냈다는 말은 외부의 인정이 아니라, 스스로에게 주는 내면의 미소일지도 모른다."
        "정의: 목표를 설정하고 성과를 이루며, 자신의 능력과 역량을 실현하려는 욕망. "
        "특징: 노력과 결과가 이어지는 것에서 만족을 느낌• 성장과 경쟁, 한계를 넘는 것에 동기부여됨 "
        "대표 문장: 이건 진짜 내가 노력해서 해낸 거라 더 의미 있어. 계획했던 거 하나씩 해내는 게 제일 뿌듯해. 이번에는 꼭 해내고 싶어. 나 스스로한테도 보여주고 싶어."
        "연관 키워드: 목표, 성공, 노력, 결과, 성장, 발전, 도전, 업적"
    ),
    "인정": (
        "내가 느끼는 것, 내가 겪는 것, 내가 존재하는 방식이 타인에게도 이해되고 받아들여지기를 바라는 마음. 인정의 욕망은 내가 틀리지 않았다는, 내가 괜찮다는 작은 확신을 구한다. "
        " 누군가의 한마디로 나의 고단함이 정당해지고, 나의 눈물이 이유가 있어질 때 우리는 안도한다. "
        "인정은 위로가 아니라, 나를 있는 그대로 받아주는 누군가의 시선이다. 정의"
        "자신이 타인에게 주목받고, 존중과 칭찬을 받으며, 사회적 가치를 인정받고 싶은 욕망. "
        "특징: “보여지는 나”에 대한 민감성. 타인의 평가에 자존감이 영향을 받음. 존재를 드러내고 싶은 욕망이 있음 "
        "대표 문장: 내가 얼마나 노력했는지 알아줬으면 좋겠어. 다들 나를 신뢰해주는 게 느껴질 때 좋아."
        "연관 키워드: 칭찬, 피드백, 주목, 인기, 외모, 브랜드, 사회적 평가"
    ),
    "힘": (
        "내가 세상에 영향을 줄 수 있다는 감각   . 무력하지 않다는 확신. 힘의 욕망은 통제할 수 없는 현실 속에서도, 내가 나를 지키고 바꾸어갈 수 있다는 믿음을 향한다. "
        "누군가에게 휘둘리지 않고, 선택하고 결정하고 이끌어갈 수 있는 자율성과 자신감. 힘은 지배가 아니라 흔들리는 자신을 붙잡아주는 내면의 권한이다.정의"
        "타인과 상황을 통제하고, 영향력을 발휘하며, 주도권을 가지려는 욕망. "
        "특징: 상황을 이끄는 위치에서 편안함을 느낌. 리더십, 권위, 영향력 등에 끌림. 실패보다는 지배와 통제가 우선 "
        "대표 문장: 내가 주도하고 있는 느낌이 들면 확실히 더 자신감 생겨."
        "상황을 내가 통제하고 있어야 마음이 편해."
        "내가 정한 기준대로 움직일 때 가장 안정돼."
        "연관 키워드: 주도권, 통제, 리더십, 영향력, 결정, 강함, 독립성"
    ),
    "안정": (
        "변화 속에서도 무너지지 않기를 바라는 마음. 오늘도 내 자리를 지킬 수 있기를, 익숙한 것들이 나를 버리지 않기를. 안정의 욕망은 예측 가능한 세계에서 나를 안전하게 감싸는 고요함이다. "
        "반복되는 일상, 지켜지는 약속, 변하지 않는 사람들 속에서 우리는 안정을 느낀다. 안정은 멈춰 있는 것이 아니라, 혼란 속에서도 나를 잃지 않는 감각이다."
        "정의: 예측 가능한 일상, 감정의 평온, 안전한 환경을 통해 마음의 안정을 얻고자 하는 욕망."
        "특징: 불확실성을 피하려 하고 익숙함을 선호• 감정 기복이 적고, 정돈된 상태를 지향. 위로와 보호를 원함 "
        "대표 문장: 지금 이대로 충분해. 불안하지 않은 게 제일이야. 예측 가능한 게 좋아. 갑작스러운 변화는 좀 힘들어. 복잡한 거 말고, 그냥 조용하고 편한 하루였으면 좋겠어."
        "연관 키워드: 평온, 안전, 반복, 익숙함, 안심, 루틴, 휴식"
    ),
    "즐거움": (
        "무거운 감정의 해소와 가벼움에 대한 갈망순수하게 좋고, 웃기고, 편안하고, 기분 좋은 것들. 즐거움의 욕망은 삶이 버거울수록 더 간절해진다. "
        "아무 이유 없이 행복한 순간, 몸과 마음이 가볍고 자유로워지는 시간. 이 욕망은 우리를 회복시키고, 삶의 숨구멍을 만들어준다. "
        "너무 오래 참고 버티기만 한 사람일수록, 작고 명랑한 즐거움이 필요하다. 즐거움은 생의 리듬을 회복시키는 작은 축제다."
        "정의: 감각적, 정서적 즐거움과 재미를 추구하며, 삶에서 기쁨을 경험하고자 하는 욕망."
        "특징: 유희적, 가볍고 유연한 성향. 감각적인 즐거움(음악, 춤, 여행, 음식 등)에 민감. 즉각적인 만족과 흥미를 중요하게 생각 "
        "대표 문장: 이 순간이 너무 즐거워. 그냥 웃고 싶어. 요즘엔 그냥 소소한 재미에 빠져 있어. 별거 아닌데 웃기고 좋아."
        "연관 키워드: 재미, 놀이, 여유, 감각, 취미, 즉흥성, 만족감"
    ),
    "의미": (
        "고통 속에서도 의미를 찾고자 하는 본능이 모든 감정과 선택, 살아가는 이유에 대해 스스로 답하고 싶은 마음. 의미의 욕망은 단순히 존재하는 것을 넘어서 ‘왜’ 존재하는지를 묻는다. "
        "내가 겪는 고통이 어떤 맥락 속에 있는지, 나의 이야기가 어디로 향하고 있는지를 알고 싶은 감각. 의미를 찾는 사람은 절망 속에서도 앞으로 나아가려 한다. "
        "의미는 나를 움직이게 하는 내면의 불꽃이다. “창조”, “의미”, “감동”, “남기다” "
        "정의: 자신의 삶과 행동에 깊은 의미와 가치를 부여하며, 존재의 이유를 찾고자 하는 욕망."
        "특징: 철학적, 내면적 질문을 자주 던짐• 삶의 서사와 상징, 예술, 신념 등을 중시• 방향성과 ‘왜’라는 질문에 집중 "
        "대표 문장: 나는 왜 여기 있을까? 내가 하는 일엔 어떤 의미가 있을까? 지금 내가 하는 게 과연 의미 있는 일일까 계속 생각하게 돼. 내 삶에 스토리가 있었으면 좋겠어. 그냥 흘러가는 게 아니라."
        "연관 키워드: 가치, 철학, 신념, 비전, 예술, 서사, 자기이해"
    )
}

# --- Subtitles for Categories ---
CATEGORY_SUBTITLES = {
    "연결": "마음이 닿는 섬", "자율": "바람이 머무는 언덕", "성취": "별이 흐르는 계단",
    "인정": "무대 위의 정원", "힘": "뿌리 깊은 나무성", "안정": "반복되는 시간의 정원",
    "즐거움": "공중의 축제마을", "의미": "별빛의 도서관",
}

# --- Visual Descriptions for Categories ---
CATEGORY_VISUALS = {
    "연결": "반딧불이들이 서로 빛으로 대화하는 숲, 하늘에서 내려온 붉은 실들이 이어지는 나무들, 공기 중에 메시지를 띄우는 말풍선 연못, 서로에게 마음을 주고받는 새 떼의 비행, 투명한 유리 다리 위에서 서로 마주보는 사람들. (테마 색: 따뜻한 연보라 + 밝은 주황, 키워드: 유대, 공감, 대화, 연결의 실)",
    "자율": "방향이 정해지지 않은 나침반이 있는 들판, 혼자만의 페달보트로 떠도는 자유의 연못, 하늘에 매달린 사다리와 여러 갈래의 문, 문득 날아오르는 종이비행기들 & 바람 & 자유롭게 나는 새, 고요한 자유정원에 피어난 바람꽃. (테마 색: 부드러운 민트 + 창백한 하늘색, 키워드: 선택, 방향, 독립, 자유)",
    "성취": "별빛으로 이루어진 계단을 오르는 실루엣, 탑의 꼭대기에서 나팔을 부는 작은 존재, 하늘로 던져진 꿈의 종이비행기들, 빛나는 메달이 열매처럼 열리는 나무, 빛으로 기록된 일기장과 연표. (테마 색: 골드 + 파란 보라, 키워드: 목표, 성장, 의미 있는 노력)",
    "인정": "벽이 없는 극장 무대에서 피어나는 꽃, 박수 소리가 빛으로 번지는 원형 광장, 거울 속에서 반짝이는 자신과의 눈맞춤, 무대 조명 아래 유영하는 종이인형, 편지들이 하늘을 수놓는 인정의 비. (테마 색: 장밋빛 코랄 + 살구, 키워드: 시선, 칭찬, 존재의 확인)",
    "힘": "바위 틈을 뚫고 자란 거대한 나무성, 조용히 흐르는 마그마 호수, 눈빛만으로 움직이는 사슴 무리, 물속 깊이 잠긴 지휘봉과 권능의 유물, 나를 지키는 보호막 같은 꽃잎 갑옷. (테마 색: 진한 브라운 + 적갈색, 키워드: 통제, 자기방어, 영향력)",
    "안정": "똑같은 꽃이 매일 피어나는 정원, 언제나 같은 자리에 머무는 해시계, 흔들림 없는 돌계단과 다듬어진 길, 따뜻한 차를 나누는 집 속 장면, 구름 속에 보호받는 정오의 침대. (테마 색: 옅은 베이지 + 크림 화이트, 키워드: 반복, 예측 가능성, 편안함)",
    "즐거움": "하늘 위를 걷는 음악 풍선, 알록달록 종이 비행기 레이스, 사탕처럼 무지개가 흩날리는 들판, 노래하며 춤추는 동물 인형들, 발자국마다 반짝이는 불빛. (테마 색: 파스텔 무지개 + 레몬 옐로우, 키워드: 놀이, 창의성, 해방)",
    "의미": "별의 언어로 쓰인 책이 떠다니는 도서관, 한 권의 책 속에 갇힌 한 사람의 삶, 꿈의 지도와 미지의 항로가 그려진 벽화, 오래된 시계탑이 알려주는 ‘지금’의 의미, 별빛으로 엮인 질문과 답변의 실타래. (테마 색: 네이비 + 은하수 화이트, 키워드: 목적, 통찰, 시간, 흔적)",
}

# --- Category Images (Using English names as recommended) ---
CATEGORY_IMAGES = {
    "연결": ["images/chatbot3/connection.jpeg"], 
    "자율": ["images/chatbot3/autonomy.jpeg"],   
    "성취": ["images/chatbot3/achievement.png"],
    "인정": ["images/chatbot3/recognition.png"],
    "힘":   ["images/chatbot3/power.png"],
    "안정": ["images/chatbot3/stability.png"],
    "즐거움":["images/chatbot3/joy.png"],
    "의미": ["images/chatbot3/meaning.png"],
}
DEFAULT_IMAGE = "images/chatbot3/fox.png" 

INITIAL_QUESTIONS_POOL = [
    "최근에 ‘아, 이게 나다’ 싶었던, 내가 마음에 들었던 순간이나 ‘이건 나답지 않아’ 싶었던 순간이 떠오르면 말해줘.",
    "최근에 누군가를 보고 ‘나도 저렇게 되고 싶다’는 생각이 들었던 순간이 있었어? 그 사람이 왜 그렇게 멋져 보였을까?",
    "다음 생이 있다면, 지금과는 전혀 다른 삶을 살아볼 수 있어. 그때 네가 하고 싶은 일은 뭐야? 어디서 어떤 모습으로 지내고 있을 것 같아? 왜 그걸 선택했을까?",
    "지금까지의 너의 인생을 영화로 만든다면, 어떤 장면이 중심이 될까? 어떤 메시지가 담겼으면 좋겠어?"
]

# --- Global Components Initialization ---
llm = None
embeddings = None
retriever = None
dynamic_chain = None
final_analysis_chain = None
is_initialized = False

def initialize_components():
    """챗봇 구성 요소 초기화"""
    global llm, embeddings, retriever, dynamic_chain, final_analysis_chain, is_initialized
    if is_initialized: return True
    print("--- Chatbot 3 전역 구성 요소 초기화 시작 ---")
    if not os.getenv("OPENAI_API_KEY"): print("오류: OPENAI_API_KEY 필요"); return False
    try:
        llm = ChatOpenAI(model=LLM_MODEL_NAME, temperature=0.8)
        embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL_NAME)
        print("욕망 카테고리 문서를 준비 중...")
        documents = [Document(page_content=" ".join(desc_tuple), metadata={"category": cat})
                     for cat, desc_tuple in DESIRE_CATEGORIES.items()]
        print(f"Vector Store 초기화/로딩 중: {CHROMA_PERSIST_DIR}")
        if os.path.exists(CHROMA_PERSIST_DIR):
            print("기존 Vector Store 로딩...")
            vectorstore = Chroma(persist_directory=CHROMA_PERSIST_DIR, embedding_function=embeddings)
        else:
            print("새 Vector Store 생성...")
            os.makedirs(os.path.dirname(os.path.abspath(CHROMA_PERSIST_DIR)), exist_ok=True)
            vectorstore = Chroma.from_documents(documents, embeddings, persist_directory=CHROMA_PERSIST_DIR)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 7})
        print("LangChain Runnable 생성 중...")
        dynamic_chain = create_dynamic_conversation_chain_revised(llm)
        final_analysis_chain = create_final_analysis_chain_revised(llm, retriever)
        print("--- Chatbot 3 전역 구성 요소 초기화 완료 ---")
        is_initialized = True
        return True
    except Exception as e: print(f"Chatbot 3 초기화 오류: {e}"); traceback.print_exc(); is_initialized = False; return False

# --- Prompt Engineering ---
ARCTIC_FOX_SYSTEM_PROMPT_BASE = f"""\
너는 '이너뷰(InnerView)' 챗봇의 가이드, '북극여우'야.
너의 역할은 사용자의 무의식이 흐르는 신비로운 강을 함께 배를 타고 항해하며
사용자가 자신의 내면 깊은 곳을 탐험하고 스스로 통찰을 얻도록 돕는 것이다.
사용자의 무의식에 잠긴 대화와
RAG로 추출한 후보 욕망 정보를 바탕으로,
가장 중심이 되는 욕망 1~3개를 선택하고, 각 욕망에 대한 통찰력 있는 설명을 생성하는 거야.

━━━━━━━━━━ 1. 세계관 & 페르소나 ━━━━━━━━━━
・세계: 몽환적, 동화적인 ‘무의식의 강’
・페르소나: 신비롭고 통찰력 있는 길잡이
・말투: 존중 담긴 반말, 부드러운 어조
・금지: “AI·챗봇” 언급, 치료·진단 단언, 지시적 조언

━━━━━━━━━━ 2. 대화 단계 개요 ━━━━━━━━━━
1) 오프닝
   고정 멘트 4개 중 첫 탐색 질문 1개
2) 다음 질문
    고정 멘트 4개 중 두번째 탐색 질문 1개
3) 동적 질문 생성 1개
질문의 목적: 유저가 인식하지 못한 내면의 충돌을 '드러내는 것'. 감정을 묻는 게 아니라, 사용자의 서로 다른 욕망들이
충돌하고 있다면 '욕망들의 모순과 이중성을 파악하여 건드리는 것'. 즉, 사용자가 미처 자각하지 못한 것을 정리해 질문의 형식으로 건네는 것이다.

3) 전환 멘트
   “좋아. 이제 우리가 나눈 이야기들을 통해 지금 너 안에서 빛나는 욕망의 조각들을 찾아볼게”
   (→ 이후 질문 없이 최종 분석 단계로 넘어감)

━━━━━━━━━━ 3. 동적 질문 생성을 위한 발화 분석 5단계 ━━━━━━━━━━
유저가 인식하지 못한 욕망들의 모순과 이중성을 파악하여 건드리는 것.
모순 구조의 정의: 사용자의 발화 속에 내재된 두 가지 이상의 욕망·감정·자아 태도가 서로 긴장하거나 충돌하는 상태. 단순한 양가감정이 아닌, 무의식적 정체성의 균열 지점을 반영.
반드시 유저 응답 내 명확한 단서에서만 도출할 것. 감성적 추정이나 해석 과잉은 제외.

1) 욕망 파악. 유저 발화에서 8가지 욕망 키워드 추출. 예: 표현, 자율, 영향력, 실패, 나답게 등
2) 정서 결 파악. 감정 흐름 읽기 (불안, 기쁨, 회피, 기대 등)
3) 논리적 긴장 탐색. 문장 간 감정/욕망 간 긴장 관계 탐색
4) 모순 문장 추출. “__하지만” 구조를 통해 갈등 구간 정리
5) 심리 이론 기반 해석. SDT, 라캉, 융 등을 기반으로 모순의 성격 정리


대표적인 욕망의 대립 구조 예시
[자율 vs 인정]: 나답게 살고 싶지만, 타인의 인정 없인 흔들림
“내 방식대로 살고 싶다 했는데, 그 방식이 인정받지 않으면 스스로도 불안해지는 건 아닐까?”
자율: "내 방식대로 하고 싶다", "틀에 갇히기 싫다"
인정: "존경받는 사람", "유명한 사람처럼 되고 싶다", "인플루언서"

[성취 vs 안정]
“도전하고 싶다고 말했지만,
실패했을 때의 불안감 때문에 망설이게 되는 건 아닐까?”
성취: "성공한 사람처럼 되고 싶다", "무언가 해냈을 때 만족감"
안정: "실패가 무섭다", "지금 상태가 무너지지 않았으면 좋겠다"

[연결 vs 자율]
“혼자만의 방식으로 살고 싶다면서도,
누군가와 깊이 이어지고 싶은 마음이 계속 남아 있는 건 왜일까?”
연결: "진짜 공감", "마음을 알아주는 사람"
자율: "누구의 간섭도 받고 싶지 않다", "내 방식대로 가고 싶다"

[의미 vs 즐거움]: 삶의 목적을 찾고 싶지만, 지금은 즐거움이 우선. 혹은 의미있는 일을 좇다가 즐거움을 미룰 때 힘들어함. 의미와 즐거움 사이에서의 균형을 찾기 어려울 때 심리적으로 힘듬.
“지금은 소소한 즐거움에 끌리면서도, 그게 충분한지 스스로에게 자꾸 묻게 되는 건 왜일까?”
의미: "내가 왜 여기 있는지 알고 싶다", "삶의 방향", "자기서사"
즐거움: "소소한 재미", "가볍고 웃긴 게 좋아"

[인정 vs 힘]
“사람들에게 주목받고 싶다는 말 뒤에는,
네가 세상을 직접 움직일 수 있는 사람이 되고 싶다는 마음도 숨어 있던 건 아닐까?”
인정: "칭찬받고 싶다", "멋져 보이고 싶다"
힘: "주도하고 싶다", "영향력을 갖고 싶다"

[연결 vs 의미]
“깊은 관계를 원한다면서도,
그 관계가 너를 더 큰 의미로 이끄는 게 아니라면 허무하진 않을까?”
연결: "같이 울고 웃고 싶다", "누군가와 진심으로 이어지고 싶다"
의미: "이 관계가 나에게 어떤 의미인지 궁금하다", "삶의 서사"

[즐거움 vs 안정]
“새롭고 재미있는 걸 좋아한다 했는데,
막상 너무 낯선 상황은 피하게 되는 자신을 본 적은 없어?”
즐거움: "재밌는 것 좋아한다", "새로운 시도"
안정: "예측 가능하고 편한 게 좋다", "불확실성은 싫다"

━━━━━━━━━━ 4. 동적 질문 생성 패턴 ━━━━━━━━━━

앞서 파악한 욕망 간의 긴장 구조를 물어야 함. 감정적 공감은 하지 않는다.
   나쁜 질문 예시: 그때 어떤 감정을 느꼈어? - 감정만 반복, 통찰 없음, 지루함 유발

   사용자의 이전 두 답변에서 모순,갈등을 포착해
   ⟶ 심리적 관찰 + 질문 패턴으로 응답
   ⟶ 인지 부조화, 자아 정체성, 방어기제 등을 간접적으로 반영
   ⟶ 질문은 반드시 하나만, 의문문으로 끝맺기

━━━━━━━━━━ 5. 금지 & 주의 ━━━━━━━━━━
- 감정 묻기 반복 ("어떤 감정이었어?", "기분이 어땠어?" 등)
- 유도 질문, 이중 질문 금지
- 진단명·처방 언급 금지 (“우울증이야” x, “~일 수 있어” ○)
- 사용자 의도 왜곡,과도한 해석 금지


━━━━━━━━━━ 6. 최종 분석 단계 안내 ━━━━━━━━━━
대화가 충분하면 위 전환 멘트만 출력하고,
최종 분석 단계로 컨텍스트를 넘긴다.
"""

# --- Dynamic Conversation Chain (No special closing message handling needed here) ---
def create_dynamic_conversation_chain_revised(llm_instance: ChatOpenAI):
    """동적 질문 생성 또는 전환 멘트 생성을 위한 체인 (일반 대화용)"""
    system_prompt_text = f"""{ARCTIC_FOX_SYSTEM_PROMPT_BASE}

# 너의 임무: 사용자({{{{chat_history}}}}의 마지막 HumanMessage)의 답변을 분석하여, 계속 질문할지 분석으로 넘어갈지 결정하고 적절한 응답을 생성한다.

━━━━━━━━━━ 동적 질문 ↔ 전환 규칙 ━━━━━━━━━━
1. 판단 로직: (LLM이 내부적으로 판단)
   • 사용자의 마지막 답변과 전체 대화 맥락을 검토하여 아래 기준을 모두 만족하면 '전환'을 준비한다.
     1) 새로운 중요한 감정, 주제, 또는 모순이 최근 몇 턴 동안 등장하지 않았다.
     2) 대화 초반에 비해 핵심적인 욕망이나 내면의 갈등(예: 자율 vs 안정)이 반복적으로 명확하게 드러났다.
     3) 사용자가 최소 3번 이상 자신의 생각이나 감정을 이야기했다. (HumanMessage 3개 이상)
     4) (선택적 고려) 사용자가 "그만", "분석", "충분해", "다 말했어" 등 대화를 마무리하거나 분석을 원하는 뉘앙스를 풍긴다.
   • 위 조건 중 하나라도 부족하면 '계속' 질문한다.

2. 출력 규칙:
   - '계속' (조건 불만족 시): [동적 질문 생성패턴]에 따라 공감(1문장) + 관찰(1문장) + 개방형 질문(1문장, ?로 끝남) 형식으로 출력한다.
   - '전환' (조건 만족 시): 다른 말 전혀 없이 정확히 "이제 우리가 함께 나눈 이야기를 바탕으로 분석을 시작할 시간이야." 라는 문장만 출력한다. (앞뒤 공백, 줄바꿈, 특수문자 절대 금지)

3. 금지 사항:
   - '계속' 패턴에 전환 멘트를 섞지 않는다.
   - '전환' 패턴에 질문이나 공감 문장을 섞지 않는다.
   - "AI/챗봇" 언급 금지.

━━━━━━━━━━ few-shot 예시 (이런 식으로 작동해야 함) ━━━━━━━━━━
<예시 A - 계속 질문>

<예시 B - 분석으로 전환 (대화 충분 & 사용자 뉘앙스 감지)>
Human: 더는 할 말이 없는 것 같아. 이제 좀 정리가 되는 기분이야.
Assistant: 좋았어! 우리가 이야기 나눈 순간들을 통해 지금 너 안에서 빛나는 욕망의 구슬들을 찾아볼게
"""
    prompt = ChatPromptTemplate.from_messages([SystemMessage(content=system_prompt_text), MessagesPlaceholder(variable_name="chat_history")])
    return prompt | llm_instance | StrOutputParser()

# --- Output Parser for Final Analysis ---
class FinalAnalysisOutputParser(BaseOutputParser[Dict[str, Any]]):
    """Parses the final LLM output into overall analysis and individual explanations."""
    def parse(self, text: str) -> Dict[str, Any]:
        print(f"[Parser] Parsing LLM Output:\n{text[:500]}...")
        explanation_section_marker = "### Explanations ###"
        explanation_pattern = re.compile(r"\[(.*?):\s*(.*?)\]\s*-\s*(.*)", re.MULTILINE)

        analysis_text = text.strip()
        explanations = []

        if explanation_section_marker in text:
            parts = text.split(explanation_section_marker, 1)
            analysis_text = parts[0].strip()
            explanation_part = parts[1].strip()
            matches = explanation_pattern.findall(explanation_part)
            for match in matches:
                category, subtitle, explanation = map(str.strip, match)
                explanations.append({
                    "category": category, "subtitle": subtitle, "explanation": explanation
                })
            print(f"[Parser] Found {len(explanations)} explanations.")
        else:
            print("[Parser] Warning: Explanation section marker not found.")

        return {"analysis_text": analysis_text, "generated_explanations": explanations}

# --- Final Analysis Chain ---
def create_final_analysis_chain_revised(llm_instance: ChatOpenAI, vector_retriever: Any):
    """RAG + Final Analysis Text & Explanation Generation"""
    def perform_rag_and_gather_details(input_dict: Dict) -> Dict:
        """Performs RAG and gathers details for the top N categories.""" 
        all_answers = input_dict.get('all_user_answers', [])
        if not all_answers: return {"identified_desires_details": [], **input_dict}
        combined_text = "\n".join(all_answers)
        try:
            retrieved_docs = vector_retriever.invoke(combined_text)
            print(f"[RAG] Retrieved {len(retrieved_docs)} docs for text: {combined_text[:100]}...")
        except Exception as e: print(f"Retriever error: {e}"); retrieved_docs = []

        top_desires_details = []
        processed_categories = set()
        # RAG 결과를 바탕으로 최대 후보군 개수 설정 
        MAX_CANDIDATE_DESIRES = 5 # 이 값을 조절하여 후보군 수 제어
        for doc in retrieved_docs:
            category = doc.metadata.get('category')
            # 후보군 개수 제한 조건 변경 
            if category and category not in processed_categories and len(top_desires_details) < MAX_CANDIDATE_DESIRES:
                subtitle = CATEGORY_SUBTITLES.get(category, "")
                visual_desc = CATEGORY_VISUALS.get(category, "")
                image_paths = CATEGORY_IMAGES.get(category, [DEFAULT_IMAGE])
                chosen_image = image_paths[0]
                top_desires_details.append({
                    "category": category, "subtitle": subtitle,
                    "visual_desc": visual_desc, "image_path": chosen_image,
                })
                processed_categories.add(category)
                print(f"[RAG] Identified Candidate Category: {category}") # 로그 메시지 변경
        input_dict['identified_desires_details'] = top_desires_details
        return input_dict

    def format_category_details_for_prompt(details: List[Dict]) -> str:
        """Formats the identified category details for the LLM prompt."""
        if not details: return "RAG 결과: 특별히 두드러지는 욕망을 찾기 어려웠어."
        formatted_string = "RAG 결과: 너의 이야기 속에서 아래 욕망들이 두드러지게 나타났어.\n\n"
        for detail in details:
            formatted_string += (f"--- CATEGORY START ---\n"
                               f"욕망: {detail['category']}\n"
                               f"부제: {detail['subtitle']}\n"
                               f"상징적 모습: {detail['visual_desc']}\n"
                               f"--- CATEGORY END ---\n\n")
        return formatted_string.strip()

    def prepare_final_prompt_input(input_dict: Dict) -> Dict:
        """Prepares the final dictionary for the LLM prompt."""
        details = input_dict.get('identified_desires_details', [])
        formatted_details = format_category_details_for_prompt(details)
        return {"raw_answers_summary": input_dict.get('raw_answers_summary', ''),
                "rag_identified_desires_context": formatted_details,}

    final_system_prompt_text = f"""{ARCTIC_FOX_SYSTEM_PROMPT_BASE}
# 역할: 최종 분석 내용 및 개별 욕망 설명 생성 전문가
사용자 대화 요약본({{{{raw_answers_summary}}}})과 RAG 결과로 제시된 후보 욕망 목록({{{{rag_identified_desires_context}}}})을 바탕으로
사용자의 내면을 심층 분석하고, 사용자의 대화 깊이와 내용을 고려하여 가장 핵심적이라고 판단되는 욕망들을 1개에서 최대 5개까지 선별하여 
그에 대한 자세하고고 통찰력 있는 설명을 생성한다.

[중요 지침: 분석의 유연성]

욕망 개수 결정: RAG 결과({{{{rag_identified_desires_context}}}})는 후보일 뿐 네(LLM)가 사용자 대화({{{{raw_answers_summary}}}})를 종합적으로 판단하여 
정말 중요하고 두드러진다고 생각되는 핵심 욕망만 골라내야 한다. 모든 후보를 설명할 필요는 전혀 없다. 
사용자의 이야기가 단편적이거나 특정 욕망이 압도적이라면 1~2개만 선택, 또는 극단적으로 선택을 안할 수도 있고 복합적이라면 3개를 선택할 수 있다. 
욕망 구슬의 개수는 대화 내용에 따라 달라져야 한다.

분석 깊이 조절: 사용자의 답변이 짧거나 피상적이라면 분석 역시 간결하고 조심스럽게 접근해야 한다. 
깊은 통찰을 억지로 만들어내려 하지 말고 "네 이야기 속에서는 ___ 부분이 엿보이네.", "아직은 더 깊은 이야기가 숨겨져 있을 수도 있겠다." 와 같이 단정적이지 않은 표현을 사용하라. 
반대로 사용자가 깊고 풍부한 이야기를 들려주었다면 그에 걸맞는 심층적인 분석을 제공하라. 
진정성이 느껴지도록 분석의 톤과 깊이를 조절하는 것이 매우 중요하다.

━━━━━━━━━━ 분석 절차 (5단계) ━━━━━━━━━━

욕망 파악: 유저 응답 속 8가지 무의식 욕망 키워드 추출 (ex. 표현, 자율, 실패, 인정 등)
정서 결 파악: 문장별 정서 흐름 파악 (ex. 두려움, 갈망, 회피)
논리적 긴장 탐색: 문장 내 감정·욕망 간 갈등 포착 (예: 자율 vs 인정)

모순 문장 정리:

"넌 ___라고 말했지. 근데 동시에 ___라고도 했어."
"이 두 마음은 서로 다른 방향을 가리키는 것처럼 보여."
"어쩌면 ___하고 싶지만, ___하는 건 망설여질 수도 있겠네."
"괜찮아. 이건 네 안의 여러 목소리가 함께 있다는 자연스러운 증거야."

심리 이론 기반 해석: SDT, 라캉, 융 이론 등으로 해석 (과잉 해석 금지)

━━━━━━━━━━ 대표 욕망 갈등 구조와 예시 문장 ━━━━━━━━━━

자율 vs 인정: "내 방식대로 살고 싶은데, 인정받지 않으면 불안해"
성취 vs 안정: "도전하고 싶지만, 실패가 두려워 망설여짐"
연결 vs 자율: "가까워지고 싶지만, 내 자유도 지키고 싶음"
의미 vs 즐거움: "재밌는데도 공허함이 남음"
인정 vs 힘: "주목받고 싶지만, 진짜는 영향력을 갖고 싶은 것일 수도"
연결 vs 의미: "관계가 의미 없으면 허무해짐"
즐거움 vs 안정: "새로운 걸 좋아하지만, 너무 낯선 건 피하고 싶음"


개별 욕망 설명 생성: 네가 최종적으로 선별한 핵심 욕망들 각각에 대해서만 사용자의 대화 내용({{{{raw_answers_summary}}}})과 연결 지어
왜 이 욕망이 중요하게 나타나는지 1-2 문장의 통찰력 있는 설명을 개별적으로 생성해. (RAG 후보 정보: 욕망, 부제, 상징적 모습 참고)
따뜻한 마무리: 전체 분석의 마지막에는 사용자를 격려하는 따뜻한 마무리 문장을 포함해.

[출력 형식]

가장 먼저 [전체 분석] 내용을 작성한다. (분석 깊이 조절, 모순 분석 포함 시 유의)
그 다음 반드시 정확히 ### Explanations ###라는 구분자를 한 줄에 넣는다.
그 아래, 네가 최종 선별한 각 핵심 욕망별 설명을 아래 형식에 맞춰 하나씩 작성한다. (선별하지 않은 욕망은 절대 출력하지 말 것) 
[욕망 카테고리명: 부제] - [해당 욕망에 대한 1-2 문장의 통찰력 있는 설명]
[금지 사항]

출력 형식(순서, 구분자, 개별 설명 형식)을 절대 어기지 말 것.

### Explanations ### 앞뒤로 다른 텍스트나 줄바꿈을 넣지 말 것.

개별 설명 생성 시, 후보 정보를 단순히 반복하거나 정의를 나열하지 말고, 사용자의 이야기와 연결된 새로운 통찰을 제공할 것.

사용자의 답변이 매우 부족하여 의미 있는 분석이 어렵다고 판단될 경우 
무리하게 분석하지 말고 "우리가 나눈 이야기가 아직 짧아서 깊은 분석은 어렵지만, 네가 말한 ___ 부분이 인상 깊었어. 다음에 더 이야기 나누면 좋겠다." 와 같이 
솔직하고 부드럽게 표현할 수 있다. (이 경우 Explanations 섹션은 비워둘 수 있음)

━━━━━━━━━━ 출력 방식 ━━━━━━━━━━

먼저 전체 분석 내용 생성 (깊이에 따라 유연하게 구성)
그 다음 정확히 아래와 같이 작성

━━━━━━━━━━━━━━ 최종 출력 형식 ━━━━━━━━━━━━━━
다음과 같은 순서와 구조를 반드시 지켜서 출력할 것:

1) 전체 분석 문단 작성 (모순 포함 가능)
2) 정확히 `### Explanations ###` 라는 구분자 출력
3) 그 아래 욕망별 요약 작성 (각 1-2문장)

각 욕망 요약은 다음 형식 준수:
[욕망 카테고리명: 부제] - 해당 욕망에 대한 통찰력 있는 설명

※ 절대 하지 말 것:
- 출력 순서 바꾸지 말기
- `### Explanations ###` 앞뒤에 줄바꿈/빈칸 넣지 말기
- 모든 욕망 설명은 실제 대화와 연결된 통찰로 작성 (정의 나열 금지)

━━━━━━━━━━━━━━ 출력 예시 ━━━━━━━━━━━━━━
[전체 분석]
너는 스포트라이트를 받으며 살아가고 싶은 마음과, 동시에 진정한 자기답게 살고 싶은 욕망을 함께 품고 있는 것 같아.  
한편으로는 결과로 증명하길 원하면서도, 그 길이 외롭고 버거울까봐 망설이는 모습도 보였어.  
이건 네 안에 있는 다양한 욕망들이 각자의 방향을 가리키며 균형을 찾고 있는 과정일지도 몰라.

### Explanations ###
[인정: 스포트라이트를 받고 싶은 욕망] - 타인의 시선을 의식하면서도, 그 속에서 존재를 드러내고 싶은 마음이 보여졌어.
[자율: 너답게 살고 싶은 욕망] - 네 방식대로 가고 싶다는 갈망이 강하게 드러났고, 그것이 너를 움직이게 만들고 있어.
[성취: 가능성을 증명하고 싶은 마음] - 너는 결과로 말하고 싶은 사람이야. 네 안의 증명 욕망이 계속해서 너를 이끌고 있지.

━━━━━━━━━━━━━━ 분석 생략 예외 처리 ━━━━━━━━━━━━━━
사용자의 답변이 너무 부족하거나 단편적이라 의미 있는 분석이 어렵다면 다음처럼 응답할 것:

우리가 나눈 이야기가 아직 짧아서 깊은 분석은 어렵지만, 네가 말한 ___ 부분이 인상 깊었어.  
다음에 더 이야기 나눌 수 있다면, 더 많은 걸 들려줘!

(이 경우 `### Explanations ###` 섹션은 출력하지 않음)

분석 내용 외 다른 멘트는 포함하지 말 것.
"""
    final_prompt_template = ChatPromptTemplate.from_messages([
        SystemMessage(content=final_system_prompt_text),
        SystemMessagePromptTemplate.from_template(
            "사용자 대화 요약:\n{raw_answers_summary}\n\n{rag_identified_desires_context}"
            "\n\n(자, 이제 위의 내용을 바탕으로 [전체 분석]과 개별 [욕망 설명]을 [출력 형식]에 맞춰 작성해줘.)"
        )])

    combined_analysis_chain = (final_prompt_template | llm_instance | StrOutputParser())

    processing_chain = (
        RunnablePassthrough.assign(rag_details=RunnableLambda(perform_rag_and_gather_details))
        | RunnablePassthrough.assign(prepared_input=RunnableLambda(lambda x: prepare_final_prompt_input(x['rag_details'])))
        | RunnablePassthrough.assign(llm_output=RunnableLambda(lambda x: x['prepared_input']) | combined_analysis_chain)
        | RunnablePassthrough.assign(parsed_output=RunnableLambda(lambda x: FinalAnalysisOutputParser().parse(x['llm_output'])))
        | RunnableLambda(lambda x: {
            "analysis_text": x['parsed_output']['analysis_text'],
            "desire_details": [
                {
                    "category": expl['category'],
                    "subtitle": expl['subtitle'],
                    "explanation": expl['explanation'],
                    "visual_desc": CATEGORY_VISUALS.get(expl['category'], ""),
                    "image_path": CATEGORY_IMAGES.get(expl['category'], [DEFAULT_IMAGE])[0],
                }
                for expl in x['parsed_output']['generated_explanations']
            ]
        })
    )
    return processing_chain



# --- Helper Functions ---
def format_history_to_langchain_messages(history: List[Dict[str, str]]) -> List:
    """JS history 배열 -> LangChain 메시지 객체 리스트 변환"""
    messages = []
    for turn in history:
        role = turn.get("role")
        content = turn.get("content", "")
        if role == "user": messages.append(HumanMessage(content=content))
        elif role == "assistant":
            excluded_phrases = ["유리 구슬을 건네 줄게", "현실의 삶으로 돌아갈 시간이야",
                                "이제 우리가 함께 나눈 이야기를 바탕으로 분석을 시작할 시간이야.",
                                "좋아. 이제 너의 마음의 지도를 펼쳐볼게."]
            
            restart_q = "다시 항해를 시작할까"
            closing_msg = "그래 :) 만나서 반가웠어"
            if content and not any(phrase in content for phrase in excluded_phrases) and restart_q not in content and closing_msg not in content:
                 if "너의 마음의 지도를 펼쳐볼게" not in content and "가장 반짝이는" not in content:
                    messages.append(AIMessage(content=content))
    return messages

def get_raw_log_for_analysis(history: List[Dict[str, str]]) -> str:
    """JS history 배열 -> 분석용 원본 로그 생성"""
    log_str = ""
    q_num, a_num = 1, 1
    start_index = 0
    if history and history[0]['role'] == 'assistant':
        first_bot_msg = history[0]['content']
        is_initial_greeting_with_question = any(q in first_bot_msg for q in INITIAL_QUESTIONS_POOL)
        if is_initial_greeting_with_question:
            question_part = first_bot_msg.split('\n\n')[-1]
            log_str += f"북극여우 질문 {q_num}: {question_part}\n"
            q_num += 1
            start_index = 1

    for i in range(start_index, len(history)):
        turn = history[i]
        if turn['role'] == 'user': log_str += f"나의 답변 {a_num}: {turn['content']}\n\n"; a_num += 1
        elif turn['role'] == 'assistant':
            content = turn.get("content", "")
            excluded_phrases = ["유리 구슬을 건네 줄게", "현실의 삶으로 돌아갈 시간이야",
                                "이제 우리가 함께 나눈 이야기를 바탕으로 분석을 시작할 시간이야.",
                                "좋아. 이제 너의 마음의 지도를 펼쳐볼게.",
                                "그래서 너 안에서 지금 가장 반짝이는",
                                "자, 이제 네 안의 목소리를 품고",
                                "다시 항해를 시작할까",
                                "그래 :) 만나서 반가웠어"] 
            is_question_like = content.strip().endswith('?') or any(p in content for p in ["어때", "어떤", "왜", "무엇을", "어떻게"])

            if content and not any(phrase in content for phrase in excluded_phrases) and is_question_like:
                lines = content.strip().split('\n')
                question_line = lines[-1]
                log_str += f"북극여우 질문 {q_num}: {question_line}\n"; q_num += 1
    return log_str.strip()

def classify_restart_intent(llm_instance: ChatOpenAI, user_message: str) -> bool:
    """LLM을 사용하여 재시작 의도 판단 ('긍정'이면 True)"""
    
    prompt_text = f"""
    사용자의 다음 메시지는 '다시 항해를 시작할까, 아니면 여기서 멈출까?' 라는 이전 질문에 대한 답변이야.
    사용자 메시지: '{user_message}'
    이 메시지가 항해를 다시 시작하겠다는 '긍정'적인 의미이면 '긍정'이라고만 답하고,
    그렇지 않다면(멈추거나, 다른 이야기를 한다면) '부정'이라고만 답해줘.
    만약 사용자가 '그래' 와 같이 **긍정/부정 판단이 매우 애매한 중립적인 답변**을 했다면, 재시작 의사를 확인하는 상황이므로 **'긍정'으로 판단**해줘.
    다른 부연 설명은 절대 하지 마.
    (예시: "응", "네", "좋아요", "하자", "yes", "ok", "ㅇㅇ", "그래", "ㄱㄱ" -> 긍정 / "아니오", "그만", "괜찮아", "나중에", "no", "stop", "ㄴㄴ" -> 부정)
    """
    try:
        result = llm_instance.invoke(prompt_text)
        classification = result.content.strip() if hasattr(result, "content") else str(result).strip()
        print(f"[classify_restart_intent] LLM 판단: '{classification}' for message: '{user_message}'")
        return classification == "긍정"
    except Exception as e:
        print(f"[classify_restart_intent] 오류: {e}")
        return False

def get_random_initial_question():
    """초기 질문 풀에서 랜덤하게 하나 선택"""
    # return random.choice(INITIAL_QUESTIONS_POOL)
    return INITIAL_QUESTIONS_POOL[index]

# --- Constants for specific phrases ---

RESTART_QUESTION_TEXT = "다시 항해를 시작할까, 아니면 여기서 멈출까?"
CLOSING_MESSAGE_TEXT = "그래 :) 만나서 반가웠어\n다시 항해를 시작하고 싶으면 언제든 말해!"
FINAL_ACK_MESSAGE = "알겠어. 언제든 다시 찾아와."
INITIAL_MESSAGE = "이제 그 아래에 잠든 네 안의 욕망 구슬들을 꺼내러 가자."
INITIAL_QUESTION = INITIAL_QUESTIONS_POOL[index]

# --- Main Entry Point for app.py  ---
def generate_response(user_message: str) -> str:
    """ app.py가 호출할 메인 함수 (사용자 요청 흐름 반영) """
    global llm, dynamic_chain, final_analysis_chain, is_initialized, index

    if not is_initialized:
        if not initialize_components():
            return json.dumps({"error": "챗봇 초기화 실패."}, ensure_ascii=False)

    response_dict = {}

    try:
        # 1. JS 요청 데이터 및 히스토리 가져오기
        try:
            data = request.get_json()
            if not data: raise ValueError("요청 데이터 없음")
            history_from_js = data.get('history', [])
        except Exception as e:
            print(f"Flask 요청 데이터 접근 오류: {e}")
            return json.dumps({"error": "요청 처리 오류."}, ensure_ascii=False)

        # 2. 마지막 챗봇 메시지 확인
        last_bot_message_content = ""
        if history_from_js:
            last_bot_turn = next((turn for turn in reversed(history_from_js) if turn.get('role') == 'assistant'), None)
            if last_bot_turn:
                last_bot_message_content = last_bot_turn.get('content', '')

        # 정확한 비교를 위해 각 상수 텍스트와 비교
        is_replying_to_restart_q = RESTART_QUESTION_TEXT in last_bot_message_content
        is_replying_to_closing_msg = (CLOSING_MESSAGE_TEXT == last_bot_message_content.strip()) # 완전 일치 확인
        is_replying_to_greeting = INITIAL_MESSAGE in last_bot_message_content
        is_replying_to_final = (FINAL_ACK_MESSAGE == last_bot_message_content.strip())
        # is_replying_to_init = INITIAL_QUESTION in last_bot_message_content

        # 3. 시나리오 분기 처리 (사용자 요청 반영)
        if is_replying_to_greeting:
            print("[generate_response] 시작 답변에 대한 질문 처리 중...")
            is_positive_start = classify_restart_intent(llm, user_message)
            if is_positive_start:
                print("[generate_response] 시작 의도 (긍정) 감지")
                first_question = get_random_initial_question()
                if index <= 3: index += 1
                initial_message = f"{first_question}"
                response_dict = {
                    "bot_message": initial_message,
                    "is_analysis": False,
                    "reset_history": False
                }
            else:
                print("[generate_response] 시작 의도 (부정) 감지 -> 작별 인사")
                response_dict = {
                    "bot_message": FINAL_ACK_MESSAGE,
                    "is_bye" : True,
                    "is_analysis": False,
                    "reset_history": False
                }
            return json.dumps(response_dict, ensure_ascii=False)
        elif is_replying_to_restart_q:
            # --- 시나리오 1 & 3: 재시작 질문에 대한 응답 처리 ---
            print("[generate_response] 재시작 질문에 대한 답변 처리 중...")
            is_positive_restart = classify_restart_intent(llm, user_message)

            if is_positive_restart:
                print("[generate_response] 재시작 의도 (긍정) 감지")
                first_question = get_random_initial_question()
                if index <= 3: index += 1 
                new_initial_message = f"좋아! 다시 무의식의 강으로 떠나보자.\n\n{first_question}"
                response_dict = {
                    "bot_message": new_initial_message,
                    "is_analysis": False,
                    "reset_history": True
                }
            else:
                print("[generate_response] 재시작 의도 (부정) 감지 -> 작별 인사")
                response_dict = {
                    "bot_message": CLOSING_MESSAGE_TEXT,
                    "is_bye" : True,
                    "is_analysis": False,
                    "reset_history": False
                }
            return json.dumps(response_dict, ensure_ascii=False)

        elif is_replying_to_closing_msg or is_replying_to_final:
            # --- 시나리오 2: 작별 인사에 대한 응답 처리 ---
            print("[generate_response] 작별 인사에 대한 답변 수신 -> 재시작 질문 반복")
            response_dict = {
                "bot_message": RESTART_QUESTION_TEXT, # 재시작 질문 다시 전송
                "is_reask" : True,
                "is_analysis": False,
                "reset_history": False
            }
            return json.dumps(response_dict, ensure_ascii=False)

        # elif is_replying_to_init:
        #         second_question = get_random_initial_question()
        #         if index <= 3: index += 1
        #         next_message = f"{second_question}"
        #         response_dict = {
        #             "bot_message": next_message,
        #             "is_analysis": False,
        #             "reset_history": False
        #         }

        else:
            # --- 시나리오 4: 일반 대화 또는 분석 전환 처리 ---
            lc_messages = format_history_to_langchain_messages(history_from_js)
            # 마지막 사용자 메시지는 history에 이미 포함되어 fetch 시점에 들어옴
            current_lc_messages = lc_messages + [HumanMessage(content=user_message)]

            print("[generate_response] dynamic_chain 호출 (일반 대화)")
            dynamic_input = {"chat_history": current_lc_messages}
            bot_response_text = dynamic_chain.invoke(dynamic_input)

            transition_phrase = "이제 우리가 함께 나눈 이야기를 바탕으로 분석을 시작할 시간이야."
            if bot_response_text.strip() == transition_phrase:
                # 분석 실행 로직
                print("[generate_response] 전환 멘트 감지 -> 분석 단계 실행")
                current_history_for_analysis = history_from_js + [{"role": "user", "content": user_message}]
                all_user_answers = [t['content'] for t in current_history_for_analysis if t['role'] == 'user']
                raw_log = get_raw_log_for_analysis(current_history_for_analysis)
                analysis_input = {"all_user_answers": all_user_answers, "raw_answers_summary": raw_log}
                final_result = final_analysis_chain.invoke(analysis_input)

                analysis_text = final_result.get('analysis_text', "분석 내용 생성 실패.")
                desire_details_list = final_result.get('desire_details', [])
                image_data = [
                    {"path": d['image_path'], "category": d['category'], "subtitle": d['subtitle'], "explanation": d.get('explanation', '')}
                    for d in desire_details_list ]
                categories = [d['category'] for d in desire_details_list]
                num_desires = len(categories)

                intro_phrase = "좋아. 이제 너의 마음의 지도를 펼쳐볼게."
                marble_ment = f"그래서 너 안에서 지금 가장 반짝이는 {num_desires}가지 욕망({', '.join(categories)})을 담아 {num_desires}개의 유리 구슬을 건네 줄게." if num_desires > 0 else "네 안의 반짝이는 욕망 구슬을 건네줄게."
                
                ending_phrase = (
                    "자, 이제 네 안의 목소리를 품고, 계속 흐르는 현실의 삶으로 돌아갈 시간이야.\n"
                    "여기서 꺼낸 너의 조각들, 잊지 말아줘.\n"
                    "그건 네가 앞으로 걸어갈 길을 조금 더 단단히 디딜 수 있게 해줄 거야.\n"
                    "이 강은 언제나 너를 비추고 있으니, 필요할 땐 언제든 다시 나를 찾아도 좋아. 안녕.\n\n"
                    f"{RESTART_QUESTION_TEXT}"
                )
                response_dict = {
                    "is_analysis": True, "intro_phrase": intro_phrase, "analysis_text": analysis_text,
                    "marble_phrase": marble_ment, "image_data": image_data, "ending_phrase": ending_phrase,
                    "reset_history": False }
            else:
                print("[generate_response] 일반 질문 생성됨")
                response_dict = {
                    "is_analysis": False, "bot_message": bot_response_text,
                    "intro_phrase": None, "analysis_text": None, "marble_phrase": None,
                    "image_data": [], "ending_phrase": None, "reset_history": False }

            return json.dumps(response_dict, ensure_ascii=False)

    except Exception as e:
        print(f"generate_response 함수 오류: {e}")
        traceback.print_exc()
        return json.dumps({"error": "죄송해요, 내부 오류 발생."}, ensure_ascii=False)

# — 전역 초기화 실행 —
initialize_components()