
import pandas as pd
import numpy as np

# 데이터 파일 경로 설정 (Set data file path)
file_path = '/Users/ivy/Documents/class/eda2/data/project1 - preprocessed_data.csv'
output_path = '/Users/ivy/Documents/class/eda2/data/project1 - classification_results.csv'

# 데이터 로드 (Load data)
try:
    df = pd.read_csv(file_path)
    print("데이터 로드 성공 (Data loaded successfully)")
except FileNotFoundError:
    print(f"파일을 찾을 수 없습니다: {file_path} (File not found)")
    exit()

# 프리미엄 여부 초기화 (Initialize premium status)
df['is_premium'] = '일반'

# 1. 선물세트: 상품 설명에 선물세트/선물용이 명시된 모든 상품
# (Gift Set: All products with 'Gift Set'/'For Gift' in product description or option)
gift_mask = (df['상품명'].str.contains('선물세트|선물용', na=False)) | \
            (df['고객선택옵션'].str.contains('선물세트|선물용', na=False))

# 2. 감귤 계열: 품종이 '감귤'이면서 크기가 '로얄과'인 경우
# (Tangerine Series: Variety is 'Tangerine' AND Size is 'Royal')
tangerine_mask = (df['품종'] == '감귤') & (df['과수 크기'] == '로얄과')

# 3. 만감류: 황금향, 한라봉, 레드향, 천혜향 중 크기가 '중과', '중대과', '대과'인 경우
# (Mangamryu: Variety is one of ['Hwanggeumhyang', 'Hallabong', 'Redhyang', 'Cheonhyehyang'] AND Size is one of ['Medium', 'Medium-Large', 'Large'])
mangamryu_varieties = ['황금향', '한라봉', '레드향', '천혜향']
mangamryu_sizes = ['중과', '중대과', '대과']
mangamryu_mask = (df['품종'].isin(mangamryu_varieties)) & (df['과수 크기'].isin(mangamryu_sizes))

# 조건 적용 (Apply conditions)
premium_mask = gift_mask | tangerine_mask | mangamryu_mask
df.loc[premium_mask, 'is_premium'] = '프리미엄'

# 결과 확인 (Verify results)
print("\n--- 분류 결과 (Classification Results) ---")
print(df['is_premium'].value_counts())

# 샘플 데이터 출력 (Print sample data for premium items)
print("\n--- 프리미엄 상품 예시 (Premium Product Examples) ---")
print(df[df['is_premium'] == '프리미엄'][['상품명', '품종', '과수 크기', 'is_premium']].head())

# 결과 저장 (Save results)
df.to_csv(output_path, index=False)
print(f"\n결과가 저장되었습니다: {output_path} (Results saved)")
