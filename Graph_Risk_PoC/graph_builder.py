import networkx as nx
import matplotlib.pyplot as plt
from data_loader import DataLoader

class GraphBuilder:
    def __init__(self, data_loader):
        self.data_loader = data_loader
        self.G = nx.MultiDiGraph() # 다중 거래 내역 저장을 위해 MultiDiGraph 사용

    def build_graph(self):
        print("🕸️ 데이터로부터 그래프 네트워크를 구축합니다...")
        data = self.data_loader.get_clean_data()
        
        # 1. 노드 추가 (도매상, 병원, 제품)
        self._add_nodes(data)
        
        # 2. 엣지 추가 (출고, 처방, 프로모션, 반품)
        self._add_sales_edges(data['sales_raw'])
        self._add_prescription_edges(data['merged_analysis']) # 정제된 월별 처방 데이터 사용
        self._add_promotion_edges(data['promotion'])
        self._add_return_edges(data['returns'])
        
        print(f"✅ 그래프 구축 완료 (노드: {self.G.number_of_nodes()}개, 엣지: {self.G.number_of_edges()}개)")
        return self.G

    def _add_nodes(self, data):
        # 도매상 노드
        wholesalers = data['sales_raw']['wholesaler_code'].unique()
        for ws in wholesalers:
            self.G.add_node(ws, type='Wholesaler', label=ws)
        
        # 병원 노드
        hospitals = data['sales_raw']['hospital_code'].unique()
        for h in hospitals:
            self.G.add_node(h, type='Hospital', label=h)
            
        # 제품 노드
        products = data['sales_raw']['product_code'].unique()
        for p in products:
            self.G.add_node(p, type='Product', label=p)

    def _add_sales_edges(self, df_sales):
        """도매상 -> 병원 간의 출고 엣지 추가"""
        for _, row in df_sales.iterrows():
            self.G.add_edge(
                row['wholesaler_code'], 
                row['hospital_code'], 
                type='SALE',
                product_code=row['product_code'],
                qty=row['sales_qty'],
                price=row['sales_price'],
                date=row['date']
            )

    def _add_prescription_edges(self, df_merged):
        """병원 -> 제품 간의 처방 엣지 추가"""
        # 처방 데이터가 있는 것들만
        for _, row in df_merged[df_merged['presc_qty'] > 0].iterrows():
            self.G.add_edge(
                row['hospital_code'], 
                row['product_code'], 
                type='PRESCRIPTION',
                qty=row['presc_qty'],
                month=row['year_month']
            )

    def _add_promotion_edges(self, df_promo):
        """병원 -> 제품 간의 프로모션 엣지 추가"""
        for _, row in df_promo.iterrows():
            self.G.add_edge(
                row['hospital_code'], 
                row['product_code'], 
                type='PROMOTION',
                discount_rate=row['discount_rate'],
                start_date=row['start_date'],
                end_date=row['end_date']
            )

    def _add_return_edges(self, df_return):
        """병원 -> 제품 간의 반품 엣지 추가"""
        for _, row in df_return.iterrows():
            self.G.add_edge(
                row['hospital_code'], 
                row['product_code'], 
                type='RETURN',
                qty=row['return_qty'],
                reason=row['return_reason'],
                date=row['return_date'],
                loss=row['loss_amount']
            )

if __name__ == "__main__":
    loader = DataLoader(data_dir='Graph_Risk_PoC/data')
    builder = GraphBuilder(loader)
    G = builder.build_graph()
    
    # 특정 병원의 연결 상태 확인 (H002 - 시나리오 2 대상)
    print("\n[병원 H002의 관련 엣지 상세 분석]")
    edges = G.edges('H002', data=True)
    for u, v, data in edges:
        print(f" -> {v} 연결 | 유형: {data['type']} | 속성: { {k:v for k,v in data.items() if k!='type'} }")
