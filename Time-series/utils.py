import pandas as pd
import streamlit as st

# ==========================================
# 데이터 로드 함수
# ==========================================
@st.cache_data
def load_data(file_path):
    """
    COVID19.csv 파일을 로드하고 전처리를 수행하는 함수입니다.
    
    [사용된 주요 함수 및 인자 설명]
    - pd.read_csv(path, encoding): CSV 파일을 읽어 DataFrame으로 변환합니다.
      * path: 파일 경로
      * encoding='cp949': 
        - 의미: 한글 윈도우에서 주로 사용하는 문자 인코딩 방식입니다.
        - 변경 시: 만약 'utf-8'로 변경하면 한글이 깨져서 보이거나 에러(UnicodeDecodeError)가 발생할 수 있습니다.
    
    - df.rename(columns, inplace): 컬럼의 이름을 변경합니다.
      * columns: {기존이름: 새이름} 형태의 딕셔너리
      * inplace=True: 
        - 의미: 원본 데이터프레임(df) 자체를 수정하겠다는 뜻입니다.
        - 변경 시: False(기본값)로 설정하면 원본은 변하지 않고, 이름이 변경된 새로운 데이터프레임이 반환됩니다.
      
    - df.drop(columns, inplace): 특정 컬럼을 삭제합니다.
    
    - pd.to_datetime(series, format, errors): 문자열을 날짜(datetime) 객체로 변환합니다.
      * format='%Y. %m. %d': 
        - 의미: 입력된 날짜 문자열의 형식을 지정합니다. (예: "2020. 01. 01")
        - 변경 시: 데이터의 실제 형식과 다르게 지정하면 변환에 실패합니다. (예: '-'로 구분되어 있는데 '.'을 쓰면 에러)
      * errors='coerce': 
        - 의미: 변환 중 오류가 발생하면 강제로 NaT(Not a Time, 결측치)로 처리합니다.
        - 변경 시: 'raise'(기본값)로 설정하면 형식이 맞지 않는 데이터가 있을 때 프로그램이 에러를 내고 멈춥니다.
    
    Args:
        file_path (str): CSV 파일의 경로
        
    Returns:
        pd.DataFrame: 전처리가 완료된 데이터프레임
    """
    try:
        # 1. CSV 파일 읽기
        df = pd.read_csv(file_path, encoding='cp949')
        
        # 2. 컬럼 이름 변경 (Renaming Columns)
        column_mapping = {
            '시점': 'Date',
            '인원[명]': 'Value',
            '구분별': 'Category',
            '상태별': 'Status'
        }
        df.rename(columns=column_mapping, inplace=True)
        
        # 3. 불필요한 컬럼 제거
        if 'Unnamed: 4' in df.columns:
            df.drop(columns=['Unnamed: 4'], inplace=True)
            
        # 4. 날짜 형식 변환 (Date Parsing)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='%Y. %m. %d', errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame()

def preprocess_data(df):
    """
    추가적인 전처리가 필요할 경우 사용할 수 있는 함수입니다.
    현재는 사용하지 않지만, 확장성을 위해 남겨두었습니다.
    """
    return df
