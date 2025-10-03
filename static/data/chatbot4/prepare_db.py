import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 문서 로드
loader = DirectoryLoader(
    path="/Users/kjb/Desktop/hateslop/3기/2-chatbot-project/static/data/chatbot4/documents",
    glob="**/*.txt",
    loader_cls=lambda p: TextLoader(p, encoding="utf-8")  # ✅ 여기에 encoding 명시
)
documents = loader.load()

# 문서 분할
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
)
chunks = text_splitter.split_documents(documents)

# 임베딩 생성 및 저장
embeddings = OpenAIEmbeddings(openai_api_key=api_key)
vectordb = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings,
    persist_directory="./chroma_db"
)
vectordb.persist()
print(f"데이터베이스에 저장된 문서 수: {vectordb._collection.count()}")