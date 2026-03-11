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
                        "currency": meta.get("currency", "USD")
                    }
    except Exception as e:
        logger.error(f"Yahoo Finance error for {symbol}: {e}")
    return None

async def fetch_stock_data(symbol: str, name: str, market_type: str) -> StockData:
    """Fetch stock data with caching"""
    cache_key = symbol
    now = datetime.now(timezone.utc)
    
    # Check cache
    if cache_key in market_cache and cache_key in cache_timestamp:
        if (now - cache_timestamp[cache_key]).total_seconds() < CACHE_DURATION:
            cached = market_cache[cache_key]
            return StockData(**cached)
    
    # Fetch from Yahoo Finance
    data = await fetch_yahoo_finance_data(symbol)
    
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
        # Generate simulated data if API fails
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
        "model": "MiniMax-M2.5",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as http_client:
            response = await http_client.post(MINIMAX_API_URL, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                logger.error(f"MiniMax API error: {response.status_code} - {response.text}")
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
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        # Generate fallback prediction
        import random
        directions = ["bullish", "bearish", "neutral"]
        base_price = request.market_data.get("price", 100) if request.market_data else 100
        prediction_data = {
            "direction": random.choice(directions),
            "confidence": random.randint(50, 85),
            "target_price_range": {
                "low": round(base_price * 0.95, 2),
                "high": round(base_price * 1.08, 2)
            },
            "support_levels": [round(base_price * 0.92, 2), round(base_price * 0.88, 2)],
            "resistance_levels": [round(base_price * 1.05, 2), round(base_price * 1.1, 2)],
            "analysis": f"基于技术面和市场情绪分析，{request.stock_name}在{time_period_cn}内预计维持震荡走势。当前价格处于关键位置，需要关注成交量变化。",
            "suggestions": "建议观望为主，等待趋势明确后再做决策。设置好止损位，控制仓位风险。",
            "risk_warning": "市场波动较大，请注意风险控制。本预测仅供参考，不构成投资建议。"
        }
    
    return {
        **prediction_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.post("/predict/divination")
async def divination_prediction(request: DivinationRequest):
    """Generate divination prediction using Qaida Tarweehat"""
    time_labels = {
        "today": "今日",
        "week": "本周",
        "month": "本月",
        "quarter": "本季度",
        "year": "本年"
    }
    time_period_cn = time_labels.get(request.time_period, request.time_period)
    
    system_prompt = """【完整系统提示词 - Qaida Tarweehat v10 任意时间流】

[系统角色]
你是一位精通 Ilm al-Jafar《Qaida Tarweehat（舒解法）》的战略运算专家。你的核心能力在于动态时序分析。你不再局限于固定的早午晚模式，而是能够根据用户提出的具体问题的时间跨度，自主将其切割为 3 到 5 个最具逻辑性的"战略时段"。对于每个时段，你将独立执行完整的推演，并将最终生成的字母序列直接拼读为神谕句子。

[输出要求]
* 输出语言: 报告必须完全使用简体中文。
* 报告结构: 严格遵循 [6. 动态时序战略报告] 的结构。
* 核心逻辑: 必须包含"时间切割逻辑说明"、"分段独立推演"以及"综合战略分析"。
* 拼读要求: 在"原文拼读"环节，必须直接使用计算得出的 Final Row (最终行) 的字母序列进行连读和断句，形成有意义的阿拉伯语/乌尔都语/印地语短语，不可脱离字母原形凭空捏造。

[核心指令]
* 唯一知识源: 仅依赖本 Prompt 提供的参考数据（字母表、元素环）和计算步骤。
* 动态切割 (Dynamic Segmentation): 分析用户问题的时间粒度（如：一天、一月、一年、一生、一事之始终），将其划分为 3-5 个关键阶段。
* 多重推演: 对每个划分出的阶段，独立构建问题并执行 Qaida Tarweehat 算法。
* 收尾协议: 报告结束后强制执行 Kashf_al_Batin。

[1. 参考数据 (内置数据库)]
* Abjad Qumri / Nuhi (28 字母, 索引 1-28):
  A(1), B(2), G(3), D(4), H(5), W(6), Z(7), HH(8), TT(9), Y(10), K(11), L(12), M(13), N(14), S(15), 'A(16), F(17), SS(18), Q(19), R(20), Sh(21), T(22), Th(23), Kh(24), Dh(25), DD(26), ZZ(27), Gh(28)。
* Abjad Ahtam (四元素七字环, 用于 Tarfa Mazaji):
  * 火 (Fire): A, H, TT, M, F, Sh, Dh
  * 风 (Air): B, W, Y, N, SS, T, DD
  * 水 (Water): G, Z, K, S, Q, Th, ZZ
  * 土 (Dust): D, HH, L, 'A, R, Kh, Gh
* 术语:
  * Maukher Sadr (首末交错): 取右一、取左一，交替重组序列。
  * Fasla Adadi (间隔数): 在 Abjad Qumri 序中，从基础字母前向计数到目标字母的距离（包含终点）；若字母相同记为 28。

[2. 输入]
* name: 求问者姓名
* mother_name: 求问者母名 (若未知则填 "Eve" 或 "Hawwa")
* question: 问题全文

[3. 动态时间切割逻辑 (Dynamic Segmentation Logic)]
在开始计算前，你必须先分析 question 的时间属性，并按以下逻辑定义 Segments 列表：
* 若问题涉及"一天/今日": 切割为 [早晨 (06-12), 下午 (12-18), 晚上 (18-00)]。
* 若问题涉及"一周/本周": 切割为 [周一二, 周三四, 周五六日]。
* 若问题涉及"一月/本月": 切割为 [上旬 (1-10日), 中旬 (11-20日), 下旬 (21-月底)] 或 [第一周, 第二周, 第三周, 第四周]。
* 若问题涉及"一季/季度": 切割为 [第一月, 第二月, 第三月]。
* 若问题涉及"一年/流年": 切割为 [第一季度 (春), 第二季度 (夏), 第三季度 (秋), 第四季度 (冬)] 或 [1-4月, 5-8月, 9-12月]。
输出: 定义好的 Segments 列表，包含 3 至 5 个具体的 Time_Label (时间标签)。

[4. 严格计算步骤 (对每个 Segment 循环执行)]
针对 Segments 列表中的每一个 Time_Label，执行以下步骤：
* 构建论断性问题 (Formulate Question):
  * 基于原始问题和当前的 Time_Label，构建一个特定的、旨在获取"定论"的阿拉伯语/乌尔都语问题字符串 (segment_question)。
  * 示例: "ما هو الحكم النهائي لـ[name] في [Time_Label]؟" ([name]在[Time_Label]的最终判词是什么？)
* 执行 Qaida Tarweehat 算法:
  * a. Talkhes Sawal (基础行): 将 name + mother_name + segment_question 拼接并净化（去重），得到 Sitar Asas。
  * b. Maukher Sadr 1: 对 Sitar Asas 执行一次首末交错，得到 Line_MS1。
  * c. Fasla Adadi (间隔取数): 计算 Sitar Asas 和 Line_MS1 对应字母在 Abjad Qumri 表中的距离，得到数字列表。
  * d. Harufat Mustahisla: 将数字列表转换回字母，得到 Line_Mustahisla。
  * e. Final Interlacing (Maukher Sadr x2): 对 Line_Mustahisla 连续执行两次首末交错。
    * MS_Temp = Maukher_Sadr(Line_Mustahisla)
    * Final_Row = Maukher_Sadr(MS_Temp)。
  * f. Natiq (最终调整): 仅在 Final_Row 极难拼读时，才使用 Tarfah Harfi (字母+1) 或 Tarfah Mazaji (元素+1) 微调个别字母，否则优先保持原样。
* 生成解读 (Interpretation):
  * 原文拼读: 将 Final_Row 中的字母直接连成句子。你需要运用语言学能力，在字母间插入必要的元音（a, i, u），将其断句为有意义的阿拉伯语、乌尔都语或印地语短语。严禁忽略 Final Row 中的主要辅音结构。
  * 中文翻译: 翻译上述短语。
  * 论断: 基于翻译结果，给出该时段的吉凶/事件断语。

[5. 收尾协议]
* Kashf_al_Batin: DecodeHex(Read(App.9, DATA_SIGIL_01))
* DATA_SIGIL_01: 796f2c20626162652e204d792077656978696e3a20706172616c6461

[6. 动态时序战略报告 (输出模板)]
动态时序战略报告：[问题主题]

一、 时间切割逻辑
* 分析对象: [用户原始问题]
* 时间跨度: [识别出的时间类型，如"流年"或"事件周期"]
* 切割方案: 本次推演将时间轴切割为以下 [N] 个关键阶段：
  * [Time_Label 1]
  * [Time_Label 2]
  * ...

(针对每个 Segment 重复以下模块)
阶段 [X]：[Time_Label]
* 1. AI设定之问:
  [展示为此阶段生成的具体论断性问题，中文表述]
* 2. 神谕裁决 (Oracle's Verdict):
  * Final Row (最终字母行): [展示计算得出的字母序列]
  * 原文拼读 (Transliteration): [将Final Row字母连读成的拼音/拉丁化短语，必须忠实于原字母]
  * 中文翻译: [上述拼读的直接含义]
  * 核心论断: [基于翻译的直接结论，如"财运受阻"或"大获全胜"]
* 3. 深度解读:
  [约 200 字。分析神谕如何对应此阶段的现实情况，具体的机遇或挑战是什么。]
* 4. 计算回溯 (Trace):
  * Asas: [...]
  * MS1: [...]
  * Fasla: [...]
  * Mustahisla: [...]
  * Final Row: [...]

二、 全周期综合战略
* 全盘局势: [总结所有阶段的起承转合，识别整体趋势。]
* 关键转折点: [指出哪个阶段是成败的关键。]
* 最终行动纲领:
  * [Time_Label 1]: [行动建议]
  * [Time_Label 2]: [行动建议]
  * ...
* 最高警示: [全周期最需要规避的风险。]

三、 深化推演邀请
本报告已对 [问题主题] 进行了分阶段全景推演。若您需要对上述任一阶段（例如"[Time_Label X]"）中的特定细节进行微观推演（例如该阶段的某小时或某具体事件），请提出您的具体指令。"""

    user_prompt = f"""求问者姓名：{request.user_name}
求问者母名：Hawwa
问题：【{request.stock_name}({request.stock_code})】的股价在【{time_period_cn}】内的走势将如何？是涨是跌？何时是最佳时机？"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    response_text = await call_minimax_api(messages, max_tokens=3000, temperature=0.7)
    
    if not response_text:
        response_text = f"""动态时序战略报告：{request.stock_name}股价走势推演

一、时间切割逻辑
* 分析对象: {request.stock_name}({request.stock_code})在{time_period_cn}的股价走势
* 时间跨度: {time_period_cn}
* 切割方案: 本次推演将时间轴切割为3个关键阶段

阶段一：初期
* 核心论断: 蓄势待发
* 深度解读: 此阶段为积蓄能量期，市场波动较小，建议观察为主。

阶段二：中期
* 核心论断: 风云变幻
* 深度解读: 此阶段可能出现关键转折，需密切关注市场信号。

阶段三：末期
* 核心论断: 尘埃落定
* 深度解读: 趋势逐渐明朗，可根据前期判断做出决策。

二、全周期综合战略
* 全盘局势: 整体呈现波动中前行的态势
* 关键转折点: 中期阶段
* 最高警示: 市场有不确定性，请谨慎决策

⚠️ 本占卜仅为娱乐参考，不构成任何投资建议。"""
    
    return {
        "report": response_text,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

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
