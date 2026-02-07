import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.font_manager as fm
import re
from collections import Counter

# Set Korean font
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False

def load_and_clean_data(filepath):
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    
    # Numeric cleanup
    numeric_cols = ['주문수량', '취소수량', '주문-취소 수량', '결제금액', '주문취소 금액', '실결제 금액', '판매단가', '공급단가', '재구매 횟수']
    for col in numeric_cols:
        if col in df.columns and df[col].dtype == object:
             try:
                df[col] = df[col].str.replace(',', '').astype(float)
             except (ValueError, AttributeError):
                pass

    # Date parse
    date_cols = ['주문일', '배송준비 처리일', '입금일']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    
    # Ensure numeric
    for col in ['주문-취소 수량', '실결제 금액', '판매단가', '공급단가']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # Net Profit Calculation
    if '판매단가' in df.columns and '공급단가' in df.columns and '주문-취소 수량' in df.columns:
        df['NetProfit'] = (df['판매단가'] - df['공급단가']) * df['주문-취소 수량']
    else:
        df['NetProfit'] = 0

    valid_sales = df[df['주문-취소 수량'] > 0].copy() if '주문-취소 수량' in df.columns else df.copy()
    
    print(f"Data Loaded. Total: {len(df)}, Valid Sales: {len(valid_sales)}")
    return df, valid_sales

# --- Original Modules (Condensed) ---
def analyze_product_names(df):
    pass # Skipped for brevity in this run, focusing on new hypotheses

# --- New Hypothesis Modules ---

def analyze_region_seller_impact(df):
    print("\n[H1] Gyeonggi-do Sales vs Sellers")
    if '광역지역' not in df.columns or '셀러명' not in df.columns:
        print("Missing columns.")
        return
        
    gyeonggi = df[df['광역지역'].astype(str).str.contains('경기', na=False)]
    total_sales = gyeonggi['실결제 금액'].sum()
    
    print(f"Total Gyeonggi Sales: {total_sales:,.0f}")
    
    top_sellers = gyeonggi.groupby('셀러명')['실결제 금액'].sum().sort_values(ascending=False).head(5)
    print("Top 5 Sellers in Gyeonggi:")
    print(top_sellers)
    
    top_share = top_sellers.sum() / total_sales * 100
    print(f"Top 5 Sellers Share in Gyeonggi: {top_share:.1f}%")

def analyze_event_efficiency(df):
    print("\n[H2] Event Product Efficiency")
    if '이벤트 여부' not in df.columns:
        print("Missing '이벤트 여부'.")
        return
        
    group = df.groupby('이벤트 여부')[['주문-취소 수량', '실결제 금액', 'NetProfit']].sum()
    group['ProfitMargin'] = group['NetProfit'] / group['실결제 금액'] * 100
    print(group)

def analyze_gift_options(df):
    print("\n[H3] Gift Buying Behavior")
    # Identify Gift purchases
    # Priority: '목적' == '선물' > '선물세트_여부' == '선물세트'
    is_gift = pd.Series(False, index=df.index)
    if '목적' in df.columns:
        is_gift |= df['목적'].astype(str).str.contains('선물', na=False)
    if '선물세트_여부' in df.columns:
        is_gift |= (df['선물세트_여부'] == '선물세트')
        
    gifts = df[is_gift]
    non_gifts = df[~is_gift]
    
    print(f"Gift Orders: {len(gifts)}, Non-Gift: {len(non_gifts)}")
    
    print("Average Price: Gift vs Non-Gift")
    print(f"Gift: {gifts['판매단가'].mean():,.0f} KRW")
    print(f"Non-: {non_gifts['판매단가'].mean():,.0f} KRW")
    
    if '과수 크기' in df.columns:
        print("\nTop 3 Fruit Sizes for Gifts:")
        print(gifts['과수 크기'].value_counts().head(3))

def analyze_seller_retention(df):
    print("\n[H4] Seller Retention (Repeat Purchase from Same Seller)")
    if 'UID' not in df.columns or '셀러명' not in df.columns: return
    
    # Count orders per User per Seller
    user_seller_counts = df.groupby(['UID', '셀러명']).size()
    
    # Repurchase is > 1
    repurchases = user_seller_counts[user_seller_counts > 1]
    
    total_pairs = len(user_seller_counts)
    repurchase_pairs = len(repurchases)
    
    print(f"Total User-Seller Pairs: {total_pairs}")
    print(f"Pairs with Repurchase (>1): {repurchase_pairs} ({repurchase_pairs/total_pairs*100:.1f}%)")
    
    # Top Sellers by Retention Rate (min 10 users)
    seller_stats = df.groupby('셀러명')['UID'].nunique().reset_index(name='UserCount')
    
    # Calculate repurchase count per seller (users who bought > 1)
    repurchase_counts = repurchases.reset_index().groupby('셀러명')['UID'].count().reset_index(name='RetainedUsers')
    
    merged = seller_stats.merge(repurchase_counts, on='셀러명', how='left').fillna(0)
    merged['RetentionRate'] = merged['RetainedUsers'] / merged['UserCount'] * 100
    
    print("\nTop 5 Sellers by Retention Rate (min 50 users):")
    valid_sellers = merged[merged['UserCount'] >= 50].sort_values('RetentionRate', ascending=False)
    print(valid_sellers.head(5))

def analyze_seller_specialty(df):
    print("\n[H5] Seller Specialty (Economy vs Premium)")
    # Define segments
    # Economy: Price <= 25000 
    # Premium: Price >= 35000 OR is_premium='프리미엄'
    
    df['Segment'] = 'Mid'
    df.loc[df['판매단가'] <= 25000, 'Segment'] = 'Economy'
    df.loc[(df['판매단가'] >= 35000) | (df.get('is_premium') == '프리미엄'), 'Segment'] = 'Premium'
    
    print("\nSegment Distribution:")
    print(df['Segment'].value_counts())
    
    print("\nTop Seller for Economy (by Volume):")
    print(df[df['Segment']=='Economy'].groupby('셀러명')['주문-취소 수량'].sum().nlargest(3))
    
    print("\nTop Seller for Premium (by Volume):")
    print(df[df['Segment']=='Premium'].groupby('셀러명')['주문-취소 수량'].sum().nlargest(3))

def analyze_seller_lifecycle(df):
    print("\n[H6] Seller Lifecycle")
    if '주문일' not in df.columns: return
    
    df['Month'] = df['주문일'].dt.to_period('M')
    
    # Active sellers per month
    monthly_sellers = df.groupby('Month')['셀러명'].unique()
    
    lifecycle_stats = []
    
    all_seen_sellers = set()
    prev_month_sellers = set()
    
    for month in sorted(monthly_sellers.index):
        current_sellers = set(monthly_sellers[month])
        
        # New: In current but never seen before
        new_entrants = current_sellers - all_seen_sellers
        
        # Churn: In prev but not in current
        # Note: This is simplified churn (churned THIS month). They might return later.
        churned = prev_month_sellers - current_sellers if prev_month_sellers else set()
        
        # Retention: In prev AND current
        retained = prev_month_sellers & current_sellers
        
        lifecycle_stats.append({
            'Month': month,
            'Active': len(current_sellers),
            'New': len(new_entrants),
            'Churned': len(churned),
            'Retained': len(retained)
        })
        
        all_seen_sellers.update(current_sellers)
        prev_month_sellers = current_sellers
        
    print(pd.DataFrame(lifecycle_stats))

def analyze_seoul_packages(df):
    print("\n[H7] Seoul Demographics (Small Package Preference)")
    if '광역지역' not in df.columns or '무게 구분' not in df.columns: return

    # Normalize Region
    df['RegionGroup'] = df['광역지역'].apply(lambda x: 'Seoul' if '서울' in str(x) else 'Non-Seoul')
    
    # Check 'Small' (<3kg) vs others
    # Assuming '무게 구분' has values like '3kg 미만' or '<3kg' or derived from data
    # Let's check distribution
    
    ct = pd.crosstab(df['무게 구분'], df['RegionGroup'], normalize='columns') * 100
    print("\nPackage Size Preference by Region (%):")
    print(ct)

def main():
    filepath = 'data/project1 - classification_results.csv'
    try:
        original_df, valid_df = load_and_clean_data(filepath)
    except FileNotFoundError:
        print(f"File not found: {filepath}")
        return

    # Running H1-H7
    analyze_region_seller_impact(valid_df)
    analyze_event_efficiency(valid_df)
    analyze_gift_options(valid_df)
    analyze_seller_retention(valid_df)
    analyze_seller_specialty(valid_df)
    analyze_seller_lifecycle(valid_df)
    analyze_seoul_packages(valid_df)
    
    print("\nExpanded Analysis Complete.")

if __name__ == "__main__":
    main()
