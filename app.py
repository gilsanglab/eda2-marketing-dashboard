import streamlit as st
import pandas as pd
import plotly.express as px

# Configuration
st.set_page_config(page_title="Marketing Insights Dashboard", layout="wide")

@st.cache_data
def load_data():
    filepath = 'data/project1 - classification_results.csv'
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        st.error(f"File not found: {filepath}")
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
        df['RegionGroup'] = df['광역지역'].apply(lambda x: 'Seoul' if '서울' in str(x) else 'Non-Seoul')
    
    return valid_sales

def main():
    st.title("🍊 E-commerce Marketing Insights Dashboard")
    
    df = load_data()
    if df.empty:
        st.warning("No data loaded. Please check data source.")
        return
        
    # Sidebar Navigation
    st.sidebar.header("Navigation")
    page = st.sidebar.radio("Go to:", ["Home (Overview)", "Detailed Analysis", "Cross-Analysis (Drill Down)"])
    
    if page == "Home (Overview)":
        render_home(df)
    elif page == "Detailed Analysis":
        render_details(df)
    elif page == "Cross-Analysis (Drill Down)":
        render_cross_analysis(df)

def render_home(df):
    st.header("Executive Summary")
    
    # KPIs
    total_sales = df['실결제 금액'].sum()
    total_orders = df['주문-취소 수량'].sum()
    total_profit = df['NetProfit'].sum()
    avg_price = df['판매단가'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", f"₩{total_sales:,.0f}")
    col2.metric("Total Orders", f"{total_orders:,.0f}")
    col3.metric("Net Profit", f"₩{total_profit:,.0f}")
    col4.metric("Avg Unit Price", f"₩{avg_price:,.0f}")
    
    st.markdown("---")
    
    # Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("Top 5 Sellers by Revenue")
        if '셀러명' in df.columns:
            top_sellers = df.groupby('셀러명')['실결제 금액'].sum().nlargest(5).reset_index()
            fig_seller = px.bar(top_sellers, x='셀러명', y='실결제 금액', title="Top Sellers")
            st.plotly_chart(fig_seller, use_container_width=True)
        else:
            st.info("Seller data not available")
        
    with c2:
        st.subheader("Top 5 Products by Revenue")
        if '상품명' in df.columns:
            top_products = df.groupby('상품명')['실결제 금액'].sum().nlargest(5).reset_index()
            top_products['ShortName'] = top_products['상품명'].str[:20] + "..."
            fig_prod = px.bar(top_products, x='ShortName', y='실결제 금액', title="Top Products", hover_data=['상품명'])
            st.plotly_chart(fig_prod, use_container_width=True)
        else:
            st.info("Product data not available")

def render_details(df):
    st.header("Detailed Analysis")
    
    tab1, tab2, tab3 = st.tabs(["Product & Price", "Seller & Retention", "Region & Logistics"])
    
    with tab1:
        st.subheader("Pricing Strategy")
        if '판매단가' in df.columns:
            fig_price = px.histogram(df, x='판매단가', nbins=50, title="Price Distribution (Sweet Spot: 29k-39k)")
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.subheader("Gift vs Non-Gift")
        if '목적' in df.columns and '판매단가' in df.columns:
            fig_gift = px.box(df, x='목적', y='판매단가', title="Price Distribution by Purpose")
            st.plotly_chart(fig_gift, use_container_width=True)
            
    with tab2:
        st.subheader("Seller Retention")
        if '셀러명' in df.columns and 'UID' in df.columns:
            user_counts = df.groupby('셀러명')['UID'].nunique()
            dup_orders = df[df.duplicated(subset=['UID', '셀러명'], keep=False)]
            repurchase_counts = dup_orders.groupby('셀러명')['UID'].nunique()
            
            retention_df = pd.concat([user_counts, repurchase_counts], axis=1).fillna(0)
            retention_df.columns = ['TotalUsers', 'RepurchasedUsers']
            retention_df['RetentionRate'] = (retention_df['RepurchasedUsers'] / retention_df['TotalUsers'] * 100).round(1)
            
            retention_df = retention_df[retention_df['TotalUsers'] > 10].sort_values('RetentionRate', ascending=False).head(10)
            
            st.write("Top Sellers by Retention Rate (min 10 users)")
            st.dataframe(retention_df)

    with tab3:
        st.subheader("Seoul vs Non-Seoul Product Preference")
        if 'RegionGroup' in df.columns and '무게 구분' in df.columns:
            cross = pd.crosstab(df['무게 구분'], df['RegionGroup'], normalize='columns').reset_index()
            cross = pd.melt(cross, id_vars='무게 구분', var_name='Region', value_name='Percentage')
            cross['Percentage'] = cross['Percentage'] * 100
            
            fig_region = px.bar(cross, x='무게 구분', y='Percentage', color='Region', barmode='group', 
                                title="Package Size Preference by Region (%)")
            st.plotly_chart(fig_region, use_container_width=True)

def render_cross_analysis(df):
    st.header("Cross-Analysis (Drill Down)")
    st.markdown("Use filters to explore sales performance by **Region, Seller, and Product**.")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        regions = ['All'] + sorted(df['광역지역'].dropna().unique().tolist()) if '광역지역' in df.columns else []
        sel_region = st.selectbox("Select Region", regions)
        
    with c2:
        sellers = ['All'] + sorted(df['셀러명'].dropna().unique().tolist()) if '셀러명' in df.columns else []
        sel_seller = st.selectbox("Select Seller", sellers)
        
    with c3:
        search_prod = st.text_input("Search Product Name keyword", "")

    filtered_df = df.copy()
    
    if sel_region != 'All':
        filtered_df = filtered_df[filtered_df['광역지역'] == sel_region]
        
    if sel_seller != 'All':
        filtered_df = filtered_df[filtered_df['셀러명'] == sel_seller]
        
    if search_prod and '상품명' in df.columns:
        filtered_df = filtered_df[filtered_df['상품명'].str.contains(search_prod, case=False, na=False)]
        
    st.metric("Filtered Records", len(filtered_df), f"Revenue: ₩{filtered_df['실결제 금액'].sum():,.0f}")
    
    st.subheader("Filtered Data Preview")
    if not filtered_df.empty:
        cols_to_show = [c for c in ['주문일', '상품명', '셀러명', '광역지역', '실결제 금액', '주문-취소 수량'] if c in df.columns]
        st.dataframe(filtered_df[cols_to_show].head(100))
        
        st.subheader("Sales Breakdown (Filtered)")
        group_opts = [c for c in ['상품명', '셀러명', '광역지역', '과수 크기', '무게 구분'] if c in df.columns]
        if group_opts:
            group_col = st.selectbox("Group By", group_opts)
            agg_df = filtered_df.groupby(group_col)['실결제 금액'].sum().reset_index().sort_values('실결제 금액', ascending=False).head(20)
            
            fig = px.bar(agg_df, x=group_col, y='실결제 금액', title=f"Sales by {group_col}", text_auto='.2s')
            st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()
