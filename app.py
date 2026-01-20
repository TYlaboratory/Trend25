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

# --- [함수 정의 구역] 호출되기 전 상단에 위치해야 오류가 나지 않습니다 ---

def get_youtube_shorts(query, display=5):
    """네이버 비디오 API에서 유튜브 링크만 필터링하여 숏츠 검색 결과 제공"""
    client_id = "9mDKko38immm22vni0rL"
    client_secret = "ONIf7vxWzZ"
    
    search_query = f"{query} shorts 숏츠"
    encText = urllib.parse.quote(search_query)
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

def get_naver_news(query, display=5):
    """네이버 뉴스 API에서 최신 기사 5개 수집"""
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

def fetch_data(keywords, months):
    """네이버 데이터랩 트렌드 수집 및 가공"""
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
                df['period'] =
