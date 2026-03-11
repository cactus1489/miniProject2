import requests
from bs4 import BeautifulSoup
import csv
import json

def collect_all_movie_data():
    main_url = "https://www.kobis.or.kr/kobis/mobile/main/findRealTicketList.do"
    ajax_url = "https://www.kobis.or.kr/kobis/mobile/main/findRealTicketListAjax.do"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Referer": main_url,
        "Host": "www.kobis.or.kr"
    }

    session = requests.Session()

    print(f"Connecting to {main_url} to get CSRFToken...")
    try:
        response = session.get(main_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # CSRFToken 추출
        csrf_tag = soup.find('input', {'name': 'CSRFToken'})
        if not csrf_tag:
            print("Failed to find CSRFToken.")
            return
        csrf_token = csrf_tag['value']
        print(f"Found CSRFToken: {csrf_token}")
        
    except Exception as e:
        print(f"Error fetching main page: {e}")
        return

    # 전체 데이터 요청을 위한 Payload
    payload = {
        "curPage": "1",
        "repNationCd": "",
        "allMoreChk": "1", # 전체 데이터를 가져오는 핵심 파라미터
        "CSRFToken": csrf_token
    }

    print(f"Sending POST request to {ajax_url} for all data...")
    try:
        # AJAX 요청은 X-Requested-With 헤더가 필요할 수 있음
        headers["X-Requested-With"] = "XMLHttpRequest"
        response = session.post(ajax_url, headers=headers, data=payload)
        response.raise_for_status()
        
        # 인코딩 설정 (한글 깨짐 방지)
        response.encoding = 'utf-8'
        
        # 응답이 JSON 형식이므로 파싱 (앞뒤 공백 제거)
        content = response.text.strip()
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            print("Response is not JSON. Parsing as HTML...")
            data = None
            
    except Exception as e:
        print(f"Error fetching AJAX data: {e}")
        return

    movie_list = []
    
    # KOBIS AJAX 응답은 리스트 형태이거나 {"realTicketList": [...]} 형태일 수 있음
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict) and 'realTicketList' in data:
        items = data['realTicketList']
        
    if items:
        print(f"Total movies found: {len(items)}")
        for item in items:
            movie_list.append({
                "순위": item.get('rank', ''),
                "영화제목": item.get('movieNm', ''),
                "영문제목": item.get('movieNmEn', ''),
                "예매율": str(item.get('totIssuCntRatio', '0')) + "%",
                "예매관객수": "{:,}".format(int(item.get('totIssuCnt', 0))) if item.get('totIssuCnt') else "0"
            })
    else:
        # JSON이 아니거나 리스트가 없는 경우 (HTML 폴백)
        print("Falling back to HTML parsing...")
        soup = BeautifulSoup(response.text, 'html.parser')
        html_items = soup.select('a.block')
        print(f"Total movies found in HTML: {len(html_items)}")
        
        import re
        for item in html_items:
            try:
                rank_tag = item.select_one('.rank .num') or item.select_one('div.rank span')
                if not rank_tag: continue
                rank = rank_tag.get_text(strip=True)
                
                tit_tag = item.select_one('strong')
                if not tit_tag: continue
                full_text = tit_tag.get_text(separator=' ', strip=True)
                
                en_title_tag = tit_tag.select_one('span')
                if en_title_tag:
                    en_title = en_title_tag.get_text(strip=True).strip('()')
                    ko_title = full_text.split('(')[0].strip()
                else:
                    ko_title = full_text
                    en_title = ""
                
                dd_tags = item.select('dd')
                if not dd_tags: continue
                data_text = dd_tags[0].get_text(strip=True)
                
                occupancy_match = re.search(r'([\d.]+)%', data_text)
                audience_match = re.search(r'\(([\d,]+)명\)', data_text)
                
                movie_list.append({
                    "순위": rank,
                    "영화제목": ko_title,
                    "영문제목": en_title,
                    "예매율": occupancy_match.group(0) if occupancy_match else "0%",
                    "예매관객수": audience_match.group(1) if audience_match else "0"
                })
            except:
                continue

    if not movie_list:
        print("No movie data could be collected.")
        return

    # CSV 파일저장
    output_file = "movie_data.csv"
    keys = movie_list[0].keys()
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(movie_list)
        print(f"Successfully saved {len(movie_list)} movies to {output_file}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    collect_all_movie_data()
