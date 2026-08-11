# -*- coding: utf-8 -*-
# =============================================================================
# [Streamlit 기반 대화형 AI 챗봇 인터페이스]
#
# 이 코드는 Streamlit을 사용하여 사용자 친화적인 챗봇 UI를 구축하고, 
# OpenAI의 LLM 모델과 실시간 스트리밍 방식으로 연동하는 전체 과정을 담고 있습니다.
# =============================================================================

import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_teddynote import logging

# 환경 변수 및 인증 설정
from dotenv import load_dotenv

# [코드 설명] .env 파일에 저장된 API_KEY를 시스템 환경 변수로 로드합니다.
# override=True 설정은 기존 환경 변수보다 .env 파일의 값을 우선시합니다.
load_dotenv(override=True)

# [코드 설명] LangSmith 추적 설정을 통해 LLM 호출 로그 및 성능을 모니터링합니다.
logging.langsmith("LangGraph-Tutorial")

# 어플리케이션 레이아웃 설정
st.set_page_config(page_title="AI 챗봇", page_icon="💬")
st.title("💬 AI 챗봇 서비스")

# =============================================================================
# 세션 상태 초기화 (Session State Management)
# Streamlit은 상호작용 시마다 스크립트가 처음부터 재실행되므로, 
# 대화 기록을 유지하기 위해 st.session_state라는 메모리 공간을 사용합니다.
# =============================================================================
if "messages" not in st.session_state:
    # [변수 설명] st.session_state["messages"]: 대화 전체 흐름을 저장하는 ChatMessage 객체 리스트입니다.
    # 각 객체는 role(user/assistant)과 content(메시지 내용)를 가집니다.
    st.session_state["messages"] = []

# =============================================================================
# 사이드바 UI 구성 (Sidebar Configuration)
# 모델의 파라미터와 시스템 페르소나를 실시간으로 제어할 수 있는 컨트롤 패널입니다.
# =============================================================================
with st.sidebar:
    st.header("🛠️ 모델 설정")
    
    # [변수 설명] clear_btn: 사용자가 대화 내역을 초기화하기 위해 클릭하는 버튼 객체입니다.
    clear_btn = st.button("🗑️ 대화 초기화", help="현재 세션의 모든 대화 기록을 삭제합니다.")

    # [변수 설명] selected_model: 사용자가 선택한 OpenAI의 언어 모델 식별자입니다.
    selected_model = st.selectbox(
        "✅ LLM 모델 선택",
        ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        index=0,
        help="사용할 인공지능 모델의 종류를 선택하세요. (모델에 따라 성능과 비용이 다름)"
    )

    # [변수 설명] temperature: 모델 답변의 무작위성(창의성)을 조절하는 수치입니다. (0.0~2.0)
    temperature = st.slider(
        "🌡️ 창의성 (Temperature)",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="0에 가까울수록 사실 기반의 일관된 답변을, 2에 가까울수록 창의적이고 다양한 답변을 생성합니다."
    )

    # [변수 설명] response_length: 답변의 상세 정도를 결정하는 사용자 선택 옵션입니다.
    response_length = st.selectbox(
        "📏 답변 길이 설정",
        ["간단", "보통", "자세함", "매우 자세함"],
        index=1,
        help="AI가 생성할 답변의 물리적 길이를 제어합니다."
    )

    st.divider()

    # [변수 설명] system_prompt: AI에게 부여할 역할(Persona)과 행동 지침(Instruction)입니다.
    st.subheader("⚙️ 시스템 프롬프트")
    system_prompt = st.text_area(
        "AI의 역할 정의",
        value="당신은 도움이 되고 친근한 AI 어시스턴트입니다. 사용자의 질문에 정확하고 유용한 답변을 제공하세요.",
        height=150,
        help="AI가 어떤 말투와 지식을 가지고 답변할지 정의할 수 있습니다."
    )


# =============================================================================
# 헬퍼 함수 정의 (Helper Functions)
# =============================================================================

def print_messages():
    """
    [함수 설명] 세션 상태에 저장된 모든 대화 기록을 화면에 시각적으로 렌더링합니다.
    st.chat_message 함수를 통해 사용자(User)와 AI(Assistant)의 메시지를 구분하여 출력합니다.
    """
    if st.session_state["messages"]:
        for chat_message in st.session_state["messages"]:
            st.chat_message(chat_message.role).write(chat_message.content)
    else:
        st.info("💭 대화를 시작해 보세요! 궁금한 점을 입력해 주세요.")


def add_message(role, message):
    """
    [함수 설명] 새로운 메시지 발생 시 세션 상태 리스트에 저장합니다.
    - role: 'user' 또는 'assistant'
    - message: 실제 텍스트 내용
    """
    st.session_state["messages"].append(ChatMessage(role=role, content=message))


def get_length_instruction(length):
    """
    [함수 설명] 사용자가 선택한 답변 길이 옵션을 LLM이 이해할 수 있는 구체적인 지시문으로 변환합니다.
    """
    length_map = {
        "간단": "간단하고 핵심적인 답변을 1-2문장 내외로 제공하세요.",
        "보통": "적절한 길이로 명확하게 답변하세요. (2-3문단 정도)",
        "자세함": "상세하고 포괄적인 답변을 제공하세요. 예시나 추가 설명을 포함하세요.",
        "매우 자세함": "매우 심층적이고 구체적인 답변을 제공하세요. 가능한 모든 관점과 상세 데이터를 포함하세요.",
    }
    return length_map.get(length, "적절한 길이로 답변하세요.")


def generate_answer(user_input, system_prompt, model_name, temperature, response_length):
    """
    [함수 설명] 최종 프롬프트를 구성하고 OpenAI LLM으로부터 답변을 생성(스트리밍)합니다.
    - user_input: 사용자의 질문 텍스트
    - model_name: 선택된 모델 ID
    - response: 스트리밍 응답을 생성하는 제네레이터 객체
    """
    try:
        # LLM 모델 인스턴스화
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
        )

        # 시스템 프롬프트 보강: 사용자의 설정값(답변 길이)을 프롬프트에 동적으로 반영
        length_instr = get_length_instruction(response_length)
        # [변수 설명] final_system_msg: 기본 페르소나와 출력 형식이 결합된 최종 지시문입니다.
        final_system_msg = f"{system_prompt}\n\n[출력 지침]: {length_instr}"

        # 메시지 시퀀스 구성 (SystemMessage -> HumanMessage 순서 권장)
        messages = [
            SystemMessage(content=final_system_msg),
            HumanMessage(content=user_input),
        ]

        # [코드 설명] llm.stream()을 사용하여 답변이 생성되는 대로 즉시 화면에 뿌려줄 수 있게 합니다.
        return llm.stream(messages)

    except Exception as e:
        # 예외 처리: API 키 오류, 네트워크 문제 등을 포착하여 에러를 던집니다.
        raise RuntimeError(f"LLM 호출 중 오류 발생: {e}")


# =============================================================================
# 메인 로직 실행 (Main App Logic)
# =============================================================================

# [이벤트 처리] 초기화 버튼 클릭 시 세션 데이터를 비우고 앱을 리프레시합니다.
if clear_btn:
    st.session_state["messages"] = []
    st.rerun()

# 기존 대화 히스토리 출력
print_messages()

# [변수 설명] user_input: 채팅 입력창에 사용자가 타이핑한 텍스트입니다.
user_input = st.chat_input("💬 AI에게 궁금한 것을 물어보세요!")

# 사용자 입력이 감지되면 실행
if user_input:
    try:
        # 1. 사용자 질문을 화면에 즉시 표시
        st.chat_message("user").write(user_input)

        # 2. AI 답변 생성 및 스트리밍 처리
        with st.chat_message("assistant"):
            # [변수 설명] stream_response: 모델로부터 실시간으로 전달받는 데이터 스트림입니다.
            stream_response = generate_answer(
                user_input=user_input,
                system_prompt=system_prompt,
                model_name=selected_model,
                temperature=temperature,
                response_length=response_length,
            )
            # st.write_stream을 사용하여 타이핑 효과와 함께 답변을 표시합니다.
            full_answer = st.write_stream(stream_response)

        # 3. 대화 쌍(질문-답변)을 세션 상태에 영구 저장
        add_message("user", user_input)
        add_message("assistant", full_answer)

    except Exception as e:
        st.error(f"❌ 답변 생성 중 문제가 발생했습니다: {str(e)}")
        st.info("💡 API 키 설정이 올바른지 확인해 보세요.")

# 하단 설정 정보 요약 (디버깅 및 사용자 확인용)
with st.sidebar:
    st.divider()
    st.markdown("### 📊 현재 설정 요약")
    st.caption(f"**모델:** `{selected_model}`")
    st.caption(f"**Temperature:** `{temperature}`")
    st.caption(f"**스타일:** `{response_length}`")
