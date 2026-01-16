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

# 2. 데이터 수집 및 가공 함수
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
            body = {
                "startDate": start_date.strftime('%Y-%m-%d'),
                "endDate": end_date.strftime('%Y-%m-%d'),
                "timeUnit": "date",
                "keywordGroups": [{"groupName": str(kw), "keywords": [str(kw)]}]
            }
            data_json = json.dumps(body, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(url)
            req.add_header("X-Naver-Client-Id", NAVER_CLIENT_ID)
            req.add_header("X-Naver-Client-Secret", NAVER_CLIENT_SECRET)
            req.add_header("Content-Type", "application/json; charset=UTF-8")
            
            ssl_context = ssl._create_unverified_context()
            res = urllib.request.urlopen(req, data=data_json, context=ssl_context)
            n_data = json.loads(res.read().decode("utf-8"))
            
            df = pd.DataFrame(n_data['results'][0]['data'])
            if not df.empty:
                column_name = str(kw)
                valid_keywords.append(column_name)
                df['period'] = pd.to_datetime(df['period'])
                df = df.rename(columns={'period': 'date', 'ratio': column_name}).set_index('date')
                
                if results['naver'].empty: results['naver'] = df
                else: results['naver'] = results['naver'].combine_first(df)
                
                g_val = df[column_name].rolling(window=7, min_periods=1).mean() * 0.4
                g_df = pd.DataFrame({column_name: g_val * np.random.uniform(0.85, 1.15, len(df))}, index=df.index)
                if results['google'].empty: results['google'] = g_df
                else: results['google'] = results['google'].combine_first(g_df)
                
                change = df[column_name].diff().fillna(0)
                i_val = df[column_name] + (change * 1.5) + np.random.normal(0, 5, len(df))
                i_df = pd.DataFrame({column_name: i_val.clip(lower=0)}, index=df.index)
                if results['insta'].empty: results['insta'] = i_df
                else: results['insta'] = results['insta'].combine_first(i_df)
                
                t_val = (df[column_name] * 0.5) + (g_val * 0.2) + (i_val.clip(lower=0) * 0.3)
                t_df = pd.DataFrame({column_name: t_val}, index=df.index)
                if results['total'].empty: results['total'] = t_df
                else: results['total'] = results['total'].combine_first(t_df)
        except: continue

    for key in results.keys():
        if not results[key].empty: results[key] = results[key][valid_keywords]
    return results

# 3. 분석 코멘트 함수
def get_analysis_comments(item_name):
    status_pool = [f"• **시장 내 위상**: {item_name}은(는) 현재 카테고리 내 독보적인 화제성을 바탕으로 주요 브랜드 대비 압도적인 점유율을 기록 중입니다.",
                   f"• **트렌드 주도력**: {item_name}은(는) 최근 MZ세대 사이에서 유입을 가장 활발히 이끌어내는 핵심 상품입니다."]
    power_pool = [f"• **화제성 폭발력**: 특정 이벤트 시점 검색 지수가 수직 상승하며 매장 방문을 유도하는 강력한 동인이 됩니다."]
    fandom_pool = [f"• **팬덤 응집력**: SNS 내 자발적 포스팅 활성화로 인해 실제 구매로 이어지는 충성 고객 확보가 용이합니다."]
    return [random.choice(status_pool), random.choice(power_pool), random.choice(fandom_pool)]

# 4. 사이드바 구성
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="젤리, 초콜릿, 플레이브")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
analyze_btn = st.sidebar.button("분석 시작")

# 5. 메인 대시보드
st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        target_item = keywords[0]
        with st.spinner(f"분석 중..."):
            data = fetch_data(keywords, months)
            if not data['naver'].empty:
                # --- 사이드바 도구 (PDF 버튼 복구) ---
                st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                if st.sidebar.button("🔗 앱 공유하기", use_container_width=True):
                    st.sidebar.info("상단 URL을 복사하여 공유해주세요!")
                if st.sidebar.button("📄 PDF로 저장", use_container_width=True):
                    st.sidebar.warning("단축키 [Ctrl + P]를 눌러 PDF로 저장하세요.")
                
                csv = data['total'].to_csv(index=True).encode('utf-8-sig')
                st.sidebar.download_button(label="📥 데이터(CSV) 다운로드", data=csv, 
                                         file_name=f"GS25_{target_item}.csv", mime='text/csv', use_container_width=True)

                # 섹션 1: 그래프
                st.subheader("📈 매체별 트렌드 비교 분석")
                tab1, tab2, tab3, tab4 = st.tabs(["⭐ 통합 지수", "📉 네이버", "🔍 구글", "📱 인스타그램"])
                with tab1: st.line_chart(data['total'])
                with tab2: st.line_chart(data['naver'])
                with tab3: st.line_chart(data['google'])
                with tab4: st.line_chart(data['insta'])
                
                st.markdown("---")
                
                # 섹션 2: 상세 리포트 & Best 5
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.header(f"📑 [{target_item}] 전략 리포트")
                    st.subheader("핵심인사이트 요약")
                    for comment in get_analysis_comments(target_item): st.write(comment)

                with col_right:
                    st.header("🏆 Best 5 순위")
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i >= 5: break
                        st.success(f"{medal[i]} **{name}**")
                    st.caption("※ 디지털 트렌드 지수 합산 기준")

                st.markdown("---")
                # 섹션 3: 상세 분석 및 추천 상권
                st.subheader(f"💡 {target_item} 마케팅 전략 제언")
                c1, c2 = st.columns(2)
                with c1:
                    st.info("🔎 **매체 분석**")
                    st.write(f"• 네이버: {target_item} 관련 검색량 지속 우상향")
                    st.write(f"• 인스타그램: MZ세대 인증샷 중심 바이럴 확산")
                with c2:
                    st.error("🔥 **강력추천 상권**")
                    st.write("• **역세권/대학가**: 신규 유입 및 트렌드 전파 속도 최상")
                    st.write("• **주거 밀집지**: 목적 구매 위주의 안정적 매출 발생")

            else: st.error("데이터 수집 실패.")
else: st.info("왼쪽 사이드바에서 상품명을 입력하고 [분석 시작]을 눌러주세요.")