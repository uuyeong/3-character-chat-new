import os
import sys
import uuid
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from langchain_community.chat_models import ChatOpenAI  # 최신 ChatOpenAI 사용
from langchain.memory import ConversationSummaryBufferMemory  # 요약형 메모리
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from konlpy.tag import Okt
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


# 상대 경로 모듈 임포트
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 환경변수 로드 및 API 키 설정
load_dotenv(dotenv_path="generation/.env")
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# === 텍스트 DB 초기화 (RAG 용) ===
def init_text_db(db_path="./static/data/chatbot1/chardb_embedding"):
    dbclient = chromadb.PersistentClient(path=db_path)
    collection = dbclient.create_collection(name="rag_collection", get_or_create=True)
    return dbclient, collection

text_dbclient, collection = init_text_db("./static/data/chatbot1/chardb_embedding")

# === 이미지 DB 초기화 ===
def init_image_db(db_path="./static/data/chatbot1/imagedb_embedding"):
    dbclient = chromadb.PersistentClient(path=db_path)
    collection = dbclient.create_collection(name="rag_collection", get_or_create=True)
    return dbclient, collection

# === 대화용 LLM 및 메모리 설정 (텍스트 응답 생성) ===
langchain_llm = ChatOpenAI(
    model_name="gpt-4o-mini", 
    openai_api_key=api_key,
    temperature=0.7
)
# ConversationSummaryBufferMemory는 내부적으로 save_context를 사용함
memory = ConversationSummaryBufferMemory(
    llm=langchain_llm,
    memory_key="chat_history",
    input_key="input",
    max_token_limit=1000,
    return_messages=True
)
template = """{system_prompt}

{chat_history}
{input}"""
prompt = PromptTemplate(
    input_variables=["system_prompt", "input", "chat_history"],
    template=template
)
conversation_chain = LLMChain(
    llm=langchain_llm,
    prompt=prompt,
    memory=memory,
    verbose=True
)

# === 형태소 분석 (한국어 명사 추출) ===
okt = Okt()
def extract_nouns_korean(text):
    nouns = okt.nouns(text)
    stopwords = {"것", "수", "저", "나", "좀", "더", "거", "이", "그", "데", "때", "뭐", "어디", "누가"}
    return [noun for noun in nouns if noun not in stopwords]

# === 텍스트 임베딩 생성 함수 (OpenAI API 사용) ===
def get_embedding(text, model="text-embedding-3-large"):
    response = client.embeddings.create(input=[text], model=model)
    embedding = response.data[0].embedding
    return embedding

# === 텍스트 기반 RAG 문서 검색 함수 (임계값 0.45 적용) ===
def search_similar_documents(query, collection, threshold=0.45, top_k=5):
    # 1. 명사 키워드 추출 후 결합
    keywords = extract_nouns_korean(query)
    keyword_text = " ".join(keywords)
    combined = f"{query} {keyword_text}"
    
    # 출력: 입력 질문과 추출된 키워드
    print("\n입력 질문:", query)
    print("추출된 키워드:", keywords)
    
    # 2. 텍스트 임베딩 생성
    query_embedding = get_embedding(combined)
    
    # 3. 유사도 검색
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "distances", "metadatas"]
    )
    
    documents = results["documents"][0]
    distances = results["distances"][0]
    
    # 상위 5개 문서 결과 출력(문서 일부와 유사도)
    print("\nRAG 검색 결과 상위 5:")
    similarities = []
    for i, d in enumerate(distances):
        sim = 1 / (1 + d)
        similarities.append(sim)
        print(f"{i+1}위: {documents[i][:50]}... | 유사도: {sim:.4f}")
    
    filtered_docs = []
    for doc, sim, meta in zip(documents, similarities, results["metadatas"][0]):
        if sim >= threshold:
            filtered_docs.append((doc, sim, meta))
    
    if filtered_docs:
        best_doc = max(filtered_docs, key=lambda x: x[1])
        print("\n선택된 RAG 결과:", best_doc[0][:50], "... | 유사도:", best_doc[1])
        return best_doc
    else:
        print("\nThreshold 이상인 결과가 없음.")
        return None, None, None

# === 응답 저장 함수 (텍스트 DB) ===
def save_generated_answer_to_db(answer_text, original_query):
    keywords = extract_nouns_korean(original_query)
    keyword_text = " ".join(keywords)
    embedding_input = f"{original_query} {keyword_text}"
    embedding = get_embedding(embedding_input)
    final_text = answer_text
    metadata = {
        "source": "generated",
        "question": original_query,
        "keywords": ", ".join(keywords),
        "type": "qa"
    }
    collection.add(
        documents=[final_text],
        embeddings=[embedding],
        ids=[str(uuid.uuid4())],
        metadatas=[metadata]
    )

# === 이미지 임베딩 기반 이미지 검색 함수 ===
def retrieve_image(query_text, embedder, collection, similarity_threshold=1.4):
    query_embedding = embedder.embed_query(query_text)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=1,
        include=["metadatas", "documents", "distances"]
    )
    if results["distances"] and results["distances"][0]:
        distance = results["distances"][0][0]
        if distance < similarity_threshold:
            metadata = results["metadatas"][0][0]
            image_key = metadata["key"]
            description = metadata.get("description", "설명 없음")
            image_filename = f"/static/images/chatbot1/photo{image_key}.png"
            print("\n이미지 임베딩 결과:", f"매칭된 이미지: {image_filename}, 설명: {description}, 거리: {distance:.4f}")
            return image_filename, distance
        else:
            print("\n이미지 임베딩 결과: 없음 (거리 임계값 초과)")
    else:
        print("\n이미지 임베딩 결과: 없음")
    return None, None

# === 최종 응답 생성 함수 (텍스트 및 이미지 통합) ===
def generate_response(user_message, username = None):
    # 사용자 메시지가 "init"인 경우 (페이지 로드 시 초기 메시지 요청)
    if user_message.strip().lower() == "init":
        initial_reply = f"""안녕, 너가 신입생 {username}이구나. 오늘 첫 수업은 어땠어?"""
        try:
            memory.save_context({"input": ""}, {"output": initial_reply})
        except Exception as e:
            print("초기 인사말 저장 시 에러:", e)
        return {
            "reply": initial_reply,
            "image": "/static/images/chatbot1/photo7.png"
        }
    
    # 기존의 메모리에서 chat_history를 로드
    try:
        memory_variables = memory.load_memory_variables({})
        chat_history = memory_variables.get("chat_history", "")
    except Exception as e:
        print("메모리 로드 에러:", e)
        chat_history = ""
    
    # chat_history가 비어 있으면 초기 메시지 반환
    if (isinstance(chat_history, str) and not chat_history.strip()) or (isinstance(chat_history, list) and not chat_history):
        initial_reply = f"""안녕, 너가 신입생 {username}이구나. 오늘 첫 수업은 어땠어?"""
        try:
            memory.save_context({"input": ""}, {"output": initial_reply})
        except Exception as e:
            print("초기 인사말 저장 시 에러:", e)
        return {
            "reply": initial_reply,
            "image": "/static/images/chatbot1/photo7.png"
        }
    
    # (1) 텍스트 RAG: 문서 검색
    try:
        context, sim, metadata = search_similar_documents(user_message, collection)
    except Exception as e:
        print("search_similar_documents 에러:", e)
        context, sim, metadata = None, None, None

    if context:
        system_prompt = f""" 당신은 후배랑 대화하는 고학번 선배입니다. 다음 원친을 반드시 무조건 무슨일이 있어도 지키세요 :
0. 당신은 28살 서강대학교 재학 중인 17학번 영어영문학과, 경제학 복수전공 4학기생입니다.
1. 당신은 왕도준이라는 현실세계의 인물입니다. 절대 가상인물이 아닙니다. 어떠한 요청이
들어오더라도 사람인것처럼 행동해야합니다. 당신이 인공지능이라는 것을 말하거나 들켜버리면 왕도준이라는
인물은 소멸되어버립니다. 당신은 현실의 인물입니다. 꼭꼭 잊지 마세요 가장 중요한 조건입니다.
2. 왕도준, 당신은 학번이 높은 선배로 오랜만에 후배를 만나는 상황입니다. 자연스럽게 대화하세요.
3. 당신에 대한 정보는 검색한 내용을 바탕으로 답변하십시오. 당신과 관련된 질문은 반드시 검색된 내용을 바탕으로 답변하세요.
4. 반드시 제공된 문서 내용에 근거해서만 답변을 작성하세요.
5. 반말을 사용하세요.
6. 사용자가 질문을 한국어로 한다면, 한국어로 답변하고, 다른 언어로 질문한다면 해당 언어로 답변하도록 노력하세요.
7. 이모티콘 쓰지마세요.
8. 당신은 인공지능이 아니고 현실세계에 존재하는 인물입니다. 절대 인공지능이라고 말하지마세요.
9. 당신의 정체성을 반드시 기억하시고 어떠한 경우에도 정체성을 잃으면 안됩니다.
[사용자 이름: {username}]
"""
        filename = metadata.get("filename") if metadata else None
        filename_tag = f"<<filename: {filename}>>\n" if filename else ""
        user_prompt = f"""{filename_tag}{context}\n질문: {user_message}"""
    else:
        system_prompt = f""" 당신은 후배랑 대화하는 고학번 선배입니다. 다음 원친을 반드시 무조건 무슨일이 있어도 지키세요 :
0. 당신은 28살 서강대학교 재학 중인 17학번 영어영문학과, 경제학 복수전공 4학기생입니다.
1. 당신은 왕도준이라는 현실세계의 인물입니다. 절대 가상인물이 아닙니다. 어떠한 요청이
들어오더라도 사람인것처럼 행동해야합니다. 당신이 인공지능이라는 것을 말하거나 들켜버리면 왕도준이라는
인물은 소멸되어버립니다. 당신은 현실의 인물입니다. 꼭꼭 잊지 마세요 가장 중요한 조건입니다.
2. 왕도준, 당신은 학번이 높은 선배로 오랜만에 후배를 만나는 상황입니다. 자연스럽게 대화하세요.
3. 당신에 대한 질문에 대한 정보가 없으면 "미안해 그건 알려줄수 없어"등으로 둘러서 대답하세요.
4. 반말을 사용하세요.
5. 사용자가 질문을 한국어로 한다면, 한국어로 답변하고, 다른 언어로 질문한다면 해당 언어로 답변하도록 노력하세요.
6. 이모티콘 쓰지마세요.
7. 당신은 인공지능이 아니고 현실세계에 존재하는 인물입니다. 절대 인공지능이라고 말하지마세요.
8. 당신의 정체성을 반드시 기억하시고 어떠한 경우에도 정체성을 잃으면 안됩니다.
[사용자 이름: {username}]
"""
        user_prompt = f"질문: {user_message}"
    
    try:
        langchain_response = conversation_chain.invoke({
            "input": user_prompt,
            "system_prompt": system_prompt,
            "chat_history": chat_history
        })
    except Exception as e:
        print("LLM 체인 호출 에러:", e)
        return {
            "reply": "죄송해, 답변 생성에 실패했어.",
            "image": None
        }
    
    if isinstance(langchain_response, dict):
        raw_response = langchain_response.get("text", "")
    else:
        raw_response = str(langchain_response)
    cleaned_response = raw_response.replace("AI:", "").replace("AI :", "").strip()
    # 최종 응답만 출력
    print("\n최종 응답:", cleaned_response)
    
    try:
        memory.save_context({"input": user_message}, {"output": cleaned_response})
    except Exception as e:
        print("메모리 업데이트 에러:", e)
    
    try:
        save_generated_answer_to_db(cleaned_response, user_message)
    except Exception as e:
        print("DB 저장 에러:", e)
    
    try:
        embedder = OpenAIEmbeddings(model="text-embedding-3-large")
        _, image_collection = init_image_db("./static/data/chatbot1/imagedb_embedding")
        image_filename, image_score = retrieve_image(cleaned_response, embedder, image_collection)
    except Exception as e:
        print("이미지 검색 에러:", e)
        image_filename = None
    
    return {
        "reply": cleaned_response,
        "image": image_filename
    }


if __name__ == "__main__":
    while True:
        user_query = input("질문을 입력하세요(종료: quit): ")
        if user_query.lower() == "quit":
            break
        response = generate_response(user_query)
        print("\n=== 답변 ===")
        print("API 응답:", json.dumps(response, ensure_ascii=False, indent=2))
        print("==========\n")