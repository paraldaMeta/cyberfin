"""
Backend API tests for Asian Financial Market Prediction Platform.
Testing: Market data APIs, Search functionality, US Stock support, AI Prediction
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://predictix-asia.preview.emergentagent.com"

class TestHealthAndRoot:
    """Basic health check tests"""
    
    def test_api_root(self):
        """Test API root endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ API root returns: {data['message']}")

    def test_markets_list(self):
        """Test getting all available markets"""
        response = requests.get(f"{BASE_URL}/api/markets")
        assert response.status_code == 200
        data = response.json()
        assert "markets" in data
        market_ids = [m["id"] for m in data["markets"]]
        # Verify all expected markets are present
        expected_markets = ["a_stock", "us_stock", "hk_stock", "jp_stock", "kr_stock", "th_stock", "futures", "forex"]
        for market in expected_markets:
            assert market in market_ids, f"Missing market: {market}"
        print(f"✓ Found {len(data['markets'])} markets including us_stock")


class TestUSStockMarket:
    """Test US Stock market support (newly added)"""
    
    def test_us_stock_market_endpoint(self):
        """Test /api/market/us_stock returns US stocks"""
        response = requests.get(f"{BASE_URL}/api/market/us_stock")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        assert data["market_type"] == "us_stock"
        
        # Verify we have US stocks
        symbols = [s["symbol"] for s in data["stocks"]]
        # Check for expected US stock symbols
        expected_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]
        found_symbols = [s for s in expected_symbols if s in symbols]
        assert len(found_symbols) >= 3, f"Expected US stocks like AAPL, MSFT but found: {symbols}"
        print(f"✓ US stock market returns {len(data['stocks'])} stocks including: {found_symbols}")

    def test_aapl_stock_detail(self):
        """Test getting AAPL stock detail"""
        response = requests.get(f"{BASE_URL}/api/stock/AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "stock" in data
        assert data["stock"]["symbol"] == "AAPL"
        assert data["stock"]["name"] == "苹果"
        assert "price" in data["stock"]
        assert "historical" in data
        print(f"✓ AAPL stock detail: price={data['stock']['price']}, has {len(data.get('historical', []))} historical records")

    def test_msft_stock_detail(self):
        """Test getting MSFT stock detail"""
        response = requests.get(f"{BASE_URL}/api/stock/MSFT")
        assert response.status_code == 200
        data = response.json()
        assert "stock" in data
        assert data["stock"]["symbol"] == "MSFT"
        print(f"✓ MSFT stock detail: price={data['stock']['price']}")


class TestSearchFunctionality:
    """Test search functionality including empty search fix"""
    
    def test_search_aapl(self):
        """Test searching for AAPL returns results"""
        response = requests.get(f"{BASE_URL}/api/search?q=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0, "Should find AAPL in search results"
        
        # Verify AAPL is in results
        symbols = [r["symbol"] for r in data["results"]]
        assert "AAPL" in symbols, f"AAPL not in search results: {symbols}"
        print(f"✓ Search 'AAPL' returns {len(data['results'])} results")

    def test_search_chinese_name(self):
        """Test searching by Chinese name"""
        response = requests.get(f"{BASE_URL}/api/search?q=苹果")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        # Apple's Chinese name search should return AAPL
        if len(data["results"]) > 0:
            print(f"✓ Search '苹果' returns {len(data['results'])} results")
        else:
            print("⚠ Search '苹果' returns 0 results (may need Chinese character handling)")

    def test_empty_search_returns_empty_array(self):
        """Test empty search query returns empty array (not 422 error) - BUG FIX VERIFICATION"""
        response = requests.get(f"{BASE_URL}/api/search?q=")
        assert response.status_code == 200, f"Empty search should return 200, got {response.status_code}"
        data = response.json()
        assert "results" in data
        assert data["results"] == [], f"Empty search should return empty array, got: {data['results']}"
        print("✓ Empty search returns 200 with empty results array (BUG FIXED)")

    def test_whitespace_only_search(self):
        """Test whitespace-only search returns empty array"""
        response = requests.get(f"{BASE_URL}/api/search?q=   ")
        assert response.status_code == 200, f"Whitespace search should return 200, got {response.status_code}"
        data = response.json()
        assert "results" in data
        assert data["results"] == [], "Whitespace search should return empty array"
        print("✓ Whitespace-only search returns empty array")

    def test_search_partial_match(self):
        """Test partial symbol search"""
        response = requests.get(f"{BASE_URL}/api/search?q=AA")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"✓ Search 'AA' returns {len(data['results'])} results")


class TestMarketOverview:
    """Test market overview showing gainers/losers"""
    
    def test_overview_returns_gainers_losers(self):
        """Test market overview endpoint returns gainers and losers"""
        response = requests.get(f"{BASE_URL}/api/overview")
        assert response.status_code == 200
        data = response.json()
        
        assert "gainers" in data
        assert "losers" in data
        assert "all" in data
        assert "timestamp" in data
        
        # Verify structure of gainers/losers
        if len(data["gainers"]) > 0:
            gainer = data["gainers"][0]
            assert "symbol" in gainer
            assert "name" in gainer
            assert "price" in gainer
            assert "change_percent" in gainer
            
        print(f"✓ Overview: {len(data['gainers'])} gainers, {len(data['losers'])} losers, {len(data['all'])} total stocks")


class TestOtherMarkets:
    """Test other market endpoints"""
    
    def test_a_stock_market(self):
        """Test A股 market"""
        response = requests.get(f"{BASE_URL}/api/market/a_stock")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        assert len(data["stocks"]) > 0
        print(f"✓ A股 market returns {len(data['stocks'])} stocks")

    def test_hk_stock_market(self):
        """Test 港股 market"""
        response = requests.get(f"{BASE_URL}/api/market/hk_stock")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        print(f"✓ 港股 market returns {len(data['stocks'])} stocks")

    def test_futures_market(self):
        """Test 期货 market"""
        response = requests.get(f"{BASE_URL}/api/market/futures")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        print(f"✓ 期货 market returns {len(data['stocks'])} contracts")

    def test_forex_market(self):
        """Test 外汇 market"""
        response = requests.get(f"{BASE_URL}/api/market/forex")
        assert response.status_code == 200
        data = response.json()
        assert "stocks" in data
        print(f"✓ 外汇 market returns {len(data['stocks'])} currency pairs")


class TestAIPrediction:
    """Test AI prediction functionality"""
    
    def test_ai_prediction_for_us_stock(self):
        """Test AI prediction for AAPL (US stock)"""
        payload = {
            "stock_code": "AAPL",
            "stock_name": "苹果",
            "time_period": "today",
            "market_data": {
                "price": 200.0,
                "change": 2.0,
                "change_percent": 1.0,
                "volume": 50000000
            }
        }
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=120)
        assert response.status_code == 200
        data = response.json()
        
        # Check for new PhD-level analysis format
        if "executive_summary" in data:
            assert "direction" in data["executive_summary"]
            assert "headline" in data["executive_summary"]
            print(f"✓ AI Prediction (new format): {data['executive_summary']['headline'][:50]}...")
        else:
            # Fallback format
            assert "direction" in data
            print(f"✓ AI Prediction (fallback format): direction={data.get('direction')}")
        
        assert "timestamp" in data

    def test_ai_prediction_response_structure(self):
        """Test AI prediction response has expected structure"""
        payload = {
            "stock_code": "600519.SS",
            "stock_name": "贵州茅台",
            "time_period": "week",
            "market_data": {"price": 1800.0}
        }
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=120)
        assert response.status_code == 200
        data = response.json()
        
        # New format fields
        expected_fields = ["timestamp"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check if new or old format
        if "executive_summary" in data:
            assert "direction" in data["executive_summary"]
            assert "scenario_analysis" in data or "risk_assessment" in data
            print("✓ AI prediction returns PhD-level analysis format")
        else:
            print("✓ AI prediction returns standard format")


class TestDivinationPrediction:
    """Test divination prediction functionality"""
    
    def test_divination_prediction(self):
        """Test divination (占卜推演) functionality"""
        payload = {
            "user_name": "测试用户",
            "stock_code": "AAPL",
            "stock_name": "苹果",
            "time_period": "today"
        }
        response = requests.post(f"{BASE_URL}/api/predict/divination", json=payload, timeout=120)
        assert response.status_code == 200
        data = response.json()
        
        assert "report" in data
        assert "timestamp" in data
        assert len(data["report"]) > 100, "Divination report should have substantial content"
        print(f"✓ Divination returns report of {len(data['report'])} characters")


class TestStockDetail:
    """Test stock detail endpoint for various markets"""
    
    def test_a_stock_detail(self):
        """Test A股 stock detail"""
        response = requests.get(f"{BASE_URL}/api/stock/600519.SS")
        assert response.status_code == 200
        data = response.json()
        assert "stock" in data
        assert "historical" in data
        print(f"✓ A股 (贵州茅台) detail: price={data['stock']['price']}")

    def test_hk_stock_detail(self):
        """Test 港股 stock detail"""
        response = requests.get(f"{BASE_URL}/api/stock/0700.HK")
        assert response.status_code == 200
        data = response.json()
        assert "stock" in data
        print(f"✓ 港股 (腾讯) detail: price={data['stock']['price']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
