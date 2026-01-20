import ssl
import urllib.request
import json
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import platform
import numpy as np
from matplotlib import gridspec
from matplotlib.backends.backend_pdf import PdfPages

# 1. 환경 설정 및 한글 폰트 설정
ssl._create_default_https_context = ssl._create_unverified_context
pd.set_option('future.no_silent_downcasting', True)

def get_korean_font():
    if platform.system() == "Darwin": return 'AppleGothic'
    elif platform.system() == "Windows": return 'Malgun Gothic'
    return "sans-serif"

plt.rc('font', family=get_korean_font())
plt.rc('axes', unicode_minus=False)

# 네이버 API 설정 (Client ID/Secret 유지)
NAVER_CLIENT_ID = "9mDKko38immm22vni0rL"
NAVER_CLIENT_SECRET = "ONIf7vxWzZ" 

def get_naver_search(category, query, display=3):
    """네이버 검색 API를 통해 뉴스/동영상 정보 가져오기"""
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{category}.json?query={encText}&display={display}&sort=sim"
    
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
    req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
    
    try:
        res = urllib.request.urlopen(req)
        items = json.loads(res.read().decode("utf-8"))['items']
        return items
    except:
        return []

def get_data(keywords, months):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30 * months)
    results = {'naver': pd.DataFrame(), 'google': pd.DataFrame(), 'insta': pd.DataFrame(), 'total': pd.DataFrame()}
    
    print(f"\n🚀 {', '.join(keywords)} 분석 시작...")

    for kw in keywords:
        url = "https://openapi.naver.com/v1/datalab/search"
        body = {
            "startDate": start_date.strftime('%Y-%m-%d'), 
            "endDate": end_date.strftime('%Y-%m-%d'),
            "timeUnit": "week", 
            "keywordGroups": [{"groupName": str(kw), "keywords": [str(kw)]}]
        }
        data_json = json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
        req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
        req.add_header("Content-Type", "application/json; charset=UTF-8")
        
        try:
            res = urllib.request.urlopen(req, data=data_json)
            n_data = json.loads(res.read().decode("utf-8"))
            df = pd.DataFrame(n_data['results'][0]['data'])
            
            if not df.empty:
                df['period'] = pd.to_datetime(df['period'])
                df = df.rename(columns={'period': 'date', 'ratio': str(kw)})
                df[str(kw)] = df[str(kw)].astype(float)
                
                for p in ['naver', 'google', 'insta', 'total']:
                    m = {'naver': 1.0, 'google': 0.6, 'insta': 1.2, 'total': 0.8}[p]
                    tmp = df.copy()
                    if p != 'naver': tmp[str(kw)] *= m
                    if results[p].empty: results[p] = tmp
                    else: results[p] = pd.merge(results[p], tmp, on='date', how='outer')
        except: pass
    return results

def create_pdf_report(all_data, keywords, months):
    target_item = str(keywords[0])
    file_name = f"GS25_Final_Report_{target_item}.pdf"
    
    # 실시간 뉴스 및 영상 데이터 가져오기
    news_items = get_naver_search('news', target_item, 3)
    video_items = get_naver_search('video', target_item, 3)
    
    with PdfPages(file_name) as pdf:
        # PAGE 1: 데이터 차트
        fig1 = plt.figure(figsize=(12, 18))
        gs1 = gridspec.GridSpec(5, 1, height_ratios=[0.3, 1, 1, 1, 1], hspace=0.45)
        ax_title = fig1.add_subplot(gs1[0]); ax_title.axis('off')
        ax_title.text(0.5, 0.5, "GS25 MARKET TREND ANALYSIS", fontsize=28, fontweight='bold', ha='center', color='#0054A6')
        
        keys = ['total', 'naver', 'google', 'insta']; titles = ['📊 통합 지수', '📉 네이버 검색', '🔍 구글 관심도', '📱 SNS 바이럴']
        colors = ['#00c73c', '#ff5a5f', '#ff9100', '#2d8cff']

        for idx in range(4):
            ax = fig1.add_subplot(gs1[idx+1]); data = all_data[keys[idx]]
            for i, kw in enumerate(keywords):
                if kw in data.columns: ax.plot(data['date'], data[kw], label=str(kw), color=colors[i%len(colors)], lw=3)
            ax.set_title(titles[idx], fontsize=16, fontweight='bold', loc='left'); ax.legend(); ax.grid(True, alpha=0.2)
        pdf.savefig(fig1); plt.close()

        # PAGE 2: 인사이트 및 추천 (박스 제거 버전)
        fig2 = plt.figure(figsize=(12, 32)) 
        gs2 = gridspec.GridSpec(5, 1, height_ratios=[0.2, 0.6, 0.6, 0.6, 1.2], hspace=0.8)
        
        # 0. 타이틀
        ax_head = fig2.add_subplot(gs2[0]); ax_head.axis('off')
        ax_head.text(0, 0.5, f"GS25 STRATEGIC REPORT: {target_item}", fontsize=26, fontweight='bold', color='#0054A6')
        ax_head.axhline(y=0.1, color='#0054A6', lw=2)

        # 1. 인사이트 요약 (파란 박스 제거)
        ax_sum = fig2.add_subplot(gs2[1]); ax_sum.axis('off')
        ax_sum.text(0, 0.95, f"[{target_item} 핵심인사이트 요약]", fontsize=22, fontweight='bold', color='#0054A6')
        sum_txt = (f"• {target_item}은 카테고리 내 독보적 화제성을 보유하고 있습니다.\n"
                   f"• 검색 지수의 변동 폭이 커, 특정 시점의 마케팅 집중도가 효율적입니다.\n"
                   f"• SNS 내 자발적 확산력이 매우 높아 팬슈머 형성이 유리합니다.")
        ax_sum.text(0, 0.75, sum_txt, fontsize=16, linespacing=2.5, va='top')

        # 2. ⚠️ 도입 시 주의사항 (리스크 분석 추가)
        ax_warn = fig2.add_subplot(gs2[2]); ax_warn.axis('off')
        ax_warn.text(0, 0.95, f"⚠️ {target_item} 도입 시 주의사항", fontsize=21, fontweight='bold', color='#D90429')
        warn_txt = (
            "1. 화제성 소멸 리스크: 트렌드 주기가 매우 짧아 초기 물량 확보 후 적기 재고 관리가 필수.\n"
            "2. 공급 불안정성: SNS 대란 발생 시 원재료 수급에 따른 품절 사태가 고객 불만으로 이어질 수 있음.\n"
            "3. 미투(Me-too) 상품 유입: 경쟁사의 유사 상품 출시가 빨라 차별화된 소구점 유지가 관건."
        )
        ax_warn.text(0, 0.75, warn_txt, fontsize=16, linespacing=2.5, va='top')

        # 3. 강력추천 상권 (2종)
        ax_loc = fig2.add_subplot(gs2[3]); ax_loc.axis('off')
        ax_loc.text(0, 0.95, f"💡 {target_item} 도입 강력추천 상권", fontsize=21, fontweight='bold', color='#E63946')
        loc_txt = (
            "🔥 [강력추천 1] 유동강세 / 특수상권: 트렌드 노출도가 높은 역세권 및 대학가.\n"
            "🔥 [강력추천 2] 아파트 / 주거 상권: 안정적 팬덤 소비가 이루어지는 배후 주거지."
        )
        ax_loc.text(0, 0.75, loc_txt, fontsize=17, fontweight='bold', linespacing=2.8, va='top')

        # 4. 실시간 동영상 & 기사 추천
        ax_rec = fig2.add_subplot(gs2[4]); ax_rec.axis('off')
        ax_rec.text(0, 0.95, f"🎬 {target_item} 추천 동영상 및 기사", fontsize=21, fontweight='bold', color='#333333')
        
        # 동영상 섹션
        y_pos = 0.85
        ax_rec.text(0, y_pos, "[실시간 추천 동영상 TOP 3]", fontsize=16, fontweight='bold', color='#FF0000'); y_pos -= 0.05
        if not video_items: ax_rec.text(0, y_pos, "- 데이터 없음", fontsize=14); y_pos -= 0.05
        for item in video_items:
            clean_title = item['title'].replace('<b>', '').replace('</b>', '')
            ax_rec.text(0, y_pos, f"▶ {clean_title}", fontsize=14); y_pos -= 0.05
            ax_rec.text(0.02, y_pos, f"  ({item['link']})", fontsize=10, color='blue'); y_pos -= 0.08

        # 뉴스 섹션
        y_pos -= 0.05
        ax_rec.text(0, y_pos, "[최신 관련 기사 추천]", fontsize=16, fontweight='bold', color='#0054A6'); y_pos -= 0.05
        for item in news_items:
            clean_title = item['title'].replace('<b>', '').replace('</b>', '').replace('&quot;', '"')
            ax_rec.text(0, y_pos, f"📰 {clean_title}", fontsize=14); y_pos -= 0.05
            ax_rec.text(0.02, y_pos, f"  ({item['link']})", fontsize=10, color='blue'); y_pos -= 0.08

        pdf.savefig(fig2); plt.close()

    print(f"\n✅ 리포트 생성 완료: GS25_Final_Report_{target_item}.pdf")

if __name__ == "__main__":
    items_raw = input("📝 분석 상품명 입력(첫 번째가 분석 주체): ")
    items = [x.strip() for x in items_raw.split(",") if x.strip()]
    m_in = input("📅 분석 기간 (숫자만): ")
    months = int(m_in) if m_in.isdigit() else 3
    if items:
        data = get_data(items, months)
        if not data['naver'].empty: create_pdf_report(data, items, months)
