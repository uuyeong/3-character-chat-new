"""
RAG-D 방식 상담 매뉴얼 벡터 DB 구축 스크립트

이 스크립트는 source_pdfs 폴더의 PDF 파일들을 로드하여
ChromaDB 벡터 데이터베이스를 구축합니다.

사용법:
    python tools/build_counseling_vectordb.py
"""

import os
import sys
from pathlib import Path
from typing import List

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

# 환경 변수 로드
load_dotenv()

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
PDF_DIR = BASE_DIR / "static" / "data" / "chatbot" / "source_pdfs"
VECTOR_DB_DIR = BASE_DIR / "static" / "data" / "chatbot" / "counseling_vectordb"


def load_pdfs() -> List[Document]:
    """PDF 파일들을 로드"""
    print(f"\n📚 PDF 파일 로드 시작...")
    print(f"   경로: {PDF_DIR}")
    
    all_documents = []
    pdf_files = list(PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("   ⚠️  PDF 파일을 찾을 수 없습니다!")
        return []
    
    print(f"   발견된 PDF: {len(pdf_files)}개")
    
    for pdf_file in pdf_files:
        try:
            print(f"\n   📄 처리 중: {pdf_file.name}")
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            
            # 메타데이터에 파일명 추가
            for doc in documents:
                doc.metadata["source_file"] = pdf_file.name
                doc.metadata["type"] = "counseling_manual"
            
            all_documents.extend(documents)
            print(f"      ✅ {len(documents)} 페이지 로드 완료")
            
        except Exception as e:
            print(f"      ❌ 에러: {e}")
            continue
    
    print(f"\n✅ 총 {len(all_documents)} 페이지 로드 완료")
    return all_documents


def split_documents(documents: List[Document]) -> List[Document]:
    """문서를 적절한 크기로 분할"""
    print(f"\n✂️  문서 분할 시작...")
    
    # 상담 매뉴얼 특성에 맞는 청킹 전략
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,  # 1000자 청크
        chunk_overlap=200,  # 200자 중복 (맥락 유지)
        length_function=len,
        separators=[
            "\n\n",  # 단락 구분 우선
            "\n",    # 줄바꿈
            ". ",    # 문장 끝
            "? ",    # 질문 끝
            "! ",    # 감탄 끝
            " ",     # 공백
            ""       # 최후 수단
        ],
        is_separator_regex=False,
    )
    
    split_docs = text_splitter.split_documents(documents)
    
    # 청크 메타데이터 보강
    for i, doc in enumerate(split_docs):
        doc.metadata["chunk_index"] = i
    
    print(f"   ✅ {len(documents)} 문서 → {len(split_docs)} 청크로 분할 완료")
    print(f"   📊 평균 청크 크기: {sum(len(d.page_content) for d in split_docs) // len(split_docs)}자")
    
    return split_docs


def build_vectordb(chunks: List[Document]):
    """벡터 DB 구축 (배치 처리로 토큰 제한 회피)"""
    print(f"\n🔨 벡터 데이터베이스 구축 시작...")
    
    # OpenAI API 키 확인
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다!")
    
    # 임베딩 모델 초기화
    print(f"   🧠 OpenAI 임베딩 모델 로드 중...")
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # 빠르고 효율적
        openai_api_key=api_key,
        chunk_size=100  # ⭐ 배치 크기 제한 (토큰 제한 회피)
    )
    
    # 기존 벡터 DB 삭제 (재구축)
    if VECTOR_DB_DIR.exists():
        import shutil
        print(f"   🗑️  기존 벡터 DB 삭제 중...")
        shutil.rmtree(VECTOR_DB_DIR)
    
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    
    # ChromaDB 구축 (배치 처리)
    print(f"   💾 ChromaDB에 {len(chunks)}개 청크 저장 중...")
    print(f"   ⏳ 배치로 나눠서 처리합니다 (OpenAI API 호출)...")
    
    try:
        # 배치 크기 설정 (토큰 제한 고려)
        batch_size = 50  # 한 번에 50개씩 처리
        total_batches = (len(chunks) + batch_size - 1) // batch_size
        
        # 첫 배치로 컬렉션 생성
        print(f"   📦 배치 처리: 총 {total_batches}개 배치")
        
        vectordb = Chroma.from_documents(
            documents=chunks[:batch_size],
            embedding=embeddings,
            persist_directory=str(VECTOR_DB_DIR),
            collection_name="counseling_knowledge"
        )
        print(f"      ✅ 배치 1/{total_batches} 완료")
        
        # 나머지 배치 추가
        for i in range(1, total_batches):
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(chunks))
            batch = chunks[start_idx:end_idx]
            
            vectordb.add_documents(batch)
            print(f"      ✅ 배치 {i+1}/{total_batches} 완료 ({end_idx}/{len(chunks)} 청크)")
        
        print(f"\n✅ 벡터 DB 구축 완료!")
        print(f"   📍 저장 위치: {VECTOR_DB_DIR}")
        print(f"   📦 컬렉션 크기: {vectordb._collection.count()} 항목")
        
        return vectordb
        
    except Exception as e:
        print(f"\n❌ 벡터 DB 구축 실패: {e}")
        raise


def test_search(vectordb):
    """검색 테스트"""
    print(f"\n🔍 검색 테스트...")
    
    test_queries = [
        "자살 위기 상황에서 어떻게 대응해야 하나요?",
        "불안 증상을 가진 내담자를 어떻게 상담하나요?",
        "정신건강 위기 개입 절차는?"
    ]
    
    for query in test_queries:
        print(f"\n   💬 질문: {query}")
        results = vectordb.similarity_search(query, k=2)
        
        if results:
            print(f"   ✅ 검색 결과 ({len(results)}개):")
            for i, doc in enumerate(results, 1):
                content_preview = doc.page_content[:150].replace('\n', ' ')
                print(f"      [{i}] {doc.metadata.get('source_file', 'Unknown')}")
                print(f"          {content_preview}...")
        else:
            print(f"   ⚠️  검색 결과 없음")


def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("🚀 RAG-D 상담 매뉴얼 벡터 DB 구축 시작")
    print("="*60)
    
    try:
        # 1. PDF 로드
        documents = load_pdfs()
        if not documents:
            print("\n❌ 로드할 PDF가 없습니다. 종료합니다.")
            return
        
        # 2. 문서 분할
        chunks = split_documents(documents)
        
        # 3. 벡터 DB 구축
        vectordb = build_vectordb(chunks)
        
        # 4. 검색 테스트
        test_search(vectordb)
        
        print("\n" + "="*60)
        print("✅ 모든 작업 완료!")
        print("="*60)
        print(f"\n💡 다음 단계:")
        print(f"   1. Docker 재시작: docker compose down && docker compose up --build")
        print(f"   2. 챗봇이 자동으로 상담 매뉴얼 지식을 참조합니다")
        
    except Exception as e:
        print(f"\n❌ 실행 중 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

