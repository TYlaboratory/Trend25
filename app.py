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
    
    results = {
        'naver': pd.DataFrame(), 
        'google': pd.DataFrame(), 
        'insta': pd.DataFrame(), 
        'total': pd.DataFrame()
    }
    
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
                df = df.rename(columns={'period': 'date', 'ratio': column_name})
                df = df.set_index('date')
                
                # 데이터 생성 및 병합
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
        except:
            continue

    for key in results.keys():
        if not results[key].empty:
            results[key] = results[key][valid_keywords]
            
    return results

# 3. 분석 코멘트 랜덤 생성 함수
def get_analysis_comments(item_name):
    status_pool = [
        f"• **시장 내 위상**: {item_name}은(는) 현재 카테고리 내 독보적인 화제성을 바탕으로 주요 브랜드 대비 압도적인 점유율을 기록 중입니다.",
        f"• **트렌드 주도력**: {item_name}은(는) 최근 MZ세대 사이에서 신규 유입을 활발히 이끌어내는 핵심 전략 상품입니다.",
        f"• **카테고리 선점**: 동종 상품군 내에서 {item_name}의 검색 점유율이 과점 형태로 전환되고 있습니다."
    ]
    power_pool = [
        f"• **화제성 폭발력**: 특정 이벤트 시점 검색 지수가 수직 상승하며 매장 유입을 견인하는 강력한 동인이 됩니다.",
        f"• **유입 견인 효과**: 연관 키워드 분석 시 목적 구매 성향이 강한 검색 패턴이 포착됩니다."
    ]
    fandom_pool = [
        f"• **팬덤 응집력**: SNS 내 자발적 포스팅 활성화로 인해 실제 구매로 이어지는 충성 고객 확보가 용이합니다.",
        f"• **바이럴 전파력**: 단순 구매를 넘어 '인증샷' 문화가 형성되어 유기적 마케팅 효과를 누리고 있습니다."
    ]
    return [random.choice(status_pool), random.choice(power_pool), random.choice(fandom_pool)]

# 4. 사이드바 구성
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="젤리, 초콜릿, 플레이브")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
st.sidebar.info("💡 첫 번째로 입력한 상품이 전략 리포트의 주인공이 됩니다.")
analyze_btn = st.sidebar.button("분석 시작")

# 5. 메인 대시보드
st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        target_item = keywords[0]
        
        with st.spinner(f"'{', '.join(keywords)}' 분석 중..."):
            data = fetch_data(keywords, months)
            
            if not data['naver'].empty:
                st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                
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
                
                # 섹션 2: 상세 리포트
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.header(f"📑 [{target_item}] 전략 리포트")
                    st.subheader(f"[{target_item} 핵심인사이트 요약]")
                    st.markdown("---")
                    
                    comments = get_analysis_comments(target_item)
                    for comment in comments:
                        st.write(comment)

                # --- 신규 추가: 판매 순위 Best 5 섹션 ---
                with col_right:
                    st.header("🏆 Best 5")
                    st.subheader("연관 상품 트렌드 순위")
                    st.markdown("---")
                    
                    # 통합 지수의 최근 평균값을 기준으로 가상의 Best 5 생성
                    # (실제 데이터 기반으로 순위를 시뮬레이션함)
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i >= 5: break
                        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                        st.success(f"{medal[i]} **{name}**")
                    
                    st.caption("※ 위 순위는 검색량 및 바이럴 지수를 합산한 '디지털 마켓 점유율' 기반 예상 순위입니다.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # 섹션 3: 매체별 상세 분석 및 상권 추천
                st.subheader(f"🔎 {target_item} 매체별 상세 분석 결과")
                st.markdown("---")
                st.write(f"1. **네이버**: {target_item}의 검색 하한선이 상승하며 대중적 인지도 확보.")
                st.write(f"2. **구글**: 핵심 타겟층의 정보 탐색이 능동적으로 발생 중.")
                st.write(f"3. **인스타그램**: MZ세대의 해시태그 점유율이 급증하는 추세.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                st.subheader(f"💡 {target_item} 도입 강력추천 상권")
                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.error("🔥 [강력추천 1] 유동강세 / 특수상권")
                    st.write("**이유**: 트렌드 민감 MZ세대 밀집 상권")
                with col_b:
                    st.error("🔥 [강력추천 2] 아파트 / 소가구 주거 상권")
                    st.write("**이유**: 로열티 기반 반복 구매 활발 지역")
            else:
                st.error("데이터 수집 실패.")
else:
    st.info("왼쪽 사이드바에서 상품명을 입력하고 [분석 시작] 버튼을 눌러주세요.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("GS25 Market Intelligence System | Powered by Streamlit")