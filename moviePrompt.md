## 1) http 요청정보와 헤더
Request URL
https://www.kobis.or.kr/kobis/mobile/mast/mvie/searchMovieDtl.do?movieCd=20242837
Request Method
GET
Status Code
200 OK
Remote Address
210.104.16.53:443
Referrer Policy
strict-origin-when-cross-origin

host
www.kobis.or.kr
referer
https://www.kobis.or.kr/kobis/mobile/main/findRealTicketList.do
sec-ch-ua
"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"
sec-ch-ua-mobile
?0
sec-ch-ua-platform
"Windows"
sec-fetch-dest
document
sec-fetch-mode
navigate
sec-fetch-site
same-origin
sec-fetch-user
?1
upgrade-insecure-requests
1
user-agent
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36
## 2) payload 정보
movieCd=20242837
## 3) 응답의 일부를 response에서 일부를 복사해서 넣기
<a href="javascript:;" class="block" onclick="fn_movieDtl('20242837');">
	                    <span class="thumb">	                    	
	                    	<img src="/common/mast/movie/2026/02/thumb_x110/thn_0987da5282ff417ca513de6c66d2c288.jpg" alt="영화 포스터" onerror="fn_replaceBlankImg(this, '110');">
	                    </span>
	                    <div class="desc seatimg">
	                        <div class="rank">
	                            <span class="num">1</span>	                            
	                        </div>
	                        
	                        <strong class="tit ellip">왕과 사는 남자
								<span class="en ellip">
									(The King's Warden)
								</span>                        	
	                        </strong>
	                        <dl class="info_sales">
	                            <dt class="ico_comm ico_seatticket">좌석점유율(좌석수)</dt>
	                            <dd>
	                                   59.3% (1,051,661석)	                                
	                            </dd>
	                        </dl>
	                        <dl class="info_audience">
	                            <dt class="ico_comm ico_audience">관객수</dt>
	                            <dd>
	                                177,185명	                                
	                            </dd>
	                        </dl>
	                    </div>
	                </a>
## 4) 한페이지가 성공적으로 수집되는지 확인하고 csv파일로 저장하기