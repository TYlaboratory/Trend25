# --- [수정본] 중복 방지 및 엔터 키워드 강화 리스크 섹션 ---
                st.markdown("---")
                st.subheader(f"⚠️ {target_item} 도입 시 주의사항")

                risk_db = {
                    "liquor": [
                        f"{target_item}은(는) 주류 품목으로, 법적 음주 규제 및 신분증 확인 교육이 철저해야 합니다.",
                        "하이볼 트렌드와 연계한 토닉워터, 레몬, 얼음컵 등 연관 구매 상품의 재고 확보가 필수입니다.",
                        "고단가 위스키의 경우 도난 리스크가 크므로 전용 보안 케이스나 카운터 안쪽 배치를 권장합니다.",
                        "가성비 위스키 경쟁 심화로 인해 단독 판매보다는 전용 잔 증정 등 기획 구성이 효과적입니다."
                    ],
                    "food": [
                        f"{target_item}은(는) 유통기한 및 선도 관리가 핵심이며, 폐기율 감소를 위한 시간대별 발주 조절이 필요합니다.",
                        "자극적인 맛이나 고칼로리 컨셉인 경우, 건강 지향 소비자의 부정적 여론을 상쇄할 마케팅이 필요합니다.",
                        "미투(Me-too) 상품 출시가 매우 빠른 카테고리이므로 브랜드 오리지널리티 강조가 중요합니다."
                    ],
                    "entertainment": [ # 플레이브 등 아이돌/캐릭터 전용
                        f"{target_item} 팬덤의 강한 화력을 고려하여, 출시 초기 매장 오픈런 및 인파 밀집에 따른 안전 관리가 필요합니다.",
                        "굿즈나 협업 상품의 경우, 팬덤의 높은 품질 기대치에 미달할 시 SNS를 통한 부정적 여론 확산 리스크가 큽니다.",
                        "한정판의 경우 리셀(Resell) 시장 과열로 인한 실구매 고객의 불만을 방지하기 위한 1인당 구매 제한이 권장됩니다.",
                        "아티스트/IP의 활동 주기나 이슈에 따라 수요 변동폭이 매우 크므로 치고 빠지는(In-and-Out) 전략이 유리합니다."
                    ],
                    "general": [
                        "온라인 최저가와의 가격 격차 발생 시 오프라인 구매 매력도가 급격히 하락할 수 있습니다.",
                        "물류 부하가 큰 상품의 경우 소규모 점포의 진열 효율성을 저해할 수 있으므로 진열 위치 선정이 중요합니다.",
                        "SNS 화제성에 비해 실제 재구매율이 낮을 수 있으니 초기 물량 이후 수요 예측에 주의해야 합니다."
                    ]
                }

                # 카테고리 판별 로직 (엔터테인먼트 키워드 추가)
                selected_cat = "general"
                liquor_kw = ["티쳐스", "위스키", "술", "맥주", "와인", "잭다니엘", "조니워커", "발렌타인", "하이볼"]
                food_kw = ["라면", "면", "볶음", "도시락", "김밥", "간식", "디저트"]
                # 플레이브, 아이돌, 굿즈 등 추가
                ent_kw = ["플레이브", "아이돌", "캐릭터", "콜라보", "방송", "유튜버", "굿즈", "연예인", "덕질"]

                if any(k in target_item for k in liquor_kw): selected_cat = "liquor"
                elif any(k in target_item for k in food_kw): selected_cat = "food"
                elif any(k in target_item for k in ent_kw): selected_cat = "entertainment"

                # --- 핵심: 중복 제거 로직 ---
                # 1. 해당 카테고리에서 2개 추출
                cat_pool = risk_db[selected_cat]
                cat_risks = random.sample(cat_pool, min(len(cat_pool), 2))
                
                # 2. 전체 리스트에서 이미 뽑힌 것을 제외하고 1개 더 추출
                all_msgs = [m for ms in risk_db.values() for m in ms]
                remaining_pool = [m for m in all_msgs if m not in cat_risks]
                other_risk = random.sample(remaining_pool, 1)
                
                final_risks = cat_risks + other_risk

                st.warning(f"""
                1. **상품군 핵심 리스크**: {final_risks[0]}
                2. **운영/마케팅 주의**: {final_risks[1]}
                3. **기타 관리 요소**: {final_risks[2]}
                """)
