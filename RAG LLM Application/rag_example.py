# =============================================================================
# [초보자를 위한 RAG(검색 증강 생성) 예제 코드]
#
# 이 코드는 RAG(Retrieval-Augmented Generation)의 핵심 과정을 단계별로 보여줍니다.
# RAG는 AI에게 "참고할 책(문서)"을 주고, 그 책 내용을 바탕으로 질문에 답하게 하는 기술입니다.
#
# [실행 방법]
# 1. .env 파일에 OPENAI_API_KEY를 설정하세요.
# 2. 터미널에서 다음 명령어로 실행하세요: uv run rag_example.py
# =============================================================================

import os
from dotenv import load_dotenv

# 1. 환경 변수 로드 (API 키 불러오기)
# .env 파일에 저장된 비밀번호(API Key)를 프로그램으로 가져옵니다.
load_dotenv()

# API 키가 잘 설정되었는지 확인합니다.
if not os.getenv("OPENAI_API_KEY"):
    print("❌ 오류: OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    exit()
else:
    print("✅ API 키가 확인되었습니다.")

# =============================================================================
# 단계 1: 문서 로드 (Document Loading)
# AI에게 읽힐 데이터를 준비하는 단계입니다.
# 여기서는 예시로 간단한 텍스트 파일을 만들어 사용하겠습니다.
# =============================================================================
print("\n[단계 1] 문서 로드 중...")

# 예제용 텍스트 데이터 (AI가 공부할 내용)
example_text = """
RAG(Retrieval-Augmented Generation)는 대규모 언어 모델(LLM)의 출력을 최적화하는 기술입니다.
LLM은 학습 데이터에 포함되지 않은 최신 정보나 비공개 정보를 알 수 없습니다.
RAG는 신뢰할 수 있는 외부 지식 베이스에서 정보를 검색(Retrieval)하여 LLM에 제공합니다.
이를 통해 LLM은 더 정확하고 최신 정보에 기반한 답변을 생성(Generation)할 수 있습니다.
RAG의 주요 구성 요소는 문서 로드, 텍스트 분할, 임베딩, 벡터 저장소, 검색기, 생성기입니다.
"""

# 파일로 저장 (실제 환경에서는 PDF, Word, 웹페이지 등을 읽어옵니다)
with open("example_data.txt", "w", encoding="utf-8") as f:
    f.write(example_text)

from langchain_community.document_loaders import TextLoader

# [함수 설명] TextLoader: 텍스트 파일을 읽어오는 도구입니다.
loader = TextLoader("example_data.txt", encoding="utf-8")
documents = loader.load()

print(f"✅ 문서를 성공적으로 읽었습니다. (길이: {len(documents[0].page_content)}자)")

# =============================================================================
# 단계 2: 텍스트 분할 (Text Splitting)
# 긴 문서를 AI가 한 번에 처리하기 좋게 작은 조각(Chunk)으로 나눕니다.
# =============================================================================
print("\n[단계 2] 텍스트 분할 중...")

from langchain_text_splitters import RecursiveCharacterTextSplitter

# [함수 설명] RecursiveCharacterTextSplitter: 문맥을 유지하며 문장을 자르는 도구입니다.
# - chunk_size=100: 한 조각의 최대 길이를 100자로 설정합니다.
# - chunk_overlap=20: 조각끼리 20자씩 겹치게 하여 문맥이 끊기지 않게 합니다.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
split_docs = text_splitter.split_documents(documents)

print(f"✅ 문서를 {len(split_docs)}개의 조각으로 나누었습니다.")
for i, doc in enumerate(split_docs):
    print(f"   - 조각 {i+1}: {doc.page_content[:30]}...") # 앞 30자만 출력

# =============================================================================
# 단계 3: 임베딩 & 벡터 저장소 (Embedding & Vector Store)
# 문자를 숫자로 변환(임베딩)하여 검색하기 좋게 저장소(Vector Store)에 넣습니다.
# =============================================================================
print("\n[단계 3] 벡터 저장소 생성 중...")

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

# [함수 설명] OpenAIEmbeddings: 문장을 AI가 이해할 수 있는 숫자 벡터로 변환합니다.
embeddings = OpenAIEmbeddings()

# [함수 설명] FAISS: 페이스북에서 만든 빠르고 효율적인 벡터 검색 라이브러리입니다.
# 문장 조각들을 벡터로 변환하여 저장합니다.
vectorstore = FAISS.from_documents(documents=split_docs, embedding=embeddings)

print("✅ 데이터를 벡터 저장소(FAISS)에 저장했습니다.")

# =============================================================================
# 단계 4: 검색기 생성 (Retriever)
# 질문과 가장 관련된 문서를 찾아주는 검색기를 만듭니다.
# =============================================================================
print("\n[단계 4] 검색기(Retriever) 설정 중...")

# [함수 설명] as_retriever: 벡터 저장소를 검색기로 변환합니다.
retriever = vectorstore.as_retriever()

print("✅ 검색기가 준비되었습니다.")

# =============================================================================
# 단계 5: 프롬프트 & 체인 생성 (Prompt & Chain)
# 검색된 내용과 질문을 합쳐서 AI에게 전달할 양식(Prompt)을 만들고 연결합니다.
# =============================================================================
print("\n[단계 5] AI 모델 연결 중...")

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# [함수 설명] ChatOpenAI: OpenAI의 GPT 모델을 불러옵니다.
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# 프롬프트 템플릿 정의
# {context}: 검색된 문서 내용이 들어갈 자리
# {question}: 사용자의 질문이 들어갈 자리
template = """
당신은 친절한 AI 어시스턴트입니다. 아래의 [참고 문서]를 바탕으로 질문에 답변해주세요.
만약 문서에 없는 내용이라면 "문서에 해당 내용이 없습니다"라고 답해주세요.

[참고 문서]
{context}

질문: {question}
답변:
"""

prompt = PromptTemplate.from_template(template)

# [함수 설명] format_docs: 검색된 여러 문서 조각을 하나의 긴 문자열로 합칩니다.
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 체인(Chain) 구성: 데이터가 흐르는 파이프라인을 만듭니다.
# 1. retriever가 관련 문서를 찾음 -> format_docs로 정리
# 2. RunnablePassthrough는 질문을 그대로 통과시킴
# 3. prompt에 문서와 질문을 넣음
# 4. llm이 답변 생성
# 5. StrOutputParser가 결과를 문자열로 깔끔하게 변환
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

print("✅ 모든 준비가 완료되었습니다!")

# =============================================================================
# 단계 6: 실행 및 테스트 (Execution)
# 실제로 질문을 던지고 AI가 어떻게 답하는지 확인합니다.
# =============================================================================
question = "RAG의 주요 구성 요소는 무엇인가요?"
print(f"\n[질문] {question}")
print("-" * 50)

# 체인 실행
response = rag_chain.invoke(question)

print(f"[답변]\n{response}")
print("-" * 50)

# 임시 파일 삭제
if os.path.exists("example_data.txt"):
    os.remove("example_data.txt")
