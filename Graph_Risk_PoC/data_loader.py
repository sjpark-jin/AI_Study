import pandas as pd
import os

class DataLoader:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        # 컬럼 매핑 (한글 -> 영문)
        self.col_map = {
            '일자': 'date', '도매상코드': 'wholesaler_code', '병원코드': 'hospital_code',
            '제품코드': 'product_code', '출고수량': 'sales_qty', '출고단가': 'sales_price',
            '처방일월': 'presc_month', '처방수량': 'presc_qty', '환자수추이': 'patient_count',
            '적용시작일': 'start_date', '종료일': 'end_date', '거래처코드': 'hospital_code',
            '적용할인율': 'discount_rate', '반품일자': 'return_date', '반품사유': 'return_reason',
            '반품수량': 'return_qty', '손실액': 'loss_amount'
        }

    def load_excel(self, filename):
        path = os.path.join(self.data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"❌ 파일을 찾을 수 없습니다: {path}")
        
        df = pd.read_excel(path)
        # 컬럼명 영문 변환
        df = df.rename(columns=self.col_map)
        # 결측치 처리 (수치형은 0, 문자열은 'Unknown')
        for col in df.columns:
            if df[col].dtype in ['int64', 'float64']:
                df[col] = df[col].fillna(0)
            else:
                df[col] = df[col].fillna('Unknown')
        return df

    def get_clean_data(self):
        print("🔍 데이터를 로드하고 전처리를 시작합니다...")
        
        # 1. 원본 파일 로드
        sales = self.load_excel('MIS_Sales.xlsx')
        presc = self.load_excel('HOPE_Prescription.xlsx')
        promo = self.load_excel('Discount_Promotion.xlsx')
        ret_hist = self.load_excel('Return_History.xlsx')

        # 2. 날짜 전처리 (MIS_Sales의 'date'에서 연-월 추출)
        sales['date'] = pd.to_datetime(sales['date'])
        sales['year_month'] = sales['date'].dt.strftime('%Y-%m')

        # 3. 월간 출고량 집계 (병원-제품-월 기준)
        sales_monthly = sales.groupby(['hospital_code', 'product_code', 'year_month'])['sales_qty'].sum().reset_index()

        # 4. 시나리오 1을 위한 출고-처방 데이터 병합
        # HOPE_Prescription의 'presc_month' 형식을 'year_month'와 맞춤
        presc['presc_month'] = pd.to_datetime(presc['presc_month']).dt.strftime('%Y-%m')
        
        merged_df = pd.merge(
            sales_monthly, 
            presc, 
            left_on=['hospital_code', 'product_code', 'year_month'],
            right_on=['hospital_code', 'product_code', 'presc_month'],
            how='outer'
        )
        
        # 병합 후 결측치 0으로 채우기 (출고는 있으나 처방이 없는 경우 등)
        merged_df[['sales_qty', 'presc_qty']] = merged_df[['sales_qty', 'presc_qty']].fillna(0)
        
        # 불일치 갭(Gap) 계산
        merged_df['mismatch_gap'] = merged_df['sales_qty'] - merged_df['presc_qty']

        print(f"✅ 데이터 전처리 완료 (병합된 레코드 수: {len(merged_df)})")
        
        return {
            'merged_analysis': merged_df,
            'sales_raw': sales,
            'promotion': promo,
            'returns': ret_hist
        }

if __name__ == "__main__":
    # 테스트 코드
    loader = DataLoader(data_dir='Graph_Risk_PoC/data')
    data = loader.get_clean_data()
    
    print("\n[병합 데이터 상위 5건]")
    print(data['merged_analysis'].head())
    
    # 시나리오 1 패턴 확인 (H001-P001)
    target = data['merged_analysis'][
        (data['merged_analysis']['hospital_code'] == 'H001') & 
        (data['merged_analysis']['product_code'] == 'P001') &
        (data['merged_analysis']['year_month'] == '2025-01')
    ]
    if not target.empty:
        print("\n[시나리오 1 탐지 테스트: H001-P001-2025-01]")
        print(target[['hospital_code', 'product_code', 'year_month', 'sales_qty', 'presc_qty', 'mismatch_gap']])
