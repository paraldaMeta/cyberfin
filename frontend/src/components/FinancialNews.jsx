/**
 * Financial News Component
 * Displays financial news from various sources
 */
import { useState, useEffect } from 'react';
import { Newspaper, ExternalLink, RefreshCw, Globe, Clock } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Skeleton } from './ui/skeleton';
import { ScrollArea } from './ui/scroll-area';
import { getFinancialNews } from '../services/api';
import { useLanguage } from '../i18n';

// Region flag mapping
const REGION_FLAGS = {
  'China': '🇨🇳',
  'Japan': '🇯🇵',
  'Hong Kong': '🇭🇰',
  'Korea': '🇰🇷',
  'Thailand': '🇹🇭',
  'Asia': '🌏',
  'Forex': '💱',
  'Commodities': '📊',
  'Market Update': '📈',
};

// Format date
const formatDate = (dateStr) => {
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

const NewsItem = ({ news }) => {
  const flag = REGION_FLAGS[news.region] || '📰';
  
  return (
    <a
      href={news.url !== '#' ? news.url : undefined}
      target="_blank"
      rel="noopener noreferrer"
      className={`block p-3 bg-[#0a0e17] rounded-sm hover:bg-[#1e2330] transition-colors ${news.url !== '#' ? 'cursor-pointer' : 'cursor-default'}`}
      data-testid={`news-item`}
    >
      <div className="flex items-start gap-3">
        <span className="text-lg mt-0.5">{flag}</span>
        <div className="flex-1 min-w-0">
          <h4 className="text-white text-sm leading-relaxed line-clamp-2 group-hover:text-[#00f0ff]">
            {news.title}
          </h4>
          <div className="flex items-center gap-2 mt-2 text-xs text-[#52525b]">
            <span className="flex items-center gap-1">
              <Globe className="w-3 h-3" />
              {news.region}
            </span>
            <span>|</span>
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDate(news.published)}
            </span>
            {news.url !== '#' && (
              <>
                <span>|</span>
                <ExternalLink className="w-3 h-3" />
              </>
            )}
          </div>
        </div>
      </div>
    </a>
  );
};

export default function FinancialNews({ limit = 8 }) {
  const { t } = useLanguage();
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchNews = async () => {
    try {
      setRefreshing(true);
      const response = await getFinancialNews(limit);
      setNews(response.data.news || []);
    } catch (error) {
      console.error('Failed to fetch news:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNews();
    // Refresh news every 5 minutes
    const interval = setInterval(fetchNews, 300000);
    return () => clearInterval(interval);
  }, [limit]);

  return (
    <Card className="bg-[#141824] border-[#2a2f3e]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Newspaper className="w-5 h-5 text-[#f0a500]" />
            <span className="text-white">{t('home.news')}</span>
          </CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchNews}
            disabled={refreshing}
            className="text-[#52525b] hover:text-white"
            data-testid="refresh-news-btn"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map(i => (
              <Skeleton key={i} className="h-16 bg-[#1e2330]" />
            ))}
          </div>
        ) : news.length === 0 ? (
          <div className="text-center py-8 text-[#52525b]">
            暂无新闻
          </div>
        ) : (
          <ScrollArea className="h-[400px]">
            <div className="space-y-2 pr-2">
              {news.map((item, index) => (
                <NewsItem key={index} news={item} />
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}
