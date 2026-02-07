
import pandas as pd

# 데이터 파일 경로 설정 (Set data file path)
file_path = '/Users/ivy/Documents/class/eda2/data/project1 - classification_results.csv'
output_path = '/Users/ivy/Documents/class/eda2/data/project1 - classification_results.csv'

# 데이터 로드 (Load data)
try:
    df = pd.read_csv(file_path)
    print("데이터 로드 성공 (Data loaded successfully)")
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {file_path} (File not found)")
    exit()

# 셀러별 총 판매 건수 계산 (Calculate total sales count per seller)
seller_counts = df['셀러명'].value_counts()

# 셀러별 지역별 판매 건수 계산 (Calculate sales count per region for each seller)
seller_region_counts = df.groupby(['셀러명', '광역지역']).size().reset_index(name='count')

# 셀러별 지역 판매 비중 계산 (Calculate regional sales share for each seller)
seller_region_counts['total_sales'] = seller_region_counts['셀러명'].map(seller_counts)
seller_region_counts['share'] = seller_region_counts['count'] / seller_region_counts['total_sales']

# 지역 셀러 식별 (Identify Regional Sellers: share >= 0.5)
regional_sellers = seller_region_counts[seller_region_counts['share'] >= 0.5]['셀러명'].unique()

print(f"\n--- 지역 셀러 분석 결과 (Regional Seller Analysis) ---")
print(f"총 셀러 수 (Total Sellers): {len(seller_counts)}")
print(f"지역 셀러 수 (Regional Sellers): {len(regional_sellers)}")

# seller_type 컬럼 추가 (Add seller_type column)
df['seller_type'] = df['셀러명'].apply(lambda x: '지역셀러' if x in regional_sellers else '일반 셀러')

# 결과 확인 (Verify results)
print("\n--- 셀러 분류 결과 (Seller Classification Results) ---")
print(df['seller_type'].value_counts())

# 지역 셀러 예시 출력 (Print examples of Regional Sellers)
print("\n--- 지역 셀러 예시 (Regional Seller Examples) ---")
sample_regional_sellers = list(regional_sellers)[:5]
for seller in sample_regional_sellers:
    region_info = seller_region_counts[(seller_region_counts['셀러명'] == seller) & (seller_region_counts['share'] >= 0.5)]
    region = region_info['광역지역'].values[0]
    share = region_info['share'].values[0]
    print(f"셀러: {seller}, 주력 지역: {region} (비중: {share:.2f})")

# 결과 저장 (Save results)
df.to_csv(output_path, index=False)
print(f"\n결과가 저장되었습니다: {output_path} (Results saved)")
