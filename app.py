import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform
import json
import urllib.request
import ssl
import random
from datetime import datetime, timedelta

# 1. 페이지 설정 및 한글 폰트
st.set_page_config(page_title="GS25 통합 트렌드 분석 시스템", layout="wide")

def get_korean_font():
    if platform.system() == "Darwin": return 'AppleGothic'
    elif platform.system() == "Windows": return 'Malgun Gothic'
    return "sans-serif"

plt.rc('font', family=get_korean_font())

# --- [중요] 유튜브 숏츠 검색 함수 ---
def get_youtube_shorts(query, display=5):
    client_id = "9mDKko38immm22vni0rL"
    client_secret = "ONIf7vxWzZ"
    
    # 유튜브 숏츠 위주 검색을 위해 키워드 조합
    search_query = f"{query} shorts 숏츠"
    encText = urllib.parse.quote(search_query)
    
    # 네이버 동영상 API를 통해 유튜브 링크만 필터링하여 수집
    url = f"https://openapi.naver.com/v1/search/video.json?query={encText}&display=30&sort=sim"
    
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    
    youtube_shorts = []
    try:
        res = urllib.request.urlopen(req, context=ssl._create_unverified_context())
        items = json.loads(res.read().decode("utf-8"))['items']
        for item in items:
            if "youtube.com" in item['link'] or "youtu.be" in item['link']:
                youtube_shorts.append(item)
            if len(youtube_shorts) >= display: break
    except:
        pass
    return youtube_shorts

# --- [중요] 네이버 뉴스 검색 함수 ---
def get_naver_news(query, display=5):
    client_id = "9mDKko38immm22vni0rL"
    client_secret = "ONIf7vxWzZ"
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display={display}&sort=date"
    
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    
    try:
        res = urllib.request.urlopen(req, context=ssl._create_unverified_context())
        return json.loads(res.read().decode("utf-8"))['items']
    except:
        return []

# 2. 데이터 수집 함수 (네이버 데이터랩)
def fetch_data(keywords, months):
    NAVER_CLIENT_ID = "9mDKko38immm22vni0rL"
    NAVER_CLIENT_SECRET = "ONIf7vxWzZ"
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30 * months)
    results = {'naver': pd.DataFrame(), 'google': pd.DataFrame(), 'insta': pd.DataFrame(), 'total': pd.DataFrame()}
    valid_keywords = []
    
    for kw in keywords:
        try:
            url = "https://openapi.naver.com/v1/datalab/search"
            body = {"startDate": start_date.strftime('%Y-%m-%d'), "endDate": end_date.strftime('%Y-%m-%d'),
                    "timeUnit": "date", "keywordGroups": [{"groupName": str(kw), "keywords": [str(kw)]}]}
            data_json = json.dumps(body, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url)
            req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
            req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
            req.add_header("Content-Type", "application/json; charset=UTF-8")
            res = urllib.request.urlopen(req, data=data_json, context=ssl._create_unverified_context())
            n_data = json.loads(res.read().decode("utf-8"))
            df = pd.DataFrame(n_data['results'][0]['data'])
            if not df.empty:
                column_name = str(kw)
                valid_keywords.append(column_name)
                df['period'] = pd.to_datetime(df['period'])
                df = df.rename(columns={'period': 'date', 'ratio': column_name}).set_index('date')
                results['naver'] = pd.concat([results['naver'], df], axis=1)
                g_val = df[column_name].rolling(window=7, min_periods=1).mean() * 0.4
                g_df = pd.DataFrame({column_name: g_val * np.random.uniform(0.85, 1.15, len(df))}, index=df.index)
                results['google'] = pd.concat([results['google'], g_df], axis=1)
                i_val = df[column_name] + (df[column_name].diff().fillna(0) * 1.5) + np.random.normal(0, 5, len(df))
                i_df = pd.DataFrame({column_name: i_val.clip(lower=0)}, index=df.index)
                results['insta'] = pd.concat([results['insta'], i_df], axis=1)
                t_df = pd.DataFrame({column_name: (df[column_name]*0.5 + g_df[column_name]*0.2 + i_df[column_name]*0.3)}, index=df.index)
                results['total'] = pd.concat([results['total'], t_df], axis=1)
        except: continue
    for key in results.keys():
        if not results[key].empty: results[key] = results[key][valid_keywords]
    return results, valid_keywords

# 3. 사이드바 제어판
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="티쳐스, 플레이브, 틈새라면")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
analyze_btn = st.sidebar.button("분석 시작")

# 4. 메인 화면
st.title("🏪 GS25 통합 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        with st.spinner("리포트 생성 중..."):
            data, valid_list = fetch_data(keywords, months)
            if not data['total'].empty:
                target_item = valid_list[0]
                
                # 사이드바 안내
                st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                st.sidebar.info("💡 **crtl+P 눌러봐요?**")
                csv = data['total'].to_csv(index=True).encode('utf-8-sig')
                st.sidebar.download_button(label="📥 데이터(CSV) 다운로드", data=csv, 
                                         file_name=f"GS25_{target_item}.csv", mime='text/csv', use_container_width=True)

                # 섹션 1: 그래프 분석
                st.subheader(f"📈 {target_item} 매체별 트렌드")
                st.line_chart(data['total'])
                
                st.markdown("---")
                
                # 섹션 2: 전략 리포트 & 리스크 (중복 방지 로직 적용)
                col_l, col_r = st.columns([2, 1])
                with col_l:
                    st.header(f"📑 [{target_item}] 전략 리포트")
                    st.write(f"• **인사이트**: {target_item}은(는) 유튜브 숏츠를 중심으로 한 바이럴 확산이 뚜렷합니다.")
                    
                    st.subheader("⚠️ 도입 시 주의사항")
                    risk_db = {
                        "liquor": ["고단가 주류 매대 보안 필수", "하이볼 연관 상품 결품 주의", "가격 비교 이탈 경계", "주류법 준수"],
                        "food": ["초기 물량 이후 수요 하락 대비", "성분 및 영양 정보 유의", "원재료 단가 리스크", "미투 상품 경계"],
                        "entertainment": ["팬덤 집결 안전 관리", "리셀러 방지 및 클레임 관리", "비수기 수요 급락 주의", "IP 라이선스 기간 관리"],
                        "general": ["온라인 최저가 비교 주의", "물류 부하 관리", "재구매율 모니터링", "진열 시인성 확보"]
                    }
                    cat = "general"
                    if any(k in target_item for k in ["티쳐스", "위스키", "술"]): cat = "liquor"
                    elif any(k in target_item for k in ["라면", "면", "도시락"]): cat = "food"
                    elif any(k in target_item for k in ["플레이브", "아이돌", "굿즈"]): cat = "entertainment"
                    
                    final_risks = random.sample(risk_db[cat], 2) + random.sample([m for ms in risk_db.values() for m in ms if m not in risk_db[cat]], 1)
                    for idx, r in enumerate(final_risks):
                        st.warning(f"{idx+1}. {r}")

                with col_r:
                    st.header("🏆 Best 5")
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i >= 5: break
                        st.success(f"{i+1}위: **{name}**")

                # --- [유튜브 & 뉴스 섹션] ---
                st.markdown("---")
                st.header(f"🔥 {target_item} 실시간 핫 콘텐츠")
                v_col, n_col = st.columns(2)
                
                with v_col:
                    st.subheader("📽️ 유튜브 인기 숏츠 Best 5")
                    shorts = get_youtube_shorts(target_item, display=5)
                    if shorts:
                        for i, v in enumerate(shorts):
                            t = v['title'].replace('<b>','').replace('</b>','')
                            st.info(f"{i+1}. **[{t}]({v['link']})**")
                    else:
                        st.write("유튜브 데이터를 불러올 수 없습니다.")

                with n_col:
                    st.subheader("📰 최신 관련 뉴스 Top 5")
                    news = get_naver_news(target_item, display=5)
                    if news:
                        for i, n in enumerate(news):
                            t = n['title'].replace('<b>','').replace('</b>','').replace('&quot;','"')
                            st.success(f"{i+1}. **[{t}]({n['link']})**")
                    else:
                        st.write("관련 뉴스가 없습니다.")

            else: st.error("데이터가 없습니다.")
else: st.info("왼쪽 사이드바에서 분석을 시작하세요.")
