import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, Loader2, TrendingUp, TrendingDown, ArrowLeft, AlertTriangle, ChevronDown, ChevronUp, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../components/ui/collapsible';
import { searchStocks, getAIPrediction, savePredictionHistory, getStockDetail } from '../services/api';
import { calculateAllIndicators } from '../utils/technicalIndicators';
import { toast } from 'sonner';

const TIME_PERIODS = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
];

const formatPrice = (value, decimals = 2) => {
  if (value === null || value === undefined) return '--';
  const num = parseFloat(value);
  if (isNaN(num)) return value;
  return num.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

// Direction Badge Component
const DirectionBadge = ({ direction }) => {
  const config = {
    bullish: { label: '看涨', icon: TrendingUp, bgClass: 'bg-[#f5222d]/20', textClass: 'text-[#f5222d]' },
    bearish: { label: '看跌', icon: TrendingDown, bgClass: 'bg-[#00b300]/20', textClass: 'text-[#00b300]' },
    neutral: { label: '中性', icon: null, bgClass: 'bg-[#8c8c8c]/20', textClass: 'text-[#8c8c8c]' }
  };
  const c = config[direction] || config.neutral;
  const Icon = c.icon;
  
  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-sm font-bold ${c.bgClass} ${c.textClass}`}>
      {Icon && <Icon className="w-5 h-5" />}
      <span>{c.label}</span>
    </div>
  );
};

// Signal Grade Badge
const SignalGradeBadge = ({ grade }) => {
  const colors = {
    A: 'bg-[#f5222d] text-white',
    B: 'bg-[#f0a500] text-black',
    C: 'bg-[#00f0ff] text-black',
    D: 'bg-[#52525b] text-white'
  };
  return (
    <span className={`px-3 py-1 rounded-sm font-bold text-lg ${colors[grade] || colors.D}`}>
      {grade}
    </span>
  );
};

// Risk Level Badge
const RiskLevelBadge = ({ level }) => {
  const config = {
    low: { label: '低风险', color: 'bg-[#00b300]' },
    medium: { label: '中风险', color: 'bg-[#f0a500]' },
    high: { label: '高风险', color: 'bg-[#f5222d]' },
    extreme: { label: '极高风险', color: 'bg-[#8b0000]' }
  };
  const c = config[level] || config.medium;
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-sm ${c.color} text-white font-bold`}>
      <AlertTriangle className="w-4 h-4" />
      {c.label}
    </div>
  );
};

// Collapsible Section Component
const CollapsibleSection = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full flex items-center justify-between p-3 bg-[#141824] hover:bg-[#1e2330] rounded-sm transition-colors">
        <span className="text-white font-medium">{title}</span>
        {isOpen ? <ChevronUp className="w-4 h-4 text-[#a1a1aa]" /> : <ChevronDown className="w-4 h-4 text-[#a1a1aa]" />}
      </CollapsibleTrigger>
      <CollapsibleContent className="pt-2">
        {children}
      </CollapsibleContent>
    </Collapsible>
  );
};

export default function AIPredictionPage() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [timePeriod, setTimePeriod] = useState('today');
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [loadingStage, setLoadingStage] = useState('');
  const [indicators, setIndicators] = useState(null);

  const handleSearch = useCallback(async (query) => {
    setSearchQuery(query);
    if (query.length >= 1) {
      try {
        const response = await searchStocks(query);
        setSearchResults(response.data.results || []);
        setShowResults(true);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      }
    } else {
      setSearchResults([]);
      setShowResults(false);
    }
  }, []);

  const handleSelectStock = (stock) => {
    setSelectedStock(stock);
    setSearchQuery(`${stock.symbol} - ${stock.name}`);
    setShowResults(false);
    setPrediction(null);
  };

  const handlePredict = async () => {
    if (!selectedStock) return;
    setLoading(true);
    setIndicators(null);
    setPrediction(null);
    
    try {
      let calculatedIndicators;
      
      // Stage 1: Try to fetch stock data
      setLoadingStage('正在获取股票数据...');
      try {
        const stockResponse = await getStockDetail(selectedStock.symbol);
        const stockData = stockResponse.data;
        
        // Stage 2: Calculate technical indicators (frontend calculation)
        setLoadingStage('正在计算技术指标...');
        calculatedIndicators = calculateAllIndicators(stockData);
      } catch (dataError) {
        console.warn('Failed to fetch stock data, using defaults:', dataError);
        // Use default indicators if stock data fetch fails
        calculatedIndicators = calculateAllIndicators({
          price: 100,
          change_percent: 0,
          volume: 1000000,
          history: []
        });
      }
      
      setIndicators(calculatedIndicators);
      
      // Stage 3: Call AI prediction API with indicators
      setLoadingStage('正在生成深度研判报告...');
      const response = await getAIPrediction({
        stock_code: selectedStock.symbol,
        stock_name: selectedStock.name,
        time_period: timePeriod,
        market_data: {
          price: calculatedIndicators.current_price,
          change_percent: calculatedIndicators.change_pct,
          volume: calculatedIndicators.volume
        },
        indicators: calculatedIndicators
      });
      setPrediction(response.data);
      
      // Save to history
      try {
        await savePredictionHistory({
          prediction_type: 'ai',
          stock_code: selectedStock.symbol,
          stock_name: selectedStock.name,
          time_period: timePeriod,
          result: JSON.stringify(response.data)
        });
      } catch (e) {
        console.error('Failed to save history:', e);
      }
    } catch (error) {
      console.error('Prediction failed:', error);
      toast.error('预测生成失败，请重试');
    } finally {
      setLoading(false);
      setLoadingStage('');
    }
  };

  // Check if we have the new format
  const isNewFormat = prediction?.executive_summary?.headline;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/')}
          className="text-[#a1a1aa] hover:text-white"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回
        </Button>
      </div>

      {/* Hero Section */}
      <div className="relative overflow-hidden rounded-md bg-gradient-to-br from-[#0a0e17] via-[#141824] to-[#0a0e17] border border-[#00f0ff]/30 p-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,240,255,0.1)_0%,transparent_70%)]"></div>
        <div className="relative">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-[#00f0ff]/20 flex items-center justify-center animate-pulse-glow">
              <Sparkles className="w-6 h-6 text-[#00f0ff]" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-white font-market">AI智能预测</h1>
              <p className="text-sm text-[#a1a1aa]">CFA+FRM+PhD级别量化分析</p>
            </div>
          </div>
        </div>
      </div>

      {/* Input Section */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Search className="w-5 h-5 text-[#00f0ff]" />
            选择分析标的
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Stock Search */}
            <div className="md:col-span-2 relative">
              <Label className="text-[#a1a1aa] text-xs mb-1.5 block">股票代码/名称</Label>
              <Input
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowResults(true)}
                placeholder="搜索股票代码或名称..."
                className="bg-[#0a0e17] border-[#2a2f3e] text-white placeholder:text-[#52525b] focus:border-[#00f0ff]"
                data-testid="ai-search-input"
              />
              {showResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-[#141824] border border-[#2a2f3e] rounded-md shadow-lg max-h-60 overflow-auto z-50">
                  {searchResults.map((result) => (
                    <button
                      key={result.symbol}
                      onClick={() => handleSelectStock(result)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#1e2330] transition-colors text-left"
                    >
                      <div>
                        <span className="text-white font-mono text-sm">{result.symbol}</span>
                        <span className="text-[#a1a1aa] ml-2 text-sm">{result.name}</span>
                      </div>
                      <span className="text-xs text-[#52525b]">{result.market_type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Time Period */}
            <div>
              <Label className="text-[#a1a1aa] text-xs mb-1.5 block">预测时间段</Label>
              <Select value={timePeriod} onValueChange={setTimePeriod}>
                <SelectTrigger className="bg-[#0a0e17] border-[#2a2f3e] text-white" data-testid="ai-period-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#141824] border-[#2a2f3e]">
                  {TIME_PERIODS.map(p => (
                    <SelectItem key={p.value} value={p.value} className="text-white hover:bg-[#1e2330]">
                      {p.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Selected Stock Preview */}
          {selectedStock && (
            <div className="flex items-center justify-between p-3 bg-[#0a0e17] rounded-sm border border-[#00f0ff]/20">
              <div>
                <span className="text-white">{selectedStock.name}</span>
                <span className="text-[#a1a1aa] text-sm ml-2 font-mono">{selectedStock.symbol}</span>
              </div>
              <span className="text-xs text-[#52525b]">{selectedStock.market_type}</span>
            </div>
          )}

          <Button
            onClick={handlePredict}
            disabled={loading || !selectedStock}
            className="w-full bg-[#00f0ff] hover:bg-[#00f0ff]/80 text-black font-bold py-6 text-lg"
            data-testid="ai-predict-submit"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                正在生成深度研判报告...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5 mr-2" />
                开始AI预测
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card className="bg-[#141824] border-[#00f0ff]/30">
          <CardContent className="py-12">
            <div className="flex flex-col items-center">
              <div className="quantum-loading mb-6"></div>
              <p className="text-[#00f0ff] text-lg animate-pulse">{loadingStage || '正在处理...'}</p>
              <p className="text-[#52525b] text-sm mt-2">博士级量化分析引擎运算中</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Technical Indicators Preview - Shows immediately after calculation */}
      {indicators && !loading && (
        <Card className="bg-[#141824] border-[#00f0ff]/30">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Activity className="w-5 h-5 text-[#00f0ff]" />
              技术指标快照（前端计算）
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">当前价格</span>
                <span className="text-white font-mono">{formatPrice(indicators.current_price)}</span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">涨跌幅</span>
                <span className={`font-mono ${indicators.change_pct > 0 ? 'text-[#f5222d]' : indicators.change_pct < 0 ? 'text-[#00b300]' : 'text-white'}`}>
                  {indicators.change_pct > 0 ? '+' : ''}{indicators.change_pct}%
                </span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">均线排列</span>
                <span className={`text-sm ${indicators.ma_alignment === '多头排列' ? 'text-[#f5222d]' : indicators.ma_alignment === '空头排列' ? 'text-[#00b300]' : 'text-[#f0a500]'}`}>
                  {indicators.ma_alignment}
                </span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">MACD</span>
                <span className={`text-sm ${indicators.macd_cross === '金叉' ? 'text-[#f5222d]' : indicators.macd_cross === '死叉' ? 'text-[#00b300]' : 'text-white'}`}>
                  {indicators.macd_cross}
                </span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">RSI(14)</span>
                <span className={`font-mono ${indicators.rsi14 > 70 ? 'text-[#f5222d]' : indicators.rsi14 < 30 ? 'text-[#00b300]' : 'text-white'}`}>
                  {indicators.rsi14}
                </span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">技术评分</span>
                <span className="text-[#00f0ff] font-mono font-bold">{indicators.tech_score}/10</span>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">MA5</span>
                <span className="text-white font-mono text-sm">{formatPrice(indicators.ma5)}</span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">MA20</span>
                <span className="text-white font-mono text-sm">{formatPrice(indicators.ma20)}</span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">布林带</span>
                <span className="text-[#f0a500] text-sm">{indicators.price_boll_position}</span>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block">量比</span>
                <span className="text-white font-mono">{indicators.volume_ratio}x</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prediction Result - New Format */}
      {prediction && !loading && isNewFormat && (
        <div className="space-y-6 animate-fade-in">
          {/* Executive Summary Card */}
          <Card className="bg-[#0a0e17] border-[#00f0ff]/30">
            <CardHeader className="border-b border-[#2a2f3e]">
              <div className="flex items-center justify-between">
                <CardTitle className="text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-[#00f0ff]" />
                  研究报告摘要
                </CardTitle>
                <SignalGradeBadge grade={prediction.executive_summary?.signal_grade} />
              </div>
            </CardHeader>
            <CardContent className="pt-6 space-y-6">
              {/* Headline */}
              <div className="text-center">
                <h2 className="text-2xl font-bold text-white mb-4">{prediction.executive_summary?.headline}</h2>
                <div className="flex items-center justify-center gap-6 flex-wrap">
                  <DirectionBadge direction={prediction.executive_summary?.direction} />
                  <div className="text-center">
                    <span className="text-xs text-[#52525b] block">综合评分</span>
                    <span className="text-3xl font-bold text-[#00f0ff]">{prediction.executive_summary?.composite_score}</span>
                    <span className="text-[#52525b]">/10</span>
                  </div>
                  <div className="text-center">
                    <span className="text-xs text-[#52525b] block">置信度</span>
                    <span className="text-2xl font-bold text-[#f0a500]">{prediction.executive_summary?.confidence_level}</span>
                  </div>
                </div>
              </div>

              {/* Three Line Summary */}
              <div className="bg-[#141824] p-4 rounded-sm">
                <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.executive_summary?.three_line_summary}</p>
              </div>
            </CardContent>
          </Card>

          {/* Market Structure */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg">市场结构分析</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block">当前阶段</span>
                  <span className="text-white font-medium">{prediction.market_structure_analysis?.current_phase}</span>
                </div>
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block">周期位置</span>
                  <span className="text-white font-medium">{prediction.market_structure_analysis?.cycle_position}</span>
                </div>
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block">流动性</span>
                  <span className="text-white font-medium">{prediction.market_structure_analysis?.liquidity_assessment}</span>
                </div>
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block">波动率</span>
                  <span className="text-white font-medium">{prediction.market_structure_analysis?.volatility_regime}</span>
                </div>
              </div>
              <div className="bg-[#0a0e17] p-3 rounded-sm">
                <span className="text-xs text-[#52525b] block mb-1">阶段判断依据</span>
                <p className="text-[#a1a1aa] text-sm">{prediction.market_structure_analysis?.phase_evidence}</p>
              </div>
            </CardContent>
          </Card>

          {/* Technical Deep Dive */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                <Activity className="w-5 h-5 text-[#00f0ff]" />
                技术面深度分析
                <span className="ml-auto text-[#00f0ff] font-mono">
                  评分: {prediction.technical_deep_dive?.technical_score}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Trend Analysis */}
              <CollapsibleSection title="趋势分析" defaultOpen={true}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div className="bg-[#0a0e17] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">主趋势</span>
                    <p className="text-white text-sm">{prediction.technical_deep_dive?.trend_analysis?.primary_trend}</p>
                  </div>
                  <div className="bg-[#0a0e17] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">次级趋势</span>
                    <p className="text-white text-sm">{prediction.technical_deep_dive?.trend_analysis?.secondary_trend}</p>
                  </div>
                </div>
                <div className="mt-3 bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">均线排列: <span className="text-[#f0a500]">{prediction.technical_deep_dive?.trend_analysis?.ma_alignment}</span></span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.technical_deep_dive?.trend_analysis?.ma_commentary}</p>
                </div>
              </CollapsibleSection>

              {/* Momentum Analysis */}
              <CollapsibleSection title="动量分析">
                <div className="space-y-3">
                  <div className="bg-[#0a0e17] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">MACD</span>
                    <p className="text-[#a1a1aa] text-sm">{prediction.technical_deep_dive?.momentum_analysis?.macd_interpretation}</p>
                  </div>
                  <div className="bg-[#0a0e17] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">RSI</span>
                    <p className="text-[#a1a1aa] text-sm">{prediction.technical_deep_dive?.momentum_analysis?.rsi_interpretation}</p>
                  </div>
                  {prediction.technical_deep_dive?.momentum_analysis?.kdj_interpretation && (
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">KDJ</span>
                      <p className="text-[#a1a1aa] text-sm">{prediction.technical_deep_dive?.momentum_analysis?.kdj_interpretation}</p>
                    </div>
                  )}
                  <div className="bg-[#00f0ff]/10 border border-[#00f0ff]/30 p-3 rounded-sm">
                    <span className="text-xs text-[#00f0ff] block mb-1">动量结论</span>
                    <p className="text-white text-sm font-medium">{prediction.technical_deep_dive?.momentum_analysis?.momentum_conclusion}</p>
                  </div>
                </div>
              </CollapsibleSection>

              {/* Volume Price Analysis */}
              {prediction.technical_deep_dive?.volume_price_analysis && (
                <CollapsibleSection title="量价分析">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">成交量趋势</span>
                      <p className="text-white text-sm">{prediction.technical_deep_dive?.volume_price_analysis?.volume_trend}</p>
                    </div>
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">量价关系</span>
                      <p className="text-white text-sm">{prediction.technical_deep_dive?.volume_price_analysis?.price_volume_relationship}</p>
                    </div>
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">机构行为</span>
                      <p className="text-[#f0a500] text-sm font-medium">{prediction.technical_deep_dive?.volume_price_analysis?.institutional_footprint}</p>
                    </div>
                  </div>
                </CollapsibleSection>
              )}

              {/* Bollinger Analysis */}
              {prediction.technical_deep_dive?.bollinger_analysis && (
                <CollapsibleSection title="布林带分析">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">带宽状态</span>
                      <p className="text-white text-sm">{prediction.technical_deep_dive?.bollinger_analysis?.band_status}</p>
                    </div>
                    <div className="bg-[#0a0e17] p-3 rounded-sm">
                      <span className="text-xs text-[#52525b] block mb-1">挤压预警</span>
                      <p className="text-white text-sm">{prediction.technical_deep_dive?.bollinger_analysis?.squeeze_alert}</p>
                    </div>
                  </div>
                  <div className="mt-3 bg-[#0a0e17] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">结论</span>
                    <p className="text-[#a1a1aa] text-sm">{prediction.technical_deep_dive?.bollinger_analysis?.bb_conclusion}</p>
                  </div>
                </CollapsibleSection>
              )}

              {/* Key Levels */}
              <CollapsibleSection title="关键价位">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <span className="text-xs text-[#f5222d] block">压力位</span>
                    {prediction.technical_deep_dive?.key_levels?.critical_resistance?.map((level, i) => (
                      <div key={i} className="flex items-center justify-between bg-[#f5222d]/10 p-2 rounded-sm">
                        <span className="text-[#f5222d] font-mono">{level.price}</span>
                        <span className="text-[#a1a1aa] text-xs">{level.basis}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${level.strength === '强' ? 'bg-[#f5222d]/30 text-[#f5222d]' : 'bg-[#f0a500]/30 text-[#f0a500]'}`}>
                          {level.strength}
                        </span>
                      </div>
                    ))}
                  </div>
                  <div className="space-y-2">
                    <span className="text-xs text-[#00b300] block">支撑位</span>
                    {prediction.technical_deep_dive?.key_levels?.critical_support?.map((level, i) => (
                      <div key={i} className="flex items-center justify-between bg-[#00b300]/10 p-2 rounded-sm">
                        <span className="text-[#00b300] font-mono">{level.price}</span>
                        <span className="text-[#a1a1aa] text-xs">{level.basis}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${level.strength === '强' ? 'bg-[#00b300]/30 text-[#00b300]' : 'bg-[#f0a500]/30 text-[#f0a500]'}`}>
                          {level.strength}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="mt-3 text-center bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b]">枢轴价位</span>
                  <p className="text-[#00f0ff] font-mono text-lg font-bold">{prediction.technical_deep_dive?.key_levels?.pivot_point}</p>
                </div>
              </CollapsibleSection>
            </CardContent>
          </Card>

          {/* Macro Fundamental Analysis */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center gap-2">
                基本面分析
                <span className="ml-auto text-[#f0a500] font-mono">
                  评分: {prediction.macro_fundamental_analysis?.fundamental_score}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">核心驱动因素</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.macro_fundamental_analysis?.market_specific_drivers}</p>
                </div>
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">政策环境</span>
                  <p className="text-white text-sm">{prediction.macro_fundamental_analysis?.policy_environment}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">跨资产信号</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.macro_fundamental_analysis?.cross_asset_signals}</p>
                </div>
                <div className="bg-[#0a0e17] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">市场情绪</span>
                  <p className={`text-sm font-medium ${
                    prediction.macro_fundamental_analysis?.sentiment_gauge === '贪婪' || prediction.macro_fundamental_analysis?.sentiment_gauge === '极度贪婪' 
                      ? 'text-[#f5222d]' 
                      : prediction.macro_fundamental_analysis?.sentiment_gauge === '恐慌' || prediction.macro_fundamental_analysis?.sentiment_gauge === '极度恐慌'
                        ? 'text-[#00b300]'
                        : 'text-[#f0a500]'
                  }`}>{prediction.macro_fundamental_analysis?.sentiment_gauge}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Scenario Analysis - Bull vs Bear */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Bull Scenario */}
            <Card className="bg-[#0a0e17] border-[#f5222d]/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-[#f5222d] flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  看多情景
                  <span className="ml-auto text-2xl font-bold">{prediction.scenario_analysis?.bull_scenario?.probability}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">核心逻辑</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.scenario_analysis?.bull_scenario?.core_thesis}</p>
                </div>
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">目标价位</span>
                  <p className="text-[#f5222d] font-mono">{prediction.scenario_analysis?.bull_scenario?.target_levels}</p>
                </div>
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">催化剂</span>
                  <ul className="text-[#a1a1aa] text-sm">
                    {prediction.scenario_analysis?.bull_scenario?.key_catalysts?.map((c, i) => (
                      <li key={i}>• {c}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-[#f5222d]/10 border border-[#f5222d]/30 p-3 rounded-sm">
                  <span className="text-xs text-[#f5222d] block mb-1">失效条件</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.scenario_analysis?.bull_scenario?.invalidation_condition}</p>
                </div>
              </CardContent>
            </Card>

            {/* Bear Scenario */}
            <Card className="bg-[#0a0e17] border-[#00b300]/30">
              <CardHeader className="pb-2">
                <CardTitle className="text-[#00b300] flex items-center gap-2">
                  <TrendingDown className="w-5 h-5" />
                  看空情景
                  <span className="ml-auto text-2xl font-bold">{prediction.scenario_analysis?.bear_scenario?.probability}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">核心逻辑</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.scenario_analysis?.bear_scenario?.core_thesis}</p>
                </div>
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">目标价位</span>
                  <p className="text-[#00b300] font-mono">{prediction.scenario_analysis?.bear_scenario?.target_levels}</p>
                </div>
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">催化剂</span>
                  <ul className="text-[#a1a1aa] text-sm">
                    {prediction.scenario_analysis?.bear_scenario?.key_catalysts?.map((c, i) => (
                      <li key={i}>• {c}</li>
                    ))}
                  </ul>
                </div>
                <div className="bg-[#00b300]/10 border border-[#00b300]/30 p-3 rounded-sm">
                  <span className="text-xs text-[#00b300] block mb-1">失效条件</span>
                  <p className="text-[#a1a1aa] text-sm">{prediction.scenario_analysis?.bear_scenario?.invalidation_condition}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Time Segmented Forecast */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg">分时段预测</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {prediction.time_segmented_forecast?.map((segment, index) => (
                  <div key={index} className="bg-[#0a0e17] p-4 rounded-sm border border-[#2a2f3e]">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white font-medium">{segment.period_label}</span>
                      <DirectionBadge direction={segment.directional_bias} />
                    </div>
                    <p className="text-[#a1a1aa] text-sm mb-2">{segment.key_price_behavior}</p>
                    <p className="text-[#52525b] text-xs">{segment.tactical_note}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Risk Assessment */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg flex items-center justify-between">
                <span>风险评估</span>
                <RiskLevelBadge level={prediction.risk_assessment?.overall_risk_level} />
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0a0e17] p-4 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-2">风险评分</span>
                  <div className="flex items-center gap-3">
                    <Progress value={parseInt(prediction.risk_assessment?.risk_score || 5) * 10} className="h-3" />
                    <span className="text-white font-mono">{prediction.risk_assessment?.risk_score}/10</span>
                  </div>
                </div>
                <div className="bg-[#0a0e17] p-4 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-2">风险收益比</span>
                  <p className="text-white text-sm">{prediction.risk_assessment?.risk_reward_ratio}</p>
                </div>
              </div>
              <div className="bg-[#0a0e17] p-4 rounded-sm">
                <span className="text-xs text-[#52525b] block mb-2">系统性风险</span>
                {prediction.risk_assessment?.systematic_risks?.map((risk, i) => (
                  <div key={i} className="flex items-center justify-between py-1 border-b border-[#2a2f3e] last:border-0">
                    <span className="text-[#a1a1aa] text-sm">{risk.risk}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[#52525b] text-xs">概率: {risk.probability}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${risk.impact === '高' ? 'bg-[#f5222d]/20 text-[#f5222d]' : risk.impact === '中' ? 'bg-[#f0a500]/20 text-[#f0a500]' : 'bg-[#00b300]/20 text-[#00b300]'}`}>
                        {risk.impact}影响
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="bg-[#f5222d]/10 border border-[#f5222d]/30 p-4 rounded-sm">
                <span className="text-xs text-[#f5222d] block mb-1">⚠️ 尾部风险情景</span>
                <p className="text-[#a1a1aa] text-sm">{prediction.risk_assessment?.tail_risk_scenario}</p>
              </div>
            </CardContent>
          </Card>

          {/* Professional Narrative */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-white text-lg">专业研究报告</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Opening - Always visible */}
              <div className="bg-[#0a0e17] p-4 rounded-sm">
                <span className="text-[#00f0ff] text-xs font-medium block mb-2">宏观背景</span>
                <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.professional_narrative?.opening_paragraph}</p>
              </div>

              {/* Collapsible sections */}
              <CollapsibleSection title="技术面深度分析">
                <div className="bg-[#0a0e17] p-4 rounded-sm">
                  <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.professional_narrative?.technical_narrative}</p>
                </div>
              </CollapsibleSection>

              <CollapsibleSection title="基本面研判">
                <div className="bg-[#0a0e17] p-4 rounded-sm">
                  <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.professional_narrative?.fundamental_narrative}</p>
                </div>
              </CollapsibleSection>

              <CollapsibleSection title="综合研判">
                <div className="bg-[#0a0e17] p-4 rounded-sm">
                  <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.professional_narrative?.synthesis_paragraph}</p>
                </div>
              </CollapsibleSection>

              <CollapsibleSection title="前瞻指引" defaultOpen={true}>
                <div className="bg-[#00f0ff]/10 border border-[#00f0ff]/30 p-4 rounded-sm">
                  <p className="text-[#a1a1aa] text-sm leading-relaxed">{prediction.professional_narrative?.forward_guidance}</p>
                </div>
              </CollapsibleSection>
            </CardContent>
          </Card>

          {/* Disclaimer */}
          <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
            <p className="text-xs text-[#52525b] text-center">{prediction.disclaimer}</p>
            <p className="text-xs text-[#52525b] text-center mt-2">
              报告生成时间: {new Date(prediction.timestamp).toLocaleString('zh-CN')}
            </p>
          </div>
        </div>
      )}

      {/* Old Format Fallback */}
      {prediction && !loading && !isNewFormat && (
        <Card className="bg-[#0a0e17] border-[#00f0ff]/30 animate-fade-in">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#00f0ff]" />
              预测报告
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-[#141824] rounded-sm">
              <DirectionBadge direction={prediction.direction} />
              <div className="text-right">
                <span className="text-xs text-[#52525b] block mb-2">置信度</span>
                <div className="flex items-center gap-3">
                  <Progress value={prediction.confidence} className="w-32 h-3" />
                  <span className="text-[#00f0ff] font-mono font-bold text-2xl">{prediction.confidence}%</span>
                </div>
              </div>
            </div>
            <div className="bg-[#141824] p-4 rounded-sm">
              <span className="text-xs text-[#52525b] block mb-2">详细分析</span>
              <p className="text-[#a1a1aa] leading-relaxed">{prediction.analysis}</p>
            </div>
            <div className="bg-[#141824] p-4 rounded-sm">
              <span className="text-xs text-[#52525b] block mb-2">操作建议</span>
              <p className="text-white leading-relaxed">{prediction.suggestions}</p>
            </div>
            <div className="bg-[#f5222d]/10 border border-[#f5222d]/30 p-4 rounded-sm">
              <span className="text-xs text-[#f5222d] block mb-2">⚠️ 风险提示</span>
              <p className="text-[#a1a1aa] text-sm">{prediction.risk_warning}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      {!prediction && (
        <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
          <p className="text-xs text-[#52525b] text-center">
            ⚠️ 免责声明：本平台提供的所有AI预测内容均仅供参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
          </p>
        </div>
      )}
    </div>
  );
}
