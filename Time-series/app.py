import streamlit as st
import pandas as pd
from utils import load_data

# ==========================================
# 1. 페이지 설정
# ==========================================
# Streamlit 앱의 기본 설정을 정의합니다.
# page_title: 브라우저 탭에 표시될 제목
# layout="wide": 화면 전체 너비를 사용하도록 설정
st.set_page_config(
    page_title="시계열 데이터 교육 앱",
    page_icon="📈",
    layout="wide"
)

# ==========================================
# 2. 앱 제목 및 소개
# ==========================================
st.title("📈 초보자를 위한 시계열 데이터 분석 & 예측")
st.markdown("""
이 앱은 **COVID-19 데이터**를 활용하여 시계열 데이터의 기초부터 딥러닝 모델링까지 학습할 수 있도록 구성되었습니다.
좌측 사이드바를 통해 단계를 선택하세요.

### 📚 학습 목표
1. **시계열 데이터**의 구조와 특성을 이해합니다.
2. **전처리** 과정(결측치 처리, 스케일링, 윈도우 생성)을 직접 조작하며 배웁니다.
3. **기초 모델(이동평균, 선형회귀)**과 **딥러닝(LSTM)**이 어떻게 미래를 예측하는지 실습합니다.
""")

# ==========================================
# 3. 사이드바 및 데이터 로드
# ==========================================
st.sidebar.title("학습 단계")
# 사용자가 학습 단계를 선택할 수 있는 라디오 버튼
step = st.sidebar.radio("이동하기", ["1. 데이터 소개 및 시각화", "2. 데이터 전처리", "3. 모델링 및 예측"])

st.sidebar.divider()
st.sidebar.header("데이터 선택")

# 데이터 로드 함수 호출 (utils.py에 정의됨)
DATA_PATH = 'COVID19.csv'
df = load_data(DATA_PATH)

if df.empty:
    st.error("데이터를 불러오는데 실패했습니다. 경로와 인코딩을 확인해주세요.")
else:
    # ------------------------------------------
    # 전역 데이터 필터링
    # ------------------------------------------
    # 사용자가 분석하고 싶은 데이터의 범주를 선택합니다.
    categories = df['Category'].unique()
    selected_category = st.sidebar.selectbox("구분 선택 (Category)", categories)
    
    statuses = df['Status'].unique()
    selected_status = st.sidebar.selectbox("상태 선택 (Status)", statuses)
    
    # 선택한 조건에 맞는 데이터만 필터링하고 날짜순으로 정렬합니다.
    # 시계열 데이터는 '시간의 순서'가 중요하므로 정렬이 필수적입니다.
    filtered_df = df[(df['Category'] == selected_category) & (df['Status'] == selected_status)].copy()
    filtered_df = filtered_df.sort_values('Date')

    # ==========================================
    # 단계 1: 데이터 소개 및 시각화
    # ==========================================
    if step == "1. 데이터 소개 및 시각화":
        st.header("1. 데이터 소개 및 시각화")
        
        st.subheader("원본 데이터 확인")
        st.markdown("불러온 CSV 파일의 상위 5개 행을 보여줍니다.")
        st.dataframe(df.head())
        
        st.subheader("데이터 구조")
        st.write(f"행 수(Rows): {df.shape[0]}, 열 수(Columns): {df.shape[1]}")
        st.write("컬럼 정보:", df.columns.tolist())
        
        st.subheader("선택된 데이터 시각화")
        st.markdown(f"**{selected_category} - {selected_status}** 데이터의 시간에 따른 변화를 그래프로 확인합니다.")
        
        if 'Date' in filtered_df.columns and 'Value' in filtered_df.columns:
            import plotly.express as px
            # Plotly를 사용하여 인터랙티브한 선 그래프를 그립니다.
            fig = px.line(filtered_df, x='Date', y='Value', title=f'{selected_category} - {selected_status} 시계열 추이')
            st.plotly_chart(fig, use_container_width=True)
            
        st.divider()
        
        st.header("시계열 데이터의 구성 요소")
        st.markdown("""
        시계열 데이터($Y_t$)는 보통 다음 세 가지 요소의 결합으로 설명됩니다 (가법 모형):
        
        $$
        Y_t = T_t + S_t + R_t
        $$
        
        1. **추세 ($T_t$)**: 장기적으로 데이터가 증가하거나 감소하는 경향.
        2. **계절성 ($S_t$)**: 일정한 주기로 반복되는 패턴 (예: 매주 주말 감소, 매년 여름 증가).
        3. **잔차 ($R_t$)**: 추세와 계절성으로 설명되지 않는 무작위 변동(잡음).
        """)
        
        if st.button("시계열 분해 결과 보기"):
            from statsmodels.tsa.seasonal import seasonal_decompose
            
            # 시계열 분해를 위해 날짜를 인덱스로 설정하고, 빈 날짜를 채웁니다.
            ts_data = filtered_df.set_index('Date')['Value']
            ts_data = ts_data.asfreq('D').fillna(method='ffill') 
            
            try:
                # seasonal_decompose 함수를 사용하여 추세, 계절성, 잔차를 분리합니다.
                decomposition = seasonal_decompose(ts_data, model='additive')
                
                st.subheader("1. 추세 (Trend)")
                st.line_chart(decomposition.trend)
                st.caption("데이터의 장기적인 흐름을 보여줍니다.")
                
                st.subheader("2. 계절성 (Seasonality)")
                st.line_chart(decomposition.seasonal)
                st.caption("반복되는 주기적 패턴을 보여줍니다.")
                
                st.subheader("3. 잔차 (Residual)")
                st.line_chart(decomposition.resid)
                st.caption("예측 불가능한 불규칙한 변동을 보여줍니다.")
                
            except Exception as e:
                st.error(f"시계열 분해 중 오류 발생: {e}")
                st.info("데이터 포인트가 충분하지 않거나 주기가 명확하지 않을 수 있습니다.")

    # ==========================================
    # 단계 2: 데이터 전처리
    # ==========================================
    elif step == "2. 데이터 전처리":
        st.header("2. 데이터 전처리")
        st.info("AI 모델이 데이터를 잘 학습하기 위해서는 **전처리** 과정이 필수적입니다.")
        
        st.write(f"현재 선택된 데이터: **{selected_category} - {selected_status}**")
        
        # ------------------------------------------
        # 2-1. 결측치 처리
        # ------------------------------------------
        st.subheader("1. 결측치 처리")
        st.markdown("""
        시계열 데이터는 연속적이어야 하므로 중간에 비어있는 날짜나 값(결측치)이 있으면 안 됩니다.
        """)
        
        # 전체 날짜 범위 생성 (시작일 ~ 종료일)
        min_date = filtered_df['Date'].min()
        max_date = filtered_df['Date'].max()
        full_range = pd.date_range(start=min_date, end=max_date, freq='D')
        
        # 빈 날짜를 채우기 위해 인덱스 재설정
        filtered_df_indexed = filtered_df.set_index('Date')
        filtered_df_full = filtered_df_indexed.reindex(full_range)
        
        missing_count = filtered_df_full['Value'].isna().sum()
        st.write(f"총 날짜 범위: {len(full_range)}일")
        st.write(f"결측치 개수: {missing_count}개")
        
        fill_method = st.radio(
            "결측치 처리 방법", 
            ["None", "Forward Fill (이전 값으로 채우기)", "Interpolation (선형 보간)"], 
            key="fill_method"
        )
        
        if fill_method == "Forward Fill (이전 값으로 채우기)":
            # ffill: 바로 직전의 유효한 값으로 빈칸을 채움
            filtered_df_full['Value'] = filtered_df_full['Value'].fillna(method='ffill')
            st.success("Forward Fill 적용 완료! (직전 값 복사)")
        elif fill_method == "Interpolation (선형 보간)":
            # interpolate: 앞뒤 값을 연결하는 직선상의 값으로 채움
            filtered_df_full['Value'] = filtered_df_full['Value'].interpolate()
            st.success("Interpolation 적용 완료! (앞뒤 값의 중간값으로 추정)")
        
        st.line_chart(filtered_df_full['Value'])
        
        # 인덱스를 다시 컬럼으로 변환
        final_df = filtered_df_full.reset_index().rename(columns={'index': 'Date'})
        
        st.divider()
        
        # ------------------------------------------
        # 2-2. 스케일링
        # ------------------------------------------
        st.subheader("2. 스케일링")
        st.markdown("""
        데이터의 값의 범위가 너무 크거나 작으면 딥러닝 모델 학습이 잘 되지 않습니다.
        데이터를 특정 범위로 변환해주는 과정을 **스케일링**이라고 합니다.
        """)
        
        scale_method = st.selectbox(
            "스케일링 방법 선택", 
            ["None", "MinMax Scaling", "Standard Scaling"], 
            key="scale_method"
        )
        
        scaled_data = final_df[['Value']].values
        
        if scale_method == "MinMax Scaling":
            # MinMax Scaling: 데이터를 0과 1 사이로 변환
            # 수식: X_new = (X - min(X)) / (max(X) - min(X))
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(scaled_data)
            st.info("데이터가 **0과 1 사이**로 변환되었습니다.")
            st.latex(r"x_{scaled} = \frac{x - x_{min}}{x_{max} - x_{min}}")
            
        elif scale_method == "Standard Scaling":
            # Standard Scaling: 평균이 0, 표준편차가 1이 되도록 변환 (정규분포화)
            # 수식: X_new = (X - mean(X)) / std(X)
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(scaled_data)
            st.info("데이터가 **평균 0, 표준편차 1**인 분포로 변환되었습니다.")
            st.latex(r"x_{scaled} = \frac{x - \mu}{\sigma}")
            
        st.line_chart(pd.DataFrame(scaled_data, columns=['Scaled Value']))
        
        st.divider()
        
        # ------------------------------------------
        # 2-3. 윈도우 생성
        # ------------------------------------------
        st.subheader("3. 윈도우 생성")
        st.markdown("""
        시계열 예측은 **지도 학습** 문제입니다.
        과거의 데이터(Input, $X$)를 보고 미래의 값(Target, $y$)을 맞추도록 데이터를 변환해야 합니다.
        
        - **Window Size**: 과거 며칠치를 볼 것인가?
        """)
        
        window_size = st.slider("Window Size 선택", min_value=1, max_value=30, value=7, key="window_size")
        
        if st.button("데이터셋 생성 예시 보기"):
            import numpy as np
            def create_dataset(dataset, look_back=1):
                X, y = [], []
                for i in range(len(dataset)-look_back-1):
                    a = dataset[i:(i+look_back), 0]
                    X.append(a)
                    y.append(dataset[i + look_back, 0])
                return np.array(X), np.array(y)
            
            X, y = create_dataset(scaled_data, window_size)
            st.write(f"**데이터셋 변환 결과**")
            st.write(f"- 입력 데이터($X$) 형태: {X.shape} (샘플 수, 윈도우 크기)")
            st.write(f"- 타겟 데이터($y$) 형태: {y.shape} (샘플 수, )")
            
            st.markdown("### 🔍 변환 원리 예시")
            st.code("""
            원본 데이터: [10, 20, 30, 40, 50]
            Window Size: 3
            
            --------------------------------
            X (과거 3일)      -> y (다음 날)
            [10, 20, 30] -> 40
            [20, 30, 40] -> 50
            """)

    # ==========================================
    # 단계 3: 모델링 및 예측
    # ==========================================
    elif step == "3. 모델링 및 예측":
        st.header("3. 모델링 및 예측")
        st.info("준비된 데이터를 사용하여 미래를 예측하는 모델을 학습합니다.")
        
        # 모델링을 위해 전처리 과정을 내부적으로 다시 수행 (사용자 편의를 위해)
        # 1. 결측치 처리
        min_date = filtered_df['Date'].min()
        max_date = filtered_df['Date'].max()
        full_range = pd.date_range(start=min_date, end=max_date, freq='D')
        filtered_df_indexed = filtered_df.set_index('Date')
        filtered_df_full = filtered_df_indexed.reindex(full_range)
        
        fill_method = st.session_state.get("fill_method", "Interpolation (선형 보간)")
        if fill_method == "Forward Fill (이전 값으로 채우기)":
            filtered_df_full['Value'] = filtered_df_full['Value'].fillna(method='ffill')
        else: 
            filtered_df_full['Value'] = filtered_df_full['Value'].interpolate()
            
        final_df = filtered_df_full.reset_index().rename(columns={'index': 'Date'})
        
        # 2. 스케일링
        scale_method = st.session_state.get("scale_method", "MinMax Scaling")
        scaled_data = final_df[['Value']].values
        scaler = None
        
        if scale_method == "MinMax Scaling":
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(scaled_data)
        elif scale_method == "Standard Scaling":
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(scaled_data)
            
        # 3. 윈도우 크기
        window_size = st.session_state.get("window_size", 7)
        
        st.write(f"**설정 확인**: 결측치 처리({fill_method}), 스케일링({scale_method}), 윈도우 크기({window_size})")
        
        model_type = st.selectbox("모델 선택", ["이동평균 (Moving Average)", "선형회귀 (Linear Regression)", "LSTM (Deep Learning)"])
        
        import numpy as np
        
        # ------------------------------------------
        # 모델 1: 이동평균
        # ------------------------------------------
        if model_type == "이동평균 (Moving Average)":
            st.subheader("이동평균 (Moving Average)")
            st.markdown("""
            가장 단순한 예측 방법으로, 과거 $N$일 간의 평균을 다음 날의 예측값으로 사용합니다.
            
            $$
            \hat{y}_{t+1} = \frac{y_t + y_{t-1} + ... + y_{t-N+1}}{N}
            $$
            """)
            ma_window = st.slider("이동평균 윈도우 크기 (N)", 1, 30, 7)
            
            # [함수 설명] rolling(window): 데이터를 윈도우 크기만큼 묶어서 연산할 준비를 합니다.
            # - window=ma_window: 
            #   * 의미: 몇 개의 데이터를 묶을지 결정합니다. (예: 7이면 7일치 데이터)
            #   * 변경 시: 값이 커지면 더 많은 과거 데이터를 평균내므로 그래프가 더 부드러워지지만, 최근 변화에 둔감해집니다.
            # mean(): 묶인 데이터의 평균을 계산합니다.
            final_df['MA'] = final_df['Value'].rolling(window=ma_window).mean()
            
            st.line_chart(final_df[['Value', 'MA']])
            st.caption("파란색: 실제 값, 주황색: 이동평균 예측 값")
            
        # ------------------------------------------
        # 모델 2: 선형회귀 (Linear Regression)
        # ------------------------------------------
        elif model_type == "선형회귀 (Linear Regression)":
            st.subheader("선형회귀 (Linear Regression)")
            st.markdown("""
            과거 데이터($X$)와 미래 데이터($y$) 사이의 **선형적인 관계(직선)**를 찾는 모델입니다.
            
            $$
            y = w_1 x_1 + w_2 x_2 + ... + w_n x_n + b
            $$
            
            여기서 $w$는 가중치(Weight), $b$는 편향(Bias)입니다.
            """)
            
            # 데이터셋 생성
            def create_dataset(dataset, look_back=1):
                """
                시계열 데이터를 지도학습용 데이터셋(X, y)으로 변환하는 함수
                - X: 과거 look_back 만큼의 데이터
                - y: 그 다음 시점의 데이터
                """
                X, y = [], []
                for i in range(len(dataset)-look_back-1):
                    a = dataset[i:(i+look_back), 0]
                    X.append(a)
                    y.append(dataset[i + look_back, 0])
                return np.array(X), np.array(y)
            
            X, y = create_dataset(scaled_data, window_size)
            
            # 학습/테스트 데이터 분리
            train_size = int(len(X) * 0.8)
            X_train, X_test = X[:train_size], X[train_size:]
            y_train, y_test = y[:train_size], y[train_size:]
            
            from sklearn.linear_model import LinearRegression
            # [함수 설명] LinearRegression(): 선형회귀 모델 객체를 생성합니다.
            # - 별다른 인자 없이 기본값을 사용하면 가장 일반적인 최소제곱법을 사용합니다.
            model = LinearRegression()
            
            # [함수 설명] fit(X, y): 모델을 데이터에 맞게 학습시킵니다. (최적의 w와 b를 찾음)
            # - X: 입력 데이터 (특성)
            # - y: 정답 데이터 (타겟)
            model.fit(X_train, y_train)
            
            # [함수 설명] predict(X): 학습된 모델을 사용하여 예측값을 생성합니다.
            train_pred = model.predict(X_train)
            test_pred = model.predict(X_test)
            
            # 스케일링 복원 (Inverse Transform)
            if scaler:
                # [함수 설명] inverse_transform(): 스케일링된 값을 원래 값의 범위로 되돌립니다.
                train_pred = scaler.inverse_transform(train_pred.reshape(-1, 1))
                test_pred = scaler.inverse_transform(test_pred.reshape(-1, 1))
                y_train_orig = scaler.inverse_transform(y_train.reshape(-1, 1))
                y_test_orig = scaler.inverse_transform(y_test.reshape(-1, 1))
            else:
                y_train_orig = y_train
                y_test_orig = y_test
                
            # 결과 시각화
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(10, 5))
            
            train_dates = final_df['Date'].iloc[window_size:window_size+len(y_train)]
            test_dates = final_df['Date'].iloc[window_size+len(y_train):window_size+len(y_train)+len(y_test)]
            
            ax.plot(train_dates, y_train_orig, label='실제 값 (Train)')
            ax.plot(train_dates, train_pred, label='예측 값 (Train)', linestyle='--')
            ax.plot(test_dates, y_test_orig, label='실제 값 (Test)')
            ax.plot(test_dates, test_pred, label='예측 값 (Test)', linestyle='--')
            ax.set_title("선형회귀 예측 결과")
            ax.legend()
            st.pyplot(fig)
            
        # ------------------------------------------
        # 모델 3: LSTM (Deep Learning)
        # ------------------------------------------
        elif model_type == "LSTM (Deep Learning)":
            st.subheader("LSTM (Long Short-Term Memory)")
            st.markdown("""
            **LSTM**은 순환 신경망(RNN)의 일종으로, 시계열 데이터의 **장기적인 패턴(Long-term dependency)**을 기억하는 데 특화된 딥러닝 모델입니다.
            과거의 정보를 잊을지(Forget Gate), 기억할지(Input Gate)를 스스로 학습합니다.
            """)
            
            epochs = st.slider("Epochs (학습 반복 횟수)", 1, 100, 10)
            st.caption("Epoch이 높을수록 모델이 데이터를 더 많이 학습하지만, 과적합(Overfitting)될 수 있습니다.")
            
            if st.button("LSTM 모델 학습 시작"):
                # 데이터셋 생성
                def create_dataset(dataset, look_back=1):
                    X, y = [], []
                    for i in range(len(dataset)-look_back-1):
                        a = dataset[i:(i+look_back), 0]
                        X.append(a)
                        y.append(dataset[i + look_back, 0])
                    return np.array(X), np.array(y)
                
                X, y = create_dataset(scaled_data, window_size)
                
                # LSTM 입력 형태 변환: [samples, time steps, features]
                # [함수 설명] reshape(): 배열의 차원을 변경합니다. LSTM은 3차원 입력을 필요로 합니다.
                X = np.reshape(X, (X.shape[0], X.shape[1], 1))
                
                # 학습/테스트 분리
                train_size = int(len(X) * 0.8)
                X_train, X_test = X[:train_size], X[train_size:]
                y_train, y_test = y[:train_size], y[train_size:]
                
                # 모델 구성
                from tensorflow.keras.models import Sequential
                from tensorflow.keras.layers import LSTM, Dense
                
                # [함수 설명] Sequential(): 층(Layer)을 순서대로 쌓아 모델을 만드는 컨테이너입니다.
                model = Sequential()
                
                # [함수 설명] LSTM(): LSTM 층을 추가합니다.
                # - units=50: 
                #   * 의미: LSTM 층 내부의 뉴런(기억 셀) 개수입니다.
                #   * 변경 시: 숫자가 클수록 더 복잡한 패턴을 학습할 수 있지만, 계산이 느려지고 과적합 위험이 커집니다.
                # - return_sequences=True: 
                #   * 의미: 모든 시점의 출력을 반환합니다. 다음 층도 LSTM일 때 사용합니다.
                #   * 변경 시: False로 하면 마지막 시점의 값만 반환하므로, 바로 Dense 층으로 연결해야 합니다.
                # - input_shape=(window_size, 1):
                #   * 의미: 입력 데이터의 형태를 정의합니다. (시간 단계 수, 특성 수)
                model.add(LSTM(units=50, return_sequences=True, input_shape=(window_size, 1)))
                
                # - return_sequences=False (기본값): 
                #   * 의미: 마지막 시점의 출력 벡터만 반환합니다. 이제 예측값을 만들기 위해 Dense 층으로 보냅니다.
                model.add(LSTM(units=50))
                
                # [함수 설명] Dense(): 완전 연결 층(Fully Connected Layer)입니다.
                # - units=1:
                #   * 의미: 최종적으로 출력할 값의 개수입니다. 여기서는 '다음 날의 인원 수' 1개를 예측하므로 1입니다.
                model.add(Dense(units=1))
                
                # [함수 설명] compile(): 모델 학습 방식을 설정합니다.
                # - loss='mean_squared_error': 
                #   * 의미: 손실 함수로 MSE(평균제곱오차)를 사용합니다. 예측값과 실제값 차이의 제곱의 평균입니다.
                #   * 변경 시: 'mae'(평균절대오차) 등을 사용할 수 있습니다.
                # - optimizer='adam': 
                #   * 의미: 최적화 알고리즘으로 Adam을 사용합니다. 가장 널리 쓰이는 성능 좋은 알고리즘입니다.
                model.compile(loss='mean_squared_error', optimizer='adam')
                
                # 학습 진행 상황 표시
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                import tensorflow as tf
                class StreamlitCallback(tf.keras.callbacks.Callback):
                    def on_epoch_end(self, epoch, logs=None):
                        progress = (epoch + 1) / epochs
                        progress_bar.progress(progress)
                        status_text.text(f"Epoch {epoch+1}/{epochs} - Loss: {logs['loss']:.4f}")
                        
                # [함수 설명] fit(): 모델을 실제로 학습시킵니다.
                # - epochs: 
                #   * 의미: 전체 데이터를 몇 번 반복해서 학습할지 설정합니다.
                #   * 변경 시: 너무 적으면 학습이 덜 되고(Underfitting), 너무 많으면 과적합(Overfitting) 됩니다.
                # - batch_size=1: 
                #   * 의미: 한 번에 학습할 데이터 샘플의 개수입니다. 1이면 매 샘플마다 가중치를 업데이트합니다.
                #   * 변경 시: 크면 학습 속도가 빨라지지만, 메모리를 많이 쓰고 수렴이 불안정할 수 있습니다.
                history = model.fit(X_train, y_train, epochs=epochs, batch_size=1, verbose=0, callbacks=[StreamlitCallback()])
                
                st.success("학습 완료!")
                
                # 학습 곡선 시각화
                st.subheader("학습 곡선 (Loss Curve)")
                st.line_chart(history.history['loss'])
                st.caption("Loss(손실)가 0에 가까워질수록 모델의 예측이 정확해지고 있음을 의미합니다.")
                
                # 예측 수행
                train_predict = model.predict(X_train)
                test_predict = model.predict(X_test)
                
                # 스케일링 복원
                if scaler:
                    train_predict = scaler.inverse_transform(train_predict)
                    y_train_orig = scaler.inverse_transform(y_train.reshape(-1, 1))
                    test_predict = scaler.inverse_transform(test_predict)
                    y_test_orig = scaler.inverse_transform(y_test.reshape(-1, 1))
                else:
                    y_train_orig = y_train
                    y_test_orig = y_test
                    
                # 결과 비교 시각화
                st.subheader("예측 결과 비교")
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(10, 5))
                
                train_dates = final_df['Date'].iloc[window_size:window_size+len(y_train)]
                test_dates = final_df['Date'].iloc[window_size+len(y_train):window_size+len(y_train)+len(y_test)]
                
                ax.plot(train_dates, y_train_orig, label='실제 값 (Train)')
                ax.plot(train_dates, train_predict, label='예측 값 (Train)')
                ax.plot(test_dates, y_test_orig, label='실제 값 (Test)')
                ax.plot(test_dates, test_predict, label='예측 값 (Test)')
                ax.legend()
                st.pyplot(fig)
