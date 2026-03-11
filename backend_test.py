#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time

class AsianFinancialPlatformTester:
    def __init__(self, base_url="https://quantum-trading-6.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    json_data = response.json()
                    return True, json_data
                except:
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                print(f"❌ Failed - {error_msg}")
                print(f"   Response: {response.text[:200]}...")
                self.failures.append(f"{name}: {error_msg}")
                return False, {}

        except requests.exceptions.Timeout:
            error_msg = "Request timeout"
            print(f"❌ Failed - {error_msg}")
            self.failures.append(f"{name}: {error_msg}")
            return False, {}
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed - Error: {error_msg}")
            self.failures.append(f"{name}: {error_msg}")
            return False, {}

    def test_basic_endpoints(self):
        """Test basic platform endpoints"""
        print("=== TESTING BASIC ENDPOINTS ===")
        
        # Test root endpoint
        self.run_test("Root API", "GET", "/", 200)
        
        # Test markets list
        success, markets_data = self.run_test("Markets List", "GET", "/markets", 200)
        if success:
            print(f"   Found {len(markets_data.get('markets', []))} markets")
        
        # Test market overview
        success, overview_data = self.run_test("Market Overview", "GET", "/overview", 200)
        if success:
            gainers = overview_data.get('gainers', [])
            losers = overview_data.get('losers', [])
            print(f"   Gainers: {len(gainers)}, Losers: {len(losers)}")

    def test_market_endpoints(self):
        """Test market-specific endpoints"""
        print("\n=== TESTING MARKET ENDPOINTS ===")
        
        markets = ['a_stock', 'hk_stock', 'jp_stock', 'kr_stock', 'th_stock', 'futures', 'forex']
        
        for market in markets:
            success, market_data = self.run_test(
                f"Market {market}", 
                "GET", 
                f"/market/{market}", 
                200,
                timeout=20
            )
            if success:
                stocks = market_data.get('stocks', [])
                print(f"   {market}: {len(stocks)} stocks")

    def test_stock_endpoints(self):
        """Test stock-specific endpoints"""
        print("\n=== TESTING STOCK ENDPOINTS ===")
        
        # Test stock search
        success, search_data = self.run_test("Stock Search", "GET", "/search?q=600519", 200)
        if success:
            results = search_data.get('results', [])
            print(f"   Search results: {len(results)}")
            
            # Test stock detail if search found results
            if results:
                symbol = results[0]['symbol']
                success, stock_detail = self.run_test(
                    f"Stock Detail ({symbol})", 
                    "GET", 
                    f"/stock/{symbol}", 
                    200,
                    timeout=20
                )
                if success:
                    historical = stock_detail.get('historical', [])
                    stock = stock_detail.get('stock', {})
                    print(f"   Stock: {stock.get('name', 'Unknown')}")
                    print(f"   Historical data points: {len(historical)}")

        # Test search with common terms
        test_queries = ['茅台', '腾讯', '黄金', 'USD']
        for query in test_queries:
            success, search_data = self.run_test(
                f"Search '{query}'", 
                "GET", 
                f"/search?q={query}", 
                200
            )
            if success:
                results = search_data.get('results', [])
                print(f"   Results for '{query}': {len(results)}")

    def test_ai_prediction(self):
        """Test AI prediction endpoint"""
        print("\n=== TESTING AI PREDICTION ===")
        
        # Test AI prediction with sample data
        test_request = {
            "stock_code": "600519.SS",
            "stock_name": "贵州茅台",
            "time_period": "week",
            "market_data": {
                "price": 1680.50,
                "change": 15.30,
                "change_percent": 0.92,
                "volume": 1500000
            }
        }
        
        success, prediction_data = self.run_test(
            "AI Prediction", 
            "POST", 
            "/predict/ai", 
            200,
            data=test_request,
            timeout=60
        )
        
        if success:
            direction = prediction_data.get('direction', 'unknown')
            confidence = prediction_data.get('confidence', 0)
            print(f"   Direction: {direction}, Confidence: {confidence}%")
            
            # Check required fields
            required_fields = ['direction', 'confidence', 'analysis', 'suggestions', 'risk_warning']
            missing_fields = [field for field in required_fields if field not in prediction_data]
            if missing_fields:
                print(f"   ⚠️  Missing fields: {missing_fields}")

    def test_divination_prediction(self):
        """Test divination prediction endpoint"""
        print("\n=== TESTING DIVINATION PREDICTION ===")
        
        # Test divination prediction
        test_request = {
            "user_name": "测试用户",
            "stock_code": "0700.HK",
            "stock_name": "腾讯控股",
            "time_period": "month"
        }
        
        success, divination_data = self.run_test(
            "Divination Prediction", 
            "POST", 
            "/predict/divination", 
            200,
            data=test_request,
            timeout=60
        )
        
        if success:
            report = divination_data.get('report', '')
            print(f"   Report length: {len(report)} characters")
            if '动态时序战略报告' in report:
                print(f"   ✅ Contains expected report structure")
            else:
                print(f"   ⚠️  Report structure may be incomplete")

    def test_error_handling(self):
        """Test error handling for invalid requests"""
        print("\n=== TESTING ERROR HANDLING ===")
        
        # Test invalid market
        self.run_test("Invalid Market", "GET", "/market/invalid", 404)
        
        # Test invalid stock
        self.run_test("Invalid Stock", "GET", "/stock/INVALID", 404)
        
        # Test invalid search
        success, _ = self.run_test("Empty Search", "GET", "/search?q=", 200)
        
        # Test invalid AI prediction
        invalid_ai_request = {
            "stock_code": "",
            "stock_name": "",
            "time_period": "invalid"
        }
        self.run_test("Invalid AI Request", "POST", "/predict/ai", 422, data=invalid_ai_request)

def main():
    print("🚀 Starting Asian Financial Platform API Tests")
    print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    tester = AsianFinancialPlatformTester()
    
    try:
        # Run all test suites
        tester.test_basic_endpoints()
        tester.test_market_endpoints()
        tester.test_stock_endpoints()
        tester.test_ai_prediction()
        tester.test_divination_prediction()
        tester.test_error_handling()
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"   Total Tests: {tester.tests_run}")
        print(f"   Passed: {tester.tests_passed}")
        print(f"   Failed: {tester.tests_run - tester.tests_passed}")
        print(f"   Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
        
        if tester.failures:
            print(f"\n❌ FAILURES:")
            for i, failure in enumerate(tester.failures, 1):
                print(f"   {i}. {failure}")
        
        return 0 if tester.tests_passed == tester.tests_run else 1
        
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())