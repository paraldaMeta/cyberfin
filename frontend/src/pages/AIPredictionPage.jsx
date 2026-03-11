import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Search, Loader2, TrendingUp, TrendingDown, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Progress } from '../components/ui/progress';
import { searchStocks, getAIPrediction } from '../services/api';

const TIME_PERIODS = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
];

const formatPrice = (value, decimals = 2) => {
  if (value === null || value === undefined) return '--';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
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
    try {
      const response = await getAIPrediction({
        stock_code: selectedStock.symbol,
        stock_name: selectedStock.name,
        time_period: timePeriod,
        market_data: {}
      });
      setPrediction(response.data);
    } catch (error) {
      console.error('Prediction failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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
              <p className="text-sm text-[#a1a1aa]">基于量化分析的智能市场预测</p>
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
                量子计算中...
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
              <p className="text-[#00f0ff] text-lg animate-pulse">量子计算中...</p>
              <p className="text-[#52525b] text-sm mt-2">正在分析市场数据并生成预测报告</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Prediction Result */}
      {prediction && !loading && (
        <Card className="bg-[#0a0e17] border-[#00f0ff]/30 animate-fade-in">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#00f0ff]" />
              预测报告
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Direction & Confidence */}
            <div className="flex items-center justify-between p-4 bg-[#141824] rounded-sm">
              <div className={`px-6 py-3 rounded-sm font-bold text-lg ${
                prediction.direction === 'bullish' ? 'bg-[#f5222d]/20 text-[#f5222d]' :
                prediction.direction === 'bearish' ? 'bg-[#00b300]/20 text-[#00b300]' :
                'bg-[#8c8c8c]/20 text-[#8c8c8c]'
              }`}>
                {prediction.direction === 'bullish' ? (
                  <span className="flex items-center gap-2"><TrendingUp className="w-5 h-5" /> 看涨</span>
                ) : prediction.direction === 'bearish' ? (
                  <span className="flex items-center gap-2"><TrendingDown className="w-5 h-5" /> 看跌</span>
                ) : (
                  '中性'
                )}
              </div>
              <div className="text-right">
                <span className="text-xs text-[#52525b] block mb-2">置信度</span>
                <div className="flex items-center gap-3">
                  <Progress value={prediction.confidence} className="w-32 h-3" />
                  <span className="text-[#00f0ff] font-mono font-bold text-2xl">{prediction.confidence}%</span>
                </div>
              </div>
            </div>

            {/* Target Price Range */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-[#141824] p-4 rounded-sm">
                <span className="text-xs text-[#52525b] block mb-2">目标价区间</span>
                <div className="flex items-center gap-2 text-xl font-mono-price">
                  <span className="text-[#00b300]">{formatPrice(prediction.target_price_range?.low)}</span>
                  <span className="text-[#52525b]">~</span>
                  <span className="text-[#f5222d]">{formatPrice(prediction.target_price_range?.high)}</span>
                </div>
              </div>
              <div className="bg-[#141824] p-4 rounded-sm">
                <span className="text-xs text-[#52525b] block mb-2">支撑位</span>
                <div className="space-y-1">
                  {prediction.support_levels?.map((level, i) => (
                    <span key={i} className="text-[#00b300] font-mono text-lg block">{formatPrice(level)}</span>
                  ))}
                </div>
              </div>
              <div className="bg-[#141824] p-4 rounded-sm">
                <span className="text-xs text-[#52525b] block mb-2">压力位</span>
                <div className="space-y-1">
                  {prediction.resistance_levels?.map((level, i) => (
                    <span key={i} className="text-[#f5222d] font-mono text-lg block">{formatPrice(level)}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Analysis */}
            <div className="bg-[#141824] p-4 rounded-sm">
              <span className="text-xs text-[#52525b] block mb-2">详细分析</span>
              <p className="text-[#a1a1aa] leading-relaxed">{prediction.analysis}</p>
            </div>

            {/* Suggestions */}
            <div className="bg-[#141824] p-4 rounded-sm">
              <span className="text-xs text-[#52525b] block mb-2">操作建议</span>
              <p className="text-white leading-relaxed">{prediction.suggestions}</p>
            </div>

            {/* Risk Warning */}
            <div className="bg-[#f5222d]/10 border border-[#f5222d]/30 p-4 rounded-sm">
              <span className="text-xs text-[#f5222d] block mb-2">⚠️ 风险提示</span>
              <p className="text-[#a1a1aa] text-sm">{prediction.risk_warning}</p>
            </div>

            <p className="text-xs text-[#52525b] text-center">
              生成时间: {new Date(prediction.timestamp).toLocaleString('zh-CN')} | 仅供参考，不构成投资建议
            </p>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center">
          ⚠️ 免责声明：本平台提供的所有AI预测内容均仅供参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
        </p>
      </div>
    </div>
  );
}
