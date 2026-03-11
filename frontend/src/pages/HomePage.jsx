import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { TrendingUp, TrendingDown, RefreshCw, ChevronRight, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { getMarketOverview } from '../services/api';
import FinancialNews from '../components/FinancialNews';
import TianjiPanel from '../components/TianjiPanel';
import { useLanguage } from '../i18n';

// Format number with commas and sign
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

const StockCard = ({ stock, onClick }) => {
  const isUp = stock.change >= 0;
  
  return (
    <div 
      onClick={onClick}
      className="market-card p-3 cursor-pointer group"
      data-testid={`stock-card-${stock.symbol}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs text-[#a1a1aa]">{stock.symbol}</span>
        <span className="text-xs text-[#52525b]">{stock.market_type}</span>
      </div>
      <div className="text-sm text-white mb-1 truncate">{stock.name}</div>
      <div className={`font-mono-price text-xl font-bold ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
        {formatPrice(stock.price)}
      </div>
      <div className="flex items-center gap-2 mt-1">
        <span className={`text-sm font-mono ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
          {formatChange(stock.change)}
        </span>
        <span className={`text-sm font-mono ${isUp ? 'text-[#f5222d]' : 'text-[#00b300]'}`}>
          ({formatChange(stock.change_percent)}%)
        </span>
        {isUp ? (
          <TrendingUp className="w-4 h-4 text-[#f5222d]" />
        ) : (
          <TrendingDown className="w-4 h-4 text-[#00b300]" />
        )}
      </div>
    </div>
  );
};

export default function HomePage() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  
  const MARKETS = [
    { id: 'a_stock', name: t('market.a_stock'), icon: '🇨🇳' },
    { id: 'us_stock', name: t('market.us_stock'), icon: '🇺🇸' },
    { id: 'hk_stock', name: t('market.hk_stock'), icon: '🇭🇰' },
    { id: 'jp_stock', name: t('market.jp_stock'), icon: '🇯🇵' },
    { id: 'kr_stock', name: t('market.kr_stock'), icon: '🇰🇷' },
    { id: 'th_stock', name: t('market.th_stock'), icon: '🇹🇭' },
    { id: 'uae_stock', name: t('market.uae_stock') || '阿联酋股', icon: '🇦🇪' },
    { id: 'futures', name: t('market.futures'), icon: '📊' },
    { id: 'forex', name: t('market.forex'), icon: '💱' },
  ];
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [countdown, setCountdown] = useState(60);
  const [refreshing, setRefreshing] = useState(false);

  const fetchOverview = async () => {
    try {
      setRefreshing(true);
      const response = await getMarketOverview();
      setOverview(response.data);
      setCountdown(60);
    } catch (error) {
      console.error('Failed to fetch overview:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOverview();
    
    // Countdown timer
    const timer = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          fetchOverview();
          return 60;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-white font-market">{t('home.market_overview')}</h1>
          <p className="text-sm text-[#a1a1aa] mt-1">{t('home.subtitle')}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-[#52525b]">
            {countdown}s {t('common.refresh')}
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={fetchOverview}
            disabled={refreshing}
            className="border-[#2a2f3e] hover:border-[#f0a500] text-[#a1a1aa]"
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            {t('common.refresh')}
          </Button>
        </div>
      </div>

      {/* Market Categories Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-2">
        {MARKETS.map((market) => (
          <Card 
            key={market.id}
            className="bg-[#141824] border-[#2a2f3e] hover:border-[#f0a500] cursor-pointer transition-colors"
            onClick={() => navigate(`/market/${market.id}`)}
            data-testid={`market-card-${market.id}`}
          >
            <CardContent className="p-3 text-center">
              <span className="text-2xl mb-1 block">{market.icon}</span>
              <span className="text-sm text-white font-medium">{market.name}</span>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 今日天机板块 */}
      <TianjiPanel />

      {/* Top Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Gainers */}
        <Card className="bg-[#141824] border-[#2a2f3e]">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingUp className="w-5 h-5 text-[#f5222d]" />
              <span className="text-white">{t('home.top_gainers')}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(i => (
                  <Skeleton key={i} className="h-16 bg-[#1e2330]" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {overview?.gainers?.map((stock, index) => (
                  <div
                    key={stock.symbol}
                    onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                    className="flex items-center justify-between p-3 bg-[#0a0e17] rounded-sm cursor-pointer hover:bg-[#1e2330] transition-colors"
                    data-testid={`gainer-${index}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[#f0a500] font-bold w-6">{index + 1}</span>
                      <div>
                        <div className="text-white text-sm">{stock.name}</div>
                        <div className="text-[#52525b] text-xs font-mono">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono-price text-[#f5222d] font-bold">{formatPrice(stock.price)}</div>
                      <div className="text-[#f5222d] text-sm font-mono">{formatChange(stock.change_percent)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Losers */}
        <Card className="bg-[#141824] border-[#2a2f3e]">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <TrendingDown className="w-5 h-5 text-[#00b300]" />
              <span className="text-white">{t('home.top_losers')}</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map(i => (
                  <Skeleton key={i} className="h-16 bg-[#1e2330]" />
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {overview?.losers?.map((stock, index) => (
                  <div
                    key={stock.symbol}
                    onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                    className="flex items-center justify-between p-3 bg-[#0a0e17] rounded-sm cursor-pointer hover:bg-[#1e2330] transition-colors"
                    data-testid={`loser-${index}`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-[#f0a500] font-bold w-6">{index + 1}</span>
                      <div>
                        <div className="text-white text-sm">{stock.name}</div>
                        <div className="text-[#52525b] text-xs font-mono">{stock.symbol}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono-price text-[#00b300] font-bold">{formatPrice(stock.price)}</div>
                      <div className="text-[#00b300] text-sm font-mono">{formatChange(stock.change_percent)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* News + All Stocks Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* All Stocks Ticker */}
        <div className="lg:col-span-2">
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Activity className="w-5 h-5 text-[#f0a500]" />
                <span className="text-white">{t('home.market_overview')}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {[1, 2, 3, 4, 5, 6].map(i => (
                    <Skeleton key={i} className="h-24 bg-[#1e2330]" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {overview?.all?.slice(0, 12).map((stock) => (
                    <StockCard
                      key={stock.symbol}
                      stock={stock}
                      onClick={() => navigate(`/stock/${encodeURIComponent(stock.symbol)}`)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
        
        {/* Financial News */}
        <div className="lg:col-span-1">
          <FinancialNews limit={8} />
        </div>
      </div>

      {/* Disclaimer */}
      <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
        <p className="text-xs text-[#52525b] text-center">
          {t('common.disclaimer')}
        </p>
      </div>
    </div>
  );
}
