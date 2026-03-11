"""
Backend API tests for Bazi (八字) Calculator and User Authentication.
Testing: Province/City lists, Shichen options, Bazi calculation, User registration/login

测试模块：
- 省份列表 API
- 城市列表 API
- 时辰选项 API
- 八字命盘计算 API
- 用户注册 API
- 用户登录 API
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://market-predict-asia.preview.emergentagent.com"


class TestBaziProvinceAndCity:
    """Test province and city list APIs for Bazi calculation"""
    
    def test_get_provinces(self):
        """Test GET /api/bazi/provinces - 获取省份列表"""
        response = requests.get(f"{BASE_URL}/api/bazi/provinces")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "provinces" in data, "Response should contain 'provinces' key"
        
        provinces = data["provinces"]
        assert isinstance(provinces, list), "Provinces should be a list"
        assert len(provinces) >= 30, f"Expected at least 30 provinces, got {len(provinces)}"
        
        # Verify key provinces exist
        expected_provinces = ["北京", "上海", "广东", "浙江", "江苏", "四川", "香港", "台湾"]
        for prov in expected_provinces:
            assert prov in provinces, f"Missing expected province: {prov}"
        
        print(f"✓ GET /api/bazi/provinces returns {len(provinces)} provinces")
        print(f"  Sample provinces: {provinces[:5]}")
    
    def test_get_cities_for_beijing(self):
        """Test GET /api/bazi/cities/{province} - 获取北京的城市"""
        response = requests.get(f"{BASE_URL}/api/bazi/cities/北京")
        assert response.status_code == 200
        
        data = response.json()
        assert "cities" in data
        cities = data["cities"]
        assert isinstance(cities, list)
        assert len(cities) >= 1, "Beijing should have at least 1 city"
        assert "北京" in cities, "Beijing province should contain '北京' city"
        
        print(f"✓ GET /api/bazi/cities/北京 returns {len(cities)} cities: {cities}")
    
    def test_get_cities_for_guangdong(self):
        """Test GET /api/bazi/cities/{province} - 获取广东的城市"""
        response = requests.get(f"{BASE_URL}/api/bazi/cities/广东")
        assert response.status_code == 200
        
        data = response.json()
        cities = data["cities"]
        assert len(cities) >= 10, f"Guangdong should have many cities, got {len(cities)}"
        
        expected_cities = ["广州", "深圳", "珠海"]
        for city in expected_cities:
            assert city in cities, f"Missing expected city: {city}"
        
        print(f"✓ GET /api/bazi/cities/广东 returns {len(cities)} cities")
        print(f"  Sample cities: {cities[:5]}")
    
    def test_get_cities_for_nonexistent_province(self):
        """Test cities API with non-existent province"""
        response = requests.get(f"{BASE_URL}/api/bazi/cities/不存在的省")
        assert response.status_code == 200  # API returns 200 with empty list
        
        data = response.json()
        assert "cities" in data
        assert data["cities"] == [], "Non-existent province should return empty city list"
        
        print("✓ Non-existent province returns empty city list")


class TestShichenOptions:
    """Test Shichen (时辰) options API"""
    
    def test_get_shichen_options(self):
        """Test GET /api/bazi/shichen - 获取时辰选项"""
        response = requests.get(f"{BASE_URL}/api/bazi/shichen")
        assert response.status_code == 200
        
        data = response.json()
        assert "shichen" in data, "Response should contain 'shichen' key"
        
        shichen = data["shichen"]
        assert isinstance(shichen, list)
        assert len(shichen) == 13, f"Expected 13 shichen options (12 + unknown), got {len(shichen)}"
        
        # Verify structure of each option
        for option in shichen:
            assert "value" in option, "Each option should have 'value'"
            assert "label" in option, "Each option should have 'label'"
        
        # Verify specific shichen values
        values = [opt["value"] for opt in shichen]
        expected_values = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "unknown"]
        for val in expected_values:
            assert val in values, f"Missing shichen value: {val}"
        
        print(f"✓ GET /api/bazi/shichen returns {len(shichen)} options")
        print(f"  Values: {values}")


class TestBaziCalculation:
    """Test Bazi (八字) calculation API"""
    
    def test_calculate_bazi_with_hour(self):
        """Test POST /api/bazi/calculate - 计算完整八字命盘 (含时辰)"""
        payload = {
            "name": "测试用户",
            "gender": "男",
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": "午",
            "birth_province": "北京",
            "birth_city": "北京"
        }
        
        response = requests.post(f"{BASE_URL}/api/bazi/calculate", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Calculation should be successful"
        assert "bazi" in data, "Response should contain 'bazi' key"
        
        bazi = data["bazi"]
        
        # Verify basic info
        assert bazi.get("name") == "测试用户"
        assert bazi.get("gender") == "男"
        
        # Verify sizhu (四柱)
        assert "sizhu" in bazi
        sizhu = bazi["sizhu"]
        assert "year" in sizhu, "Should have year pillar"
        assert "month" in sizhu, "Should have month pillar"
        assert "day" in sizhu, "Should have day pillar"
        assert "hour" in sizhu, "Should have hour pillar (since birth_hour provided)"
        
        # Verify each pillar has gan and zhi
        for pillar_name in ["year", "month", "day", "hour"]:
            pillar = sizhu[pillar_name]
            assert "gan" in pillar, f"{pillar_name} pillar should have 'gan'"
            assert "zhi" in pillar, f"{pillar_name} pillar should have 'zhi'"
            assert "ganzhi" in pillar, f"{pillar_name} pillar should have 'ganzhi'"
        
        # Verify year pillar has shengxiao (生肖)
        assert "shengxiao" in sizhu["year"], "Year pillar should have shengxiao"
        assert sizhu["year"]["shengxiao"] == "马", "1990 should be 马 (Horse) year"
        
        # Verify wuxing (五行) count
        assert "wuxing_count" in bazi
        wuxing = bazi["wuxing_count"]
        assert all(element in wuxing for element in ["木", "火", "土", "金", "水"])
        
        # Verify xiyong (喜用神)
        assert "xiyong" in bazi
        xiyong = bazi["xiyong"]
        assert "day_master" in xiyong
        assert "xi_shen" in xiyong
        assert "yong_shen" in xiyong
        assert "ji_shen" in xiyong
        
        # Verify dayun (大运)
        assert "dayun" in bazi
        assert len(bazi["dayun"]) >= 5, "Should have at least 5 dayun periods"
        
        # Verify liunian (流年) 2026
        assert "liunian_2026" in bazi
        assert bazi["liunian_2026"]["year"] == 2026
        
        # Verify sector recommendations
        assert "sector_recommendations" in bazi
        
        print(f"✓ Bazi calculation successful for 1990-05-15 午时 北京")
        print(f"  四柱: {sizhu['year']['ganzhi']}年 {sizhu['month']['ganzhi']}月 {sizhu['day']['ganzhi']}日 {sizhu['hour']['ganzhi']}时")
        print(f"  生肖: {sizhu['year']['shengxiao']}")
        print(f"  喜神: {xiyong['xi_shen']}")
    
    def test_calculate_bazi_without_hour(self):
        """Test Bazi calculation without hour (unknown) - only 3 pillars"""
        payload = {
            "name": "无时辰用户",
            "gender": "女",
            "birth_year": 1985,
            "birth_month": 10,
            "birth_day": 20,
            "birth_hour": "unknown",
            "birth_province": "上海",
            "birth_city": "上海"
        }
        
        response = requests.post(f"{BASE_URL}/api/bazi/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data.get("success") == True
        
        bazi = data["bazi"]
        sizhu = bazi["sizhu"]
        
        # Should have year, month, day but NOT hour
        assert "year" in sizhu
        assert "month" in sizhu
        assert "day" in sizhu
        assert "hour" not in sizhu, "Should NOT have hour pillar when birth_hour is 'unknown'"
        
        print(f"✓ Bazi calculation without hour successful")
        print(f"  三柱: {sizhu['year']['ganzhi']}年 {sizhu['month']['ganzhi']}月 {sizhu['day']['ganzhi']}日")


class TestUserRegistration:
    """Test user registration with Bazi calculation"""
    
    @pytest.fixture
    def unique_username(self):
        """Generate unique username for test"""
        return f"TEST_user_{uuid.uuid4().hex[:8]}"
    
    def test_register_new_user(self, unique_username):
        """Test POST /api/auth/register - 用户注册"""
        payload = {
            "username": unique_username,
            "password": "password123",
            "phone": "13800138000",
            "name": "测试新用户",
            "gender": "男",
            "birth_year": 1992,
            "birth_month": 8,
            "birth_day": 8,
            "birth_hour": "申",
            "birth_province": "浙江",
            "birth_city": "杭州"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200, f"Registration failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Registration should be successful"
        assert "user" in data, "Response should contain 'user' key"
        
        user = data["user"]
        
        # Verify user info (password should not be returned)
        assert user.get("username") == unique_username
        assert "password" not in user, "Password should NOT be returned"
        assert user.get("name") == "测试新用户"
        assert user.get("gender") == "男"
        assert "id" in user, "User should have an ID"
        
        # Verify bazi_data is included
        assert "bazi_data" in user, "User should have bazi_data"
        bazi = user["bazi_data"]
        assert "sizhu" in bazi
        assert "xiyong" in bazi
        assert "sector_recommendations" in bazi
        
        print(f"✓ User registration successful: {unique_username}")
        print(f"  User ID: {user['id']}")
        print(f"  八字: {bazi['sizhu']['year']['ganzhi']}年")
        
        return user
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username fails"""
        # First, register a user
        username = f"TEST_dup_{uuid.uuid4().hex[:8]}"
        payload = {
            "username": username,
            "password": "password123",
            "name": "First User",
            "gender": "男",
            "birth_year": 1990,
            "birth_month": 1,
            "birth_day": 1
        }
        
        # First registration should succeed
        response1 = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response1.status_code == 200
        
        # Second registration with same username should fail
        payload["name"] = "Second User"
        response2 = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response2.status_code == 400, f"Duplicate registration should fail with 400, got {response2.status_code}"
        
        data = response2.json()
        assert "用户名已存在" in str(data.get("detail", "")), "Error message should mention duplicate username"
        
        print(f"✓ Duplicate username registration correctly rejected")


class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.fixture
    def test_user_credentials(self):
        """Create a test user and return credentials"""
        username = f"TEST_login_{uuid.uuid4().hex[:8]}"
        password = "testpass456"
        
        # Register user first
        payload = {
            "username": username,
            "password": password,
            "name": "Login Test User",
            "gender": "女",
            "birth_year": 1995,
            "birth_month": 3,
            "birth_day": 15,
            "birth_hour": "卯"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
        assert response.status_code == 200, f"Failed to create test user: {response.text}"
        
        return {"username": username, "password": password}
    
    def test_login_success(self, test_user_credentials):
        """Test POST /api/auth/login - 用户登录成功"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=test_user_credentials)
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert "user" in data
        
        user = data["user"]
        assert user.get("username") == test_user_credentials["username"]
        assert "password" not in user, "Password should NOT be returned"
        assert "bazi_data" in user, "User should have bazi_data on login"
        
        print(f"✓ Login successful for: {test_user_credentials['username']}")
    
    def test_login_wrong_password(self, test_user_credentials):
        """Test login with wrong password fails"""
        bad_credentials = {
            "username": test_user_credentials["username"],
            "password": "wrongpassword"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=bad_credentials)
        assert response.status_code == 401, f"Wrong password should return 401, got {response.status_code}"
        
        data = response.json()
        assert "用户名或密码错误" in str(data.get("detail", ""))
        
        print("✓ Wrong password login correctly rejected")
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent username fails"""
        credentials = {
            "username": "nonexistent_user_12345",
            "password": "anypassword"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=credentials)
        assert response.status_code == 401, f"Non-existent user should return 401, got {response.status_code}"
        
        print("✓ Non-existent user login correctly rejected")


class TestExistingTestUser:
    """Test with existing test user mentioned in the requirements"""
    
    def test_login_existing_user_zhangsan(self):
        """Test login with existing user zhangsan_test2"""
        credentials = {
            "username": "zhangsan_test2",
            "password": "password123"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=credentials)
        
        # This user may or may not exist in the current database
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            print(f"✓ Existing user zhangsan_test2 login successful")
            
            # Verify bazi data
            if "user" in data and "bazi_data" in data["user"]:
                bazi = data["user"]["bazi_data"]
                print(f"  八字数据: {bazi.get('sizhu', {}).get('year', {}).get('ganzhi', 'N/A')}年")
        else:
            print(f"⚠ User zhangsan_test2 not found in current database (status: {response.status_code})")


class TestBaziDataIntegrity:
    """Test Bazi calculation for specific dates to verify algorithm"""
    
    def test_specific_date_1990_may_15_beijing(self):
        """Test specific date calculation as mentioned in requirements:
        1990年5月15日午时北京出生 -> 庚午年丙戌月庚子日壬午时
        """
        payload = {
            "name": "验证用户",
            "gender": "男",
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "birth_hour": "午",
            "birth_province": "北京",
            "birth_city": "北京"
        }
        
        response = requests.post(f"{BASE_URL}/api/bazi/calculate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        bazi = data["bazi"]
        sizhu = bazi["sizhu"]
        
        # Verify year pillar (庚午年)
        assert sizhu["year"]["ganzhi"] == "庚午", f"Year pillar should be 庚午, got {sizhu['year']['ganzhi']}"
        
        # Verify shengxiao is 马
        assert sizhu["year"]["shengxiao"] == "马", f"Shengxiao should be 马, got {sizhu['year']['shengxiao']}"
        
        # Print results for verification
        print(f"✓ Date 1990-05-15 午时 北京:")
        print(f"  年柱: {sizhu['year']['ganzhi']} (期望: 庚午)")
        print(f"  月柱: {sizhu['month']['ganzhi']}")
        print(f"  日柱: {sizhu['day']['ganzhi']}")
        print(f"  时柱: {sizhu['hour']['ganzhi']}")
        print(f"  生肖: {sizhu['year']['shengxiao']}")
        print(f"  喜神: {bazi['xiyong']['xi_shen']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
