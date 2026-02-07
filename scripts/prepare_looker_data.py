import pandas as pd
import re
import os

def load_and_clean_data(input_path, output_path):
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"Error: File not found at {input_path}")
        return

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
    
    # Net Profit (Removed as per user request, but keeping columns if needed for other calcs)
    # if {'판매단가', '공급단가', '주문-취소 수량'}.issubset(df.columns):
    #     df['NetProfit'] = (df['판매단가'] - df['공급단가']) * df['주문-취소 수량']
    # else:
    #     df['NetProfit'] = 0

    valid_sales = df[df['주문-취소 수량'] > 0].copy()
    
    # Derived Columns
    if '광역지역' in valid_sales.columns:
        valid_sales['RegionGroup'] = valid_sales['광역지역'].apply(lambda x: '서울' if '서울' in str(x) else '비서울')
        
    # Month for Lifecycle
    if '주문일' in valid_sales.columns:
        valid_sales['YearMonth'] = valid_sales['주문일'].dt.to_period('M').astype(str)

    # Keywords Extraction (Simple - flattened for CSV)
    # Looker Studio doesn't handle lists well, so we might skip this or create a string
    # created a simple string of top keywords might be better, but for now we skip complex list columns
    
    print(f"Data Processed. Rows: {len(valid_sales)}")
    
    # Save to CSV
    valid_sales.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Saved cleaned data to {output_path}")

if __name__ == "__main__":
    input_csv = 'data/project1 - classification_results.csv'
    output_csv = 'data/project1 - looker_studio_source.csv'
    load_and_clean_data(input_csv, output_csv)
