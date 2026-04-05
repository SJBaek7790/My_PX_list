import streamlit as st
import pandas as pd

st.set_page_config(layout="centered") # 모바일은 centered가 안정적입니다.

# 1. Airtable 디자인 시스템 CSS (모바일 대응 여백 조정)
airtable_css = """
<style>
    html, body, [class*="css"] {
        font-family: -apple-system, system-ui, Roboto, sans-serif !important;
        color: #181d26 !important;
        background-color: #ffffff !important;
    }
    .stButton > button {
        background-color: #1b61c9 !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 20px !important;
        font-weight: 500 !important;
        width: 100% !important; /* 모바일에서는 버튼을 꽉 차게 */
    }
    .detail-card h3 { margin-top: 0; margin-bottom: 8px; }
    .price-text { color: #1b61c9; font-weight: 600; font-size: 22px; margin-bottom: 16px; }
</style>
"""
st.markdown(airtable_css, unsafe_allow_html=True)

# 2. 데이터 로드 (Excel 파일 연동)
@st.cache_data
def load_data():
    try:
        # Excel 파일 로드
        xls = pd.ExcelFile("PX (1).xlsx")
        sheet_names = xls.sheet_names
        # 사용자가 언급한 시트가 있으면 사용, 없으면 첫 번째 시트 사용
        target_sheet = "Results_0405_0506" if "Results_0405_0506" in sheet_names else sheet_names[0]
        df = pd.read_excel(xls, sheet_name=target_sheet)
        
        # 컬럼명 공백 제거 및 정문화
        df.columns = [str(c).strip() for c in df.columns]
        
        # 컬럼명 매핑 (KOR -> ENG)
        rename_map = {
            '상품명': 'name',
            '가격': 'price',
            '군마트가격(원)': 'price',
            '카테고리': 'category',
            '규격': 'spec',
            '비고': 'note',
            '이미지URL': 'image_url',
            '이미지': 'image_url'
        }
        df = df.rename(columns=rename_map)
        
        # 필수 컬럼 존재 여부 확인 및 기본값 생성 (KeyError 방지)
        for col in ['name', 'price', 'category', 'spec', 'note', 'image_url']:
            if col not in df.columns:
                df[col] = '-'
        
        # 데이터 타입 및 결측치 정제
        df['name'] = df['name'].fillna('품목 불명')
        df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)
        df['category'] = df['category'].fillna('기타')
        df['spec'] = df['spec'].fillna('-')
        df['note'] = df['note'].fillna('-')
        
        return df
    except Exception as e:
        st.error(f"Excel 파일 로드 오류: {e}")
        # 오류 시 최소한의 컬럼을 가진 빈 데이터프레임 반환
        return pd.DataFrame(columns=['name', 'price', 'category', 'spec', 'note', 'image_url'])

df = load_data()

# 3. 팝업(모달) UI 정의 
# @st.dialog 데코레이터를 사용하면 이 함수가 호출될 때 화면 위에 팝업이 생성됩니다.
@st.dialog("상품 상세 정보")
def show_detail_modal(item):
    # 상단 이미지 컨테이너 (고급스러운 여백과 테두리)
    img_placeholder = "https://via.placeholder.com/600x400?text=No+Image"
    img_url = item['image_url'] if pd.notna(item['image_url']) and str(item['image_url']).startswith('http') else img_placeholder
    
    # 이미지 중앙 배치 및 줌 효과 유도
    st.image(img_url, use_container_width=True, caption=item['name'])
    
    # 상세 텍스트 정보
    st.markdown(f"""
    <div class="detail-card" style="background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #e1e4e8;">
        <h2 style="color: #1b61c9; margin-bottom: 4px;">{item['name']}</h2>
        <div style="font-size: 24px; font-weight: 700; color: #181d26; margin-bottom: 16px;">{item['price']:,}원</div>
        
        <div style="display: grid; grid-template-columns: 80px 1fr; gap: 8px; font-size: 14px; line-height: 1.6;">
            <div style="color: #6a737d; font-weight: 600;">카테고리</div>
            <div style="color: #181d26;">{item['category']}</div>
            
            <div style="color: #6a737d; font-weight: 600;">규격</div>
            <div style="color: #181d26;">{item['spec']}</div>
            
            <div style="color: #6a737d; font-weight: 600;">비고</div>
            <div style="color: #181d26;">{item['note']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("구매 페이지로 이동"):
        st.write("구매 링크 연결 필요")

# 4. 메인 화면 (모바일 리스트 뷰)
st.title("PX 품목 검색")

# 검색 및 필터 패널
search_query = st.text_input("상품 검색", placeholder="상품명 입력...")

# 사이드바 카테고리 필터
categories = ["전체"] + sorted(df['category'].unique().tolist())
selected_category = st.sidebar.selectbox("카테고리 선택", categories)

# 데이터 필터링
filtered_df = df.copy()
if selected_category != "전체":
    filtered_df = filtered_df[filtered_df['category'] == selected_category]
if search_query:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_query, case=False, na=False)]

st.caption(f"총 {len(filtered_df)}개의 품목이 있습니다. 터치 시 상세 정보를 확인합니다.")

# 모바일 화면에 맞게 데이터프레임 너비 100% 사용
event = st.dataframe(
    filtered_df[['category', 'name', 'price']], 
    use_container_width=True,
    hide_index=True,
    on_select="rerun", 
    selection_mode="single-row"
)

# 데이터프레임에서 행이 선택되었을 때 다이얼로그 함수 호출
if len(event.selection.rows) > 0:
    selected_idx = event.selection.rows[0]
    show_detail_modal(filtered_df.iloc[selected_idx])