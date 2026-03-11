/**
 * Technical Indicators Chart Component
 * Displays MACD, RSI, and Bollinger Bands below the main K-line chart
 */
import { 
  ResponsiveContainer, 
  ComposedChart, 
  Line, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ReferenceLine,
  Area
} from 'recharts';
import { useLanguage } from '../i18n';

// Calculate MACD data
export const calculateMACDData = (data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
  if (!data || data.length < slowPeriod + signalPeriod) return [];
  
  // Calculate EMAs
  const ema = (data, period, key = 'close') => {
    const k = 2 / (period + 1);
    let emaVal = data[0][key];
    return data.map((d, i) => {
      if (i === 0) return emaVal;
      emaVal = d[key] * k + emaVal * (1 - k);
      return emaVal;
    });
  };
  
  const fastEMA = ema(data, fastPeriod);
  const slowEMA = ema(data, slowPeriod);
  
  // DIF = Fast EMA - Slow EMA
  const dif = fastEMA.map((f, i) => f - slowEMA[i]);
  
  // DEA = Signal EMA of DIF
  const difData = dif.map((d, i) => ({ close: d, date: data[i].date }));
  const dea = ema(difData, signalPeriod, 'close');
  
  // MACD Histogram
  return data.map((d, i) => ({
    date: d.date,
    dif: Math.round(dif[i] * 100) / 100,
    dea: Math.round(dea[i] * 100) / 100,
    macd: Math.round((dif[i] - dea[i]) * 2 * 100) / 100,
  }));
};

// Calculate RSI data
export const calculateRSIData = (data, period = 14) => {
  if (!data || data.length < period + 1) return [];
  
  return data.map((d, i) => {
    if (i < period) return { date: d.date, rsi: 50 };
    
    let gains = 0, losses = 0;
    for (let j = i - period + 1; j <= i; j++) {
      const change = data[j].close - data[j - 1].close;
      if (change > 0) gains += change;
      else losses -= change;
    }
    
    const avgGain = gains / period;
    const avgLoss = losses / period;
    const rs = avgLoss === 0 ? 100 : avgGain / avgLoss;
    const rsi = 100 - (100 / (1 + rs));
    
    return {
      date: d.date,
      rsi: Math.round(rsi * 100) / 100,
    };
  });
};

// Calculate Bollinger Bands data
export const calculateBollingerData = (data, period = 20, multiplier = 2) => {
  if (!data || data.length < period) return [];
  
  return data.map((d, i) => {
    if (i < period - 1) {
      return { date: d.date, upper: d.close, mid: d.close, lower: d.close, close: d.close };
    }
    
    const slice = data.slice(i - period + 1, i + 1);
    const closes = slice.map(s => s.close);
    const mid = closes.reduce((a, b) => a + b, 0) / period;
    const variance = closes.reduce((a, b) => a + Math.pow(b - mid, 2), 0) / period;
    const stdDev = Math.sqrt(variance);
    
    return {
      date: d.date,
      upper: Math.round((mid + multiplier * stdDev) * 100) / 100,
      mid: Math.round(mid * 100) / 100,
      lower: Math.round((mid - multiplier * stdDev) * 100) / 100,
      close: d.close,
    };
  });
};

// MACD Chart Component
export const MACDChart = ({ data }) => {
  const { t } = useLanguage();
  const macdData = calculateMACDData(data);
  
  if (macdData.length === 0) return <div className="h-32 flex items-center justify-center text-[#52525b]">数据不足</div>;
  
  return (
    <div className="h-32 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={macdData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <XAxis dataKey="date" hide />
          <YAxis domain={['auto', 'auto']} hide />
          <Tooltip
            contentStyle={{ backgroundColor: '#141824', border: '1px solid #2a2f3e', borderRadius: '4px' }}
            labelStyle={{ color: '#a1a1aa' }}
            itemStyle={{ color: '#fff' }}
            formatter={(value, name) => [value, name === 'dif' ? 'DIF' : name === 'dea' ? 'DEA' : 'MACD']}
          />
          <ReferenceLine y={0} stroke="#2a2f3e" />
          <Bar dataKey="macd" fill={(entry) => entry?.macd >= 0 ? '#f5222d' : '#00b300'} />
          <Line type="monotone" dataKey="dif" stroke="#00f0ff" dot={false} strokeWidth={1} />
          <Line type="monotone" dataKey="dea" stroke="#f0a500" dot={false} strokeWidth={1} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// RSI Chart Component
export const RSIChart = ({ data }) => {
  const { t } = useLanguage();
  const rsiData = calculateRSIData(data);
  
  if (rsiData.length === 0) return <div className="h-24 flex items-center justify-center text-[#52525b]">数据不足</div>;
  
  return (
    <div className="h-24 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={rsiData} margin={{ top: 5, right: 5, left: 0, bottom: 5 }}>
          <XAxis dataKey="date" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip
            contentStyle={{ backgroundColor: '#141824', border: '1px solid #2a2f3e', borderRadius: '4px' }}
            labelStyle={{ color: '#a1a1aa' }}
            itemStyle={{ color: '#fff' }}
            formatter={(value) => [value, 'RSI']}
          />
          <ReferenceLine y={70} stroke="#f5222d" strokeDasharray="3 3" />
          <ReferenceLine y={30} stroke="#00b300" strokeDasharray="3 3" />
          <ReferenceLine y={50} stroke="#2a2f3e" />
          <Area type="monotone" dataKey="rsi" stroke="#9333ea" fill="#9333ea" fillOpacity={0.2} />
          <Line type="monotone" dataKey="rsi" stroke="#9333ea" dot={false} strokeWidth={2} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// Bollinger Bands Chart Component (for overlay on main chart)
export const BollingerOverlay = ({ data }) => {
  const bollData = calculateBollingerData(data);
  
  if (bollData.length === 0) return null;
  
  return (
    <>
      <Area
        type="monotone"
        dataKey="upper"
        stroke="none"
        fill="#f0a500"
        fillOpacity={0.1}
        data={bollData}
      />
      <Line type="monotone" dataKey="upper" stroke="#f0a500" dot={false} strokeWidth={1} strokeDasharray="3 3" data={bollData} />
      <Line type="monotone" dataKey="mid" stroke="#f0a500" dot={false} strokeWidth={1} data={bollData} />
      <Line type="monotone" dataKey="lower" stroke="#f0a500" dot={false} strokeWidth={1} strokeDasharray="3 3" data={bollData} />
    </>
  );
};

// Combined Technical Indicators Panel
export const TechnicalIndicatorsPanel = ({ data, showMACD = true, showRSI = true }) => {
  const { t } = useLanguage();
  
  if (!data || data.length === 0) {
    return (
      <div className="bg-[#141824] rounded-sm p-4 text-center text-[#52525b]">
        {t('common.loading')}
      </div>
    );
  }
  
  return (
    <div className="space-y-2">
      {showMACD && (
        <div className="bg-[#141824] rounded-sm p-2">
          <div className="flex items-center justify-between mb-1 px-2">
            <span className="text-xs text-[#a1a1aa]">{t('indicator.macd')}</span>
            <div className="flex gap-3 text-xs">
              <span className="text-[#00f0ff]">DIF</span>
              <span className="text-[#f0a500]">DEA</span>
              <span className="text-[#52525b]">MACD</span>
            </div>
          </div>
          <MACDChart data={data} />
        </div>
      )}
      
      {showRSI && (
        <div className="bg-[#141824] rounded-sm p-2">
          <div className="flex items-center justify-between mb-1 px-2">
            <span className="text-xs text-[#a1a1aa]">{t('indicator.rsi')} (14)</span>
            <div className="flex gap-3 text-xs">
              <span className="text-[#f5222d]">70</span>
              <span className="text-[#00b300]">30</span>
            </div>
          </div>
          <RSIChart data={data} />
        </div>
      )}
    </div>
  );
};

export default TechnicalIndicatorsPanel;
