/**
 * Technical Indicators Calculator
 * Calculates technical indicators from historical price data
 */

// Simple Moving Average (SMA)
export const calculateSMA = (data, period) => {
  if (!data || data.length < period) return null;
  const slice = data.slice(-period);
  return slice.reduce((sum, d) => sum + d.close, 0) / period;
};

// Calculate multiple SMAs
export const calculateMAs = (data) => {
  if (!data || data.length < 60) {
    return { ma5: null, ma10: null, ma20: null, ma60: null };
  }
  return {
    ma5: calculateSMA(data, 5),
    ma10: calculateSMA(data, 10),
    ma20: calculateSMA(data, 20),
    ma60: calculateSMA(data, 60),
  };
};

// Determine MA alignment status
export const getMaAlignment = (price, ma5, ma10, ma20, ma60) => {
  if (!ma5 || !ma10 || !ma20 || !ma60) return '数据不足';
  
  if (price > ma5 && ma5 > ma10 && ma10 > ma20 && ma20 > ma60) {
    return '多头排列';
  } else if (price < ma5 && ma5 < ma10 && ma10 < ma20 && ma20 < ma60) {
    return '空头排列';
  } else if (Math.abs(ma5 - ma20) / ma20 < 0.02) {
    return '纠缠粘合';
  } else if (ma5 > ma20 && ma5 > ma10) {
    return '金叉形态';
  } else if (ma5 < ma20 && ma5 < ma10) {
    return '死叉形态';
  }
  return '震荡整理';
};

// Exponential Moving Average (EMA)
export const calculateEMA = (data, period) => {
  if (!data || data.length < period) return null;
  
  const k = 2 / (period + 1);
  let ema = data[0].close;
  
  for (let i = 1; i < data.length; i++) {
    ema = data[i].close * k + ema * (1 - k);
  }
  
  return ema;
};

// MACD Calculation
export const calculateMACD = (data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
  if (!data || data.length < slowPeriod + signalPeriod) {
    return { dif: 0, dea: 0, macd_bar: 0, macd_cross: '数据不足' };
  }
  
  // Calculate EMAs
  const fastEMA = calculateEMA(data, fastPeriod);
  const slowEMA = calculateEMA(data, slowPeriod);
  
  // DIF = Fast EMA - Slow EMA
  const dif = fastEMA - slowEMA;
  
  // DEA = EMA of DIF (simplified calculation)
  const difHistory = [];
  for (let i = slowPeriod; i < data.length; i++) {
    const slicedData = data.slice(0, i + 1);
    const fastE = calculateEMA(slicedData, fastPeriod);
    const slowE = calculateEMA(slicedData, slowPeriod);
    difHistory.push({ close: fastE - slowE });
  }
  
  const dea = difHistory.length >= signalPeriod 
    ? calculateEMA(difHistory, signalPeriod) 
    : dif * 0.8;
  
  // MACD Bar
  const macd_bar = (dif - dea) * 2;
  
  // Cross status
  let macd_cross = '无交叉';
  if (difHistory.length >= 2) {
    const prevDif = difHistory[difHistory.length - 2]?.close || 0;
    const prevDea = dea - (dif - dea) * 0.2; // Estimate previous DEA
    if (prevDif < prevDea && dif > dea) {
      macd_cross = '金叉';
    } else if (prevDif > prevDea && dif < dea) {
      macd_cross = '死叉';
    }
  }
  
  return {
    dif: Math.round(dif * 100) / 100,
    dea: Math.round(dea * 100) / 100,
    macd_bar: Math.round(macd_bar * 100) / 100,
    macd_cross
  };
};

// RSI Calculation
export const calculateRSI = (data, period = 14) => {
  if (!data || data.length < period + 1) {
    return { value: 50, status: '数据不足' };
  }
  
  let gains = 0;
  let losses = 0;
  
  // Calculate average gain and loss
  for (let i = data.length - period; i < data.length; i++) {
    const change = data[i].close - data[i - 1].close;
    if (change > 0) {
      gains += change;
    } else {
      losses -= change;
    }
  }
  
  const avgGain = gains / period;
  const avgLoss = losses / period;
  
  if (avgLoss === 0) return { value: 100, status: '超买区域' };
  
  const rs = avgGain / avgLoss;
  const rsi = 100 - (100 / (1 + rs));
  
  let status = '中性区域';
  if (rsi > 80) status = '超买区域';
  else if (rsi > 60) status = '偏强区域';
  else if (rsi < 20) status = '超卖区域';
  else if (rsi < 40) status = '偏弱区域';
  
  return {
    value: Math.round(rsi * 100) / 100,
    status
  };
};

// KDJ Calculation
export const calculateKDJ = (data, period = 9) => {
  if (!data || data.length < period) {
    return { k: 50, d: 50, j: 50 };
  }
  
  const recentData = data.slice(-period);
  const low = Math.min(...recentData.map(d => d.low));
  const high = Math.max(...recentData.map(d => d.high));
  const close = data[data.length - 1].close;
  
  if (high === low) {
    return { k: 50, d: 50, j: 50 };
  }
  
  const rsv = ((close - low) / (high - low)) * 100;
  
  // Simplified K, D, J calculation
  const k = Math.round(rsv * 0.67 + 50 * 0.33);
  const d = Math.round(k * 0.67 + 50 * 0.33);
  const j = 3 * k - 2 * d;
  
  return {
    k: Math.min(100, Math.max(0, k)),
    d: Math.min(100, Math.max(0, d)),
    j: Math.min(100, Math.max(0, j))
  };
};

// Bollinger Bands Calculation
export const calculateBollingerBands = (data, period = 20, multiplier = 2) => {
  if (!data || data.length < period) {
    return { upper: null, mid: null, lower: null, bandwidth: '数据不足', position: '数据不足' };
  }
  
  const recentData = data.slice(-period);
  const closes = recentData.map(d => d.close);
  
  // Middle band (SMA)
  const mid = closes.reduce((a, b) => a + b, 0) / period;
  
  // Standard deviation
  const squaredDiffs = closes.map(c => Math.pow(c - mid, 2));
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / period;
  const stdDev = Math.sqrt(variance);
  
  // Upper and lower bands
  const upper = mid + multiplier * stdDev;
  const lower = mid - multiplier * stdDev;
  
  // Current price position
  const currentPrice = data[data.length - 1].close;
  const bandWidth = (upper - lower) / mid * 100;
  
  // Bandwidth status
  let bandwidth = '正常';
  if (bandWidth < 5) bandwidth = '收缩';
  else if (bandWidth > 15) bandwidth = '扩张';
  
  // Position status
  let position = '中轨附近';
  const upperDist = (upper - currentPrice) / (upper - mid);
  const lowerDist = (currentPrice - lower) / (mid - lower);
  
  if (upperDist < 0.3) position = '上轨附近';
  else if (lowerDist < 0.3) position = '下轨附近';
  else if (currentPrice > mid) position = '中轨上方';
  else position = '中轨下方';
  
  return {
    upper: Math.round(upper * 100) / 100,
    mid: Math.round(mid * 100) / 100,
    lower: Math.round(lower * 100) / 100,
    bandwidth,
    position
  };
};

// Calculate volume ratio
export const calculateVolumeRatio = (data) => {
  if (!data || data.length < 20) return 1.0;
  
  const recentVolumes = data.slice(-20).map(d => d.volume);
  const avgVolume = recentVolumes.reduce((a, b) => a + b, 0) / 20;
  const currentVolume = data[data.length - 1].volume;
  
  if (avgVolume === 0) return 1.0;
  return Math.round((currentVolume / avgVolume) * 100) / 100;
};

// Calculate 52-week percentile
export const calculate52WeekPercentile = (currentPrice, week52High, week52Low) => {
  if (!week52High || !week52Low || week52High === week52Low) return 50;
  return Math.round(((currentPrice - week52Low) / (week52High - week52Low)) * 100);
};

// Calculate technical score based on indicators
export const calculateTechScore = (indicators) => {
  let score = 5; // Base score
  
  // MA alignment contribution (+/- 1.5)
  if (indicators.ma_alignment === '多头排列') score += 1.5;
  else if (indicators.ma_alignment === '空头排列') score -= 1.5;
  else if (indicators.ma_alignment === '金叉形态') score += 1;
  else if (indicators.ma_alignment === '死叉形态') score -= 1;
  
  // MACD contribution (+/- 1)
  if (indicators.macd_cross === '金叉') score += 1;
  else if (indicators.macd_cross === '死叉') score -= 1;
  if (indicators.dif > indicators.dea) score += 0.5;
  else if (indicators.dif < indicators.dea) score -= 0.5;
  
  // RSI contribution (+/- 1)
  const rsi = indicators.rsi14 || 50;
  if (rsi > 70) score -= 0.5; // Overbought
  else if (rsi < 30) score += 0.5; // Oversold
  else if (rsi > 50) score += 0.3;
  else score -= 0.3;
  
  // Volume contribution (+/- 0.5)
  const volRatio = indicators.volume_ratio || 1;
  if (volRatio > 1.5 && indicators.change_pct > 0) score += 0.5;
  else if (volRatio > 1.5 && indicators.change_pct < 0) score -= 0.5;
  
  return Math.min(10, Math.max(1, Math.round(score * 10) / 10));
};

// Calculate signal direction and strength
export const calculateSignal = (indicators) => {
  let bullishSignals = 0;
  let bearishSignals = 0;
  
  // MA signals
  if (indicators.ma_alignment === '多头排列') bullishSignals += 2;
  else if (indicators.ma_alignment === '空头排列') bearishSignals += 2;
  
  // MACD signals
  if (indicators.dif > indicators.dea) bullishSignals += 1;
  else bearishSignals += 1;
  if (indicators.macd_cross === '金叉') bullishSignals += 1;
  else if (indicators.macd_cross === '死叉') bearishSignals += 1;
  
  // RSI signals
  if (indicators.rsi14 > 50) bullishSignals += 1;
  else bearishSignals += 1;
  
  // Price vs MA signals
  if (indicators.current_price > indicators.ma20) bullishSignals += 1;
  else bearishSignals += 1;
  
  const totalSignals = bullishSignals + bearishSignals;
  const netSignal = bullishSignals - bearishSignals;
  
  let direction = 'neutral';
  if (netSignal > 2) direction = 'bullish';
  else if (netSignal < -2) direction = 'bearish';
  
  const strength = Math.min(5, Math.max(1, Math.ceil(Math.abs(netSignal) / 2)));
  
  return { direction, strength };
};

// Main function to calculate all indicators
export const calculateAllIndicators = (stockData) => {
  if (!stockData || !stockData.history || stockData.history.length < 5) {
    // Return default values when no historical data
    const price = stockData?.price || 100;
    const change = stockData?.change_percent || 0;
    return {
      current_price: price,
      change_pct: change,
      amplitude: Math.abs(change) * 1.5,
      volume: stockData?.volume || 0,
      volume_ratio: 1.0,
      high: stockData?.high || price * 1.01,
      low: stockData?.low || price * 0.99,
      week52_high: stockData?.week52_high || price * 1.2,
      week52_low: stockData?.week52_low || price * 0.8,
      percentile_52w: 50,
      ma5: price * 0.99,
      ma10: price * 0.985,
      ma20: price * 0.98,
      ma60: price * 0.97,
      ma_alignment: '纠缠粘合',
      dif: 0,
      dea: 0,
      macd_bar: 0,
      macd_cross: '无交叉',
      rsi6: 50,
      rsi14: 50,
      rsi_status: '中性区域',
      kdj_k: 50,
      kdj_d: 50,
      kdj_j: 50,
      boll_upper: price * 1.04,
      boll_mid: price,
      boll_lower: price * 0.96,
      boll_bandwidth: '正常',
      price_boll_position: '中轨附近',
      tech_score: 5,
      fundamental_score: 5,
      signal_direction: 'neutral',
      signal_strength: 2,
      news_summary: '[实时资讯数据缺失，宏观面分析基于该市场通用框架推断]'
    };
  }
  
  const history = stockData.history;
  const current = history[history.length - 1];
  const price = current.close;
  const change_pct = stockData.change_percent || 
    ((current.close - current.open) / current.open * 100);
  
  // Calculate all MAs
  const mas = calculateMAs(history);
  const ma_alignment = getMaAlignment(price, mas.ma5, mas.ma10, mas.ma20, mas.ma60);
  
  // Calculate MACD
  const macd = calculateMACD(history);
  
  // Calculate RSI
  const rsi6 = calculateRSI(history, 6);
  const rsi14 = calculateRSI(history, 14);
  
  // Calculate KDJ
  const kdj = calculateKDJ(history);
  
  // Calculate Bollinger Bands
  const boll = calculateBollingerBands(history);
  
  // Calculate volume ratio
  const volume_ratio = calculateVolumeRatio(history);
  
  // Calculate 52-week data
  const week52_high = stockData.week52_high || Math.max(...history.map(d => d.high));
  const week52_low = stockData.week52_low || Math.min(...history.map(d => d.low));
  const percentile_52w = calculate52WeekPercentile(price, week52_high, week52_low);
  
  // Build indicators object
  const indicators = {
    current_price: price,
    change_pct: Math.round(change_pct * 100) / 100,
    amplitude: Math.round((current.high - current.low) / current.low * 10000) / 100,
    volume: current.volume || stockData.volume || 0,
    volume_ratio,
    high: current.high,
    low: current.low,
    week52_high,
    week52_low,
    percentile_52w,
    ma5: mas.ma5 ? Math.round(mas.ma5 * 100) / 100 : price * 0.99,
    ma10: mas.ma10 ? Math.round(mas.ma10 * 100) / 100 : price * 0.985,
    ma20: mas.ma20 ? Math.round(mas.ma20 * 100) / 100 : price * 0.98,
    ma60: mas.ma60 ? Math.round(mas.ma60 * 100) / 100 : price * 0.97,
    ma_alignment,
    ...macd,
    rsi6: rsi6.value,
    rsi14: rsi14.value,
    rsi_status: rsi14.status,
    kdj_k: kdj.k,
    kdj_d: kdj.d,
    kdj_j: kdj.j,
    boll_upper: boll.upper || price * 1.04,
    boll_mid: boll.mid || price,
    boll_lower: boll.lower || price * 0.96,
    boll_bandwidth: boll.bandwidth,
    price_boll_position: boll.position,
    news_summary: '[实时资讯数据缺失，宏观面分析基于该市场通用框架推断]'
  };
  
  // Calculate scores
  indicators.tech_score = calculateTechScore(indicators);
  indicators.fundamental_score = Math.round((5 + change_pct / 3) * 10) / 10;
  
  // Calculate signal
  const signal = calculateSignal(indicators);
  indicators.signal_direction = signal.direction;
  indicators.signal_strength = signal.strength;
  
  return indicators;
};
