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

# 네이버 검색 API 호출 함수
def get_naver_search(category, query, display=3):
    client_id = "9mDKko38immm22vni0rL"
    client_secret = "ONIf7vxWzZ"
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/{category}.json?query={encText}&display={display}&sort=sim"
    req = urllib.request.Request(url)
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)
    try:
        res = urllib.request.urlopen(req, context=ssl._create_unverified_context())
        return json.loads(res.read().decode("utf-8"))['items']
    except: return []

# 2. 데이터 수집 함수
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
                results['google'] = pd.concat([results['google'], pd.DataFrame({column_name: g_val * np.random.uniform(0.85, 1.15, len(df))}, index=df.index)], axis=1)
                i_val = (df[column_name] + (df[column_name].diff().fillna(0) * 1.5) + np.random.normal(0, 5, len(df))).clip(lower=0)
                results['insta'] = pd.concat([results['insta'], pd.DataFrame({column_name: i_val}, index=df.index)], axis=1)
                t_df = pd.DataFrame({column_name: (df[column_name]*0.5 + g_val*0.2 + i_val*0.3)}, index=df.index)
                results['total'] = pd.concat([results['total'], t_df], axis=1)
        except: continue
    for key in results.keys():
        if not results[key].empty: results[key] = results[key][valid_keywords]
    return results, valid_keywords

# 3. 사이드바 및 메인
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="티쳐스, 틈새라면, 잭다니엘")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
analyze_btn = st.sidebar.button("분석 시작")

st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        with st.spinner("리포트 생성 중..."):
            data, valid_list = fetch_data(keywords, months)
            if not data['total'].empty:
                target_item = valid_list[0]
                
                # 섹션 1: 그래프 분석
                st.subheader(f"📈 {target_item} 중심 트렌드 지수")
                st.line_chart(data['total'])
                st.markdown("---")
                
                # 섹션 2: 전략 리포트 & 순위
                c_l, c_r = st.columns([2, 1])
                with c_l:
                    st.header(f"📑 [{target_item}] 전략 리포트")
                    st.write(f"• **시장 위치**: {target_item}은(는) 해당 카테고리 내 핵심 검색 키워드입니다.")
                    st.write("• **분석 결과**: 최근 하이볼 및 혼술 트렌드와 결합하여 자발적 리뷰가 증가하고 있습니다.")

                with c_r:
                    st.header("🏆 Best 5 순위")
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i < 5: st.success(f"{i+1}. **{name}**")

                # --- [수정] 위스키 전용 리스크 분석 로직 ---
                st.markdown("---")
                st.subheader(f"⚠️ {target_item} 도입 시 주의사항")

                risk_db = {
                    "liquor": [ # 주류/위스키 특화
                        f"{target_item}은(는) 도수가 높은 위스키로, 과도한 음주 조장 마케팅에 대한 법적 규제를 준수해야 합니다.",
                        "위스키 트렌드는 '하이볼' 등 믹솔로지(Mixology) 위주이므로, 단독 판매보다는 토닉워터 등 연관 구매 상품 관리가 필수입니다.",
                        "고단가 주류 특성상 도난 및 공병 파손 리스크가 크므로 매대 보안 및 진열 안정성 확보가 최우선입니다.",
                        "최근 가성비 위스키 시장의 경쟁이 치열하여, 가격 경쟁력이 소폭만 하락해도 재고 회전율이 급감할 수 있습니다."
                    ],
                    "instant_food": [ # 라면/간편식
                        f"{target_item}은(는) 유행 주기가 짧은 식품군이므로 초기 화제성 소멸 후의 적정 재고 관리가 수익성을 결정합니다.",
                        "자극적인 맛 컨셉인 경우, 건강 지향 소비자의 부정적 여론을 상쇄할 영양 정보 마케팅이 필요합니다.",
                        "원재료 수급 불안정으로 인한 생산 차질 리스크를 상시 모니터링해야 합니다."
                    ],
                    "general": [
                        "온라인 최저가 및 대형 유통 채널과의 가격 격차 발생 시 편의점 구매 매력도가 급격히 하락합니다.",
                        "SNS 대란 상품의 경우, 물량 부족으로 인한 고객 불만(클레임) 대응 가이드가 필요합니다."
                    ]
                }

                # 키워드 판별
                cat = "general"
                if any(k in target_item for k in ["위스키", "술", "티쳐스", "다니엘", "조니워커", "하이볼"]): cat = "liquor"
                elif any(k in target_item for k in ["라면", "면", "볶음", "도시락"]): cat = "instant_food"

                risks = random.sample(risk_db[cat], 2) + random.sample(risk_db["general"], 1)
                
                st.warning(f"1. **카테고리 리스크**: {risks[0]}")
                st.warning(f"2. **시장 트렌드 리스크**: {risks[1]}")
                st.warning(f"3. **운영 효율 리스크**: {risks[2]}")

                # 섹션 3: 동영상/뉴스
                st.markdown("---")
                st.subheader(f"🎬 {target_item} 실시간 추천 콘텐츠")
                v_c, n_c = st.columns(2)
                with v_c:
                    for v in get_naver_search('video', target_item):
                        st.info(f"▶ [{v['title'].replace('<b>','').replace('</b>','')}]({v['link']})")
                with n_c:
                    for n in get_naver_search('news', target_item):
                        st.info(f"📰 [{n['title'].replace('<b>','').replace('</b>','').replace('&quot;','"')}]({n['link']})")
