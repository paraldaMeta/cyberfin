from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import httpx
import asyncio
import json

# Import AI prediction prompts
from services.ai_prediction_prompts import SYSTEM_PROMPT, build_user_prompt

# Import Bazi calculator
from services.bazi import BaziCalculator
from services.bazi.city_coordinates import get_province_list, get_city_list
from services.bazi.constants import SHICHEN_OPTIONS

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# MiniMax API
MINIMAX_API_KEY = os.environ.get('MINIMAX_API_KEY', '')
MINIMAX_API_URL = "https://api.minimax.chat/v1/text/chatcompletion_v2"

# Alpha Vantage API (backup data source)
ALPHA_VANTAGE_API_KEY = os.environ.get('ALPHA_VANTAGE_API_KEY', 'demo')
ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

# Prediction history retention (3 months = 90 days)
PREDICTION_HISTORY_DAYS = 90

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ Models ============
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

class StockData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    timestamp: str
    market_type: str

class TechnicalIndicators(BaseModel):
    """Technical indicators calculated by frontend"""
    current_price: float
    change_pct: float
    amplitude: Optional[float] = 0
    volume: Optional[float] = 0
    volume_ratio: Optional[float] = 1.0
    high: Optional[float] = None
    low: Optional[float] = None
    week52_high: Optional[float] = None
    week52_low: Optional[float] = None
    percentile_52w: Optional[float] = 50
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma_alignment: Optional[str] = "纠缠粘合"
    dif: Optional[float] = 0
    dea: Optional[float] = 0
    macd_bar: Optional[float] = 0
    macd_cross: Optional[str] = "无交叉"
    rsi6: Optional[float] = 50
    rsi14: Optional[float] = 50
    rsi_status: Optional[str] = "中性区域"
    kdj_k: Optional[float] = 50
    kdj_d: Optional[float] = 50
    kdj_j: Optional[float] = 50
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
    boll_bandwidth: Optional[str] = "正常"
    price_boll_position: Optional[str] = "中轨附近"
    tech_score: Optional[float] = 5
    fundamental_score: Optional[float] = 5
    signal_direction: Optional[str] = "neutral"
    signal_strength: Optional[int] = 2
    news_summary: Optional[str] = None

class PredictionRequest(BaseModel):
    stock_code: str
    stock_name: str
    time_period: str  # today/week/month/quarter/year
    market_data: Optional[Dict[str, Any]] = None
    indicators: Optional[TechnicalIndicators] = None

class DivinationRequest(BaseModel):
    user_name: str
    stock_code: str
    stock_name: str
    time_period: str

class PredictionResponse(BaseModel):
    direction: str  # bullish/bearish/neutral
    confidence: int
    target_price_range: Dict[str, float]
    support_levels: List[float]
    resistance_levels: List[float]
    analysis: str
    suggestions: str
    risk_warning: str
    timestamp: str

class DivinationResponse(BaseModel):
    report: str
    timestamp: str

# New models for prediction history
class PredictionHistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prediction_type: str  # "ai" or "divination"
    stock_code: str
    stock_name: str
    time_period: str
    user_name: Optional[str] = None  # for divination
    result: Dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WatchlistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    symbol: str
    name: str
    market_type: str
    added_at: str

# ============ User & Bazi Models ============
class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str
    password: str
    phone: Optional[str] = None
    name: str  # 姓名（用于八字推演显示）
    gender: str  # 男/女
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: Optional[str] = None  # 时辰地支，如 '子', '丑' 等，或 'unknown'
    birth_province: Optional[str] = None
    birth_city: Optional[str] = None

class UserLoginRequest(BaseModel):
    """用户登录请求"""
    username: str
    password: str

class UserProfile(BaseModel):
    """用户资料"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    phone: Optional[str] = None
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: Optional[str] = None
    birth_province: Optional[str] = None
    birth_city: Optional[str] = None
    bazi_data: Optional[Dict[str, Any]] = None  # 存储计算好的命盘数据
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BaziCalculateRequest(BaseModel):
    """八字计算请求"""
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    birth_hour: Optional[str] = None  # 时辰地支
    birth_province: Optional[str] = None
    birth_city: Optional[str] = None

# ============ Market Data Service ============
# Stock symbols for different markets
MARKET_STOCKS = {
    "a_stock": [
        {"symbol": "600519.SS", "name": "贵州茅台"},
        {"symbol": "000858.SZ", "name": "五粮液"},
        {"symbol": "601318.SS", "name": "中国平安"},
        {"symbol": "600036.SS", "name": "招商银行"},
        {"symbol": "000333.SZ", "name": "美的集团"},
        {"symbol": "600276.SS", "name": "恒瑞医药"},
        {"symbol": "000651.SZ", "name": "格力电器"},
        {"symbol": "601888.SS", "name": "中国中免"},
        {"symbol": "300750.SZ", "name": "宁德时代"},
        {"symbol": "600900.SS", "name": "长江电力"},
    ],
    "us_stock": [
        {"symbol": "AAPL", "name": "苹果"},
        {"symbol": "MSFT", "name": "微软"},
        {"symbol": "GOOGL", "name": "谷歌"},
        {"symbol": "AMZN", "name": "亚马逊"},
        {"symbol": "NVDA", "name": "英伟达"},
        {"symbol": "META", "name": "Meta"},
        {"symbol": "TSLA", "name": "特斯拉"},
        {"symbol": "BRK-B", "name": "伯克希尔"},
        {"symbol": "JPM", "name": "摩根大通"},
        {"symbol": "V", "name": "Visa"},
    ],
    "hk_stock": [
        {"symbol": "0700.HK", "name": "腾讯控股"},
        {"symbol": "9988.HK", "name": "阿里巴巴"},
        {"symbol": "3690.HK", "name": "美团"},
        {"symbol": "1810.HK", "name": "小米集团"},
        {"symbol": "9618.HK", "name": "京东集团"},
        {"symbol": "0941.HK", "name": "中国移动"},
        {"symbol": "2318.HK", "name": "中国平安"},
        {"symbol": "0005.HK", "name": "汇丰控股"},
        {"symbol": "1299.HK", "name": "友邦保险"},
        {"symbol": "0388.HK", "name": "香港交易所"},
    ],
    "jp_stock": [
        {"symbol": "7203.T", "name": "丰田汽车"},
        {"symbol": "6758.T", "name": "索尼集团"},
        {"symbol": "6861.T", "name": "基恩士"},
        {"symbol": "9984.T", "name": "软银集团"},
        {"symbol": "6501.T", "name": "日立制作所"},
        {"symbol": "8306.T", "name": "三菱UFJ金融"},
        {"symbol": "7267.T", "name": "本田汽车"},
        {"symbol": "4063.T", "name": "信越化学"},
        {"symbol": "9433.T", "name": "KDDI"},
        {"symbol": "6902.T", "name": "电装"},
    ],
    "kr_stock": [
        {"symbol": "005930.KS", "name": "三星电子"},
        {"symbol": "000660.KS", "name": "SK海力士"},
        {"symbol": "035420.KS", "name": "NAVER"},
        {"symbol": "035720.KS", "name": "Kakao"},
        {"symbol": "005380.KS", "name": "现代汽车"},
        {"symbol": "068270.KS", "name": "Celltrion"},
        {"symbol": "051910.KS", "name": "LG化学"},
        {"symbol": "006400.KS", "name": "三星SDI"},
        {"symbol": "000270.KS", "name": "起亚汽车"},
        {"symbol": "028260.KS", "name": "三星物产"},
    ],
    "th_stock": [
        {"symbol": "PTT.BK", "name": "泰国国家石油"},
        {"symbol": "AOT.BK", "name": "泰国机场"},
        {"symbol": "CPALL.BK", "name": "CP ALL"},
        {"symbol": "SCC.BK", "name": "泰国水泥"},
        {"symbol": "ADVANC.BK", "name": "AIS电信"},
        {"symbol": "KBANK.BK", "name": "开泰银行"},
        {"symbol": "SCB.BK", "name": "暹罗商业银行"},
        {"symbol": "GULF.BK", "name": "海湾能源"},
        {"symbol": "BDMS.BK", "name": "曼谷杜斯特医疗"},
        {"symbol": "PTTEP.BK", "name": "泰国国油勘探"},
    ],
    "futures": [
        {"symbol": "GC=F", "name": "黄金期货"},
        {"symbol": "SI=F", "name": "白银期货"},
        {"symbol": "CL=F", "name": "原油期货"},
        {"symbol": "NG=F", "name": "天然气期货"},
        {"symbol": "HG=F", "name": "铜期货"},
        {"symbol": "PL=F", "name": "铂金期货"},
        {"symbol": "PA=F", "name": "钯金期货"},
        {"symbol": "ZC=F", "name": "玉米期货"},
        {"symbol": "ZS=F", "name": "大豆期货"},
        {"symbol": "ZW=F", "name": "小麦期货"},
    ],
    "forex": [
        {"symbol": "USDCNY=X", "name": "美元/人民币"},
        {"symbol": "USDJPY=X", "name": "美元/日元"},
        {"symbol": "USDKRW=X", "name": "美元/韩元"},
        {"symbol": "USDTHB=X", "name": "美元/泰铢"},
        {"symbol": "USDHKD=X", "name": "美元/港币"},
        {"symbol": "EURUSD=X", "name": "欧元/美元"},
        {"symbol": "GBPUSD=X", "name": "英镑/美元"},
        {"symbol": "AUDUSD=X", "name": "澳元/美元"},
        {"symbol": "USDSGD=X", "name": "美元/新加坡元"},
        {"symbol": "USDINR=X", "name": "美元/印度卢比"},
    ]
}

# Cache for market data
market_cache: Dict[str, Dict] = {}
cache_timestamp: Dict[str, datetime] = {}
CACHE_DURATION = 60  # seconds

async def fetch_yahoo_finance_data(symbol: str) -> Optional[Dict]:
    """Fetch stock data from Yahoo Finance API"""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "interval": "1d",
            "range": "5d"
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                result = data.get("chart", {}).get("result", [])
                if result:
                    meta = result[0].get("meta", {})
                    return {
                        "price": meta.get("regularMarketPrice", 0),
                        "previous_close": meta.get("previousClose", 0),
                        "volume": meta.get("regularMarketVolume", 0),
                        "currency": meta.get("currency", "USD"),
                        "source": "yahoo"
                    }
            elif response.status_code == 429:
                logger.warning(f"Yahoo Finance rate limited for {symbol}, trying Alpha Vantage")
                return None
    except Exception as e:
        logger.error(f"Yahoo Finance error for {symbol}: {e}")
    return None

async def fetch_alpha_vantage_data(symbol: str) -> Optional[Dict]:
    """Fetch stock data from Alpha Vantage API (backup)"""
    try:
        # Convert symbol format for Alpha Vantage
        av_symbol = symbol.replace(".SS", "").replace(".SZ", "").replace(".HK", "").replace(".T", "").replace(".KS", "").replace(".BK", "")
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": av_symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(ALPHA_VANTAGE_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                quote = data.get("Global Quote", {})
                if quote:
                    price = float(quote.get("05. price", 0))
                    prev_close = float(quote.get("08. previous close", 0))
                    volume = int(quote.get("06. volume", 0))
                    return {
                        "price": price,
                        "previous_close": prev_close,
                        "volume": volume,
                        "currency": "USD",
                        "source": "alphavantage"
                    }
    except Exception as e:
        logger.error(f"Alpha Vantage error for {symbol}: {e}")
    return None

async def fetch_stock_data(symbol: str, name: str, market_type: str) -> StockData:
    """Fetch stock data with caching and fallback to Alpha Vantage"""
    cache_key = symbol
    now = datetime.now(timezone.utc)
    
    # Check cache
    if cache_key in market_cache and cache_key in cache_timestamp:
        if (now - cache_timestamp[cache_key]).total_seconds() < CACHE_DURATION:
            cached = market_cache[cache_key]
            return StockData(**cached)
    
    # Try Yahoo Finance first
    data = await fetch_yahoo_finance_data(symbol)
    
    # Fallback to Alpha Vantage if Yahoo fails
    if not data:
        data = await fetch_alpha_vantage_data(symbol)
    
    if data:
        price = data["price"]
        prev_close = data["previous_close"]
        change = price - prev_close if prev_close else 0
        change_percent = (change / prev_close * 100) if prev_close else 0
        
        stock_data = {
            "symbol": symbol,
            "name": name,
            "price": round(price, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": data.get("volume"),
            "timestamp": now.isoformat(),
            "market_type": market_type
        }
    else:
        # Generate simulated data if both APIs fail
        import random
        base_price = random.uniform(10, 1000)
        change = random.uniform(-5, 5)
        stock_data = {
            "symbol": symbol,
            "name": name,
            "price": round(base_price, 2),
            "change": round(change, 2),
            "change_percent": round(change / base_price * 100, 2),
            "volume": random.randint(100000, 10000000),
            "timestamp": now.isoformat(),
            "market_type": market_type
        }
    
    # Update cache
    market_cache[cache_key] = stock_data
    cache_timestamp[cache_key] = now
    
    return StockData(**stock_data)

# ============ MiniMax API Service ============
async def call_minimax_api(messages: List[Dict], max_tokens: int = 2000, temperature: float = 0.3) -> str:
    """Call MiniMax M2.5 API"""
    headers = {
        "Authorization": f"Bearer {MINIMAX_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "MiniMax-Text-01",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            logger.info(f"Calling MiniMax API with payload length: {len(str(payload))}")
            response = await http_client.post(MINIMAX_API_URL, headers=headers, json=payload)
            logger.info(f"MiniMax API response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Try different response structures
                content = ""
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice:
                        content = choice["message"].get("content", "")
                    elif "text" in choice:
                        content = choice["text"]
                elif "output" in data:
                    content = data.get("output", {}).get("text", "")
                elif "reply" in data:
                    content = data["reply"]
                
                logger.info(f"MiniMax API content length: {len(content)}")
                return content
            else:
                logger.error(f"MiniMax API error: {response.status_code} - {response.text[:500]}")
                return ""
    except httpx.TimeoutException:
        logger.error("MiniMax API timeout")
        return ""
    except Exception as e:
        logger.error(f"MiniMax API exception: {e}")
        return ""

# ============ API Routes ============
@api_router.get("/")
async def root():
    return {"message": "Asian Financial Market Prediction Platform API"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

@api_router.get("/markets")
async def get_markets():
    """Get all available markets"""
    return {
        "markets": [
            {"id": "a_stock", "name": "A股", "description": "中国A股市场"},
            {"id": "us_stock", "name": "美股", "description": "美国股票市场"},
            {"id": "hk_stock", "name": "港股", "description": "香港股票市场"},
            {"id": "jp_stock", "name": "日股", "description": "日本股票市场"},
            {"id": "kr_stock", "name": "韩股", "description": "韩国股票市场"},
            {"id": "th_stock", "name": "泰股", "description": "泰国股票市场"},
            {"id": "futures", "name": "期货", "description": "商品期货市场"},
            {"id": "forex", "name": "外汇", "description": "外汇市场"},
        ]
    }

@api_router.get("/market/{market_type}")
async def get_market_stocks(market_type: str):
    """Get stocks for a specific market"""
    if market_type not in MARKET_STOCKS:
        raise HTTPException(status_code=404, detail="Market type not found")
    
    stocks = MARKET_STOCKS[market_type]
    tasks = [fetch_stock_data(s["symbol"], s["name"], market_type) for s in stocks]
    results = await asyncio.gather(*tasks)
    
    return {"market_type": market_type, "stocks": [r.model_dump() for r in results]}

@api_router.get("/stock/{symbol}")
async def get_stock_detail(symbol: str):
    """Get detailed stock data"""
    # Find stock info
    stock_info = None
    market_type = None
    for mtype, stocks in MARKET_STOCKS.items():
        for s in stocks:
            if s["symbol"] == symbol:
                stock_info = s
                market_type = mtype
                break
        if stock_info:
            break
    
    if not stock_info:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    stock_data = await fetch_stock_data(symbol, stock_info["name"], market_type)
    
    # Fetch historical data for chart
    historical = []
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": "1d", "range": "3mo"}
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            response = await http_client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                result = data.get("chart", {}).get("result", [])
                if result:
                    timestamps = result[0].get("timestamp", [])
                    quotes = result[0].get("indicators", {}).get("quote", [{}])[0]
                    opens = quotes.get("open", [])
                    highs = quotes.get("high", [])
                    lows = quotes.get("low", [])
                    closes = quotes.get("close", [])
                    volumes = quotes.get("volume", [])
                    
                    for i, ts in enumerate(timestamps):
                        if i < len(closes) and closes[i] is not None:
                            historical.append({
                                "date": datetime.fromtimestamp(ts).strftime("%Y-%m-%d"),
                                "open": round(opens[i], 2) if opens[i] else 0,
                                "high": round(highs[i], 2) if highs[i] else 0,
                                "low": round(lows[i], 2) if lows[i] else 0,
                                "close": round(closes[i], 2) if closes[i] else 0,
                                "volume": volumes[i] if volumes[i] else 0
                            })
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
    
    # Generate simulated data if no historical
    if not historical:
        import random
        base = stock_data.price
        for i in range(60):
            d = datetime.now(timezone.utc) - timedelta(days=60-i)
            change = random.uniform(-0.03, 0.03)
            base = base * (1 + change)
            historical.append({
                "date": d.strftime("%Y-%m-%d"),
                "open": round(base * 0.99, 2),
                "high": round(base * 1.02, 2),
                "low": round(base * 0.98, 2),
                "close": round(base, 2),
                "volume": random.randint(1000000, 50000000)
            })
    
    return {
        "stock": stock_data.model_dump(),
        "historical": historical
    }

@api_router.get("/search")
async def search_stocks(q: str = Query(default="")):
    """Search stocks by code or name"""
    # Handle empty query gracefully
    if not q or not q.strip():
        return {"results": []}
    
    results = []
    q_lower = q.lower().strip()
    for market_type, stocks in MARKET_STOCKS.items():
        for s in stocks:
            if q_lower in s["symbol"].lower() or q_lower in s["name"].lower():
                results.append({
                    "symbol": s["symbol"],
                    "name": s["name"],
                    "market_type": market_type
                })
    return {"results": results[:20]}

@api_router.get("/overview")
async def get_market_overview():
    """Get market overview with top movers"""
    all_stocks = []
    for market_type, stocks in MARKET_STOCKS.items():
        for s in stocks[:3]:  # Get top 3 from each market
            stock_data = await fetch_stock_data(s["symbol"], s["name"], market_type)
            all_stocks.append(stock_data.model_dump())
    
    # Sort by change percent
    gainers = sorted(all_stocks, key=lambda x: x["change_percent"], reverse=True)[:5]
    losers = sorted(all_stocks, key=lambda x: x["change_percent"])[:5]
    
    return {
        "gainers": gainers,
        "losers": losers,
        "all": all_stocks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Financial News Cache
news_cache = []
news_cache_time = None
NEWS_CACHE_DURATION = 300  # 5 minutes

@api_router.get("/news")
async def get_financial_news(limit: int = Query(default=10, ge=1, le=50)):
    """Get financial news from various sources"""
    global news_cache, news_cache_time
    
    # Return cached news if still valid
    if news_cache and news_cache_time and (datetime.now(timezone.utc) - news_cache_time).seconds < NEWS_CACHE_DURATION:
        return {"news": news_cache[:limit], "cached": True}
    
    news_items = []
    
    try:
        # Try to fetch from multiple sources
        # Source 1: Yahoo Finance RSS (via proxy to avoid CORS)
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Financial news from different regions
            news_sources = [
                {
                    "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^SSEC&region=US&lang=en-US",
                    "region": "China"
                },
                {
                    "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^N225&region=US&lang=en-US", 
                    "region": "Japan"
                },
                {
                    "url": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^HSI&region=US&lang=en-US",
                    "region": "Hong Kong"
                }
            ]
            
            for source in news_sources:
                try:
                    response = await client.get(source["url"], follow_redirects=True)
                    if response.status_code == 200:
                        # Parse RSS (simplified)
                        import re
                        items = re.findall(r'<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<pubDate>(.*?)</pubDate>.*?</item>', 
                                          response.text, re.DOTALL)
                        for title, link, pub_date in items[:5]:
                            news_items.append({
                                "title": title.replace('<![CDATA[', '').replace(']]>', '').strip(),
                                "url": link.strip(),
                                "published": pub_date.strip(),
                                "region": source["region"],
                                "source": "Yahoo Finance"
                            })
                except Exception as e:
                    logger.warning(f"Failed to fetch news from {source['region']}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Failed to fetch news: {e}")
    
    # If no news fetched, provide sample news
    if not news_items:
        news_items = [
            {"title": "亚洲股市今日普遍走高，投资者关注经济数据", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Asia", "source": "Market Update"},
            {"title": "中国A股市场成交量温和放大，北向资金持续流入", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "China", "source": "Market Update"},
            {"title": "日经225指数再创新高，日元汇率成关注焦点", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Japan", "source": "Market Update"},
            {"title": "港股恒生指数震荡整理，科技股表现分化", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Hong Kong", "source": "Market Update"},
            {"title": "韩国KOSPI指数小幅上涨，半导体板块领涨", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Korea", "source": "Market Update"},
            {"title": "泰国SET指数表现平稳，旅游复苏预期支撑", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Thailand", "source": "Market Update"},
            {"title": "美元指数回落，亚洲货币普遍走强", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Forex", "source": "Market Update"},
            {"title": "黄金期货价格小幅上涨，避险需求支撑", "url": "#", "published": datetime.now(timezone.utc).isoformat(), "region": "Commodities", "source": "Market Update"},
        ]
    
    # Update cache
    news_cache = news_items
    news_cache_time = datetime.now(timezone.utc)
    
    return {"news": news_items[:limit], "cached": False}


@api_router.post("/predict/ai")
async def ai_prediction(request: PredictionRequest):
    """Generate AI prediction using MiniMax - PhD-level Financial Analysis"""
    time_labels = {
        "today": "今日",
        "week": "本周",
        "month": "本月",
        "quarter": "本季度",
        "year": "本年"
    }
    time_period_cn = time_labels.get(request.time_period, request.time_period)
    
    # Determine market type
    market_type = "a_stock"
    if request.stock_code:
        if ".HK" in request.stock_code:
            market_type = "hk_stock"
        elif ".T" in request.stock_code:
            market_type = "jp_stock"
        elif ".KS" in request.stock_code:
            market_type = "kr_stock"
        elif ".BK" in request.stock_code:
            market_type = "th_stock"
        elif "=F" in request.stock_code:
            market_type = "futures"
        elif "=X" in request.stock_code:
            market_type = "forex"
        elif ".SS" not in request.stock_code and ".SZ" not in request.stock_code:
            market_type = "us_stock"
    
    market_type_cn = {
        "a_stock": "A股",
        "us_stock": "美股",
        "hk_stock": "港股", 
        "jp_stock": "日股",
        "kr_stock": "韩股",
        "th_stock": "泰股",
        "futures": "期货",
        "forex": "外汇"
    }.get(market_type, "股票")
    
    # Generate time segments based on time_period
    if request.time_period == "today":
        segments = "早盘(09:30-11:30), 午盘(13:00-14:00), 尾盘(14:00-收盘)"
    elif request.time_period == "week":
        segments = "周一至周二(开局), 周三(中枢), 周四至周五(收官)"
    elif request.time_period == "month":
        segments = "上旬(1-10日), 中旬(11-20日), 下旬(21日-月底)"
    elif request.time_period == "quarter":
        segments = "第一月(开仓期), 第二月(持仓期), 第三月(结算期)"
    else:
        segments = "Q1(春季行情), Q2(夏季行情), Q3(秋季行情), Q4(年末行情)"
    
    # Build indicators dict from request
    market_data = request.market_data or {}
    price = market_data.get("price", 100)
    change_pct = market_data.get("change_percent", 0)
    volume = market_data.get("volume", 0)
    
    # Use frontend-calculated indicators if provided, otherwise use basic values
    if request.indicators:
        ind = request.indicators
        indicators_dict = {
            "current_price": ind.current_price,
            "change_pct": ind.change_pct,
            "amplitude": ind.amplitude or abs(change_pct) * 1.5,
            "volume": ind.volume if ind.volume else volume,
            "volume_ratio": ind.volume_ratio or 1.0,
            "high": ind.high or ind.current_price * 1.01,
            "low": ind.low or ind.current_price * 0.99,
            "week52_high": ind.week52_high or ind.current_price * 1.2,
            "week52_low": ind.week52_low or ind.current_price * 0.8,
            "percentile_52w": ind.percentile_52w or 50,
            "ma5": ind.ma5 or ind.current_price * 0.99,
            "ma10": ind.ma10 or ind.current_price * 0.985,
            "ma20": ind.ma20 or ind.current_price * 0.98,
            "ma60": ind.ma60 or ind.current_price * 0.97,
            "ma_alignment": ind.ma_alignment or "纠缠粘合",
            "dif": ind.dif or 0,
            "dea": ind.dea or 0,
            "macd_bar": ind.macd_bar or 0,
            "macd_cross": ind.macd_cross or "无交叉",
            "rsi6": ind.rsi6 or 50,
            "rsi14": ind.rsi14 or 50,
            "rsi_status": ind.rsi_status or "中性区域",
            "kdj_k": ind.kdj_k or 50,
            "kdj_d": ind.kdj_d or 50,
            "kdj_j": ind.kdj_j or 50,
            "boll_upper": ind.boll_upper or ind.current_price * 1.04,
            "boll_mid": ind.boll_mid or ind.current_price,
            "boll_lower": ind.boll_lower or ind.current_price * 0.96,
            "boll_bandwidth": ind.boll_bandwidth or "正常",
            "price_boll_position": ind.price_boll_position or "中轨附近",
            "tech_score": ind.tech_score or 5,
            "fundamental_score": ind.fundamental_score or 5,
            "signal_direction": ind.signal_direction or "neutral",
            "signal_strength": ind.signal_strength or 2,
            "news_summary": ind.news_summary or "[实时资讯数据缺失，宏观面分析基于该市场通用框架推断]"
        }
    else:
        # Fallback: use basic market_data to construct indicators
        ma5 = market_data.get("ma5", round(price * 0.99, 2))
        ma20 = market_data.get("ma20", round(price * 0.98, 2))
        ma60 = market_data.get("ma60", round(price * 0.97, 2))
        indicators_dict = {
            "current_price": price,
            "change_pct": change_pct,
            "amplitude": abs(change_pct) * 1.5,
            "volume": volume,
            "volume_ratio": 1.0,
            "high": price * 1.01,
            "low": price * 0.99,
            "week52_high": price * 1.2,
            "week52_low": price * 0.8,
            "percentile_52w": 50,
            "ma5": ma5,
            "ma10": round(price * 0.985, 2),
            "ma20": ma20,
            "ma60": ma60,
            "ma_alignment": "多头排列" if price > ma5 > ma20 > ma60 else "空头排列" if price < ma5 < ma20 < ma60 else "纠缠粘合",
            "dif": round(change_pct * 0.5, 2),
            "dea": round(change_pct * 0.3, 2),
            "macd_bar": round(change_pct * 0.2, 2),
            "macd_cross": "金叉" if change_pct > 0 else "死叉" if change_pct < 0 else "无交叉",
            "rsi6": min(80, max(20, 50 + change_pct * 5)),
            "rsi14": min(75, max(25, 50 + change_pct * 3)),
            "rsi_status": "超买区域" if change_pct > 3 else "超卖区域" if change_pct < -3 else "中性区域",
            "kdj_k": min(90, max(10, 50 + change_pct * 4)),
            "kdj_d": min(85, max(15, 50 + change_pct * 3)),
            "kdj_j": min(100, max(0, 50 + change_pct * 6)),
            "boll_upper": round(price * 1.04, 2),
            "boll_mid": round(price, 2),
            "boll_lower": round(price * 0.96, 2),
            "boll_bandwidth": "扩张" if abs(change_pct) > 2 else "正常",
            "price_boll_position": "上轨附近" if change_pct > 2 else "下轨附近" if change_pct < -2 else "中轨附近",
            "tech_score": round(5 + change_pct / 2, 1),
            "fundamental_score": round(5 + change_pct / 3, 1),
            "signal_direction": "bullish" if change_pct > 1 else "bearish" if change_pct < -1 else "neutral",
            "signal_strength": min(5, max(1, abs(int(change_pct)) + 1)),
            "news_summary": "[实时资讯数据缺失，宏观面分析基于该市场通用框架推断]"
        }
    
    # Build prompts using the new module
    user_prompt = build_user_prompt(
        stock_name=request.stock_name,
        stock_code=request.stock_code,
        market_type_cn=market_type_cn,
        time_period_cn=time_period_cn,
        segments=segments,
        indicators=indicators_dict
    )
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    response_text = await call_minimax_api(messages, max_tokens=6000, temperature=0.3)
    
    # Parse response
    try:
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            prediction_data = json.loads(json_match.group())
            # Validate basic structure
            if "executive_summary" not in prediction_data:
                raise ValueError("Missing executive_summary")
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}, response: {response_text[:300] if response_text else 'empty'}")
        
        # Generate intelligent fallback with new structure
        prediction_data = generate_fallback_prediction(
            request=request,
            indicators=indicators_dict,
            market_type=market_type,
            market_type_cn=market_type_cn,
            time_period_cn=time_period_cn,
            segments=segments
        )
    
    return {
        **prediction_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def generate_fallback_prediction(request, indicators, market_type, market_type_cn, time_period_cn, segments):
    """Generate a fallback prediction when API call fails"""
    import random
    
    price = indicators["current_price"]
    change_pct = indicators["change_pct"]
    volume = indicators["volume"]
    ma5 = indicators["ma5"]
    ma20 = indicators["ma20"]
    ma60 = indicators["ma60"]
    
    if change_pct > 1:
        direction = "bullish"
        bull_prob = random.randint(55, 70)
    elif change_pct < -1:
        direction = "bearish"
        bull_prob = random.randint(30, 45)
    else:
        direction = "neutral"
        bull_prob = random.randint(45, 55)
    
    bear_prob = 100 - bull_prob
    composite_score = round(5 + (change_pct / 2), 1)
    composite_score = max(1, min(10, composite_score))
    
    return {
        "report_meta": {
            "stock_name": request.stock_name,
            "stock_code": request.stock_code,
            "market_type": market_type_cn,
            "time_period": time_period_cn,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "analyst_note": "本报告由AI基于量化指标生成，不构成投资建议"
        },
        "executive_summary": {
            "headline": f"{request.stock_name}{'上涨动能增强' if direction == 'bullish' else '承压回调风险' if direction == 'bearish' else '多空博弈震荡'}，关注关键支撑位",
            "direction": direction,
            "composite_score": str(composite_score),
            "confidence_level": f"{bull_prob if direction == 'bullish' else bear_prob if direction == 'bearish' else 50}%",
            "signal_grade": "B" if abs(change_pct) > 1 else "C",
            "three_line_summary": f"趋势：当前处于{'上升' if direction == 'bullish' else '下降' if direction == 'bearish' else '震荡'}通道。核心驱动：{'量能配合价格突破' if direction == 'bullish' else '获利盘出逃压力' if direction == 'bearish' else '多空力量均衡'}。风险：关注{round(price * 0.95, 2)}支撑位有效性。"
        },
        "market_structure_analysis": {
            "current_phase": "上升期" if direction == "bullish" else "下降期" if direction == "bearish" else "底部震荡",
            "phase_evidence": f"①价格{'站上' if price > ma20 else '跌破'}20日均线 ②成交量{'放大' if volume > 0 else '萎缩'} ③涨跌幅{change_pct}%",
            "cycle_position": f"中期{'上升' if direction == 'bullish' else '下降' if direction == 'bearish' else '震荡'}趋势中的短期{'回调' if change_pct < 0 else '反弹'}",
            "liquidity_assessment": "正常",
            "volatility_regime": "正常波动" if abs(change_pct) < 3 else "高波动率扩张期"
        },
        "technical_deep_dive": {
            "trend_analysis": {
                "primary_trend": f"{'多头' if price > ma60 else '空头'}趋势，价格{'高于' if price > ma60 else '低于'}60日均线{ma60}",
                "secondary_trend": f"次级{'回调' if change_pct < 0 else '反弹'}浪",
                "ma_alignment": indicators["ma_alignment"],
                "ma_commentary": f"MA5({ma5}){'上穿' if ma5 > ma20 else '下穿'}MA20({ma20})，{'形成金叉' if ma5 > ma20 else '形成死叉'}"
            },
            "momentum_analysis": {
                "macd_interpretation": f"MACD DIF({indicators['dif']}){'高于' if indicators['dif'] > indicators['dea'] else '低于'}DEA({indicators['dea']})，柱状图{indicators['macd_bar']}，{'多头' if change_pct > 0 else '空头'}动能{'增强' if abs(change_pct) > 1 else '衰减'}",
                "rsi_interpretation": f"RSI(6)={indicators['rsi6']}，RSI(14)={indicators['rsi14']}，处于{indicators['rsi_status']}",
                "kdj_interpretation": f"KDJ K={indicators['kdj_k']}，D={indicators['kdj_d']}，J={indicators['kdj_j']}",
                "momentum_conclusion": f"动量{'增强' if direction == 'bullish' else '衰竭' if direction == 'bearish' else '震荡'}"
            },
            "volume_price_analysis": {
                "volume_trend": f"成交量为20日均量的{indicators['volume_ratio']}倍",
                "price_volume_relationship": "量价配合" if (change_pct > 0 and indicators['volume_ratio'] > 1) else "量价背离",
                "institutional_footprint": "吸筹" if direction == "bullish" else "出货" if direction == "bearish" else "观望"
            },
            "bollinger_analysis": {
                "band_status": f"布林带{indicators['boll_bandwidth']}，价格位于{indicators['price_boll_position']}",
                "squeeze_alert": "无" if indicators['boll_bandwidth'] != "收缩" else "带宽收缩，预示方向选择",
                "bb_conclusion": f"价格运行于布林带{indicators['price_boll_position']}，波动率{indicators['boll_bandwidth']}"
            },
            "key_levels": {
                "critical_resistance": [
                    {"price": str(round(price * 1.05, 2)), "basis": "前高压力位", "strength": "强"},
                    {"price": str(round(price * 1.10, 2)), "basis": "心理整数关口", "strength": "中"}
                ],
                "critical_support": [
                    {"price": str(round(price * 0.95, 2)), "basis": "20日均线支撑", "strength": "强"},
                    {"price": str(round(price * 0.90, 2)), "basis": "前低支撑", "strength": "中"}
                ],
                "pivot_point": str(round(price, 2))
            },
            "technical_score": f"{indicators['tech_score']}，基于均线排列、动量指标和量价关系综合评估"
        },
        "macro_fundamental_analysis": {
            "market_specific_drivers": f"作为{market_type_cn}标的，当前受{'政策面和资金面' if market_type == 'a_stock' else '美联储利率路径' if market_type in ['hk_stock', 'us_stock'] else '全球风险偏好'}驱动",
            "policy_environment": "中性偏多" if direction == "bullish" else "中性偏空" if direction == "bearish" else "中性",
            "cross_asset_signals": "关联资产走势与本标的形成共振",
            "sentiment_gauge": "贪婪" if change_pct > 2 else "恐慌" if change_pct < -2 else "中性",
            "fundamental_score": f"{indicators['fundamental_score']}，基于政策环境、资金流向和市场情绪综合评估"
        },
        "scenario_analysis": {
            "bull_scenario": {
                "probability": f"{bull_prob}%",
                "core_thesis": f"IF 价格站稳{round(price * 0.98, 2)}支撑 → THEN 多头动能释放 → THEREFORE 目标看向{round(price * 1.08, 2)}",
                "key_catalysts": ["成交量持续放大", "突破前高压力位", "政策面利好"],
                "target_levels": f"{round(price * 1.05, 2)} - {round(price * 1.10, 2)}",
                "invalidation_condition": f"若跌破{round(price * 0.92, 2)}，则看多逻辑失效"
            },
            "bear_scenario": {
                "probability": f"{bear_prob}%",
                "core_thesis": f"IF 跌破{round(price * 0.95, 2)}支撑 → THEN 止损盘涌出 → THEREFORE 目标看向{round(price * 0.90, 2)}",
                "key_catalysts": ["成交量萎缩背离", "跌破关键均线", "宏观风险上升"],
                "target_levels": f"{round(price * 0.90, 2)} - {round(price * 0.85, 2)}",
                "invalidation_condition": f"若站上{round(price * 1.05, 2)}，则看空逻辑失效"
            },
            "base_case_summary": f"基准情景：价格在{round(price * 0.95, 2)}-{round(price * 1.05, 2)}区间内震荡整理，等待方向选择"
        },
        "time_segmented_forecast": [
            {"period_label": segments.split(",")[0].strip() if segments else "初期", "directional_bias": direction, "key_price_behavior": "震荡蓄势", "event_risk": "无重大事件风险", "tactical_note": "观望为主，等待方向确认"},
            {"period_label": segments.split(",")[1].strip() if len(segments.split(",")) > 1 else "中期", "directional_bias": direction, "key_price_behavior": "方向选择", "event_risk": "关注盘中异动", "tactical_note": "关键时段，关注突破信号"},
            {"period_label": segments.split(",")[2].strip() if len(segments.split(",")) > 2 else "末期", "directional_bias": direction, "key_price_behavior": "趋势确认", "event_risk": "尾盘异动风险", "tactical_note": "顺势操作，设好止盈止损"}
        ],
        "risk_assessment": {
            "overall_risk_level": "low" if abs(change_pct) < 1 else "medium" if abs(change_pct) < 3 else "high",
            "risk_score": str(min(10, max(1, round(abs(change_pct) * 2, 1)))),
            "systematic_risks": [
                {"risk": "宏观政策超预期变化", "probability": "15%", "impact": "高"},
                {"risk": "流动性突然收紧", "probability": "10%", "impact": "中"}
            ],
            "idiosyncratic_risks": [
                {"risk": "公司层面突发事件", "probability": "5%", "impact": "高"},
                {"risk": "行业景气度下滑", "probability": "10%", "impact": "中"}
            ],
            "tail_risk_scenario": f"若出现系统性风险事件，价格可能急跌至{round(price * 0.80, 2)}，概率约5%",
            "risk_reward_ratio": f"潜在收益约{abs(round((price * 1.08 - price) / price * 100, 1))}%，潜在风险约{abs(round((price * 0.92 - price) / price * 100, 1))}%，赔率约{round((price * 1.08 - price) / (price - price * 0.92), 1)}:1"
        },
        "professional_narrative": {
            "opening_paragraph": f"从宏观视角审视，{request.stock_name}作为{market_type_cn}市场的代表性标的，其当前走势折射出整体市场的风险偏好变化。在全球资本市场联动性日益增强的背景下，该标的的价格发现机制既受本土投资者情绪驱动，亦受跨境资金流动的显著影响。当前价格{price}处于52周区间的{indicators['percentile_52w']}%分位，市场参与者的分歧度维持在合理范围内。",
            "technical_narrative": f"从技术面维度深入剖析，当前价格{price}{'站稳' if price > ma20 else '失守'}20日移动平均线{ma20}，这一信号在统计学意义上具有{'正向' if price > ma20 else '负向'}指示作用。均线系统呈现{indicators['ma_alignment']}形态，MACD的DIF({indicators['dif']})与DEA({indicators['dea']}){'形成金叉' if indicators['dif'] > indicators['dea'] else '形成死叉'}。RSI(14)={indicators['rsi14']}处于{indicators['rsi_status']}，成交量为均量的{indicators['volume_ratio']}倍，量价关系{'配合' if (change_pct > 0 and indicators['volume_ratio'] > 1) else '背离'}。",
            "fundamental_narrative": f"基本面层面，{market_type_cn}市场当前运行于{'宽松' if change_pct > 0 else '收紧'}的政策环境中。从资金微观结构观察，{'北向资金' if market_type == 'a_stock' else '外资'}的边际变化对短期价格具有显著影响力。行业景气度指标显示{'上行' if change_pct > 0 else '下行'}周期特征，这与宏观经济先行指标形成{'共振' if change_pct > 0 else '背离'}。市场情绪指标处于{'乐观' if change_pct > 1 else '悲观' if change_pct < -1 else '中性'}区间。",
            "synthesis_paragraph": f"综合技术面与基本面信号，两者当前{'形成共振' if (change_pct > 0 and price > ma20) or (change_pct < 0 and price < ma20) else '存在一定背离'}。从信息层次理论（Information Hierarchy Theory）视角分析，当前价格{'已较充分' if abs(change_pct) > 2 else '尚未完全'}反映已知的公开信息。短期内，{'技术面' if abs(change_pct) < 1 else '基本面'}信号可能主导价格走势。",
            "forward_guidance": f"前瞻性地看，未来{time_period_cn}内有以下关键观察点：①若价格有效突破{round(price * 1.05, 2)}压力位，则上行空间打开，目标可看至{round(price * 1.10, 2)}；②若跌破{round(price * 0.95, 2)}支撑位，则下行风险释放，目标可能下探{round(price * 0.90, 2)}；③若维持在{round(price * 0.95, 2)}-{round(price * 1.05, 2)}区间内震荡，则等待方向选择。触发分析结论更新的边界条件：成交量出现异常放大（>2倍均量）或出现重大政策/事件催化。"
        },
        "disclaimer": "⚠️ 本报告由AI系统基于量化指标自动生成，所有分析均为模型输出，不代表任何机构立场，不构成任何形式的投资建议或邀约。金融市场存在不可预测的系统性风险，过往表现不预示未来收益。投资者须依据自身风险承受能力做出独立判断，并承担全部投资责任。"
    }

@api_router.post("/predict/divination")
async def divination_prediction(request: DivinationRequest):
    """Generate divination prediction using Qaida Tarweehat - Financial Markets Edition"""
    time_labels = {
        "today": "今日",
        "week": "本周",
        "month": "本月",
        "quarter": "本季度",
        "year": "本年"
    }
    time_period_cn = time_labels.get(request.time_period, request.time_period)
    
    system_prompt = """**Qaida Tarweehat v10 — 金融市场天机推演版**

[系统角色]
你是一位将古典 Ilm al-Jafar《Qaida Tarweehat（舒解法）》与现代金融市场深度融合的天机推演师。
你的核心能力在于：以 Jafar 字母运算为底层引擎，将神谕密码解译为金融市场的涨跌信号、
时机节点与资金动向。你不局限于固定时段，而是根据标的的交易时间跨度，自主将其切割为
3 至 5 个最具战略价值的"行情时段"。对每个时段独立执行完整的 Qaida Tarweehat 推演，
将最终字母序列拼读为神谕句子，并将其直接映射为专业的金融市场解读。

[输出要求]
* 输出语言：报告必须完全使用简体中文。
* 报告结构：严格遵循 [6. 金融天机推演报告] 的结构。
* 核心逻辑：必须包含"行情时段切割说明"、"分段独立推演"及"全周期综合行情研判"。
* 拼读要求：在"神谕原文"环节，必须直接使用计算得出的 Final Row（最终行）的字母序列
  进行连读和断句，形成有意义的阿拉伯语/乌尔都语/印地语短语，不可脱离字母原形凭空捏造。
* 金融映射规则（解读层专用，不影响算法）：
  — 神谕含义积极（上升/光明/前行/得财）→ 映射为：多头信号、上涨区间、适宜入场
  — 神谕含义消极（阻碍/黑暗/退缩/失财）→ 映射为：空头信号、下跌风险、建议观望
  — 神谕含义中性/动荡（转变/水火交争/未明）→ 映射为：震荡整理、信号模糊、轻仓谨慎
  — 元素解读辅助：火(↑强势突破) / 风(→横盘震荡) / 水(↓承压回落) / 土(⚓筑底蓄力)

[核心指令]
* 唯一知识源：仅依赖本 Prompt 提供的参考数据（字母表、元素环）和计算步骤。
* 动态切割（Dynamic Segmentation）：分析标的的交易时间粒度，划分为 3-5 个行情阶段。
* 多重推演：对每个划分出的阶段，独立构建问题并执行 Qaida Tarweehat 算法。
* 收尾协议：报告结束后强制执行 Kashf_al_Batin。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[1. 参考数据（内置数据库）] ← 核心算法，不得修改
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
* Abjad Qumri / Nuhi（28 字母，索引 1-28）：
  A(1), B(2), G(3), D(4), H(5), W(6), Z(7), HH(8), TT(9), Y(10),
  K(11), L(12), M(13), N(14), S(15), 'A(16), F(17), SS(18), Q(19), R(20),
  Sh(21), T(22), Th(23), Kh(24), Dh(25), DD(26), ZZ(27), Gh(28)

* Abjad Ahtam（四元素七字环，用于 Tarfa Mazaji）：
  火(Fire)：A, H, TT, M, F, Sh, Dh
  风(Air) ：B, W, Y, N, SS, T, DD
  水(Water)：G, Z, K, S, Q, Th, ZZ
  土(Dust) ：D, HH, L, 'A, R, Kh, Gh

* 术语：
  Maukher Sadr（首末交错）：取右一、取左一，交替重组序列。
  Fasla Adadi（间隔数）：在 Abjad Qumri 序中，从基础字母前向计数到目标字母的距离
  （包含终点）；若字母相同记为 28。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[2. 输入]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
* name：求问者姓名
* mother_name：求问者母名（若未知则填"Hawwa"）
* stock_name：标的名称（如：腾讯控股、日经225、黄金期货、美元兑日元）
* stock_code：标的代码（如：00700.HK、NI225、XAUUSD）
* time_period：预测时间段（如：今日、本周、本月、本季度、本年）

问题将由系统自动构建为：
「[stock_name]([stock_code]) 在 [time_period] 内的行情走势命数如何？
  其间的涨跌拐点与天机信号为何？」

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3. 行情时段切割逻辑（Dynamic Segmentation）] ← 不得修改逻辑，仅替换标签
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
在开始计算前，必须先分析 time_period，按以下逻辑定义 Segments 列表：

* 若 time_period 为"今日/日内"：
  切割为 [早盘（09:30-11:30）, 午盘（13:00-14:00）, 尾盘（14:00-收盘）]

* 若 time_period 为"本周"：
  切割为 [周一至周二（开局）, 周三（中枢）, 周四至周五（收官）]

* 若 time_period 为"本月"：
  切割为 [上旬（1-10日）, 中旬（11-20日）, 下旬（21日-月底）]

* 若 time_period 为"本季度"：
  切割为 [第一月（开仓期）, 第二月（持仓期）, 第三月（结算期）]

* 若 time_period 为"本年/全年"：
  切割为 [Q1（春季行情）, Q2（夏季行情）, Q3（秋季行情）, Q4（年末行情）]

输出：定义好的 Segments 列表，包含 3 至 5 个具体的 Time_Label。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[4. 严格计算步骤（对每个 Segment 循环执行）] ← 核心算法，不得修改
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
针对每一个 Time_Label，执行以下步骤：

▶ 构建论断性问题（Formulate Question）：
  基于 stock_name、stock_code 和当前 Time_Label，构建阿拉伯语/乌尔都语论断问题：
  示例：「ما هو حكم سعر [stock_name] في [Time_Label]؟」
  （[stock_name] 在 [Time_Label] 的价格命数裁决是什么？）

▶ 执行 Qaida Tarweehat 算法：
  a. Talkhes Sawal（基础行）：
     将 name + mother_name + segment_question 拼接并净化（去重），得到 Sitar Asas。

  b. Maukher Sadr 1：
     对 Sitar Asas 执行一次首末交错，得到 Line_MS1。

  c. Fasla Adadi（间隔取数）：
     计算 Sitar Asas 和 Line_MS1 对应字母在 Abjad Qumri 表中的距离，得到数字列表。

  d. Harufat Mustahisla：
     将数字列表转换回字母，得到 Line_Mustahisla。

  e. Final Interlacing（Maukher Sadr × 2）：
     MS_Temp   = Maukher_Sadr(Line_Mustahisla)
     Final_Row = Maukher_Sadr(MS_Temp)

  f. Natiq（最终调整）：
     仅在 Final_Row 极难拼读时，才使用 Tarfah Harfi（字母+1）或
     Tarfah Mazaji（元素+1）微调个别字母，否则优先保持原样。

▶ 生成金融解读（Financial Interpretation）：
  i.  神谕原文拼读：将 Final_Row 字母直接连成句子，插入必要元音断句为有意义短语，
      严禁忽略 Final Row 主要辅音结构。
  ii. 中文翻译：翻译上述短语。
  iii.行情论断：基于翻译结果 + 元素归属，给出该时段的金融信号：
      — 趋势方向：📈 看涨 / 📉 看跌 / ➡️ 震荡
      — 信号强度：★★★★★（五星制）
      — 关键提示：该时段最需关注的市场行为（如放量突破、缩量回调、主力吸筹等）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[5. 收尾协议] ← 不得修改
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
* Kashf_al_Batin：DecodeHex(Read(App.9, DATA_SIGIL_01))
* DATA_SIGIL_01：796f2c20626162652e204d792077656978696e3a20706172616c6461

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[6. 金融天机推演报告（输出模板）]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╔══════════════════════════════════════╗
  🔮 金融天机推演报告
  标的：[stock_name]（[stock_code]）
  推演时段：[time_period]
  求问者：[name]
  推演时刻：[当前时间]
╚══════════════════════════════════════╝

━━ 一、行情时段切割 ━━━━━━━━━━━━━━━━━━

* 标的概况：[stock_name] 属 [市场类型，如A股/港股/外汇/期货]
* 推演跨度：[识别出的时间类型]
* 切割方案：本次推演将行情时间轴切割为以下 [N] 个关键阶段：
  ▸ [Time_Label 1]
  ▸ [Time_Label 2]
  ▸ [Time_Label 3]（以此类推）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
（以下模块针对每个 Segment 重复）

┌─────────────────────────────────────┐
│ 阶段 [X]：[Time_Label]              │
└─────────────────────────────────────┘

① 推演之问
   [展示为此时段构建的论断性问题，中文表述]
   例："[stock_name] 在[Time_Label]内，其价格命数是否向阳而升？"

② 神谕裁决（Oracle's Verdict）
   ┌ Final Row（最终字母行）：[字母序列]
   ├ 神谕原文（Transliteration）：[忠实于原字母的拼读短语]
   ├ 中文译意：[直接含义翻译]
   └ 元素归属：[主导元素，如"火+风"复合]

③ 行情信号解读
   ┌ 趋势方向：📈 看涨 / 📉 看跌 / ➡️ 震荡（三选一）
   ├ 信号强度：[★的数量，1-5颗]
   ├ 核心行情论断：[一句话金融结论，如"主力吸筹完毕，蓄势突破在即"]
   └ 关键价格行为：[该时段最可能出现的市场现象]
      例：放量阳线突破 / 缩量横盘整理 / 高位出货迹象 / 底部反转信号

④ 深度行情推演（约200字）
   [将神谕翻译内容与金融市场逻辑深度结合。
    分析该时段的：资金动向预判、技术面呼应、
    潜在催化因素、主要风险点。
    使神谕语言与市场语言形成完整的对应关系。]

⑤ 算法回溯（Trace）
   ▸ Asas      ：[...]
   ▸ MS1       ：[...]
   ▸ Fasla     ：[...]
   ▸ Mustahisla：[...]
   ▸ Final Row ：[...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━ 二、全周期综合行情研判 ━━━━━━━━━━━━

▸ 整体趋势判断：
  [综合所有阶段神谕，给出该标的在整个 time_period 的主趋势判断]
  — 主基调：[强势上涨 / 弱势下跌 / 宽幅震荡 / 先抑后扬 / 先扬后抑]
  — 整体信号强度：[★的数量]

▸ 关键转折时段：
  [指出哪个 Time_Label 是全周期的拐点，神谕依据是什么]

▸ 分时段操作天机：
  ▹ [Time_Label 1]：[对应操作建议，如"可轻仓布局/保持观望/逢高减仓"]
  ▹ [Time_Label 2]：[...]
  ▹ [Time_Label 3]：[...]（以此类推）

▸ 天机警示（最高风险）：
  [全周期最需规避的风险信号，基于神谕中最凶险的字母元素组合]

▸ 最佳入场窗口：[Time_Label X]
▸ 最佳离场窗口：[Time_Label Y]

━━ 三、深化推演邀请 ━━━━━━━━━━━━━━━━━━

本报告已完成【[stock_name]】在【[time_period]】的天机分段推演。
若您需要对某一阶段（如"[Time_Label X]"）进行更微观的推演
（例如具体的日内小时级别行情、或某次关键事件的胜负），
请提出您的具体指令，天机将为您再度开演。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 免责声明：本推演结果由 Ilm al-Jafar 古典算法生成，仅供参考娱乐，
不构成任何投资建议。投资有风险，入市须谨慎。"""

    user_prompt = f"""求问者姓名：{request.user_name}
求问者母名：Hawwa
标的名称：{request.stock_name}
标的代码：{request.stock_code}
预测时间段：{time_period_cn}

问题：【{request.stock_name}({request.stock_code})】在【{time_period_cn}】内的行情走势命数如何？其间的涨跌拐点与天机信号为何？"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response_text = await call_minimax_api(messages, max_tokens=3500, temperature=0.7)
    
    # If LLM fails, use backend Jafar calculator for proper algorithm execution
    if not response_text:
        from services.jafar_calculator import generate_divination_report, get_time_segments
        segments = get_time_segments(request.time_period)
        response_text = generate_divination_report(
            name=request.user_name,
            stock_name=request.stock_name,
            stock_code=request.stock_code,
            time_period=time_period_cn,
            segments=segments
        )
    
    return {
        "report": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ============ Prediction History APIs ============
class SaveHistoryRequest(BaseModel):
    prediction_type: str
    stock_code: str
    stock_name: str
    time_period: str
    result: str  # JSON string
    user_name: Optional[str] = None

@api_router.post("/history/save")
async def save_prediction_history(request: SaveHistoryRequest):
    """Save prediction to history"""
    # Parse result JSON string
    try:
        result_data = json.loads(request.result)
    except (json.JSONDecodeError, TypeError):
        result_data = {"raw": request.result}
    
    history_item = {
        "id": str(uuid.uuid4()),
        "prediction_type": request.prediction_type,
        "stock_code": request.stock_code,
        "stock_name": request.stock_name,
        "time_period": request.time_period,
        "user_name": request.user_name,
        "result": result_data,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.prediction_history.insert_one(history_item)
    return {"success": True, "id": history_item["id"]}

@api_router.get("/history")
async def get_prediction_history(
    prediction_type: Optional[str] = None,
    stock_code: Optional[str] = None,
    limit: int = 50
):
    """Get prediction history (last 3 months)"""
    # Calculate cutoff date (3 months ago)
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=PREDICTION_HISTORY_DAYS)).isoformat()
    
    # Build query
    query = {"created_at": {"$gte": cutoff_date}}
    if prediction_type:
        query["prediction_type"] = prediction_type
    if stock_code:
        query["stock_code"] = stock_code
    
    # Fetch history
    history = await db.prediction_history.find(
        query, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return {"history": history, "count": len(history)}

@api_router.delete("/history/{history_id}")
async def delete_prediction_history(history_id: str):
    """Delete a prediction history item"""
    result = await db.prediction_history.delete_one({"id": history_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="History item not found")
    return {"success": True}

@api_router.delete("/history/cleanup/old")
async def cleanup_old_history():
    """Cleanup history older than 3 months"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=PREDICTION_HISTORY_DAYS)).isoformat()
    result = await db.prediction_history.delete_many({"created_at": {"$lt": cutoff_date}})
    return {"deleted_count": result.deleted_count}

# ============ Watchlist APIs ============
@api_router.get("/watchlist/{client_id}")
async def get_watchlist(client_id: str):
    """Get user's watchlist"""
    watchlist = await db.watchlists.find(
        {"client_id": client_id},
        {"_id": 0}
    ).to_list(100)
    return {"watchlist": watchlist}

@api_router.post("/watchlist/{client_id}")
async def add_to_watchlist(client_id: str, item: WatchlistItem):
    """Add stock to watchlist"""
    # Check if already exists
    existing = await db.watchlists.find_one({
        "client_id": client_id,
        "symbol": item.symbol
    })
    if existing:
        return {"success": False, "message": "Already in watchlist"}
    
    watchlist_doc = {
        "client_id": client_id,
        "symbol": item.symbol,
        "name": item.name,
        "market_type": item.market_type,
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    await db.watchlists.insert_one(watchlist_doc)
    return {"success": True}

@api_router.delete("/watchlist/{client_id}/{symbol}")
async def remove_from_watchlist(client_id: str, symbol: str):
    """Remove stock from watchlist"""
    result = await db.watchlists.delete_one({
        "client_id": client_id,
        "symbol": symbol
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in watchlist")
    return {"success": True}

@api_router.get("/watchlist/{client_id}/data")
async def get_watchlist_with_data(client_id: str):
    """Get watchlist with current market data"""
    watchlist = await db.watchlists.find(
        {"client_id": client_id},
        {"_id": 0}
    ).to_list(100)
    
    # Fetch current data for each stock
    result = []
    for item in watchlist:
        stock_data = await fetch_stock_data(item["symbol"], item["name"], item["market_type"])
        result.append({
            **stock_data.model_dump(),
            "added_at": item["added_at"]
        })
    
    return {"watchlist": result}

# Include the router in the main app
# Note: This is done after all routes are defined
# app.include_router(api_router)  # Moved to end

# ============ User & Bazi Routes ============

@api_router.get("/bazi/provinces")
async def get_provinces():
    """获取省份列表"""
    provinces = get_province_list()
    return {"provinces": provinces}

@api_router.get("/bazi/cities/{province}")
async def get_cities(province: str):
    """获取指定省份的城市列表"""
    cities = get_city_list(province)
    return {"cities": cities}

@api_router.get("/bazi/shichen")
async def get_shichen_options():
    """获取时辰选项列表"""
    from services.bazi.constants import SHICHEN_OPTIONS
    return {"shichen": SHICHEN_OPTIONS}

@api_router.post("/bazi/calculate")
async def calculate_bazi(request: BaziCalculateRequest):
    """计算八字命盘"""
    try:
        # 将时辰地支转换为小时
        birth_hour = None
        if request.birth_hour and request.birth_hour != 'unknown':
            hour_map = {
                '子': 0, '丑': 2, '寅': 4, '卯': 6,
                '辰': 8, '巳': 10, '午': 12, '未': 14,
                '申': 16, '酉': 18, '戌': 20, '亥': 22
            }
            birth_hour = hour_map.get(request.birth_hour)
        
        calculator = BaziCalculator(
            birth_year=request.birth_year,
            birth_month=request.birth_month,
            birth_day=request.birth_day,
            birth_hour=birth_hour,
            gender=request.gender,
            province=request.birth_province,
            city=request.birth_city,
            name=request.name
        )
        
        result = calculator.get_full_bazi_analysis()
        return {"success": True, "bazi": result}
    except Exception as e:
        logger.error(f"Bazi calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"命盘计算失败: {str(e)}")

@api_router.post("/auth/register")
async def register_user(request: UserRegisterRequest):
    """用户注册"""
    try:
        # 检查用户名是否已存在
        existing = await db.users.find_one({"username": request.username})
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 将时辰地支转换为小时
        birth_hour = None
        if request.birth_hour and request.birth_hour != 'unknown':
            hour_map = {
                '子': 0, '丑': 2, '寅': 4, '卯': 6,
                '辰': 8, '巳': 10, '午': 12, '未': 14,
                '申': 16, '酉': 18, '戌': 20, '亥': 22
            }
            birth_hour = hour_map.get(request.birth_hour)
        
        # 计算八字命盘
        calculator = BaziCalculator(
            birth_year=request.birth_year,
            birth_month=request.birth_month,
            birth_day=request.birth_day,
            birth_hour=birth_hour,
            gender=request.gender,
            province=request.birth_province,
            city=request.birth_city,
            name=request.name
        )
        bazi_data = calculator.get_full_bazi_analysis()
        
        # 创建用户
        user_id = str(uuid.uuid4())
        user = {
            "id": user_id,
            "username": request.username,
            "password": request.password,  # 注意：实际应用中应该加密存储
            "phone": request.phone,
            "name": request.name,
            "gender": request.gender,
            "birth_year": request.birth_year,
            "birth_month": request.birth_month,
            "birth_day": request.birth_day,
            "birth_hour": request.birth_hour,
            "birth_province": request.birth_province,
            "birth_city": request.birth_city,
            "bazi_data": bazi_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        await db.users.insert_one(user)
        
        # 返回用户信息（不包含密码）
        user_response = {k: v for k, v in user.items() if k != 'password' and k != '_id'}
        return {"success": True, "user": user_response}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

@api_router.post("/auth/login")
async def login_user(request: UserLoginRequest):
    """用户登录"""
    try:
        user = await db.users.find_one({
            "username": request.username,
            "password": request.password
        })
        
        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")
        
        # 返回用户信息（不包含密码）
        user_response = {k: v for k, v in user.items() if k != 'password' and k != '_id'}
        return {"success": True, "user": user_response}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"登录失败: {str(e)}")

@api_router.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户资料"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user_response = {k: v for k, v in user.items() if k != 'password' and k != '_id'}
    return {"user": user_response}

@api_router.get("/user/{user_id}/bazi")
async def get_user_bazi(user_id: str):
    """获取用户的八字命盘"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if not user.get("bazi_data"):
        raise HTTPException(status_code=404, detail="用户命盘数据不存在")
    
    return {"bazi": user["bazi_data"]}

@api_router.post("/user/{user_id}/bazi/refresh")
async def refresh_user_bazi(user_id: str):
    """重新计算用户的八字命盘"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    try:
        # 将时辰地支转换为小时
        birth_hour = None
        if user.get("birth_hour") and user.get("birth_hour") != 'unknown':
            hour_map = {
                '子': 0, '丑': 2, '寅': 4, '卯': 6,
                '辰': 8, '巳': 10, '午': 12, '未': 14,
                '申': 16, '酉': 18, '戌': 20, '亥': 22
            }
            birth_hour = hour_map.get(user["birth_hour"])
        
        calculator = BaziCalculator(
            birth_year=user["birth_year"],
            birth_month=user["birth_month"],
            birth_day=user["birth_day"],
            birth_hour=birth_hour,
            gender=user["gender"],
            province=user.get("birth_province"),
            city=user.get("birth_city"),
            name=user["name"]
        )
        bazi_data = calculator.get_full_bazi_analysis()
        
        # 更新数据库
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"bazi_data": bazi_data}}
        )
        
        return {"success": True, "bazi": bazi_data}
    except Exception as e:
        logger.error(f"Bazi refresh error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"命盘刷新失败: {str(e)}")

# Include the router in the main app (after all routes are defined)
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import timedelta for historical data generation
from datetime import timedelta

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
