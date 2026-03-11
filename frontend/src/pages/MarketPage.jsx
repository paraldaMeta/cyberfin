import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, RefreshCw, ArrowLeft } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { getMarketStocks } from '../services/api';

const MARKET_NAMES = {
  'a_stock': { name: 'A股', icon: '🇨🇳', description: '中国A股市场' },
  'hk_stock': { name: '港股', icon: '🇭🇰', description: '香港股票市场' },
  'jp_stock': { name: '日股', icon: '🇯🇵', description: '日本股票市场' },
  'kr_stock': { name: '韩股', icon: '🇰🇷', description: '韩国股票市场' },
  'th_stock': { name: '泰股', icon: '🇹🇭', description: '泰国股票市场' },
  'futures': { name: '期货', icon: '📊', description: '商品期货市场' },
  'forex': { name: '外汇', icon: '💱', description: '外汇市场' },
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

const formatVolume = (value) => {
  if (!value) return '--';
  if (value >= 1000000000) return (value / 1000000000).toFixed(2) + 'B';
  if (value >= 1000000) return (value / 1000000).toFixed(2) + 'M';
  if (value >= 1000) return (value / 1000).toFixed(2) + 'K';
  return value.toString();
};

export default function MarketPage() {
  const { type } = useParams();
  const navigate = useNavigate();
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [countdown, setCountdown] = useState(60);
  const [sortConfig, setSortConfig] = useState({ key: 'change_percent', direction: 'desc' });

  const marketInfo = MARKET_NAMES[type] || { name: type, icon: '📈', description: '' };

  const fetchStocks = async () => {
    try {
      setRefreshing(true);
      const response = await getMarketStocks(type);
      setStocks(response.data.stocks || []);
      setCountdown(60);
    } catch (error) {
      console.error('Failed to fetch stocks:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchStocks();
    
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          fetchStocks();
          return 60;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [type]);

  const sortedStocks = [...stocks].sort((a, b) => {
    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];
    if (sortConfig.direction === 'asc') {
      return aValue > bValue ? 1 : -1;
    }
    return aValue < bValue ? 1 : -1;
  });

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
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
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">{marketInfo.icon}</span>
              <h1 className="text-2xl md:text-3xl font-bold text-white font-market">{marketInfo.name}</h1>
            </div>
            <p className="text-sm text-[#a1a1aa] mt-1">{marketInfo.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[#52525b]">
            {countdown}s 后刷新
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchStocks}
            disabled={refreshing}
            className="border-[#2a2f3e] hover:border-[#f0a500] text-[#a1a1aa]"
            data-testid="refresh-market-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Stocks Table */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4 space-y-3">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(i => (
                <Skeleton key={i} className="h-12 bg-[#1e2330]" />
              ))}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="border-[#2a2f3e] hover:bg-transparent">
                    <TableHead className="text-[#a1a1aa] font-medium">代码</TableHead>
                    <TableHead className="text-[#a1a1aa] font-medium">名称</TableHead>
                    <TableHead 
                      className="text-[#a1a1aa] font-medium text-right cursor-pointer hover:text-white"
                      onClick={() => handleSort('price')}
                    >
                      最新价 {sortConfig.key === 'price' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                    </TableHead>
                    <TableHead 
                      className="text-[#a1a1aa] font-medium text-right cursor-pointer hover:text-white"
                      onClick={() => handleSort('change')}
                    >
                      涨跌额 {sortConfig.key === 'change' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                    </TableHead>
                    <TableHead 
                      className="text-[#a1a1aa] font-medium text-right cursor-pointer hover:text-white"
                      onClick={() => handleSort('change_percent')}
                    >
                      涨跌幅 {sortConfig.key === 'change_percent' && (sortConfig.direction === 'desc' ? '↓' : '↑')}
                    </TableHead>
                    <TableHead className="text-[#a1a1aa] font-medium text-right">成交量</TableHead>
                    <TableHead className="text-[#a1a1aa] font-medium text-center">趋势</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedStocks.map((stock) => {
                    const isUp = stock.change >= 0;
                    return (
                      <TableRow
                        key={stock.symbol}
                        onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                        className="border-[#2a2f3e] cursor-pointer hover:bg-[#1e2330] transition-colors"
                        data-testid={`stock-row-${stock.symbol}`}
                      >
                        <TableCell className="font-mono text-sm text-[#a1a1aa]">{stock.symbol}</TableCell>
                        <TableCell className="text-white">{stock.name}</TableCell>
                        <TableCell className={`text-right font-mono-price font-bold ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                          {formatPrice(stock.price)}
                        </TableCell>
                        <TableCell className={`text-right font-mono ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                          {formatChange(stock.change)}
                        </TableCell>
                        <TableCell className={`text-right font-mono ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                          {formatChange(stock.change_percent)}%
                        </TableCell>
                        <TableCell className="text-right font-mono text-[#a1a1aa]">
                          {formatVolume(stock.volume)}
                        </TableCell>
                        <TableCell className="text-center">
                          {isUp ? (
                            <TrendingUp className="w-4 h-4 text-[#f5222d] inline" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-[#00b300] inline" />
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Disclaimer */}
      <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center">
          ⚠️ 数据仅供参考，不构成任何投资建议。投资有风险，入市须谨慎。
        </p>
      </div>
    </div>
  );
}
