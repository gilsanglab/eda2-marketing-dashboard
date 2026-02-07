import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import re

# Configuration
st.set_page_config(page_title="마케팅 인사이트 대시보드", layout="wide")

# Korean font support for Plotly
import plotly.io as pio
pio.templates.default = "plotly_white"

@st.cache_data
def load_data():
    filepath = 'data/project1 - classification_results.csv'
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(f"파일을 찾을 수 없습니다: {filepath}")
        return pd.DataFrame()

    # Numeric cleanup
    numeric_cols = ['주문수량', '취소수량', '주문-취소 수량', '결제금액', '실결제 금액', '판매단가', '공급단가', '재구매 횟수']
    for col in numeric_cols:
        if col in df.columns and df[col].dtype == object:
             try:
                df[col] = df[col].str.replace(',', '').astype(float)
             except:
                pass

    # Date parse
    date_cols = ['주문일', '배송준비 처리일', '입금일']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Net Profit
    if {'판매단가', '공급단가', '주문-취소 수량'}.issubset(df.columns):
        df['NetProfit'] = (df['판매단가'] - df['공급단가']) * df['주문-취소 수량']
    else:
        df['NetProfit'] = 0

    valid_sales = df[df['주문-취소 수량'] > 0].copy()
    
    # Derived Columns
    if '광역지역' in df.columns:
        df['RegionGroup'] = df['광역지역'].apply(lambda x: '서울' if '서울' in str(x) else '비서울')
        
    # Month for Lifecycle
    if '주문일' in df.columns:
        df['YearMonth'] = df['주문일'].dt.to_period('M').astype(str)

    # Keywords Extraction (Simple)
    if '상품명' in df.columns:
        def extract_keywords(text):
            # Extract distinct words, remove numbers/symbols
            words = re.findall(r'[가-힣]+', str(text))
            return words
        df['Keywords'] = df['상품명'].apply(extract_keywords)

    return valid_sales

def main():
    st.title("🍊 이커머스 마케팅 인사이트 대시보드")
    
    df = load_data()
    if df.empty:
        st.warning("데이터가 없습니다. 데이터 소스를 확인해주세요.")
        return
        
    # Sidebar Navigation
    st.sidebar.header("네비게이션")
    page = st.sidebar.radio("이동:", ["홈 (개요)", "상세 분석", "교차 분석 (Drill Down)"])
    
    if page == "홈 (개요)":
        render_home(df)
    elif page == "상세 분석":
        render_details(df)
    elif page == "교차 분석 (Drill Down)":
        render_cross_analysis(df)

def render_home(df):
    st.header("경영 요약 (Executive Summary)")
    
    # KPIs
    total_sales = df['실결제 금액'].sum()
    total_orders = df['주문-취소 수량'].sum()
    total_profit = df['NetProfit'].sum()
    avg_price = df['판매단가'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 매출", f"₩{total_sales:,.0f}")
    col2.metric("총 주문량", f"{total_orders:,.0f}")
    col3.metric("순이익", f"₩{total_profit:,.0f}")
    col4.metric("평균 단가", f"₩{avg_price:,.0f}")
    
    st.markdown("---")
    
    # Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("매출 상위 5개 셀러")
        if '셀러명' in df.columns:
            top_sellers = df.groupby('셀러명')['실결제 금액'].sum().nlargest(5).reset_index()
            fig_seller = px.bar(top_sellers, x='셀러명', y='실결제 금액', title="상위 셀러 매출")
            st.plotly_chart(fig_seller, use_container_width=True)
        else:
            st.info("셀러 데이터가 없습니다.")
        
    with c2:
        st.subheader("매출 상위 5개 상품")
        if '상품명' in df.columns:
            top_products = df.groupby('상품명')['실결제 금액'].sum().nlargest(5).reset_index()
            top_products['ShortName'] = top_products['상품명'].str[:20] + "..."
            fig_prod = px.bar(top_products, x='ShortName', y='실결제 금액', title="상위 상품 매출", hover_data=['상품명'])
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("상품 데이터가 없습니다.")

def render_details(df):
    st.header("상세 분석")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["상품명(키워드)", "가격 & 기획", "이벤트 효율", "셀러 & 리텐션", "지역 & 배송"])
    
    with tab1:
        st.subheader("상품명 키워드 분석")
        st.markdown("매출을 견인하는 핵심 키워드는 **'감귤', '타이벡', '전용'** 등 입니다.")
        
        all_keywords = [word for keywords in df['Keywords'] for word in keywords]
        keyword_counts = Counter(all_keywords)
        common_keywords = keyword_counts.most_common(20)
        
        kw_df = pd.DataFrame(common_keywords, columns=['Keyword', 'Count'])
        fig_kw = px.bar(kw_df, x='Keyword', y='Count', title="상위 20개 상품명 키워드 등장 빈도")
        st.plotly_chart(fig_kw, use_container_width=True)
        
        # Keyword Profitability (Optional/Advanced)
        # Calculate average sales for products containing specific keywords
        
    with tab2:
        st.subheader("가격 정책")
        if '판매단가' in df.columns:
            fig_price = px.histogram(df, x='판매단가', nbins=50, title="가격대별 분포 (Sweet Spot: 29k-39k)")
            fig_price.add_vline(x=29000, line_dash="dash", line_color="red", annotation_text="Sweet Spot Start")
            fig_price.add_vline(x=39000, line_dash="dash", line_color="red", annotation_text="Sweet Spot End")
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.subheader("선물 vs 가정용")
        if '목적' in df.columns and '판매단가' in df.columns:
            fig_gift = px.box(df, x='목적', y='판매단가', title="목적별 판매단가 분포")
            st.plotly_chart(fig_gift, use_container_width=True)

    with tab3:
        st.subheader("이벤트 효율 분석")
        if '이벤트 여부' in df.columns:
            event_stats = df.groupby('이벤트 여부')[['실결제 금액', 'NetProfit']].sum().reset_index()
            event_stats['ProfitMargin'] = (event_stats['NetProfit'] / event_stats['실결제 금액'] * 100).round(1)
            
            c1, c2 = st.columns(2)
            with c1:
                fig_event_sales = px.pie(event_stats, values='실결제 금액', names='이벤트 여부', title="이벤트 여부별 매출 비중")
                st.plotly_chart(fig_event_sales, use_container_width=True)
            with c2:
                fig_event_margin = px.bar(event_stats, x='이벤트 여부', y='ProfitMargin', title="이벤트 여부별 순이익률 (%)", text_auto=True)
                st.plotly_chart(fig_event_margin, use_container_width=True)
                
            st.success("💡 **인사이트**: 이벤트 상품은 마진율이 높고 매출 기여도가 큽니다. 비이벤트 상품은 적자 판매 우려가 있습니다.")
        else:
            st.info("'이벤트 여부' 컬럼이 없습니다.")

    with tab4:
        st.subheader("셀러 리텐션 (재구매율)")
        if '셀러명' in df.columns and 'UID' in df.columns:
            user_counts = df.groupby('셀러명')['UID'].nunique()
            dup_orders = df[df.duplicated(subset=['UID', '셀러명'], keep=False)]
            repurchase_counts = dup_orders.groupby('셀러명')['UID'].nunique()
            
            retention_df = pd.concat([user_counts, repurchase_counts], axis=1).fillna(0)
            retention_df.columns = ['총 구매자 수', '재구매자 수']
            retention_df['재구매율(%)'] = (retention_df['재구매자 수'] / retention_df['총 구매자 수'] * 100).round(1)
            
            retention_df = retention_df[retention_df['총 구매자 수'] > 10].sort_values('재구매율(%)', ascending=False).head(10)
            
            st.write("재구매율 상위 셀러 (최소 10명 이상 구매)")
            st.dataframe(retention_df)
            
        st.subheader("셀러 생애주기 (월별 활동)")
        if 'YearMonth' in df.columns:
            monthly_active = df.groupby('YearMonth')['셀러명'].nunique().reset_index()
            fig_lifecycle = px.line(monthly_active, x='YearMonth', y='셀러명', markers=True, title="월별 활동 셀러 수 추이")
            st.plotly_chart(fig_lifecycle, use_container_width=True)

    with tab5:
        st.subheader("서울 vs 비서울 상품 선호도")
        if 'RegionGroup' in df.columns and '무게 구분' in df.columns:
            cross = pd.crosstab(df['무게 구분'], df['RegionGroup'], normalize='columns').reset_index()
            cross = pd.melt(cross, id_vars='무게 구분', var_name='지역', value_name='비율')
            cross['비율'] = cross['비율'] * 100
            
            fig_region = px.bar(cross, x='무게 구분', y='비율', color='지역', barmode='group', 
                                title="지역별 포장 단위 선호도 (%)")
            st.plotly_chart(fig_region, use_container_width=True)

def render_cross_analysis(df):
    st.header("교차 분석 (Drill Down)")
    st.markdown("필터를 사용하여 **지역, 셀러, 상품**별 성과를 교차 분석하세요.")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        regions = ['전체'] + sorted(df['광역지역'].dropna().unique().tolist()) if '광역지역' in df.columns else []
        sel_region = st.selectbox("지역 선택", regions)
        
    with c2:
        sellers = ['전체'] + sorted(df['셀러명'].dropna().unique().tolist()) if '셀러명' in df.columns else []
        sel_seller = st.selectbox("셀러 선택", sellers)
        
    with c3:
        search_prod = st.text_input("상품명 검색 (키워드)", "")

    filtered_df = df.copy()
    
    if sel_region != '전체':
        filtered_df = filtered_df[filtered_df['광역지역'] == sel_region]
        
    if sel_seller != '전체':
        filtered_df = filtered_df[filtered_df['셀러명'] == sel_seller]
        
    if search_prod and '상품명' in df.columns:
        filtered_df = filtered_df[filtered_df['상품명'].str.contains(search_prod, case=False, na=False)]
        
    st.metric("필터링된 데이터 건수", f"{len(filtered_df)}건", f"매출: ₩{filtered_df['실결제 금액'].sum():,.0f}")
    
    st.subheader("필터링 데이터 미리보기")
    if not filtered_df.empty:
        cols_to_show = [c for c in ['주문일', '상품명', '셀러명', '광역지역', '실결제 금액', '주문-취소 수량'] if c in df.columns]
        st.dataframe(filtered_df[cols_to_show].head(100))
        
        st.subheader("매출 분석 (필터링)")
        group_opts = [c for c in ['상품명', '셀러명', '광역지역', '과수 크기', '무게 구분', '이벤트 여부'] if c in df.columns]
        if group_opts:
            group_col = st.selectbox("그룹화 기준", group_opts)
            agg_df = filtered_df.groupby(group_col)['실결제 금액'].sum().reset_index().sort_values('실결제 금액', ascending=False).head(20)
            
            fig = px.bar(agg_df, x=group_col, y='실결제 금액', title=f"{group_col}별 매출", text_auto='.2s')
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
