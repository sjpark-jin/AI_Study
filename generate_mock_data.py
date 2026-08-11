import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 1. 폴더 구조 생성
os.makedirs('Graph_Risk_PoC/data', exist_ok=True)

# 설정값
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 12, 31)
HOSPITALS = [f'H{i:03d}' for i in range(1, 51)]  # 병원 50개
WHOLESALERS = [f'W{i:03d}' for i in range(1, 6)] # 도매상 5개
PRODUCTS = [f'P{i:03d}' for i in range(1, 21)]   # 제품 20개

def generate_data():
    print("🚀 가짜(Mock) 데이터 생성을 시작합니다...")

    # --- 1. MIS_Sales.xlsx (출고 데이터) ---
    sales_data = []
    current_date = START_DATE
    while current_date <= END_DATE:
        # 매일 약 10~20건의 랜덤 출고 발생
        for _ in range(np.random.randint(10, 21)):
            h_code = np.random.choice(HOSPITALS)
            p_code = np.random.choice(PRODUCTS)
            qty = np.random.randint(10, 101)
            
            # 시나리오 1용: 특정 병원(H001)에 특정 제품(P001)을 2025년 1월에 대량 밀어넣기
            if h_code == 'H001' and p_code == 'P001' and current_date.year == 2025 and current_date.month == 1:
                qty = np.random.randint(500, 1000)

            sales_data.append({
                '일자': current_date.strftime('%Y-%m-%d'),
                '도매상코드': np.random.choice(WHOLESALERS),
                '병원코드': h_code,
                '제품코드': p_code,
                '출고수량': qty,
                '출고단가': np.random.randint(10000, 50001)
            })
        current_date += timedelta(days=1)
    
    df_sales = pd.DataFrame(sales_data)
    df_sales.to_excel('Graph_Risk_PoC/data/MIS_Sales.xlsx', index=False)
    print("✅ MIS_Sales.xlsx 생성 완료")

    # --- 2. HOPE_Prescription.xlsx (처방 데이터) ---
    presc_data = []
    # 월별 데이터 생성
    for year in range(2023, 2026):
        for month in range(1, 13):
            for h_code in HOSPITALS:
                for p_code in PRODUCTS:
                    avg_qty = np.random.randint(5, 50)
                    
                    # 시나리오 1용: H001-P001은 출고는 많지만 처방은 그대로인 상황 연출
                    if h_code == 'H001' and p_code == 'P001' and year == 2025 and month == 1:
                        avg_qty = 40 # 출고량(500~1000) 대비 현저히 낮음

                    presc_data.append({
                        '처방일월': f'{year}-{month:02d}',
                        '병원코드': h_code,
                        '제품코드': p_code,
                        '처방수량': avg_qty,
                        '환자수추이': np.random.randint(10, 100)
                    })
    
    df_presc = pd.DataFrame(presc_data)
    df_presc.to_excel('Graph_Risk_PoC/data/HOPE_Prescription.xlsx', index=False)
    print("✅ HOPE_Prescription.xlsx 생성 완료")

    # --- 3. Discount_Promotion.xlsx (프로모션 데이터) ---
    # 가끔 발생하는 고할인 이벤트
    promo_data = [
        # 시나리오 2용: H002-P002 고할인율 적용 (2025년 2월)
        {'적용시작일': '2025-02-01', '종료일': '2025-02-28', '거래처코드': 'H002', '제품코드': 'P002', '적용할인율': 0.35}
    ]
    # 나머지 랜덤 프로모션
    for _ in range(30):
        s_date = START_DATE + timedelta(days=np.random.randint(0, 1000))
        promo_data.append({
            '적용시작일': s_date.strftime('%Y-%m-%d'),
            '종료일': (s_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            '거래처코드': np.random.choice(HOSPITALS),
            '제품코드': np.random.choice(PRODUCTS),
            '적용할인율': round(np.random.uniform(0.05, 0.20), 2)
        })
    
    df_promo = pd.DataFrame(promo_data)
    df_promo.to_excel('Graph_Risk_PoC/data/Discount_Promotion.xlsx', index=False)
    print("✅ Discount_Promotion.xlsx 생성 완료")

    # --- 4. Return_History.xlsx (반품 데이터) ---
    return_data = [
        # 시나리오 2용: 고할인율(H002-P002) 적용 물량이 2025년 4월에 대량 반품됨
        {'반품일자': '2025-04-15', '거래처코드': 'H002', '제품코드': 'P002', '반품사유': '재고과다', '반품수량': 850, '손실액': 15000000}
    ]
    # 나머지 랜덤 반품 (매달 1~2건)
    for _ in range(50):
        r_date = START_DATE + timedelta(days=np.random.randint(0, 1000))
        return_data.append({
            '반품일자': r_date.strftime('%Y-%m-%d'),
            '거래처코드': np.random.choice(HOSPITALS),
            '제품코드': np.random.choice(PRODUCTS),
            '반품사유': np.random.choice(['유효기간경과', '포장파손', '단종']),
            '반품수량': np.random.randint(1, 20),
            '손실액': np.random.randint(100000, 1000000)
        })

    df_return = pd.DataFrame(return_data)
    df_return.to_excel('Graph_Risk_PoC/data/Return_History.xlsx', index=False)
    print("✅ Return_History.xlsx 생성 완료")

if __name__ == "__main__":
    generate_data()
    print("\n✨ 모든 PoC용 Mock 데이터가 Graph_Risk_PoC/data 폴더에 저장되었습니다.")
