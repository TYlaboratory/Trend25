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

# 2. 데이터 수집 함수 (입력 순서 유지 로직 포함)
def fetch_data(keywords, months):
    NAVER_CLIENT_ID = "9mDKko38immm22vni0rL"
    NAVER_CLIENT_SECRET = "ONIf7vxWzZ"
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30 * months)
    
    results = {'naver': pd.DataFrame(), 'google': pd.DataFrame(), 'insta': pd.DataFrame(), 'total': pd.DataFrame()}
    
    # 실제 수집에 성공한 키워드들을 입력 순서대로 담을 리스트
    ordered_keywords = []
    
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
                ordered_keywords.append(column_name) # 수집 성공 시 순서 리스트에 추가
                
                df['period'] = pd.to_datetime(df['period'])
                df = df.rename(columns={'period': 'date', 'ratio': column_name}).set_index('date')
                
                # 데이터 병합
                if results['naver'].empty: results['naver'] = df
                else: results['naver'] = results['naver'].combine_first(df)
                
                # 구글/인스타/통합 지수 생성 (시뮬레이션)
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

    # 핵심: 모든 결과 데이터프레임의 컬럼 순서를 입력받은 ordered_keywords 순서로 강제 재배치
    for key in results.keys():
        if not results[key].empty:
            # 존재하는 컬럼만 필터링하여 순서 적용
            actual_cols = [c for c in ordered_keywords if c in results[key].columns]
            results[key] = results[key][actual_cols]
            
    return results

# 3. 코멘트 함수
def get_analysis_comments(item_name):
    status_pool = [f"• **시장 내 위상**: {item_name}은(는) 현재 카테고리 내 독보적인 화제성을 보유하고 있습니다.",
                   f"• **트렌드 주도력**: 최근 편의점 신상품 중 가장 활발한 유입을 이끄는 핵심 상품입니다."]
    power_pool = [f"• **화제성 폭발력**: 특정 이슈 발생 시 검색 지수가 급상승하는 강력한 동력을 가집니다."]
    fandom_pool = [f"• **바이럴 전파력**: SNS 내 자발적 인증샷 문화가 견고하게 형성되어 있습니다."]
    return [random.choice(status_pool), random.choice(power_pool), random.choice(fandom_pool)]

# 4. 사이드바 구성
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="신라면, 틈새라면, 삼양라면")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
analyze_btn = st.sidebar.button("분석 시작")

# 5. 메인 대시보드
st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    # 입력된 순서 그대로 리스트 생성
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    
    if keywords:
        target_item = keywords[0]
        with st.spinner(f"순서에 맞춰 분석 리포트 생성 중..."):
            data = fetch_data(keywords, months)
            
            if not data['naver'].empty:
                # 사이드바 결과물 도구
                st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                if st.sidebar.button("🔗 앱 공유하기", use_container_width=True):
                    st.sidebar.info("상단 URL을 복사하여 공유해주세요!")
                if st.sidebar.button("📄 PDF로 저장", use_container_width=True):
                    st.sidebar.warning("단축키 [Ctrl + P]를 눌러 PDF로 저장하세요.")
                
                csv = data['total'].to_csv(index=True).encode('utf-8-sig')
                st.sidebar.download_button(label="📥 데이터(CSV) 다운로드", data=csv, 
                                         file_name=f"GS25_{target_item}.csv", mime='text/csv', use_container_width=True)

                # 섹션 1: 그래프 (이제 입력 순서대로 범례가 나옵니다)
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
                    # 순위는 데이터 수치(평균) 기준 정렬
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i >= 5: break
                        st.success(f"{medal[i]} **{name}**")
                    st.caption("※ 디지털 트렌드 지수 평균치 기준")

                st.markdown("---")
                # 섹션 3: 전략 제언
                st.subheader(f"💡 {target_item} 마케팅 전략 제언")
                c1, c2 = st.columns(2)
                with c1:
                    st.info("🔎 **매체 분석**")
                    st.write(f"• 해당 상품군은 포털 검색보다 SNS 바이럴 민감도가 높게 나타남")
                with c2:
                    st.error("🔥 **강력추천 상권**")
                    st.write("• **오피스/대학가**: 트렌드 상품 소비 속도가 가장 빠른 지역")

            else: st.error("데이터 수집 실패. 상품명을 확인해주세요.")
else: st.info("왼쪽 사이드바에서 상품명을 입력하고 [분석 시작]을 눌러주세요.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("GS25 Market Intelligence System | Powered by Streamlit")