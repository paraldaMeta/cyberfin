import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Search, Loader2, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { searchStocks, getDivinationPrediction } from '../services/api';

const TIME_PERIODS = [
  { value: 'today', label: '今日' },
  { value: 'week', label: '本周' },
  { value: 'month', label: '本月' },
  { value: 'quarter', label: '本季度' },
  { value: 'year', label: '本年' },
];

export default function DivinationPage() {
  const navigate = useNavigate();
  const [userName, setUserName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [selectedStock, setSelectedStock] = useState(null);
  const [timePeriod, setTimePeriod] = useState('today');
  const [divination, setDivination] = useState(null);
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
    setDivination(null);
  };

  const handleDivination = async () => {
    if (!selectedStock || !userName.trim()) return;
    setLoading(true);
    try {
      const response = await getDivinationPrediction({
        user_name: userName,
        stock_code: selectedStock.symbol,
        stock_name: selectedStock.name,
        time_period: timePeriod
      });
      setDivination(response.data);
    } catch (error) {
      console.error('Divination failed:', error);
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
      <div className="relative overflow-hidden rounded-md divination-bg border border-[#ffd700]/30 p-8 stars-bg">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(75,0,130,0.3)_0%,transparent_70%)]"></div>
        <div className="relative">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-[#ffd700]/20 flex items-center justify-center gold-border">
              <Star className="w-6 h-6 text-[#ffd700] animate-pulse" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-bold text-[#ffd700] font-divination gold-text">占卜推演</h1>
              <p className="text-sm text-[#a1a1aa] font-divination">Qaida Tarweehat 神谕系统</p>
            </div>
          </div>
          <p className="text-[#a1a1aa] text-sm max-w-xl font-divination">
            基于古老的 Ilm al-Jafar 知识体系，通过《Qaida Tarweehat（舒解法）》进行动态时序战略分析，
            为您揭示市场走势的神秘指引。
          </p>
        </div>
      </div>

      {/* Input Section */}
      <Card className="bg-[#1a0b2e] border-[#ffd700]/30">
        <CardHeader>
          <CardTitle className="text-[#ffd700] flex items-center gap-2 font-divination">
            <Star className="w-5 h-5" />
            开始推演
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* User Name */}
          <div>
            <Label className="text-[#a1a1aa] text-xs mb-1.5 block font-divination">求问者姓名 *</Label>
            <Input
              value={userName}
              onChange={(e) => setUserName(e.target.value)}
              placeholder="请输入您的姓名（必填）"
              className="bg-[#0a0e17] border-[#ffd700]/30 text-white placeholder:text-[#52525b] focus:border-[#ffd700]"
              data-testid="div-name-input"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Stock Search */}
            <div className="md:col-span-2 relative">
              <Label className="text-[#a1a1aa] text-xs mb-1.5 block font-divination">求问标的</Label>
              <Input
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowResults(true)}
                placeholder="搜索股票代码或名称..."
                className="bg-[#0a0e17] border-[#ffd700]/30 text-white placeholder:text-[#52525b] focus:border-[#ffd700]"
                data-testid="div-search-input"
              />
              {showResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-[#1a0b2e] border border-[#ffd700]/30 rounded-md shadow-lg max-h-60 overflow-auto z-50">
                  {searchResults.map((result) => (
                    <button
                      key={result.symbol}
                      onClick={() => handleSelectStock(result)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#2e1065] transition-colors text-left"
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
              <Label className="text-[#a1a1aa] text-xs mb-1.5 block font-divination">推演时间段</Label>
              <Select value={timePeriod} onValueChange={setTimePeriod}>
                <SelectTrigger className="bg-[#0a0e17] border-[#ffd700]/30 text-white" data-testid="div-period-select">
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
          </div>

          {/* Selected Stock Preview */}
          {selectedStock && (
            <div className="flex items-center justify-between p-3 bg-[#0a0e17] rounded-sm border border-[#ffd700]/20">
              <div>
                <span className="text-white">{selectedStock.name}</span>
                <span className="text-[#a1a1aa] text-sm ml-2 font-mono">{selectedStock.symbol}</span>
              </div>
              <span className="text-xs text-[#52525b]">{selectedStock.market_type}</span>
            </div>
          )}

          <Button
            onClick={handleDivination}
            disabled={loading || !selectedStock || !userName.trim()}
            className="w-full bg-transparent border-2 border-[#ffd700] text-[#ffd700] hover:bg-[#ffd700]/20 font-divination py-6 text-lg shadow-[0_0_20px_rgba(255,215,0,0.3)] hover:shadow-[0_0_30px_rgba(255,215,0,0.6)] transition-all"
            data-testid="div-submit-btn"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                神谕降临中...
              </>
            ) : (
              <>
                <Star className="w-5 h-5 mr-2" />
                开始推演
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Loading State */}
      {loading && (
        <Card className="bg-[#1a0b2e] border-[#ffd700]/30 stars-bg">
          <CardContent className="py-16">
            <div className="flex flex-col items-center">
              <div className="relative">
                <div className="w-24 h-24 border-2 border-[#ffd700]/50 rounded-full animate-star-rotate flex items-center justify-center">
                  <div className="w-16 h-16 border-2 border-[#ffd700] rounded-full animate-star-rotate flex items-center justify-center" style={{ animationDirection: 'reverse', animationDuration: '30s' }}>
                    <Star className="w-8 h-8 text-[#ffd700]" />
                  </div>
                </div>
              </div>
              <p className="text-[#ffd700] text-lg mt-6 font-divination gold-text animate-pulse">星盘运转中...</p>
              <p className="text-[#52525b] text-sm mt-2 font-divination">正在通过 Qaida Tarweehat 推演神谕</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Divination Result */}
      {divination && !loading && (
        <Card className="bg-[#1a0b2e] border-[#ffd700]/30 animate-fade-in stars-bg">
          <CardHeader>
            <CardTitle className="text-[#ffd700] flex items-center gap-2 font-divination">
              <Star className="w-5 h-5" />
              动态时序战略报告
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[600px]">
              <div className="bg-[#0a0e17]/80 p-6 rounded-sm border border-[#ffd700]/20">
                <pre className="whitespace-pre-wrap text-[#a1a1aa] text-sm leading-relaxed font-sans">
                  {divination.report}
                </pre>
              </div>
            </ScrollArea>
            <p className="text-xs text-[#52525b] text-center mt-4 font-divination">
              推演时间: {new Date(divination.timestamp).toLocaleString('zh-CN')}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Disclaimer */}
      <div className="bg-[#1a0b2e] border border-[#ffd700]/20 rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center font-divination">
          ⚠️ 免责声明：本占卜仅为娱乐参考，不构成任何投资建议。投资有风险，入市须谨慎。
          本推演基于古老的 Ilm al-Jafar 知识体系，结果仅供参考研究。
        </p>
      </div>
    </div>
  );
}
