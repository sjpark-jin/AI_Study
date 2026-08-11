import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import DataLoader
from graph_builder import GraphBuilder
from risk_detector import RiskDetector

# 페이지 설정
st.set_page_config(page_title="MIS 리스크 탐지 PoC 대시보드", layout="wide")

# 1. 데이터 로드 및 분석 수행
@st.cache_data
def get_analysis_data():
    # 루트 폴더 기준 실행 경로 지원 (Data_dir 설정은 실행 환경에 따라 유동적)
    loader = DataLoader(data_dir='Graph_Risk_PoC/data')
    builder = GraphBuilder(loader)
    G = builder.build_graph()
    
    detector = RiskDetector(G)
    risk_report = detector.run_analysis()
    
    # 세부 분석을 위한 원본 데이터 확보
    raw_data = loader.get_clean_data()
    return risk_report, raw_data, G

st.title("🛡️ MIS 리스크 네트워크 모니터링 PoC")
st.markdown("---")

try:
    risk_report, raw_data, G = get_analysis_data()
except Exception as e:
    st.error(f"❌ 데이터를 로드하는 중 오류가 발생했습니다: {e}")
    st.info("💡 `generate_mock_data.py`를 먼저 실행하여 엑셀 파일을 생성해 주세요.")
    st.stop()

# 2. 대시보드 레이아웃 (좌측: 리스크 리스트, 우측: 상세 분석)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🚩 고위험군 탐지 리스트 (Top 10)")
    # 리스트에서 필터링
    node_type = st.radio("노드 유형 필터", ["전체", "Hospital", "Wholesaler"])
    if node_type != "전체":
        display_df = risk_report[risk_report['Type'] == node_type]
    else:
        display_df = risk_report
    
    st.dataframe(
        display_df.head(10), 
        use_container_width=True,
        hide_index=True
    )
    
    selected_node = st.selectbox(
        "🔎 상세 분석할 노드 선택", 
        display_df['Node_ID'].tolist(),
        index=0 if not display_df.empty else None
    )

with col2:
    if selected_node:
        st.subheader(f"📊 상세 분석 리포트: {selected_node}")
        score = risk_report[risk_report['Node_ID'] == selected_node]['Risk_Score'].values[0]
        st.metric("최종 리스크 스코어", f"{score}점", delta="고위험" if score > 30 else "정상")
        
        # 병원일 경우 시나리오별 시각화
        if risk_report[risk_report['Node_ID'] == selected_node]['Type'].values[0] == 'Hospital':
            
            tab1, tab2, tab3 = st.tabs(["[시나리오 1] 출고-처방 갭", "[시나리오 2] 할인-반품 연계", "🔗 네트워크 관계"])
            
            with tab1:
                st.write("**시나리오 1: 출고량 vs 처방량 불일치 트렌드 (월별)**")
                merged = raw_data['merged_analysis']
                node_trend = merged[merged['hospital_code'] == selected_node].sort_values('year_month')
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=node_trend['year_month'], y=node_trend['sales_qty'], name="출고량(MIS)"))
                fig.add_trace(go.Scatter(x=node_trend['year_month'], y=node_trend['presc_qty'], name="처방량(HOPE)", line=dict(color='red', width=3)))
                fig.update_layout(title=f"{selected_node} 월별 수급 현황", barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
            with tab2:
                st.write("**시나리오 2: 고할인율 프로모션 및 반품 이력**")
                # 프로모션 이력
                promo = raw_data['promotion'][raw_data['promotion']['hospital_code'] == selected_node]
                # 반품 이력
                returns = raw_data['returns'][raw_data['returns']['hospital_code'] == selected_node]
                
                if not promo.empty:
                    st.write("✅ 적용된 프로모션 리스트")
                    st.dataframe(promo, use_container_width=True)
                if not returns.empty:
                    st.write("🔴 반품/폐기 발생 이력 (근거 데이터)")
                    st.dataframe(returns, use_container_width=True)
                if promo.empty and returns.empty:
                    st.info("해당 병원은 특이 프로모션이나 반품 이력이 없습니다.")

            with tab3:
                st.write("**병원 거래 네트워크 연결망**")
                # 인접 노드 리스트업
                in_edges = G.in_edges(selected_node, data=True)
                out_edges = G.out_edges(selected_node, data=True)
                
                st.write(f"🔹 **{selected_node}** 에 제품을 공급하는 도매상:")
                suppliers = list(set([u for u, v, d in in_edges]))
                st.write(", ".join(suppliers))
                
                st.write(f"🔸 **{selected_node}** 에서 처방/반품된 주요 제품:")
                products = list(set([v for u, v, d in out_edges if G.nodes[v]['type'] == 'Product']))
                st.write(", ".join(products[:10]) + ("..." if len(products) > 10 else ""))

        else: # 도매상일 경우
            st.write("해당 도매상이 관리하는 병원들의 리스크 분포를 분석 중입니다.")
            supplied_h = [v for u, v in G.out_edges(selected_node) if G.nodes[v]['type'] == 'Hospital']
            ws_risk = risk_report[risk_report['Node_ID'].isin(supplied_h)]
            
            fig = px.pie(ws_risk, values='Risk_Score', names='Node_ID', title=f"{selected_node} 공급처 리스크 비중")
            st.plotly_chart(fig, use_container_width=True)

# 3. 사이드바 - 피드백 세션 (To-Be R&R 반영)
with st.sidebar:
    st.markdown("### 📝 리스크 처리 결과 기록 (R&R)")
    if selected_node:
        st.write(f"현재 선택: **{selected_node}**")
        status = st.radio("조치 결정", ["대기 중", "이상 징후 확정 (출고 통제)", "정상 거래 확인 (보류)", "추가 모니터링"])
        comment = st.text_area("조치 근거 및 메모", placeholder="예: H002는 2025-02 프로모션 직후 반품 대량 발생으로 체리피킹 의심됨.")
        if st.button("결과 저장"):
            st.success(f"{selected_node}에 대한 '{status}' 판정이 저장되었습니다.")
            st.caption("(PoC 환경에서는 메모리에만 임시 저장됩니다.)")
