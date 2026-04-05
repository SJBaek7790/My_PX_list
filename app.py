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

# 2. 데이터 로드 (CSV 파일 연동)
# 2. 데이터 로드 (CSV 파일 연동)
@st.cache_data
def load_data():
    try:
        # CSV 파일 로드 (Excel보다 안정적)
        df = pd.read_csv("PX_data.csv")
        
        # 컬럼명 공백 제거 및 정문화
        df.columns = [str(c).strip() for c in df.columns]
        
        # 컬럼명 매핑 (KOR -> ENG)
        rename_map = {
            '군마트가격(원)': 'PX_price',
            '추정_인터넷총가': 'internet_price',
            '할인율(%)': 'discount_rate',
            '최저가_링크': 'internet_link',
            '비고': 'note',
            '이미지URL': 'image_url',
            '이미지': 'image_url'
        }
        df = df.rename(columns=rename_map)
        
        # 필수 컬럼 존재 여부 확인 및 기본값 생성
        for col in ['name', 'PX_price', 'internet_price', 'discount_rate', 'category', 'spec', 'note', 'image_url', 'internet_link']:
            if col not in df.columns:
                df[col] = '-'
        
        # 데이터 타입 및 결측치 정제
        df['PX_price'] = pd.to_numeric(df['PX_price'], errors='coerce').fillna(0).astype(int)
        df['internet_price'] = pd.to_numeric(df['internet_price'], errors='coerce').fillna(0).astype(int)
        df['discount_rate'] = pd.to_numeric(df['discount_rate'], errors='coerce').fillna(0)
        df['name'] = df['name'].fillna('품목 불명')
        df['category'] = df['category'].fillna('기타')
        df['spec'] = df['spec'].fillna('-')
        df['note'] = df['note'].fillna('-')
        df['image_url'] = df['image_url'].fillna('https://via.placeholder.com/600x400?text=No+Image')
        df['internet_link'] = df['internet_link'].fillna('-')
        
        # 카테고리별 정렬 (기본 설정)
        df = df.sort_values(by='category').reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"CSV 파일 로드 오류: {e}")
        # 오류 시 모든 필수 컬럼을 가진 빈 데이터프레임 반환 (KeyError 방지)
        return pd.DataFrame(columns=['name', 'PX_price', 'internet_price', 'discount_rate', 'category', 'spec', 'note', 'image_url', 'internet_link'])

df = load_data()

# 3. 팝업(모달) UI 정의 
# @st.dialog 데코레이터를 사용하면 이 함수가 호출될 때 화면 위에 팝업이 생성됩니다.
@st.dialog("상품 상세 정보")
def show_detail_modal(item):
    # 상단 이미지 컨테이너
    img_placeholder = "https://via.placeholder.com/600x400?text=No+Image"
    img_url = item['image_url'] if pd.notna(item['image_url']) and str(item['image_url']).startswith('http') else img_placeholder
    st.image(img_url, use_container_width=True, caption=item['name'])
    
    # 상세 정보 HTML (들여쓰기 제거로 렌더링 문제 해결)
    html_content = f"""<div style="background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 1px solid #e1e4e8;">
<h2 style="color: #1b61c9; margin-bottom: 4px;">{item['name']}</h2>
<div style="font-size: 24px; font-weight: 700; color: #181d26; margin-bottom: 16px;">{item['PX_price']:,}원</div>
<div style="display: grid; grid-template-columns: 80px 1fr; gap: 8px; font-size: 14px; line-height: 1.6;">
<div style="color: #6a737d; font-weight: 600;">카테고리</div><div style="color: #181d26;">{item['category']}</div>
<div style="color: #6a737d; font-weight: 600;">인터넷가</div><div style="color: #d73a49; text-decoration: line-through;">{item['internet_price']:,}원</div>
<div style="color: #1b61c9; font-weight: 600;">할인율</div><div style="color: #1b61c9; font-weight: 700;">{item['discount_rate']}%</div>
<div style="color: #6a737d; font-weight: 600;">규격</div><div style="color: #181d26;">{item['spec']}</div>
<div style="color: #6a737d; font-weight: 600;">비고</div><div style="color: #181d26;">{item['note']}</div>
</div>
</div>"""
    st.markdown(html_content, unsafe_allow_html=True)
    
    if pd.notna(item['internet_link']) and str(item['internet_link']).startswith('http'):
        st.link_button("인터넷 최저가 보기", item['internet_link'])
    else:
        st.button("인터넷 링크 없음", disabled=True)

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
    filtered_df[['category', 'name', 'PX_price', 'internet_price', 'discount_rate']], 
    use_container_width=True,
    hide_index=True,
    on_select="rerun", 
    selection_mode="single-row"
)

# 데이터프레임에서 행이 선택되었을 때 다이얼로그 함수 호출
if len(event.selection.rows) > 0:
    selected_idx = event.selection.rows[0]
    show_detail_modal(filtered_df.iloc[selected_idx])