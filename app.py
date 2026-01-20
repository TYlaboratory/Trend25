import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.request
import json

# 페이지 설정
st.set_page_config(page_title="GS25 Trend Analysis", layout="wide")

st.title("📊 GS25 마켓 트렌드 분석 리포트")

# 검색어 입력
target_item = st.text_input("분석할 상품명을 입력하세요", "틈새라면")

if st.button("분석 시작"):
    # 1. 인사이트 요약
    st.subheader(f"📝 [{target_item}] 전략 리포트")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**핵심 인사이트**\n\n• {target_item}은 최근 MZ세대 사이에서 핵심 전략 상품입니다.\n• SNS 내 자발적 확산력이 매우 높습니다.")
    
    # 2. ⚠️ 도입 시 주의사항 (요청하신 기능)
    st.markdown("---")
    st.subheader(f"⚠️ {target_item} 도입 시 주의사항")
    st.warning("""
    1. **화제성 소멸 리스크**: 트렌드 주기가 매우 짧아 초기 물량 확보 후 적기 재고 관리가 필수입니다.
    2. **공급 불안정성**: SNS 대란 발생 시 원재료 수급에 따른 품절 사태가 고객 불만으로 이어질 수 있습니다.
    3. **미투 상품 유입**: 경쟁사의 유사 상품 출시가 빨라 차별화된 소구점 유지가 관건입니다.
    """)

    # 3. 실시간 뉴스 및 영상 추천 (요청하신 기능)
    st.markdown("---")
    st.subheader(f"🎬 {target_item} 관련 최신 영상 및 뉴스")
    
    # 네이버 API를 활용한 데이터 가져오기 (예시 UI)
    col3, col4 = st.columns(2)
    with col3:
        st.write("**📽️ 추천 동영상 TOP 3**")
        st.write("1. [리뷰] 요즘 난리난 그 상품! (유튜브 링크)")
        st.write("2. GS25 신상 털기 - 먹방 (유튜브 링크)")
        st.write("3. 틈새라면 더 맛있게 먹는 법 (유튜브 링크)")
    with col4:
        st.write("**📰 관련 최신 뉴스**")
        st.write("- GS25, 역대급 콜라보 상품 출시...")
        st.write("- 편의점 트렌드, 이제는 '매운맛'이 대세")
