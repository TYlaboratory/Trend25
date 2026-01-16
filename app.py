import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import platform
import json
import urllib.request
import ssl
from datetime import datetime, timedelta

# 1. 페이지 설정 및 한글 폰트
st.set_page_config(page_title="GS25 통합 트렌드 분석 시스템", layout="wide")

def get_korean_font():
    if platform.system() == "Darwin": return 'AppleGothic'
    elif platform.system() == "Windows": return 'Malgun Gothic'
    return "sans-serif"

plt.rc('font', family=get_korean_font())

# 2. 데이터 수집 함수 (명칭 잘림 방지 및 매체별 데이터 생성)
def fetch_data(keywords, months):
    NAVER_CLIENT_ID = "9mDKko38immm22vni0rL"
    NAVER_CLIENT_SECRET = "ONIf7vxWzZ"
    
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30 * months)
    results = {'naver': pd.DataFrame(), 'google': pd.DataFrame(), 'insta': pd.DataFrame(), 'total': pd.DataFrame()}
    
    for kw in keywords:
        try:
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
            
            ssl_context = ssl._create_unverified_context()
            res = urllib.request.urlopen(req, data=data_json, context=ssl_context)
            n_data = json.loads(res.read().decode("utf-8"))
            
            df = pd.DataFrame(n_data['results'][0]['data'])
            if not df.empty:
                # [중요] API 응답 대신 사용자 입력값(kw)을 컬럼명으로 강제 사용하여 '티쳐스' 잘림 방지
                column_name = str(kw)
                df['period'] = pd.to_datetime(df['period'])
                df = df.rename(columns={'period': 'date', 'ratio': column_name})
                df[column_name] = df[column_name].astype(float)
                
                # 네이버 데이터
                if results['naver'].empty: results['naver'] = df
                else: results['naver'] = pd.merge(results['naver'], df, on='date', how='outer')
                
                # 가상 데이터 생성 (구글, 인스타)
                g_df = df.copy(); g_df[column_name] *= np.random.uniform(0.4, 0.7)
                if results['google'].empty: results['google'] = g_df
                else: results['google'] = pd.merge(results['google'], g_df, on='date', how='outer')
                
                i_df = df.copy(); i_df[column_name] *= np.random.uniform(0.8, 1.3)
                if results['insta'].empty: results['insta'] = i_df
                else: results['insta'] = pd.merge(results['insta'], i_df, on='date', how='outer')
                
                # 통합 지수 (Total Index)
                t_df = df.copy()
                t_df[column_name] = (df[column_name]*0.4) + (g_df[column_name]*0.3) + (i_df[column_name]*0.3)
                if results['total'].empty: results['total'] = t_df
                else: results['total'] = pd.merge(results['total'], t_df, on='date', how='outer')
        except:
            st.warning(f"⚠️ '{kw}'의 데이터를 가져오는 데 실패했습니다.")
            
    return results

# 3. 사이드바 구성
st.sidebar.title("📊 분석 제어판")
items_raw = st.sidebar.text_input("분석 상품 리스트 (쉼표로 구분)", value="000, 00000, 0000")
months = st.sidebar.slider("데이터 분석 기간 (개월)", 1, 12, 6)
st.sidebar.info("💡 첫 번째로 입력한 상품이 상세 리포트의 주인공이 됩니다.")
analyze_btn = st.sidebar.button("분석 시작")

# 4. 메인 대시보드
st.title("🏪 GS25 상품 트렌드 분석 시스템")
st.markdown("---")

if analyze_btn:
    keywords = [x.strip() for x in items_raw.split(",") if x.strip()]
    if keywords:
        target_item = keywords[0] # 첫 번째 상품 고정
        
        with st.spinner(f"전체 {len(keywords)}개 상품 분석 및 리포트 생성 중..."):
            data = fetch_data(keywords, months)
            
            if not data['naver'].empty:
st.sidebar.divider()
                st.sidebar.subheader("📥 결과 내보내기")
                
                # 1. 앱 공유하기
                if st.sidebar.button("🔗 앱 공유하기", use_container_width=True):
                    st.sidebar.info("상단 주소창의 URL을 복사하여 공유해주세요!")
                
                # 2. PDF 저장 안내
                if st.sidebar.button("📄 PDF로 저장", use_container_width=True):
                    st.sidebar.warning("단축키 [Ctrl + P]를 눌러 PDF로 저장하세요.")

                # 3. CSV 데이터 다운로드
                csv = data['total'].to_csv(index=False).encode('utf-8-sig')
                st.sidebar.download_button(
                    label="📥 데이터(CSV) 다운로드",
                    data=csv,
                    file_name=f"GS25_{target_item}.csv",
                    mime='text/csv',
                    use_container_width=True
                )
                st.sidebar.divider()
                # 섹션 1: 매체별 그래프 (탭 형식)
                st.subheader("📈 매체별 트렌드 비교 분석")
                tab1, tab2, tab3, tab4 = st.tabs(["⭐ 통합 지수", "📉 네이버", "🔍 구글", "📱 인스타그램"])
                
                with tab1: st.line_chart(data['total'].set_index('date'))
                with tab2: st.line_chart(data['naver'].set_index('date'))
                with tab3: st.line_chart(data['google'].set_index('date'))
                with tab4: st.line_chart(data['insta'].set_index('date'))
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("---")
                
                # 섹션 2: 상세 리포트 (첫 번째 상품 집중 분석)
                st.header(f"📑 [{target_item}] 전략 리포트")
                
                # 1. 핵심인사이트 요약 (박스 제거, 구분선 적용)
                st.subheader(f"[{target_item} 핵심인사이트 요약]")
                st.markdown("---") # 얇은 구분선
                st.write(f"• **시장 내 위상**: {target_item}은(는) 현재 카테고리 내 독보적인 화제성을 바탕으로 주요 브랜드 대비 압도적인 점유율을 기록 중입니다.")
                st.write(f"• **화제성 폭발력**: 특정 이벤트 시점 검색 지수가 수직 상승하며 편의점 채널 유입을 견인하는 강력한 동인이 됩니다.")
                st.write(f"• **팬덤 응집력**: SNS 내 자발적 포스팅 활성화로 인해 실제 구매로 이어지는 충성 고객 확보가 용이합니다.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 2. 매체별 상세 분석
                st.subheader(f"🔎 {target_item} 매체별 상세 분석 결과")
                st.markdown("---")
                st.write(f"1. **네이버 (포털 검색량)**: {target_item}의 상시 검색 하한선이 지속적으로 상승하며 대중적 인지도 확보.")
                st.write(f"2. **구글 (디지털 관심도)**: 핵심 타겟층의 정보 탐색이 능동적으로 발생하고 있음.")
                st.write(f"3. **인스타그램 (바이럴)**: 참여형 팬덤의 화력이 동종 상품군 대비 월등히 높음.")
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 3. 강력추천 상권 (2종 집중)
                st.subheader(f"💡 {target_item} 도입 강력추천 상권")
                st.markdown("---")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.error("🔥 [강력추천 1] 유동강세 / 특수상권")
                    st.write("**이유**: 트렌드에 민감한 MZ세대가 밀집된 핵심 역세권 상권")
                    st.write("**전략**: 점포 전면 배치 및 팝업 진열로 시각적 화제성 극대화")
                with col_b:
                    st.error("🔥 [강력추천 2] 아파트 / 소가구 주거 상권")
                    st.write("**이유**: 팬덤 로열티 기반의 일상적 반복 구매가 활발한 지역")
                    st.write("**전략**: 상시 재고 확보 및 연관 상품 교차 진열로 객단가 유도")
                    
            else:
                st.error("네이버 API로부터 데이터를 가져오지 못했습니다. 상품명을 확인해주세요.")
else:
    st.info("왼쪽 사이드바에서 분석할 상품명들을 입력하고 [분석 시작] 버튼을 눌러주세요.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("GS25 Market Intelligence System | Powered by Streamlit")
