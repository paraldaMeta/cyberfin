import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  TrendingUp, 
  BarChart3, 
  Globe2, 
  Sparkles, 
  Star,
  Menu,
  X,
  ChevronRight,
  History,
  Heart
} from 'lucide-react';
import { Input } from './ui/input';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { searchStocks } from '../services/api';

const MARKETS = [
  { id: 'a_stock', name: 'A股', icon: '🇨🇳' },
  { id: 'us_stock', name: '美股', icon: '🇺🇸' },
  { id: 'hk_stock', name: '港股', icon: '🇭🇰' },
  { id: 'jp_stock', name: '日股', icon: '🇯🇵' },
  { id: 'kr_stock', name: '韩股', icon: '🇰🇷' },
  { id: 'th_stock', name: '泰股', icon: '🇹🇭' },
  { id: 'futures', name: '期货', icon: '📊' },
  { id: 'forex', name: '外汇', icon: '💱' },
];

export default function Layout({ children }) {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  const handleSelectStock = (symbol) => {
    navigate(`/stock/${encodeURIComponent(symbol)}`);
    setSearchQuery('');
    setShowResults(false);
  };

  return (
    <div className="flex min-h-screen bg-[#0a0e17]">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-[#141824] border-r border-[#2a2f3e] transform transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div 
            className="p-4 border-b border-[#2a2f3e] cursor-pointer"
            onClick={() => { navigate('/'); setSidebarOpen(false); }}
            data-testid="sidebar-logo"
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-[#f0a500]" />
              <div>
                <h1 className="text-lg font-bold text-white font-market">亚洲金融预测</h1>
                <p className="text-xs text-[#a1a1aa]">Intelligent Prediction</p>
              </div>
            </div>
          </div>

          {/* Market Categories */}
          <ScrollArea className="flex-1 py-4">
            <div className="px-3 mb-4">
              <h2 className="text-xs uppercase tracking-wider text-[#52525b] mb-2 px-2">市场分类</h2>
              {MARKETS.map((market) => (
                <button
                  key={market.id}
                  onClick={() => { navigate(`/market/${market.id}`); setSidebarOpen(false); }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-left hover:bg-[#1e2330] transition-colors group"
                  data-testid={`market-${market.id}`}
                >
                  <span className="text-lg">{market.icon}</span>
                  <span className="text-sm text-[#a1a1aa] group-hover:text-white transition-colors">{market.name}</span>
                  <ChevronRight className="w-4 h-4 text-[#52525b] ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>
              ))}
            </div>

            <div className="px-3 mb-4">
              <h2 className="text-xs uppercase tracking-wider text-[#52525b] mb-2 px-2">智能预测</h2>
              <button
                onClick={() => { navigate('/predict/ai'); setSidebarOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-left hover:bg-[#1e2330] transition-colors group"
                data-testid="nav-ai-predict"
              >
                <Sparkles className="w-5 h-5 text-[#00f0ff]" />
                <span className="text-sm text-[#a1a1aa] group-hover:text-white transition-colors">AI智能预测</span>
              </button>
              <button
                onClick={() => { navigate('/predict/divination'); setSidebarOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-left hover:bg-[#1e2330] transition-colors group"
                data-testid="nav-divination"
              >
                <Star className="w-5 h-5 text-[#ffd700]" />
                <span className="text-sm text-[#a1a1aa] group-hover:text-white transition-colors">占卜推演</span>
              </button>
            </div>

            <div className="px-3 mb-4">
              <h2 className="text-xs uppercase tracking-wider text-[#52525b] mb-2 px-2">我的</h2>
              <button
                onClick={() => { navigate('/watchlist'); setSidebarOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-left hover:bg-[#1e2330] transition-colors group"
                data-testid="nav-watchlist"
              >
                <Heart className="w-5 h-5 text-[#f0a500]" />
                <span className="text-sm text-[#a1a1aa] group-hover:text-white transition-colors">自选股</span>
              </button>
              <button
                onClick={() => { navigate('/history'); setSidebarOpen(false); }}
                className="w-full flex items-center gap-3 px-3 py-2.5 rounded-sm text-left hover:bg-[#1e2330] transition-colors group"
                data-testid="nav-history"
              >
                <History className="w-5 h-5 text-[#a1a1aa]" />
                <span className="text-sm text-[#a1a1aa] group-hover:text-white transition-colors">预测历史</span>
              </button>
            </div>
          </ScrollArea>

          {/* Footer */}
          <div className="p-4 border-t border-[#2a2f3e]">
            <p className="text-xs text-[#52525b] text-center">
              仅供参考 · 不构成投资建议
            </p>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Top Navigation */}
        <header className="sticky top-0 z-30 bg-[#0a0e17]/95 backdrop-blur-sm border-b border-[#2a2f3e]">
          <div className="flex items-center justify-between px-4 py-3">
            {/* Mobile menu button */}
            <button
              className="lg:hidden p-2 text-[#a1a1aa] hover:text-white"
              onClick={() => setSidebarOpen(!sidebarOpen)}
              data-testid="mobile-menu-btn"
            >
              {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>

            {/* Search */}
            <div className="relative flex-1 max-w-xl mx-4">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#52525b]" />
              <Input
                type="text"
                placeholder="搜索股票代码或名称..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                onFocus={() => searchResults.length > 0 && setShowResults(true)}
                onBlur={() => setTimeout(() => setShowResults(false), 200)}
                className="pl-10 bg-[#141824] border-[#2a2f3e] text-white placeholder:text-[#52525b] focus:border-[#f0a500]"
                data-testid="search-input"
              />
              
              {/* Search Results Dropdown */}
              {showResults && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-[#141824] border border-[#2a2f3e] rounded-md shadow-lg max-h-80 overflow-auto z-50">
                  {searchResults.map((result) => (
                    <button
                      key={result.symbol}
                      onClick={() => handleSelectStock(result.symbol)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-[#1e2330] transition-colors text-left"
                      data-testid={`search-result-${result.symbol}`}
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

            {/* Quick Actions */}
            <div className="hidden md:flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/predict/ai')}
                className="text-[#00f0ff] hover:text-[#00f0ff] hover:bg-[#00f0ff]/10"
                data-testid="header-ai-btn"
              >
                <Sparkles className="w-4 h-4 mr-1" />
                AI预测
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/predict/divination')}
                className="text-[#ffd700] hover:text-[#ffd700] hover:bg-[#ffd700]/10"
                data-testid="header-divination-btn"
              >
                <Star className="w-4 h-4 mr-1" />
                占卜
              </Button>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-4 md:p-6">
          {children}
        </main>

        {/* Status Bar */}
        <footer className="sticky bottom-0 bg-[#141824] border-t border-[#2a2f3e] px-4 py-2 flex items-center justify-between text-xs">
          <div className="flex items-center gap-4">
            <span className="text-[#52525b]">
              {new Date().toLocaleString('zh-CN', { 
                year: 'numeric', 
                month: '2-digit', 
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              })}
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#00b300] animate-pulse"></span>
              <span className="text-[#a1a1aa]">实时连接</span>
            </span>
          </div>
          <span className="text-[#52525b]">数据来源: Yahoo Finance</span>
        </footer>
      </div>
    </div>
  );
}
