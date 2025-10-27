import json
import os

# JSON 파일 읽기
file_path = 'nasdaqlisted.json'
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== JSON 파일 정보 ===')
print(f'파일 경로: {file_path}')
print(f'총 항목 수: {len(data):,}개')
print(f'파일 크기: {os.path.getsize(file_path) / 1024:.1f} KB')

print('\n=== 구조 검증 ===')
print(f'키 이름: {list(data[0].keys())}')
print(f'첫 항목: {data[0]}')
print(f'마지막 항목: {data[-1]}')

print('\n=== 사용자 예시 확인 ===')
examples = {
    'AAPL': 'Apple',
    'MSFT': 'Microsoft',
    'TSLL': 'TSLA Bull 2X',
    'AMDL': 'AMD 2x Long ETF',
    'AMD': 'Advanced Micro Devices'
}

for item in data:
    if item['Symbol'] in examples:
        expected = examples[item['Symbol']]
        actual = item['CompanyName']
        status = '✓' if actual == expected else '✗'
        print(f"{status} {item['Symbol']}: {actual}")

print('\n=== AMD 관련 항목 샘플 ===')
amd_items = [item for item in data if 'AMD' in item['Symbol']]
for item in amd_items[:8]:
    print(f"{item['Symbol']}: {item['CompanyName']}")
