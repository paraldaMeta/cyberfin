import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, TrendingUp, TrendingDown, Sparkles, Star, RefreshCw, Loader2, Heart } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Skeleton } from '../components/ui/skeleton';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, ComposedChart, Bar } from 'recharts';
import { toast } from 'sonner';
import { getStockDetail, getAIPrediction, getDivinationPrediction, savePredictionHistory, addToWatchlist } from '../services/api';

// Get client ID for watchlist
const getClientId = () => {
  let clientId = localStorage.getItem('watchlist_client_id');
  if (!clientId) {
    clientId = 'client_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('watchlist_client_id', clientId);
  }
  return clientId;
};

const formatPrice = (value, decimals = 2) => {
  if (value === null || value === undefined) return '--';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

const formatChange = (value, decimals = 2) => {
  if (value === null || value === undefined) return '--';
  const sign = value >= 0 ? '+' : '';
  return sign + value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
};

const TIME_PERIODS = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
];

// Custom Tooltip for Chart
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-[#141824] border border-[#f0a500] p-3 rounded-sm shadow-lg">
        <p className="text-white text-sm mb-1">{label}</p>
        <p className="text-[#a1a1aa] text-xs">开: {formatPrice(data.open)}</p>
        <p className="text-[#a1a1aa] text-xs">高: {formatPrice(data.high)}</p>
        <p className="text-[#a1a1aa] text-xs">低: {formatPrice(data.low)}</p>
        <p className="text-white text-xs font-bold">收: {formatPrice(data.close)}</p>
      </div>
    );
  }
  return null;
};

export default function StockDetailPage() {
  const { symbol } = useParams();
  const navigate = useNavigate();
  const decodedSymbol = decodeURIComponent(symbol);
  
  const [stockData, setStockData] = useState(null);
  const [historical, setHistorical] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('ai');
  
  // AI Prediction State
  const [aiTimePeriod, setAiTimePeriod] = useState('today');
  const [aiPrediction, setAiPrediction] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  
  // Divination State
  const [userName, setUserName] = useState('');
  const [divTimePeriod, setDivTimePeriod] = useState('today');
  const [divination, setDivination] = useState(null);
  const [divLoading, setDivLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await getStockDetail(decodedSymbol);
        setStockData(response.data.stock);
        setHistorical(response.data.historical || []);
      } catch (error) {
        console.error('Failed to fetch stock detail:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [decodedSymbol]);

  const handleAIPrediction = async () => {
    if (!stockData) return;
    setAiLoading(true);
    try {
      const response = await getAIPrediction({
        stock_code: stockData.symbol,
        stock_name: stockData.name,
        time_period: aiTimePeriod,
        market_data: {
          price: stockData.price,
          change: stockData.change,
          change_percent: stockData.change_percent,
          volume: stockData.volume
        }
      });
      setAiPrediction(response.data);
      
      // Save to history
      try {
        await savePredictionHistory({
          prediction_type: 'ai',
          stock_code: stockData.symbol,
          stock_name: stockData.name,
          time_period: aiTimePeriod,
          result: JSON.stringify(response.data)
        });
      } catch (e) {
        console.error('Failed to save history:', e);
      }
    } catch (error) {
      console.error('AI prediction failed:', error);
      toast.error('AI预测失败，请重试');
    } finally {
      setAiLoading(false);
    }
  };

  const handleDivination = async () => {
    if (!stockData || !userName.trim()) return;
    setDivLoading(true);
    try {
      const response = await getDivinationPrediction({
        user_name: userName,
        stock_code: stockData.symbol,
        stock_name: stockData.name,
        time_period: divTimePeriod
      });
      setDivination(response.data);
      
      // Save to history
      try {
        await savePredictionHistory({
          prediction_type: 'divination',
          stock_code: stockData.symbol,
          stock_name: stockData.name,
          time_period: divTimePeriod,
          user_name: userName,
          result: JSON.stringify(response.data)
        });
      } catch (e) {
        console.error('Failed to save history:', e);
      }
    } catch (error) {
      console.error('Divination failed:', error);
    } finally {
      setDivLoading(false);
    }
  };

  const isUp = stockData?.change >= 0;

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48 bg-[#1e2330]" />
        <Skeleton className="h-32 bg-[#1e2330]" />
        <Skeleton className="h-64 bg-[#1e2330]" />
      </div>
    );
  }

  if (!stockData) {
    return (
      <div className="text-center py-12">
        <p className="text-[#a1a1aa]">未找到股票数据</p>
        <Button onClick={() => navigate('/')} className="mt-4">返回首页</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="text-[#a1a1aa] hover:text-white"
          data-testid="back-btn"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          返回
        </Button>
      </div>

      {/* Stock Info */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-2xl md:text-3xl font-bold text-white">{stockData.name}</h1>
                <span className="text-[#a1a1aa] font-mono">{stockData.symbol}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className={`font-mono-price text-4xl font-bold ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                  {formatPrice(stockData.price)}
                </span>
                <div className="flex items-center gap-2">
                  <span className={`font-mono text-lg ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                    {formatChange(stockData.change)}
                  </span>
                  <span className={`font-mono text-lg ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                    ({formatChange(stockData.change_percent)}%)
                  </span>
                  {isUp ? (
                    <TrendingUp className="w-6 h-6 text-[#f5222d]" />
                  ) : (
                    <TrendingDown className="w-6 h-6 text-[#00b300]" />
                  )}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={async () => {
                  try {
                    await addToWatchlist(getClientId(), {
                      symbol: stockData.symbol,
                      name: stockData.name,
                      market_type: stockData.market_type,
                      added_at: new Date().toISOString()
                    });
                    toast.success(`已添加 ${stockData.name} 到自选股`);
                  } catch (error) {
                    if (error.response?.data?.message === 'Already in watchlist') {
                      toast.info('已在自选股中');
                    } else {
                      toast.error('添加失败');
                    }
                  }
                }}
                className="bg-transparent text-[#f0a500] border border-[#f0a500] hover:bg-[#f0a500]/10"
                data-testid="add-watchlist-btn"
              >
                <Heart className="w-4 h-4 mr-1" />
                自选
              </Button>
              <Button
                onClick={() => { setActiveTab('ai'); }}
                className={`${activeTab === 'ai' ? 'bg-[#00f0ff]/20 text-[#00f0ff] border-[#00f0ff]' : 'bg-transparent text-[#a1a1aa]'} border`}
                data-testid="tab-ai-btn"
              >
                <Sparkles className="w-4 h-4 mr-1" />
                AI预测
              </Button>
              <Button
                onClick={() => { setActiveTab('divination'); }}
                className={`${activeTab === 'divination' ? 'bg-[#ffd700]/20 text-[#ffd700] border-[#ffd700]' : 'bg-transparent text-[#a1a1aa]'} border`}
                data-testid="tab-divination-btn"
              >
                <Star className="w-4 h-4 mr-1" />
                占卜推演
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardHeader>
          <CardTitle className="text-white text-lg">历史走势</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 md:h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={historical.slice(-60)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2f3e" />
                <XAxis 
                  dataKey="date" 
                  stroke="#52525b" 
                  tick={{ fill: '#52525b', fontSize: 10 }}
                  tickFormatter={(value) => value.slice(5)}
                />
                <YAxis 
                  stroke="#52525b" 
                  tick={{ fill: '#52525b', fontSize: 10 }}
                  domain={['auto', 'auto']}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="close" 
                  fill={isUp ? 'rgba(245, 34, 45, 0.1)' : 'rgba(0, 179, 0, 0.1)'}
                  stroke="transparent"
                />
                <Line 
                  type="monotone" 
                  dataKey="close" 
                  stroke={isUp ? '#f5222d' : '#00b300'} 
                  strokeWidth={2}
                  dot={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Prediction Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Prediction Panel */}
        <Card className={`border transition-all ${activeTab === 'ai' ? 'bg-[#0a0e17] border-[#00f0ff]/50 ai-border' : 'bg-[#141824] border-[#2a2f3e]'}`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#00f0ff]" />
              <span className="text-white">AI智能预测</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Label className="text-[#a1a1aa] text-xs mb-1.5 block">预测时间段</Label>
                <Select value={aiTimePeriod} onValueChange={setAiTimePeriod}>
                  <SelectTrigger className="bg-[#141824] border-[#2a2f3e] text-white" data-testid="ai-time-select">
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
              <Button
                onClick={handleAIPrediction}
                disabled={aiLoading}
                className="bg-[#00f0ff] hover:bg-[#00f0ff]/80 text-black font-bold mt-auto"
                data-testid="ai-predict-btn"
              >
                {aiLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                    计算中...
                  </>
                ) : (
                  'AI预测'
                )}
              </Button>
            </div>

            {aiLoading && (
              <div className="flex flex-col items-center py-8">
                <div className="quantum-loading mb-4"></div>
                <p className="text-[#00f0ff] text-sm animate-pulse">量子计算中...</p>
              </div>
            )}

            {aiPrediction && !aiLoading && (
              <div className="space-y-4 animate-fade-in">
                {/* Direction Badge - Support both old and new format */}
                <div className="flex items-center justify-between">
                  <div className={`px-4 py-2 rounded-sm font-bold ${
                    (aiPrediction.direction || aiPrediction.executive_summary?.direction) === 'bullish' ? 'bg-[#f5222d]/20 text-[#f5222d]' :
                    (aiPrediction.direction || aiPrediction.executive_summary?.direction) === 'bearish' ? 'bg-[#00b300]/20 text-[#00b300]' :
                    'bg-[#8c8c8c]/20 text-[#8c8c8c]'
                  }`}>
                    {(aiPrediction.direction || aiPrediction.executive_summary?.direction) === 'bullish' ? '🔴 看涨' :
                     (aiPrediction.direction || aiPrediction.executive_summary?.direction) === 'bearish' ? '🟢 看跌' : '⚪ 中性'}
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-[#52525b]">置信度</span>
                    <div className="flex items-center gap-2">
                      <Progress value={parseInt(aiPrediction.confidence || aiPrediction.executive_summary?.confidence_level || '50')} className="w-24 h-2" />
                      <span className="text-[#00f0ff] font-mono font-bold">{aiPrediction.confidence || aiPrediction.executive_summary?.confidence_level || '50%'}</span>
                    </div>
                  </div>
                </div>

                {/* New Format: Executive Summary */}
                {aiPrediction.executive_summary && (
                  <div className="bg-[#00f0ff]/10 border border-[#00f0ff]/30 p-3 rounded-sm">
                    <span className="text-xs text-[#00f0ff] block mb-1">研报摘要</span>
                    <p className="text-white text-sm font-medium">{aiPrediction.executive_summary.headline}</p>
                    <p className="text-[#a1a1aa] text-xs mt-2">{aiPrediction.executive_summary.three_line_summary}</p>
                  </div>
                )}

                {/* Target Price Range - Support both formats */}
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">目标价区间</span>
                  <div className="flex items-center gap-2">
                    {aiPrediction.target_price_range ? (
                      <>
                        <span className="text-[#00b300] font-mono">{formatPrice(aiPrediction.target_price_range?.low)}</span>
                        <span className="text-[#52525b]">-</span>
                        <span className="text-[#f5222d] font-mono">{formatPrice(aiPrediction.target_price_range?.high)}</span>
                      </>
                    ) : aiPrediction.scenario_analysis ? (
                      <>
                        <span className="text-[#00b300] font-mono">{aiPrediction.scenario_analysis.bear_scenario?.target_levels || '--'}</span>
                        <span className="text-[#52525b]">~</span>
                        <span className="text-[#f5222d] font-mono">{aiPrediction.scenario_analysis.bull_scenario?.target_levels || '--'}</span>
                      </>
                    ) : (
                      <span className="text-[#a1a1aa]">--</span>
                    )}
                  </div>
                </div>

                {/* Support & Resistance - Support both formats */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#141824] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">支撑位</span>
                    <div className="space-y-1">
                      {aiPrediction.support_levels?.map((level, i) => (
                        <span key={i} className="text-[#00b300] font-mono text-sm block">{formatPrice(level)}</span>
                      )) || aiPrediction.technical_deep_dive?.key_levels?.critical_support?.map((level, i) => (
                        <span key={i} className="text-[#00b300] font-mono text-sm block">{level.price}</span>
                      )) || <span className="text-[#a1a1aa] text-sm">--</span>}
                    </div>
                  </div>
                  <div className="bg-[#141824] p-3 rounded-sm">
                    <span className="text-xs text-[#52525b] block mb-1">压力位</span>
                    <div className="space-y-1">
                      {aiPrediction.resistance_levels?.map((level, i) => (
                        <span key={i} className="text-[#f5222d] font-mono text-sm block">{formatPrice(level)}</span>
                      )) || aiPrediction.technical_deep_dive?.key_levels?.critical_resistance?.map((level, i) => (
                        <span key={i} className="text-[#f5222d] font-mono text-sm block">{level.price}</span>
                      )) || <span className="text-[#a1a1aa] text-sm">--</span>}
                    </div>
                  </div>
                </div>

                {/* Analysis - Support both formats */}
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">分析详情</span>
                  <p className="text-[#a1a1aa] text-sm">
                    {aiPrediction.analysis || aiPrediction.professional_narrative?.synthesis_paragraph || aiPrediction.market_structure_analysis?.phase_evidence || '暂无分析详情'}
                  </p>
                </div>

                {/* Suggestions - Support both formats */}
                <div className="bg-[#141824] p-3 rounded-sm">
                  <span className="text-xs text-[#52525b] block mb-1">操作建议</span>
                  <p className="text-white text-sm">
                    {aiPrediction.suggestions || aiPrediction.professional_narrative?.forward_guidance || aiPrediction.scenario_analysis?.base_case_summary || '暂无操作建议'}
                  </p>
                </div>

                {/* Risk Warning - Support both formats */}
                <div className="bg-[#f5222d]/10 border border-[#f5222d]/30 p-3 rounded-sm">
                  <span className="text-xs text-[#f5222d] block mb-1">⚠️ 风险提示</span>
                  <p className="text-[#a1a1aa] text-xs">
                    {aiPrediction.risk_warning || aiPrediction.disclaimer || aiPrediction.risk_assessment?.tail_risk_scenario || '投资有风险，入市需谨慎。本分析仅供参考，不构成投资建议。'}
                  </p>
                </div>

                <p className="text-xs text-[#52525b] text-center">
                  生成时间: {new Date(aiPrediction.timestamp || aiPrediction.report_meta?.generated_at || new Date()).toLocaleString('zh-CN')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Divination Panel */}
        <Card className={`border transition-all ${activeTab === 'divination' ? 'divination-bg border-[#ffd700]/50 gold-border' : 'bg-[#141824] border-[#2a2f3e]'}`}>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2">
              <Star className="w-5 h-5 text-[#ffd700]" />
              <span className="text-white font-divination">占卜推演</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div>
                <Label className="text-[#a1a1aa] text-xs mb-1.5 block font-divination">求问者姓名</Label>
                <Input
                  value={userName}
                  onChange={(e) => setUserName(e.target.value)}
                  placeholder="请输入您的姓名"
                  className="bg-[#1a0b2e] border-[#ffd700]/30 text-white placeholder:text-[#52525b] focus:border-[#ffd700]"
                  data-testid="divination-name-input"
                />
              </div>
              <div>
                <Label className="text-[#a1a1aa] text-xs mb-1.5 block font-divination">推演时间段</Label>
                <Select value={divTimePeriod} onValueChange={setDivTimePeriod}>
                  <SelectTrigger className="bg-[#1a0b2e] border-[#ffd700]/30 text-white" data-testid="divination-time-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1a0b2e] border-[#ffd700]/30">
                    {TIME_PERIODS.map(p => (
                      <SelectItem key={p.value} value={p.value} className="text-white hover:bg-[#2e1065]">
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button
                onClick={handleDivination}
                disabled={divLoading || !userName.trim()}
                className="w-full bg-transparent border border-[#ffd700] text-[#ffd700] hover:bg-[#ffd700]/20 font-divination shadow-[0_0_15px_rgba(255,215,0,0.3)] hover:shadow-[0_0_25px_rgba(255,215,0,0.6)] transition-all"
                data-testid="divination-btn"
              >
                {divLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    神谕降临中...
                  </>
                ) : (
                  '开始推演'
                )}
              </Button>
            </div>

            {divLoading && (
              <div className="flex flex-col items-center py-8 stars-bg">
                <div className="w-16 h-16 border-2 border-[#ffd700] rounded-full animate-star-rotate flex items-center justify-center">
                  <Star className="w-8 h-8 text-[#ffd700]" />
                </div>
                <p className="text-[#ffd700] text-sm mt-4 font-divination animate-pulse">星盘运转中...</p>
              </div>
            )}

            {divination && !divLoading && (
              <ScrollArea className="h-96 animate-fade-in">
                <div className="bg-[#1a0b2e] p-4 rounded-sm border border-[#ffd700]/20 stars-bg">
                  <div className="prose prose-sm prose-invert max-w-none">
                    <pre className="whitespace-pre-wrap text-[#a1a1aa] text-sm font-sans leading-relaxed">
                      {divination.report}
                    </pre>
                  </div>
                </div>
                <p className="text-xs text-[#52525b] text-center mt-4 font-divination">
                  推演时间: {new Date(divination.timestamp).toLocaleString('zh-CN')}
                </p>
              </ScrollArea>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Disclaimer */}
      <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center">
          ⚠️ 免责声明：本平台提供的所有预测内容（包括AI分析和占卜推演）均仅供参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
        </p>
      </div>
    </div>
  );
}
