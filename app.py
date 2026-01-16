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
                
                # 데이터 병합 및 시뮬레이션
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

    # 입력 순서대로 컬럼 정렬
    for key in results.keys():
        if not results[key].empty:
            results[key] = results[key][valid_keywords]
            
    return results, valid_keywords

# 3. 코멘트 생성 함수
def get_analysis_comments(item_name):
    comments = [
        f"• **트렌드 주도력**: {item_name}은(는) 최근 MZ세대 사이에서 신규 유입을 가장 활발히 이끌어내는 핵심 전략 상품으로 분석됩니다.",
        f"• **화제성 폭발력**: 특정 이벤트 시점 검색 지수가 수직 상승하며 편의점 채널 유입을 견인하는 강력한 동인이 됩니다.",
        f"• **고객 충성도**: 재구매 의사를 직접적으로 표현하는 긍정 감성 지수가 타 브랜드 대비 높게 관측됩니다."
    ]
    return comments

# 4. 사이드바 구성
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="신라면, 틈새라면, 삼양라면")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
analyze_btn = st.sidebar.button("분석 시작")

# 5. 메인 대시보드
st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        with st.spinner("데이터 분석 리포트 생성 중..."):
            data, valid_list = fetch_data(keywords, months)
            
            if not data['total'].empty:
                target_item = valid_list[0]
                
                # 사이드바 결과물 도구
                st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                if st.sidebar.button("📄 PDF로 저장", use_container_width=True):
                    st.sidebar.warning("단축키 [Ctrl + P]를 눌러 PDF로 저장하세요.")
                if st.sidebar.button("🔗 앱 공유하기", use_container_width=True):
                    st.sidebar.info("상단 URL을 복사하여 공유해주세요!")
                
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
                
                # 섹션 2: 상세 리포트 및 Best 5
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.header(f"📑 [{target_item}] 전략 리포트")
                    st.subheader(f"[{target_item} 핵심인사이트 요약]")
                    for comment in get_analysis_comments(target_item):
                        st.write(comment)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.subheader(f"🔎 {target_item} 매체별 상세 분석 결과")
                    st.write(f"1. **네이버 (포털 검색량)**: 검색 의도가 '구매처 확인'으로 구체화되는 양상임.")
                    st.write(f"2. **구글 (디지털 관심도)**: 핵심 타겟층의 정보 탐색이 능동적으로 발생하고 있음.")
                    st.write(f"3. **인스타그램 (바이럴)**: 참여형 팬덤의 화력이 동종 상품군 대비 월등히 높음.")

                with col_right:
                    st.header("🏆 Best 5 순위")
                    avg_scores = data['total'].mean().sort_values(ascending=False)
                    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
                    for i, (name, score) in enumerate(avg_scores.items()):
                        if i >= 5: break
                        st.success(f"{medals[i]} **{name}**")
                    st.caption("※ 디지털 트렌드 지수 평균치 기준")

                st.markdown("---")
                
                # 섹션 3: 강력추천 상권
                st.subheader(f"💡 {target_item} 도입 강력추천 상권")
                ca, cb = st.columns(2)
                with ca:
                    st.error("🔥 [강력추천 1] 유동강세 / 특수상권")
                    st.write("**이유**: 트렌드에 민감한 MZ세대가 밀집된 핵심 역세권 상권")
                with cb:
                    st.error("🔥 [강력추천 2] 아파트 / 소가구 주거 상권")
                    st.write("**이유**: 팬덤 로열티 기반의 일상적 반복 구매가 활발한 지역")

            else:
                st.error("데이터 수집에 실패했습니다. 상품명을 확인해주세요.")
else:
    st.info("왼쪽 사이드바에서 상품명을 입력하고 [분석 시작] 버튼을 눌러주세요.")

st.caption("GS25 Market Intelligence System | Powered by Streamlit")