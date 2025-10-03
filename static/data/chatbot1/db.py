import os
import uuid
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# 환경변수 로드 및 API 키 설정
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI 클라이언트 초기화 (텍스트 임베딩용)
client = OpenAI(api_key=api_key)

# ========= DB 초기화 함수 =========
# 텍스트 임베딩 DB 초기화 (예: 질문/답변 + 일반 텍스트)
def init_text_db(db_path="./chardb_embedding"):
    dbclient = chromadb.PersistentClient(path=db_path)
    collection = dbclient.create_collection(name="rag_collection", get_or_create=True)
    return dbclient, collection

# 이미지 임베딩 DB 초기화 (예: 이미지 정보)
def init_image_db(db_path="./imagedb_embedding"):
    dbclient = chromadb.PersistentClient(path=db_path)
    collection = dbclient.create_collection(name="rag_collection", get_or_create=True)
    return dbclient, collection

# ========= 텍스트 데이터 처리 =========
def load_text_files(folder_path):
    """
    지정한 폴더 내의 모든 .txt 파일을 읽어 (파일명, 내용) 튜플 형태로 반환.
    """
    docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                docs.append((filename, text))
                print(f"[불러옴] {filename}")
    return docs

def get_text_embedding(text, model="text-embedding-3-large"):
    """
    OpenAI API를 이용해 텍스트 임베딩 생성.
    """
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def parse_qa_blocks(filename, raw_text):
    """
    '키워드:', '질문:', '답변:' 형식의 Q&A 블록을 파싱하여
    (질문+키워드 텍스트, 답변, 메타데이터) 튜플 리스트로 반환.
    """
    blocks = []
    # 각 Q&A 블록은 빈 줄로 구분한다.
    for raw in raw_text.strip().split("\n\n"):
        lines = raw.strip().split("\n")
        keywords = []
        questions = []
        answer = ""
        for line in lines:
            if line.startswith("키워드:"):
                raw_keywords = line.replace("키워드:", "").strip()
                keywords = [kw.strip() for kw in raw_keywords.split(",") if kw.strip()]
            elif line.startswith("질문:"):
                questions.append(line.replace("질문:", "").strip())
            elif line.startswith("답변:"):
                answer = line.replace("답변:", "").strip()
        if questions and answer:
            # 임베딩 텍스트는 질문과 키워드를 결합
            embedding_text = " ".join(keywords + questions)
            metadata = {
                "type": "qa_block",
                "keywords": ", ".join(keywords),
                "questions": " / ".join(questions),
                "filename": filename
            }
            blocks.append((embedding_text, answer, metadata))
    return blocks

# 일반 텍스트 파일을 일정 길이로 청킹하기 위한 텍스트 분할기
text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)

# ========= 이미지 데이터 처리 =========
def load_json_mapping(file_path):
    """
    JSON 파일을 읽어 이미지 매핑 데이터를 반환.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        mapping = json.load(f)
    return mapping

def get_image_embedding(text, embedder):
    """
    LangChain의 OpenAIEmbeddings를 이용하여 텍스트 임베딩 생성.
    """
    return embedder.embed_query(text)

# ========= 실행 =========
if __name__ == "__main__":
    # -- 텍스트 데이터 임베딩 처리 --
    # 텍스트 파일들이 위치한 폴더 (예: 질문답변식.txt 등 포함)
    text_folder_path = "./chardb_text"
    docs = load_text_files(text_folder_path)
    
    dbclient, text_collection = init_text_db("./chardb_embedding")
    doc_id = 0
    for filename, text in docs:
        if filename == "질문답변식.txt":
            # Q&A 형식 파일 처리
            qa_blocks = parse_qa_blocks(filename, text)
            for emb_text, answer, metadata in qa_blocks:
                doc_id += 1
                embedding = get_text_embedding(emb_text)
                text_collection.add(
                    documents=[answer],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[str(doc_id)]
                )
        else:
            # 일반 텍스트 파일을 청크 단위로 처리
            chunks = text_splitter.split_text(text)
            for idx, chunk in enumerate(chunks):
                doc_id += 1
                embedding = get_text_embedding(chunk)
                text_collection.add(
                    documents=[chunk],
                    embeddings=[embedding],
                    metadatas=[{
                        "type": "text",
                        "filename": filename,
                        "chunk_index": idx
                    }],
                    ids=[str(doc_id)]
                )
    print("질문답변 블록 + 일반 텍스트 청킹 및 임베딩 완료!")
    
    # -- 이미지 데이터 임베딩 처리 --
    image_dbclient, image_collection = init_image_db("./imagedb_embedding")
    
    # 이미지 임베딩용 embedder 초기화 (langchain OpenAIEmbeddings 사용)
    embedder = OpenAIEmbeddings(model="text-embedding-3-large")
    
    # 이미지 매핑 JSON 파일 경로 (예: photo_data.json)
    json_path = "imagedb_text/photo_data.json"
    mapping = load_json_mapping(json_path)
    
    doc_id_image = 0
    for key, description in mapping.items():
        doc_id_image += 1
        embedding = get_image_embedding(description, embedder)
        image_collection.add(
            documents=[description],
            embeddings=[embedding],
            metadatas=[{"key": key, "description": description}],
            ids=[str(doc_id_image)]
        )
    print("모든 이미지 매핑 데이터의 임베딩 벡터를 DB에 저장 완료")