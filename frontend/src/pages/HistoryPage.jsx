import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Sparkles, Star, Trash2, Filter, ChevronDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { ScrollArea } from '../components/ui/scroll-area';
import { toast } from 'sonner';
import { getPredictionHistory, deletePredictionHistory } from '../services/api';

const TIME_LABELS = {
  today: '今日',
  week: '本周',
  month: '本月',
  quarter: '本季度',
  year: '本年'
};

export default function HistoryPage() {
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, ai, divination

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      const params = filter !== 'all' ? { prediction_type: filter } : {};
      const response = await getPredictionHistory(params);
      setHistory(response.data.history || []);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleDelete = async (historyId) => {
    try {
      await deletePredictionHistory(historyId);
      toast.success('已删除');
      fetchHistory();
    } catch (error) {
      toast.error('删除失败');
    }
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white font-market flex items-center gap-2">
            <History className="w-7 h-7 text-[#f0a500]" />
            预测历史
          </h1>
          <p className="text-sm text-[#a1a1aa] mt-1">最近3个月的预测记录</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger className="w-32 bg-[#141824] border-[#2a2f3e] text-white" data-testid="history-filter">
              <Filter className="w-4 h-4 mr-1" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-[#141824] border-[#2a2f3e]">
              <SelectItem value="all" className="text-white hover:bg-[#1e2330]">全部</SelectItem>
              <SelectItem value="ai" className="text-white hover:bg-[#1e2330]">AI预测</SelectItem>
              <SelectItem value="divination" className="text-white hover:bg-[#1e2330]">占卜推演</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* History List */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardHeader>
          <CardTitle className="text-white text-lg">历史记录 ({history.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-24 bg-[#1e2330]" />
              ))}
            </div>
          ) : history.length === 0 ? (
            <div className="text-center py-12">
              <History className="w-12 h-12 text-[#52525b] mx-auto mb-4" />
              <p className="text-[#a1a1aa]">暂无预测记录</p>
              <p className="text-sm text-[#52525b] mt-2">开始使用AI预测或占卜推演后，记录将显示在这里</p>
            </div>
          ) : (
            <ScrollArea className="h-[600px]">
              <div className="space-y-3">
                {history.map((item) => (
                  <div
                    key={item.id}
                    className={`p-4 rounded-sm border transition-colors group ${
                      item.prediction_type === 'ai' 
                        ? 'bg-[#0a0e17] border-[#00f0ff]/20 hover:border-[#00f0ff]/50' 
                        : 'bg-[#1a0b2e]/50 border-[#ffd700]/20 hover:border-[#ffd700]/50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        {item.prediction_type === 'ai' ? (
                          <div className="w-10 h-10 rounded-full bg-[#00f0ff]/20 flex items-center justify-center">
                            <Sparkles className="w-5 h-5 text-[#00f0ff]" />
                          </div>
                        ) : (
                          <div className="w-10 h-10 rounded-full bg-[#ffd700]/20 flex items-center justify-center">
                            <Star className="w-5 h-5 text-[#ffd700]" />
                          </div>
                        )}
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-white font-medium">{item.stock_name}</span>
                            <span className="text-[#52525b] text-xs font-mono">{item.stock_code}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              item.prediction_type === 'ai' 
                                ? 'bg-[#00f0ff]/20 text-[#00f0ff]' 
                                : 'bg-[#ffd700]/20 text-[#ffd700]'
                            }`}>
                              {item.prediction_type === 'ai' ? 'AI预测' : '占卜推演'}
                            </span>
                            <span className="text-xs text-[#52525b]">
                              {TIME_LABELS[item.time_period] || item.time_period}
                            </span>
                            {item.user_name && (
                              <span className="text-xs text-[#52525b]">
                                求问者: {item.user_name}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-[#52525b]">{formatDate(item.created_at)}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(item.id)}
                          className="opacity-0 group-hover:opacity-100 text-[#f5222d] hover:text-[#f5222d] hover:bg-[#f5222d]/10"
                          data-testid={`delete-${item.id}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Preview of result */}
                    {item.prediction_type === 'ai' && item.result && (
                      <div className="mt-3 pt-3 border-t border-[#2a2f3e]">
                        <div className="flex items-center gap-4">
                          <span className={`px-2 py-1 rounded text-sm font-medium ${
                            item.result.direction === 'bullish' ? 'bg-[#f5222d]/20 text-[#f5222d]' :
                            item.result.direction === 'bearish' ? 'bg-[#00b300]/20 text-[#00b300]' :
                            'bg-[#8c8c8c]/20 text-[#8c8c8c]'
                          }`}>
                            {item.result.direction === 'bullish' ? '看涨' :
                             item.result.direction === 'bearish' ? '看跌' : '中性'}
                          </span>
                          <span className="text-sm text-[#a1a1aa]">
                            置信度: <span className="text-[#00f0ff] font-mono">{item.result.confidence}%</span>
                          </span>
                        </div>
                      </div>
                    )}
                    
                    {item.prediction_type === 'divination' && item.result && (
                      <div className="mt-3 pt-3 border-t border-[#ffd700]/20">
                        <p className="text-sm text-[#a1a1aa] line-clamp-2">
                          {item.result.report?.substring(0, 150)}...
                        </p>
                      </div>
                    )}
                    
                    {/* View Detail Button */}
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => navigate(`/stock/${encodeURIComponent(item.stock_code)}`)}
                      className="mt-3 text-[#a1a1aa] hover:text-white"
                    >
                      查看详情
                      <ChevronDown className="w-4 h-4 ml-1 rotate-[-90deg]" />
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          )}
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center">
          ⚠️ 预测记录仅保留最近3个月。历史预测仅供参考，不构成任何投资建议。
        </p>
      </div>
    </div>
  );
}
