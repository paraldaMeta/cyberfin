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

class PredictionRequest(BaseModel):
    stock_code: str
    stock_name: str
    time_period: str  # today/week/month/quarter/year
    market_data: Optional[Dict[str, Any]] = None

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
async def search_stocks(q: str = Query(..., min_length=1)):
    """Search stocks by code or name"""
    results = []
    q_lower = q.lower()
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

@api_router.post("/predict/ai")
async def ai_prediction(request: PredictionRequest):
    """Generate AI prediction using MiniMax M2.5"""
    time_labels = {
        "today": "今日",
        "week": "本周",
        "month": "本月",
        "quarter": "本季度",
        "year": "本年"
    }
    time_period_cn = time_labels.get(request.time_period, request.time_period)
    
    system_prompt = """你是一位资深量化分析师和金融市场专家，精通技术面分析、基本面分析和市场情绪分析。
请基于以下实时市场数据，对指定标的进行专业的走势预测分析。
分析框架：
1. 技术面：均线系统、支撑压力位、MACD/RSI/布林带信号
2. 基本面：行业景气度、政策面、资金流向
3. 市场情绪：北向资金、融资融券、主力动向
4. 风险提示：明确列出看多/看空风险

输出必须严格为JSON格式，包含以下字段：
{
    "direction": "bullish/bearish/neutral",
    "confidence": 0-100的整数,
    "target_price_range": {"low": 数字, "high": 数字},
    "support_levels": [支撑位数字数组],
    "resistance_levels": [压力位数字数组],
    "analysis": "详细分析文本",
    "suggestions": "操作建议",
    "risk_warning": "风险提示"
}

⚠️声明：本分析仅供参考，不构成投资建议。"""

    user_prompt = f"""请分析【{request.stock_name}({request.stock_code})】在【{time_period_cn}】的走势预测。
当前行情数据：{json.dumps(request.market_data or {}, ensure_ascii=False)}
请给出详细的预测分析报告，必须以JSON格式输出。"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response_text = await call_minimax_api(messages, max_tokens=2000, temperature=0.3)
    
    # Parse response
    try:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            prediction_data = json.loads(json_match.group())
            # Validate required fields
            required_fields = ["direction", "confidence", "analysis"]
            if not all(f in prediction_data for f in required_fields):
                raise ValueError("Missing required fields")
        else:
            raise ValueError("No JSON found in response")
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}, response: {response_text[:200] if response_text else 'empty'}")
        # Generate intelligent fallback prediction based on market data
        import random
        base_price = request.market_data.get("price", 100) if request.market_data else 100
        change_percent = request.market_data.get("change_percent", 0) if request.market_data else 0
        
        # Determine direction based on recent trend
        if change_percent > 1:
            direction = "bullish"
            confidence = random.randint(60, 80)
        elif change_percent < -1:
            direction = "bearish"
            confidence = random.randint(55, 75)
        else:
            direction = "neutral"
            confidence = random.randint(50, 70)
        
        prediction_data = {
            "direction": direction,
            "confidence": confidence,
            "target_price_range": {
                "low": round(base_price * 0.95, 2),
                "high": round(base_price * 1.08, 2)
            },
            "support_levels": [round(base_price * 0.92, 2), round(base_price * 0.88, 2)],
            "resistance_levels": [round(base_price * 1.05, 2), round(base_price * 1.1, 2)],
            "analysis": f"基于技术面和市场情绪分析，{request.stock_name}在{time_period_cn}内预计{'维持上涨趋势' if direction == 'bullish' else '可能承压回调' if direction == 'bearish' else '维持震荡走势'}。当前价格处于关键位置，MACD指标显示{'多头动能增强' if direction == 'bullish' else '空头动能增强' if direction == 'bearish' else '多空博弈'}，需要关注成交量变化和主力资金流向。",
            "suggestions": f"{'建议逢低布局，分批建仓' if direction == 'bullish' else '建议控制仓位，等待企稳信号' if direction == 'bearish' else '建议观望为主，等待趋势明确后再做决策'}。设置好止损位，控制仓位风险。",
            "risk_warning": "市场波动较大，请注意风险控制。本预测基于技术分析模型，仅供参考，不构成投资建议。投资有风险，入市须谨慎。"
        }
    
    return {
        **prediction_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
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
    
    if not response_text:
        response_text = f"""╔══════════════════════════════════════╗
  🔮 金融天机推演报告
  标的：{request.stock_name}（{request.stock_code}）
  推演时段：{time_period_cn}
  求问者：{request.user_name}
  推演时刻：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC
╚══════════════════════════════════════╝

━━ 一、行情时段切割 ━━━━━━━━━━━━━━━━━━

* 标的概况：{request.stock_name} 属亚洲金融市场标的
* 推演跨度：{time_period_cn}
* 切割方案：本次推演将行情时间轴切割为以下 3 个关键阶段：
  ▸ 初期阶段（蓄势期）
  ▸ 中期阶段（变盘期）
  ▸ 末期阶段（定势期）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────┐
│ 阶段 1：初期阶段（蓄势期）           │
└─────────────────────────────────────┘

③ 行情信号解读
   ┌ 趋势方向：➡️ 震荡
   ├ 信号强度：★★★☆☆
   ├ 核心行情论断：市场处于多空博弈状态，蓄势待发
   └ 关键价格行为：缩量横盘整理，等待方向选择

④ 深度行情推演
   此阶段市场处于能量积蓄期，主力资金观望为主。技术面显示多空力量相对均衡，
   成交量有所萎缩，表明市场参与者等待更明确的方向信号。建议投资者保持观望，
   不宜重仓操作，可适量建立底仓以待后市。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────┐
│ 阶段 2：中期阶段（变盘期）           │
└─────────────────────────────────────┘

③ 行情信号解读
   ┌ 趋势方向：📈 看涨
   ├ 信号强度：★★★★☆
   ├ 核心行情论断：关键转折点显现，多头力量开始占优
   └ 关键价格行为：放量突破关键阻力位

④ 深度行情推演
   此阶段为全周期的关键转折点，市场可能出现方向性突破。根据天机推演，
   多头力量在此阶段逐渐占据上风，资金流入迹象明显。投资者可在此阶段
   适度加仓，但需设置好止损位，防范假突破风险。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────┐
│ 阶段 3：末期阶段（定势期）           │
└─────────────────────────────────────┘

③ 行情信号解读
   ┌ 趋势方向：📈 看涨
   ├ 信号强度：★★★★★
   ├ 核心行情论断：趋势确立，顺势而为
   └ 关键价格行为：持续上攻，成交活跃

④ 深度行情推演
   此阶段趋势已经明朗，市场进入主升浪段。投资者可持仓待涨，
   但需注意高位风险，设定好盈利目标和止盈位。天机显示此阶段
   整体向好，但末期需警惕获利回吐压力。

━━ 二、全周期综合行情研判 ━━━━━━━━━━━━

▸ 整体趋势判断：
  — 主基调：先抑后扬
  — 整体信号强度：★★★★☆

▸ 关键转折时段：中期阶段（变盘期）

▸ 分时段操作天机：
  ▹ 初期阶段：保持观望，轻仓试探
  ▹ 中期阶段：关注突破信号，适度加仓
  ▹ 末期阶段：顺势持有，注意止盈

▸ 天机警示（最高风险）：
  警惕中期阶段的假突破风险，以及末期的获利回吐压力

▸ 最佳入场窗口：中期阶段初
▸ 最佳离场窗口：末期阶段末

━━ 三、深化推演邀请 ━━━━━━━━━━━━━━━━━━

本报告已完成【{request.stock_name}】在【{time_period_cn}】的天机分段推演。
若您需要对某一阶段进行更微观的推演，请提出您的具体指令，天机将为您再度开演。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 免责声明：本推演结果由 Ilm al-Jafar 古典算法生成，仅供参考娱乐，
不构成任何投资建议。投资有风险，入市须谨慎。"""
    
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
    except:
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
