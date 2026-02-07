
import pandas as pd
import numpy as np

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

# 결제금액 전처리 (Clean payment amount)
# 콤마 제거 및 숫자형 변환 (Remove commas and convert to numeric)
if df['결제금액'].dtype == 'object':
    df['결제금액_숫자'] = df['결제금액'].str.replace(',', '').astype(float)
else:
    df['결제금액_숫자'] = df['결제금액']

# 셀러별 총 매출액 계산 (Calculate total sales revenue per seller)
seller_revenue = df.groupby('셀러명')['결제금액_숫자'].sum().reset_index()
seller_revenue.rename(columns={'결제금액_숫자': 'total_revenue'}, inplace=True)

# 매출액 기준 내림차순 정렬 (Sort by revenue descending)
seller_revenue = seller_revenue.sort_values(by='total_revenue', ascending=False)

# 백분위수 계산 (Calculate percentile rank)
# pct=True인 경우 0~1 사이의 값 반환. 1일수록 높은 순위. (rank(pct=True) returns 0~1. Closer to 1 is higher rank.)
# 하지만 여기서는 상위 N%를 구해야 하므로, 내림차순 정렬 후 누적 비율을 계산하거나, rank를 사용하여 백분위를 계산해야 함.
# 여기서는 qcut을 사용하는 것이 더 간편할 수 있음. 하지만 정확한 상위 10%, 30% 등을 위해 rank 사용.

# 상위 % 계산을 위해 rank(method='min', ascending=False) 사용 -> 1등이 1
seller_revenue['rank'] = seller_revenue['total_revenue'].rank(method='min', ascending=False)
total_sellers = len(seller_revenue)
seller_revenue['percentile'] = seller_revenue['rank'] / total_sellers

# 등급 부여 함수 (Grade assignment function)
def assign_grade(percentile):
    if percentile <= 0.1: # Top 10%
        return 'A'
    elif percentile <= 0.3: # Top 10% ~ 30%
        return 'B'
    elif percentile <= 0.6: # Top 30% ~ 60%
        return 'C'
    else: # Bottom 40%
        return 'D'

seller_revenue['seller_grade'] = seller_revenue['percentile'].apply(assign_grade)

# 원본 데이터에 등급 정보 병합 (Merge grade info to original data)
# 기존에 seller_grade 컬럼이 있다면 삭제 후 병합 (Drop existing column if exists)
if 'seller_grade' in df.columns:
    df.drop(columns=['seller_grade'], inplace=True)

df = df.merge(seller_revenue[['셀러명', 'seller_grade']], on='셀러명', how='left')

# 결과 확인 (Verify results)
print("\n--- 셀러 등급 분포 (Seller Grade Distribution) ---")
print(seller_revenue['seller_grade'].value_counts().sort_index())

print("\n--- 등급별 평균 매출액 (Average Revenue by Grade) ---")
grade_avg_revenue = seller_revenue.groupby('seller_grade')['total_revenue'].mean()
print(grade_avg_revenue.apply(lambda x: f"{x:,.0f}원"))

# 등급별 셀러 예시 (Seller Examples by Grade)
print("\n--- 등급별 셀러 예시 (Seller Examples by Grade) ---")
for grade in ['A', 'B', 'C', 'D']:
    sample_seller = seller_revenue[seller_revenue['seller_grade'] == grade].iloc[0]
    print(f"[{grade}등급] {sample_seller['셀러명']} (매출: {sample_seller['total_revenue']:,.0f}원, 백분위: {sample_seller['percentile']*100:.1f}%)")

# 임시 컬럼 삭제 (Drop temporary column)
df.drop(columns=['결제금액_숫자'], inplace=True)

# 결과 저장 (Save results)
df.to_csv(output_path, index=False)
print(f"\n결과가 저장되었습니다: {output_path} (Results saved)")
