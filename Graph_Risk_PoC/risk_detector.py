import pandas as pd
import networkx as nx
from data_loader import DataLoader
from graph_builder import GraphBuilder

class RiskDetector:
    def __init__(self, graph):
        self.G = graph
        self.risk_scores = {} # {node_id: score}

    def run_analysis(self):
        print("🔍 그래프 기반 리스크 탐지 시나리오를 실행합니다...")
        
        # 병원 노드들에 대해 개별 리스크 산정
        hospital_nodes = [n for n, d in self.G.nodes(data=True) if d.get('type') == 'Hospital']
        
        for hospital in hospital_nodes:
            score = 0
            
            # 시나리오 1: 출고-처방 불일치 (Mismatch) 탐지
            score += self._detect_mismatch_scenario(hospital)
            
            # 시나리오 2: 고할인율-반품 연계 (Cherry-picking) 탐지
            score += self._detect_cherry_picking_scenario(hospital)
            
            # 스코어 정규화 (최대 100점)
            self.risk_scores[hospital] = min(score, 100)

        # 도매상 리스크 산정 (자신이 공급하는 병원들의 평균 리스크 반영)
        self._calculate_wholesaler_risk()

        # 결과 정렬 및 반환
        return self._format_results()

    def _detect_mismatch_scenario(self, hospital):
        """시나리오 1: 특정 제품에 대해 출고량은 많으나 처방량이 현저히 적은 경우"""
        penalty = 0
        
        # 병원의 모든 출고(SALE)와 처방(PRESCRIPTION) 엣지 분석
        sales_qty = {}
        presc_qty = {}
        
        # 도매상 -> 병원 (Inbound)
        for u, v, data in self.G.in_edges(hospital, data=True):
            if data['type'] == 'SALE':
                p_code = data['product_code']
                sales_qty[p_code] = sales_qty.get(p_code, 0) + data['qty']
                
        # 병원 -> 제품 (Outbound)
        for u, v, data in self.G.out_edges(hospital, data=True):
            if data['type'] == 'PRESCRIPTION':
                p_code = v # Product 노드
                presc_qty[p_code] = presc_qty.get(p_code, 0) + data['qty']
        
        # 갭 분석
        for p_code, s_qty in sales_qty.items():
            p_qty = presc_qty.get(p_code, 0)
            if s_qty > p_qty * 3 and s_qty > 100: # 처방 대비 3배 이상 & 최소 100개 이상
                gap_ratio = s_qty / max(p_qty, 1)
                penalty += min(gap_ratio * 5, 40) # 최대 40점 페널티
        
        return penalty

    def _detect_cherry_picking_scenario(self, hospital):
        """시나리오 2: 고할인율 프로모션 적용 후 대량 반품이 발생하는 패턴"""
        penalty = 0
        
        # 병원의 프로모션과 반품 내역 조회
        promo_products = []
        for u, v, data in self.G.out_edges(hospital, data=True):
            if data['type'] == 'PROMOTION' and data['discount_rate'] >= 0.3: # 30% 이상 고할인
                promo_products.append(v)
                
        for u, v, data in self.G.out_edges(hospital, data=True):
            if data['type'] == 'RETURN' and v in promo_products:
                if data['qty'] > 500: # 대량 반품 발생 시
                    penalty += 50 # 시나리오 2는 매우 의심스러우므로 높은 점수 부여
        
        return penalty

    def _calculate_wholesaler_risk(self):
        """도매상은 관리하는 병원들의 리스크 수준에 비례하여 스코어링"""
        wholesaler_nodes = [n for n, d in self.G.nodes(data=True) if d.get('type') == 'Wholesaler']
        
        for ws in wholesaler_nodes:
            supplied_hospitals = [v for u, v in self.G.out_edges(ws) if self.G.nodes[v]['type'] == 'Hospital']
            if supplied_hospitals:
                avg_risk = sum(self.risk_scores.get(h, 0) for h in supplied_hospitals) / len(supplied_hospitals)
                self.risk_scores[ws] = round(avg_risk, 1)

    def _format_results(self):
        results = []
        for node, score in self.risk_scores.items():
            node_type = self.G.nodes[node]['type']
            results.append({
                'Node_ID': node,
                'Type': node_type,
                'Risk_Score': score
            })
        
        df = pd.DataFrame(results).sort_values(by='Risk_Score', ascending=False)
        return df

if __name__ == "__main__":
    # 통합 테스트 실행 (루트 폴더 실행 기준)
    loader = DataLoader(data_dir='Graph_Risk_PoC/data')
    builder = GraphBuilder(loader)
    G = builder.build_graph()
    
    detector = RiskDetector(G)
    risk_report = detector.run_analysis()
    
    print("\n" + "="*50)
    print("🚩 PoC 최종 리스크 리포트 (상위 10개)")
    print("="*50)
    print(risk_report.head(10))
    print("="*50)
    
    # 특정 고위험 노드 분석 결과 확인
    top_risk = risk_report.iloc[0]
    print(f"\n💡 알람 탐지: {top_risk['Node_ID']} ({top_risk['Type']})가 {top_risk['Risk_Score']}점으로 가장 위험합니다.")
    print("기초 데이터 매핑을 통해 세부 원인(시나리오 1, 2) 확인이 필요합니다.")
