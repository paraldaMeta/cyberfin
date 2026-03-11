"""
AI Prediction Module Tests - PhD-Level Financial Analysis
Tests for the optimized AI prediction features including:
1. Frontend technical indicators calculation (passed via API)
2. New JSON structure with volume_price_analysis, bollinger_analysis, idiosyncratic_risks
3. Bull/Bear scenario probabilities summing to 100%
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAIPredictionNewFeatures:
    """Test new AI prediction features with PhD-level analysis"""
    
    def test_api_health(self):
        """Test API is responding"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        assert "Asian Financial Market" in response.json().get("message", "")
        print("✅ API health check passed")
    
    def test_ai_prediction_accepts_indicators(self):
        """Test /api/predict/ai accepts frontend-calculated indicators"""
        # Simulate frontend-calculated indicators
        indicators = {
            "current_price": 1850.00,
            "change_pct": 1.25,
            "amplitude": 2.5,
            "volume": 50000000,
            "volume_ratio": 1.2,
            "high": 1865.00,
            "low": 1840.00,
            "week52_high": 2100.00,
            "week52_low": 1500.00,
            "percentile_52w": 58,
            "ma5": 1845.00,
            "ma10": 1838.00,
            "ma20": 1825.00,
            "ma60": 1790.00,
            "ma_alignment": "多头排列",
            "dif": 15.5,
            "dea": 12.3,
            "macd_bar": 6.4,
            "macd_cross": "金叉",
            "rsi6": 62,
            "rsi14": 58,
            "rsi_status": "偏强区域",
            "kdj_k": 65,
            "kdj_d": 60,
            "kdj_j": 75,
            "boll_upper": 1920.00,
            "boll_mid": 1825.00,
            "boll_lower": 1730.00,
            "boll_bandwidth": "正常",
            "price_boll_position": "中轨上方",
            "tech_score": 7.2,
            "fundamental_score": 6.5,
            "signal_direction": "bullish",
            "signal_strength": 3,
            "news_summary": "[测试新闻摘要]"
        }
        
        payload = {
            "stock_code": "600519.SS",
            "stock_name": "贵州茅台",
            "time_period": "today",
            "market_data": {
                "price": 1850.00,
                "change_percent": 1.25,
                "volume": 50000000
            },
            "indicators": indicators
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response has new structure
        assert "executive_summary" in data
        assert "timestamp" in data
        print(f"✅ AI prediction accepts indicators parameter - Response received")
    
    def test_ai_prediction_executive_summary(self):
        """Test executive_summary structure (headline, direction, score, confidence)"""
        payload = {
            "stock_code": "AAPL",
            "stock_name": "苹果",
            "time_period": "week",
            "market_data": {"price": 225.0, "change_percent": 0.5, "volume": 80000000}
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        summary = data.get("executive_summary", {})
        
        # Verify headline
        assert "headline" in summary, "Missing headline in executive_summary"
        assert len(summary.get("headline", "")) > 0, "Headline should not be empty"
        
        # Verify direction
        assert "direction" in summary
        assert summary["direction"] in ["bullish", "bearish", "neutral"], f"Invalid direction: {summary['direction']}"
        
        # Verify composite_score
        assert "composite_score" in summary
        
        # Verify confidence_level
        assert "confidence_level" in summary
        
        print(f"✅ Executive summary validated: headline='{summary['headline'][:30]}...', direction={summary['direction']}")
    
    def test_ai_prediction_market_structure_analysis(self):
        """Test market_structure_analysis section"""
        payload = {
            "stock_code": "0700.HK",
            "stock_name": "腾讯控股",
            "time_period": "today"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        msa = data.get("market_structure_analysis", {})
        
        assert "current_phase" in msa
        assert "phase_evidence" in msa
        assert "cycle_position" in msa
        assert "liquidity_assessment" in msa
        assert "volatility_regime" in msa
        
        print(f"✅ Market structure analysis validated: phase={msa.get('current_phase')}")
    
    def test_ai_prediction_technical_deep_dive(self):
        """Test technical_deep_dive with collapsible sections"""
        payload = {
            "stock_code": "NVDA",
            "stock_name": "英伟达",
            "time_period": "month"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        tech = data.get("technical_deep_dive", {})
        
        # Verify trend_analysis
        assert "trend_analysis" in tech
        trend = tech["trend_analysis"]
        assert "primary_trend" in trend
        assert "ma_alignment" in trend
        
        # Verify momentum_analysis
        assert "momentum_analysis" in tech
        momentum = tech["momentum_analysis"]
        assert "macd_interpretation" in momentum
        assert "rsi_interpretation" in momentum
        
        # Verify volume_price_analysis (NEW FIELD)
        assert "volume_price_analysis" in tech, "Missing volume_price_analysis section"
        vpa = tech["volume_price_analysis"]
        assert "volume_trend" in vpa
        assert "price_volume_relationship" in vpa
        assert "institutional_footprint" in vpa
        
        # Verify bollinger_analysis (NEW FIELD)
        assert "bollinger_analysis" in tech, "Missing bollinger_analysis section"
        boll = tech["bollinger_analysis"]
        assert "band_status" in boll
        assert "squeeze_alert" in boll
        assert "bb_conclusion" in boll
        
        print(f"✅ Technical deep dive validated with volume_price_analysis and bollinger_analysis")
    
    def test_ai_prediction_scenario_probability_100(self):
        """Test that bull + bear scenario probabilities = 100%"""
        payload = {
            "stock_code": "MSFT",
            "stock_name": "微软",
            "time_period": "quarter"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        scenario = data.get("scenario_analysis", {})
        
        bull_prob_str = scenario.get("bull_scenario", {}).get("probability", "0%")
        bear_prob_str = scenario.get("bear_scenario", {}).get("probability", "0%")
        
        # Extract numeric values
        bull_prob = float(bull_prob_str.replace("%", "").strip())
        bear_prob = float(bear_prob_str.replace("%", "").strip())
        
        total = bull_prob + bear_prob
        assert 98 <= total <= 102, f"Bull({bull_prob}%) + Bear({bear_prob}%) = {total}%, should be ~100%"
        
        print(f"✅ Scenario probabilities validated: Bull={bull_prob}% + Bear={bear_prob}% = {total}%")
    
    def test_ai_prediction_risk_assessment_idiosyncratic(self):
        """Test risk_assessment includes idiosyncratic_risks (NEW FIELD)"""
        payload = {
            "stock_code": "TSLA",
            "stock_name": "特斯拉",
            "time_period": "year"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        risk = data.get("risk_assessment", {})
        
        assert "overall_risk_level" in risk
        assert risk["overall_risk_level"] in ["low", "medium", "high", "extreme"]
        
        assert "systematic_risks" in risk
        assert "idiosyncratic_risks" in risk, "Missing idiosyncratic_risks section"
        
        # Verify idiosyncratic_risks is a list
        idio_risks = risk["idiosyncratic_risks"]
        assert isinstance(idio_risks, list), "idiosyncratic_risks should be a list"
        
        if len(idio_risks) > 0:
            assert "risk" in idio_risks[0]
            assert "probability" in idio_risks[0]
            assert "impact" in idio_risks[0]
        
        print(f"✅ Risk assessment validated with idiosyncratic_risks: {len(idio_risks)} risks found")
    
    def test_ai_prediction_time_segmented_forecast(self):
        """Test time_segmented_forecast with multiple periods"""
        payload = {
            "stock_code": "GC=F",
            "stock_name": "黄金期货",
            "time_period": "today"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        forecast = data.get("time_segmented_forecast", [])
        
        assert isinstance(forecast, list)
        assert len(forecast) >= 1, "Should have at least 1 time segment"
        
        for segment in forecast:
            assert "period_label" in segment
            assert "directional_bias" in segment
            assert segment["directional_bias"] in ["bullish", "bearish", "neutral"]
            assert "key_price_behavior" in segment
        
        print(f"✅ Time segmented forecast validated: {len(forecast)} segments")
    
    def test_ai_prediction_professional_narrative(self):
        """Test professional_narrative with 5 collapsible paragraphs"""
        payload = {
            "stock_code": "USDCNY=X",
            "stock_name": "美元/人民币",
            "time_period": "month"
        }
        
        response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
        assert response.status_code == 200
        data = response.json()
        
        narrative = data.get("professional_narrative", {})
        
        # Check for 5 paragraphs
        expected_sections = [
            "opening_paragraph",
            "technical_narrative",
            "fundamental_narrative",
            "synthesis_paragraph",
            "forward_guidance"
        ]
        
        for section in expected_sections:
            assert section in narrative, f"Missing {section} in professional_narrative"
            assert len(narrative.get(section, "")) > 0, f"{section} should not be empty"
        
        print(f"✅ Professional narrative validated with all 5 sections")
    
    def test_different_markets(self):
        """Test AI prediction for different market types"""
        markets = [
            ("600519.SS", "贵州茅台", "a_stock"),  # A股
            ("0700.HK", "腾讯控股", "hk_stock"),   # 港股
            ("7203.T", "丰田汽车", "jp_stock"),    # 日股
            ("005930.KS", "三星电子", "kr_stock"), # 韩股
            ("CL=F", "原油期货", "futures"),       # 期货
            ("USDJPY=X", "美元/日元", "forex"),    # 外汇
        ]
        
        for code, name, mtype in markets:
            payload = {
                "stock_code": code,
                "stock_name": name,
                "time_period": "today"
            }
            
            response = requests.post(f"{BASE_URL}/api/predict/ai", json=payload, timeout=90)
            assert response.status_code == 200
            data = response.json()
            
            assert "executive_summary" in data
            print(f"✅ {mtype}: {name} ({code}) - Prediction generated")
        
        print("✅ All market types tested successfully")


class TestStockDetailWithIndicators:
    """Test stock detail endpoint that provides data for frontend calculations"""
    
    def test_stock_detail_returns_historical_data(self):
        """Test /api/stock/{symbol} returns historical data for indicator calculation"""
        response = requests.get(f"{BASE_URL}/api/stock/AAPL", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "stock" in data
        assert "historical" in data
        
        historical = data["historical"]
        assert isinstance(historical, list)
        assert len(historical) > 0
        
        # Verify historical data structure
        first_item = historical[0]
        assert "date" in first_item
        assert "open" in first_item
        assert "high" in first_item
        assert "low" in first_item
        assert "close" in first_item
        assert "volume" in first_item
        
        print(f"✅ Stock detail returns {len(historical)} historical data points for indicator calculation")
    
    def test_stock_detail_a_stock(self):
        """Test A股 stock detail"""
        response = requests.get(f"{BASE_URL}/api/stock/600519.SS", timeout=30)
        assert response.status_code == 200
        data = response.json()
        
        assert "stock" in data
        assert data["stock"]["symbol"] == "600519.SS"
        print(f"✅ A股 stock detail: {data['stock']['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
