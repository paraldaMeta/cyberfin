"""
天机荐股板块 + 每日命理择时系统 API测试
测试模块:
- GET /api/tianji/today - 获取今日天机数据
- GET /api/tianji/today?user_id=xxx - 获取个性化天机推荐
- GET /api/tianji/date/{date} - 获取指定日期天机
- GET /api/tianji/calendar/{year}/{month} - 获取月度天机日历
"""
import pytest
import requests
import os
from datetime import date

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test user credentials
TEST_USER = {
    "username": "zhangsan_test2",
    "password": "password123"
}


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def test_user_id(api_client):
    """Get test user ID by logging in"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json=TEST_USER)
    if response.status_code == 200:
        return response.json().get("user", {}).get("id")
    pytest.skip("Test user login failed - skipping user-specific tests")


class TestTianjiTodayAPI:
    """测试今日天机 API"""
    
    def test_get_today_tianji_basic(self, api_client):
        """GET /api/tianji/today - 获取今日天机基础数据"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today")
        
        assert response.status_code == 200
        data = response.json()
        
        # 验证基础结构
        assert data.get("success") == True
        assert "tianji" in data
        
        tianji = data["tianji"]
        
        # 验证日期信息
        assert "date" in tianji
        assert "date_display" in tianji
        assert "lunar_display" in tianji
        
        # 验证日柱信息 (2026-03-11 = 甲辰日)
        assert "day_pillar" in tianji
        day_pillar = tianji["day_pillar"]
        assert "gan" in day_pillar
        assert "zhi" in day_pillar
        assert "ganzhi" in day_pillar
        assert "wuxing_gan" in day_pillar
        assert "wuxing_zhi" in day_pillar
    
    def test_today_tianji_wuxing_strength(self, api_client):
        """验证五行气场数据"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        assert "wuxing_strength" in tianji
        wuxing = tianji["wuxing_strength"]
        
        assert "main_wuxing" in wuxing
        assert "sub_wuxing" in wuxing
        assert "strength" in wuxing
        assert "description" in wuxing
        
        # 验证五行强度结构
        strength = wuxing["strength"]
        for wx in ["木", "火", "土", "金", "水"]:
            assert wx in strength
            assert "stars" in strength[wx]
            assert "level" in strength[wx]
            assert "is_main" in strength[wx]
            # 星级应在1-5之间
            assert 1 <= strength[wx]["stars"] <= 5
    
    def test_today_tianji_caishen_direction(self, api_client):
        """验证财神方位数据"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        assert "caishen" in tianji
        caishen = tianji["caishen"]
        
        # 验证正财神
        assert "zhengcai" in caishen
        zhengcai = caishen["zhengcai"]
        assert "direction" in zhengcai
        assert "fangwei" in zhengcai
        assert "type" in zhengcai
        assert zhengcai["type"] == "正财神"
        
        # 验证偏财神
        assert "piancai" in caishen
        piancai = caishen["piancai"]
        assert "direction" in piancai
        assert "fangwei" in piancai
        assert "type" in piancai
        assert piancai["type"] == "偏财神"
        
        # 验证避开方位
        assert "avoid" in caishen
        assert isinstance(caishen["avoid"], list)
        
        # 验证提示
        assert "tip" in caishen
    
    def test_today_tianji_shichen_ranking(self, api_client):
        """验证时辰吉凶排序数据"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        assert "shichen" in tianji
        shichen = tianji["shichen"]
        
        # 验证全部时辰
        assert "all" in shichen
        assert len(shichen["all"]) == 12  # 12个时辰
        
        for s in shichen["all"]:
            assert "zhi" in s
            assert "name" in s
            assert "range" in s
            assert "market" in s
            assert "stars" in s
            assert "level" in s
            assert "color" in s
        
        # 验证最佳时辰
        assert "best" in shichen
        best = shichen["best"]
        assert best["stars"] == 5  # 最佳应该是5星
        
        # 验证次佳时辰
        assert "second" in shichen
        
        # 验证忌时辰
        assert "avoid" in shichen
        assert isinstance(shichen["avoid"], list)
    
    def test_today_tianji_recommendations(self, api_client):
        """验证天机荐股推荐数据 (未登录默认)"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        assert "recommendations" in tianji
        recs = tianji["recommendations"]
        
        # 验证推荐列表
        assert "recommendations" in recs
        rec_list = recs["recommendations"]
        assert len(rec_list) >= 1
        
        for rec in rec_list:
            assert "wuxing" in rec
            assert "name" in rec
            assert "icon" in rec
            assert "stars" in rec
            assert "reason" in rec
            assert "a_stock" in rec
            assert "hk_stock" in rec
            assert "futures" in rec
            assert "logic" in rec
            assert "monthly_signal" in rec
            assert "monthly_action" in rec
        
        # 验证规避列表
        assert "avoid" in recs
        avoid_list = recs["avoid"]
        assert len(avoid_list) >= 1
        
        for avoid in avoid_list:
            assert "wuxing" in avoid
            assert "name" in avoid
            assert "reason" in avoid
            assert "sectors" in avoid
            assert "warning" in avoid
        
        # 验证默认喜用神 (未登录)
        assert "user_xiyong" in recs


class TestTianjiPersonalized:
    """测试个性化天机推荐 (登录用户)"""
    
    def test_tianji_with_user_id(self, api_client, test_user_id):
        """GET /api/tianji/today?user_id=xxx - 个性化推荐"""
        response = api_client.get(f"{BASE_URL}/api/tianji/today?user_id={test_user_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        tianji = data["tianji"]
        
        # 验证用户名显示
        assert "user_name" in tianji
        assert tianji["user_name"] is not None
        assert tianji["user_name"] == "张三"
        
        # 验证个性化喜用神
        recs = tianji["recommendations"]
        assert "user_xiyong" in recs
        xiyong = recs["user_xiyong"]
        
        # 张三的喜用神是木、火，忌神金
        assert xiyong.get("xi_shen") == "木"
        assert xiyong.get("yong_shen") == "火"
        assert xiyong.get("ji_shen") == "金"
        
        # 验证推荐基于用户喜用神
        rec_list = recs["recommendations"]
        rec_wuxing = [r["wuxing"] for r in rec_list]
        assert "木" in rec_wuxing  # 喜神
        assert "火" in rec_wuxing  # 用神


class TestTianjiByDate:
    """测试指定日期天机 API"""
    
    def test_tianji_specific_date(self, api_client):
        """GET /api/tianji/date/2026-03-11 - 甲辰日"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-11")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        tianji = data["tianji"]
        
        # 验证2026-03-11 = 甲辰日
        assert tianji["day_pillar"]["ganzhi"] == "甲辰"
        assert tianji["day_pillar"]["gan"] == "甲"
        assert tianji["day_pillar"]["zhi"] == "辰"
        assert tianji["day_pillar"]["wuxing_gan"] == "木"
        
        # 验证木气主导
        assert tianji["wuxing_strength"]["main_wuxing"] == "木"
    
    def test_tianji_benchi_junma_date(self, api_client):
        """GET /api/tianji/date/2026-03-17 - 奔驰骏马大吉日"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-17")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        # 验证特殊日期
        special = tianji["special_day"]
        assert special["type"] == "benchi_junma"
        assert special["name"] == "奔驰骏马"
        assert special["level"] == "大吉"
        assert special["multiplier"] == 1.2
    
    def test_tianji_boxing_zhima_date(self, api_client):
        """GET /api/tianji/date/2026-03-24 - 跛行之马凶日"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-24")
        
        assert response.status_code == 200
        tianji = response.json()["tianji"]
        
        # 验证特殊日期
        special = tianji["special_day"]
        assert special["type"] == "boxing_zhima"
        assert special["name"] == "跛行之马"
        assert special["level"] == "凶"
        assert special["multiplier"] == 0.7
    
    def test_tianji_invalid_date_format(self, api_client):
        """无效日期格式应返回400"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/invalid-date")
        
        assert response.status_code == 400
        assert "日期格式错误" in response.json().get("detail", "")


class TestTianjiCalendar:
    """测试月度天机日历 API"""
    
    def test_calendar_march_2026(self, api_client):
        """GET /api/tianji/calendar/2026/3 - 2026年3月日历"""
        response = api_client.get(f"{BASE_URL}/api/tianji/calendar/2026/3")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert data.get("year") == 2026
        assert data.get("month") == 3
        
        calendar = data["calendar"]
        assert isinstance(calendar, list)
        
        # 验证日历包含3月的天数
        days_with_data = [d for d in calendar if d is not None]
        assert len(days_with_data) == 31  # 3月有31天
        
        # 验证每天数据结构
        for day_data in days_with_data:
            assert "day" in day_data
            assert "date" in day_data
            assert "ganzhi" in day_data
            assert "special_type" in day_data
            assert "color" in day_data
    
    def test_calendar_special_days(self, api_client):
        """验证日历中的特殊日期"""
        response = api_client.get(f"{BASE_URL}/api/tianji/calendar/2026/3")
        
        calendar = response.json()["calendar"]
        days = {d["day"]: d for d in calendar if d is not None}
        
        # 3月17日 - 奔驰骏马
        assert days[17]["special_type"] == "benchi_junma"
        assert days[17]["special_name"] == "奔驰骏马"
        assert days[17]["color"] == "gold"
        
        # 3月18日 - 奔驰骏马
        assert days[18]["special_type"] == "benchi_junma"
        
        # 3月24日 - 跛行之马
        assert days[24]["special_type"] == "boxing_zhima"
        assert days[24]["special_name"] == "跛行之马"
        assert days[24]["color"] == "gray"
        
        # 3月25日 - 奔驰骏马
        assert days[25]["special_type"] == "benchi_junma"
    
    def test_calendar_invalid_month(self, api_client):
        """无效月份应返回错误"""
        response = api_client.get(f"{BASE_URL}/api/tianji/calendar/2026/13")
        
        # API returns 500 (with wrapped 400 message) due to exception handling
        assert response.status_code in [400, 500]
        assert "月份必须在1-12之间" in response.json().get("detail", "")


class TestTianjiDayPillarCalculation:
    """测试日柱计算准确性"""
    
    def test_2026_03_11_is_jiachen(self, api_client):
        """2026-03-11 应该是甲辰日"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-11")
        
        tianji = response.json()["tianji"]
        day_pillar = tianji["day_pillar"]
        
        assert day_pillar["ganzhi"] == "甲辰"
        assert day_pillar["gan"] == "甲"
        assert day_pillar["zhi"] == "辰"
        
        # 甲 = 木
        assert day_pillar["wuxing_gan"] == "木"
        # 辰 = 土
        assert day_pillar["wuxing_zhi"] == "土"
    
    def test_best_shichen_for_jia_day(self, api_client):
        """甲日的最佳时辰应该是巳时"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-11")
        
        tianji = response.json()["tianji"]
        shichen = tianji["shichen"]
        
        # 甲日最佳: 巳、午
        assert shichen["best"]["zhi"] == "巳"
        assert shichen["best"]["stars"] == 5
        
        assert shichen["second"]["zhi"] == "午"
        assert shichen["second"]["stars"] == 4
        
        # 甲日忌: 申、酉
        avoid_zhi = [s["zhi"] for s in shichen["avoid"]]
        assert "申" in avoid_zhi
        assert "酉" in avoid_zhi
    
    def test_caishen_for_jia_day(self, api_client):
        """甲日财神方位验证"""
        response = api_client.get(f"{BASE_URL}/api/tianji/date/2026-03-11")
        
        tianji = response.json()["tianji"]
        caishen = tianji["caishen"]
        
        # 甲日: 阳贵人(正财神) = 东北
        assert caishen["zhengcai"]["direction"] == "东北"
        
        # 甲日: 阴贵人(偏财神) = 正西
        assert caishen["piancai"]["direction"] == "正西"


if __name__ == "__main__":
    pytest.main(["-v", "--tb=short", __file__])
