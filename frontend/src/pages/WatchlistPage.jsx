import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, TrendingUp, TrendingDown, Trash2, Plus, Search, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Skeleton } from '../components/ui/skeleton';
import { toast } from 'sonner';
import { getWatchlistWithData, addToWatchlist, removeFromWatchlist, searchStocks } from '../services/api';

// Get or create client ID for watchlist
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

export default function WatchlistPage() {
  const navigate = useNavigate();
  const [watchlist, setWatchlist] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showSearch, setShowSearch] = useState(false);
  const clientId = getClientId();

  const fetchWatchlist = useCallback(async () => {
    try {
      setRefreshing(true);
      const response = await getWatchlistWithData(clientId);
      setWatchlist(response.data.watchlist || []);
    } catch (error) {
      console.error('Failed to fetch watchlist:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [clientId]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const handleSearch = useCallback(async (query) => {
    setSearchQuery(query);
    if (query.length >= 1) {
      try {
        const response = await searchStocks(query);
        setSearchResults(response.data.results || []);
      } catch (error) {
        console.error('Search error:', error);
        setSearchResults([]);
      }
    } else {
      setSearchResults([]);
    }
  }, []);

  const handleAddStock = async (stock) => {
    try {
      await addToWatchlist(clientId, {
        symbol: stock.symbol,
        name: stock.name,
        market_type: stock.market_type,
        added_at: new Date().toISOString()
      });
      toast.success(`已添加 ${stock.name} 到自选股`);
      setSearchQuery('');
      setSearchResults([]);
      setShowSearch(false);
      fetchWatchlist();
    } catch (error) {
      toast.error('添加失败');
    }
  };

  const handleRemoveStock = async (symbol, name) => {
    try {
      await removeFromWatchlist(clientId, symbol);
      toast.success(`已移除 ${name}`);
      fetchWatchlist();
    } catch (error) {
      toast.error('移除失败');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white font-market flex items-center gap-2">
            <Star className="w-7 h-7 text-[#f0a500]" />
            我的自选股
          </h1>
          <p className="text-sm text-[#a1a1aa] mt-1">关注的股票实时行情</p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSearch(!showSearch)}
            className="border-[#f0a500] text-[#f0a500] hover:bg-[#f0a500]/10"
            data-testid="add-stock-btn"
          >
            <Plus className="w-4 h-4 mr-1" />
            添加
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchWatchlist}
            disabled={refreshing}
            className="border-[#2a2f3e] hover:border-[#f0a500] text-[#a1a1aa]"
            data-testid="refresh-watchlist-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>
      </div>

      {/* Search Section */}
      {showSearch && (
        <Card className="bg-[#141824] border-[#2a2f3e] animate-fade-in">
          <CardContent className="p-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525b]" />
              <Input
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="搜索股票代码或名称添加到自选..."
                className="pl-10 bg-[#0a0e17] border-[#2a2f3e] text-white placeholder:text-[#52525b] focus:border-[#f0a500]"
                data-testid="watchlist-search-input"
              />
            </div>
            {searchResults.length > 0 && (
              <div className="mt-2 max-h-60 overflow-auto">
                {searchResults.map((result) => (
                  <div
                    key={result.symbol}
                    className="flex items-center justify-between p-3 hover:bg-[#1e2330] rounded-sm cursor-pointer"
                    onClick={() => handleAddStock(result)}
                  >
                    <div>
                      <span className="text-white font-mono text-sm">{result.symbol}</span>
                      <span className="text-[#a1a1aa] ml-2 text-sm">{result.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[#52525b]">{result.market_type}</span>
                      <Plus className="w-4 h-4 text-[#f0a500]" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Watchlist */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardHeader>
          <CardTitle className="text-white text-lg">自选列表 ({watchlist.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map(i => (
                <Skeleton key={i} className="h-16 bg-[#1e2330]" />
              ))}
            </div>
          ) : watchlist.length === 0 ? (
            <div className="text-center py-12">
              <Star className="w-12 h-12 text-[#52525b] mx-auto mb-4" />
              <p className="text-[#a1a1aa]">暂无自选股</p>
              <p className="text-sm text-[#52525b] mt-2">点击上方"添加"按钮添加关注的股票</p>
            </div>
          ) : (
            <div className="space-y-2">
              {watchlist.map((stock) => {
                const isUp = stock.change >= 0;
                return (
                  <div
                    key={stock.symbol}
                    className="flex items-center justify-between p-4 bg-[#0a0e17] rounded-sm hover:bg-[#1e2330] transition-colors group"
                  >
                    <div 
                      className="flex-1 cursor-pointer"
                      onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                    >
                      <div className="flex items-center gap-3">
                        <Star className="w-4 h-4 text-[#f0a500]" />
                        <div>
                          <span className="text-white">{stock.name}</span>
                          <span className="text-[#52525b] text-xs ml-2 font-mono">{stock.symbol}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-6">
                      <div className="text-right">
                        <div className={`font-mono-price text-lg font-bold ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                          {formatPrice(stock.price)}
                        </div>
                        <div className={`text-sm font-mono ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
                          {formatChange(stock.change)} ({formatChange(stock.change_percent)}%)
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {isUp ? (
                          <TrendingUp className="w-5 h-5 text-[#f5222d]" />
                        ) : (
                          <TrendingDown className="w-5 h-5 text-[#00b300]" />
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRemoveStock(stock.symbol, stock.name);
                          }}
                          className="opacity-0 group-hover:opacity-100 text-[#f5222d] hover:text-[#f5222d] hover:bg-[#f5222d]/10"
                          data-testid={`remove-${stock.symbol}`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
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
