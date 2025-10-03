from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os, re, time, urllib.parse

# 크롬 옵션 설정
options = Options()
options.add_argument("--headless")
options.add_argument("--log-level=3")  # 오류 로그 줄이기
options.add_argument("--ignore-certificate-errors")  # SSL 인증서 오류 무시

driver = webdriver.Chrome(options=options)

# 스크래핑할 나무위키 페이지 URL 목록
urls = [
    #서강대
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90",
    #역사
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%EC%97%AD%EC%82%AC",
    #상징
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%EC%83%81%EC%A7%95",
    #학사 제도
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%ED%95%99%EC%82%AC%20%EC%A0%9C%EB%8F%84",
    #전공 제도
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%EC%A0%84%EA%B3%B5%20%EC%A0%9C%EB%8F%84",
    #교류 제도
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%EA%B5%90%EB%A5%98%20%EC%A0%9C%EB%8F%84",
    #학부
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%ED%95%99%EB%B6%80",
    #캠퍼스
    "https://namu.wiki/w/%EC%84%9C%EA%B0%95%EB%8C%80%ED%95%99%EA%B5%90/%EC%BA%A0%ED%8D%BC%EC%8A%A4"
]

for url in urls:
    driver.get(url)
    time.sleep(10)

    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # 텍스트들이 들어 있는 요소들
    text_blocks = soup.select(".M8xPxt04")

    output_lines = []
    for block in text_blocks:
        text = block.get_text(strip=True)
        if not text:
            continue

        # 제목인지 여부: bold 태그 포함 & 길이 제한
        if block.find("strong") and len(text) <= 50:
            output_lines.append(f"\n\n### {text}")
        else:
            output_lines.append(text)
    
    # 파일 이름: URL에서 마지막 부분만 추출
    title = urllib.parse.unquote(url.split("/")[-1]).replace(" ", "_")
    filename = f"namuwiki_{title}.txt"

    with open(os.path.join("documents", filename), "w", encoding="utf-8") as f:
        f.write("\n\n".join(output_lines))

    print(f"✅ 저장 완료: {filename}")
    
driver.quit()

print("모든 페이지 처리 완료")