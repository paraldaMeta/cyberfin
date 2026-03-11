/**
 * 今日天机板块组件
 * 显示财神方位、最佳时辰、五行气场、天机荐股
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, Clock, Sparkles, TrendingUp, TrendingDown, AlertTriangle, Calendar, ChevronRight, Star, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { ScrollArea } from './ui/scroll-area';
import api from '../services/api';
import { userStorage } from '../services/authService';

// 五行颜色
const WUXING_COLORS = {
  '木': '#22c55e',
  '火': '#ef4444',
  '土': '#eab308',
  '金': '#f0a500',
  '水': '#3b82f6',
};

// 星级显示
const StarRating = ({ stars, max = 5 }) => (
  <div className="flex gap-0.5">
    {Array.from({ length: max }).map((_, i) => (
      <Star
        key={i}
        className={`w-3 h-3 ${i < stars ? 'fill-[#f0a500] text-[#f0a500]' : 'text-[#2a2f3e]'}`}
      />
    ))}
  </div>
);

// 今日天机横幅
const TianjiHeader = ({ tianji }) => {
  const specialDay = tianji.special_day;
  const isSpecial = specialDay.type !== 'normal';
  
  return (
    <div className={`rounded-sm p-4 mb-4 ${
      isSpecial && specialDay.type === 'benchi_junma' 
        ? 'bg-gradient-to-r from-[#f0a500]/20 to-[#f0a500]/5 border border-[#f0a500]/50'
        : isSpecial && specialDay.type === 'boxing_zhima'
        ? 'bg-gradient-to-r from-[#52525b]/20 to-[#52525b]/5 border border-[#52525b]/50'
        : 'bg-gradient-to-r from-[#141824] to-[#0a0e17] border border-[#2a2f3e]'
    }`}>
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{isSpecial ? specialDay.icon : '🔮'}</span>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-white font-bold">今日天机</span>
              <span className="text-[#a1a1aa]">{tianji.date_display}</span>
            </div>
            <div className="text-sm text-[#52525b]">
              {tianji.lunar_display} · {tianji.year_info.description}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="text-center">
            <div className="text-xs text-[#52525b]">今日五行</div>
            <div className="flex items-center gap-1">
              <span className="text-lg" style={{ color: WUXING_COLORS[tianji.wuxing_strength.main_wuxing] }}>
                {tianji.wuxing_strength.main_wuxing}
              </span>
              <span className="text-[#a1a1aa] text-sm">{tianji.wuxing_strength.description}</span>
            </div>
          </div>
          
          {isSpecial && (
            <div className={`px-3 py-1.5 rounded-full text-sm font-medium ${
              specialDay.type === 'benchi_junma' 
                ? 'bg-[#f0a500]/20 text-[#f0a500]'
                : 'bg-[#52525b]/20 text-[#52525b]'
            }`}>
              {specialDay.icon} {specialDay.name}
            </div>
          )}
        </div>
      </div>
      
      {isSpecial && specialDay.message && (
        <div className={`mt-3 text-sm ${
          specialDay.type === 'benchi_junma' ? 'text-[#f0a500]' : 'text-[#52525b]'
        }`}>
          {specialDay.message}
        </div>
      )}
    </div>
  );
};

// 财神方位卡片
const CaishenCard = ({ caishen }) => (
  <Card className="bg-[#141824] border-[#2a2f3e] h-full">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm flex items-center gap-2 text-[#f0a500]">
        <Compass className="w-4 h-4" />
        财神方位
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-[#52525b] text-sm">正财神</span>
        <div className="flex items-center gap-2">
          <span className="text-white font-bold text-lg">{caishen.zhengcai.direction}</span>
          {caishen.zhengcai.feixing?.effect === 'good' && (
            <span className="text-xs text-green-500">★{caishen.zhengcai.feixing.note}</span>
          )}
        </div>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-[#52525b] text-sm">偏财神</span>
        <span className="text-[#a1a1aa]">{caishen.piancai.direction}</span>
      </div>
      {caishen.avoid.length > 0 && (
        <div className="pt-2 border-t border-[#2a2f3e]">
          <div className="text-xs text-red-400 flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            避开: {caishen.avoid.join('、')}
          </div>
        </div>
      )}
      <div className="text-xs text-[#52525b] mt-2">{caishen.tip}</div>
    </CardContent>
  </Card>
);

// 最佳时辰卡片
const ShichenCard = ({ shichen }) => (
  <Card className="bg-[#141824] border-[#2a2f3e] h-full">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm flex items-center gap-2 text-[#f0a500]">
        <Clock className="w-4 h-4" />
        最佳时辰
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-3">
      {shichen.best && (
        <div className="p-2 bg-green-500/10 rounded-sm border border-green-500/30">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-green-500 font-bold">{shichen.best.name}</span>
              <span className="text-[#a1a1aa] text-sm ml-2">{shichen.best.range}</span>
            </div>
            <StarRating stars={shichen.best.stars} />
          </div>
          <div className="text-xs text-[#52525b] mt-1">{shichen.best.market}</div>
        </div>
      )}
      {shichen.second && (
        <div className="flex items-center justify-between">
          <div>
            <span className="text-[#a1a1aa]">{shichen.second.name}</span>
            <span className="text-[#52525b] text-sm ml-2">{shichen.second.range}</span>
          </div>
          <StarRating stars={shichen.second.stars} />
        </div>
      )}
      {shichen.avoid.length > 0 && (
        <div className="pt-2 border-t border-[#2a2f3e]">
          <div className="text-xs text-red-400">
            忌: {shichen.avoid.map(s => `${s.name} ${s.range}`).join('、')}
          </div>
        </div>
      )}
    </CardContent>
  </Card>
);

// 五行气场卡片
const WuxingCard = ({ wuxing_strength }) => (
  <Card className="bg-[#141824] border-[#2a2f3e] h-full">
    <CardHeader className="pb-2">
      <CardTitle className="text-sm flex items-center gap-2 text-[#f0a500]">
        ☯️ 今日气场
      </CardTitle>
    </CardHeader>
    <CardContent className="space-y-2">
      {['木', '火', '土', '金', '水'].map(wx => {
        const info = wuxing_strength.strength[wx];
        return (
          <div key={wx} className="flex items-center gap-2">
            <span className="w-4 text-sm" style={{ color: WUXING_COLORS[wx] }}>{wx}</span>
            <div className="flex-1 h-2 bg-[#0a0e17] rounded-full overflow-hidden">
              <div 
                className="h-full rounded-full transition-all"
                style={{ 
                  width: `${info.stars * 20}%`,
                  backgroundColor: WUXING_COLORS[wx],
                }}
              />
            </div>
            <span className="text-xs text-[#52525b] w-8">{info.level}</span>
          </div>
        );
      })}
    </CardContent>
  </Card>
);

// 天机荐股卡片
const RecommendationCard = ({ rec, onClick }) => (
  <div 
    className="flex-shrink-0 w-72 p-4 bg-[#0a0e17] rounded-sm border border-[#2a2f3e] hover:border-[#f0a500]/50 transition-colors cursor-pointer"
    onClick={onClick}
  >
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <span className="text-xl">{rec.icon}</span>
        <span className="text-white font-bold">{rec.name}首选</span>
      </div>
      <div className="flex items-center gap-1">
        <span className="text-xs text-[#52525b]">今日{rec.wuxing}气{rec.strength_level}</span>
        <StarRating stars={rec.stars} />
      </div>
    </div>
    
    <div className="space-y-2 text-sm">
      <div>
        <span className="text-[#52525b]">A股:</span>
        <span className="text-[#a1a1aa] ml-1">{rec.a_stock.sectors.slice(0, 2).join('、')}</span>
      </div>
      <div className="text-xs text-[#52525b]">
        推荐: {rec.a_stock.stocks.slice(0, 3).join('/')}
      </div>
      <div>
        <span className="text-[#52525b]">港股:</span>
        <span className="text-[#a1a1aa] ml-1">{rec.hk_stock.sectors.slice(0, 2).join('、')}</span>
      </div>
      <div>
        <span className="text-[#52525b]">期货:</span>
        <span className="text-[#a1a1aa] ml-1">{rec.futures.slice(0, 3).join('、')}</span>
      </div>
    </div>
    
    <div className="mt-3 pt-3 border-t border-[#2a2f3e] flex items-center justify-between">
      <span className="text-xs px-2 py-0.5 rounded bg-green-500/10 text-green-500">{rec.reason}</span>
      <span className="text-xs text-[#f0a500]">{rec.monthly_signal} {rec.monthly_action}</span>
    </div>
    
    {rec.warning && (
      <div className="mt-2 text-xs text-orange-400 flex items-center gap-1">
        <AlertTriangle className="w-3 h-3" />
        {rec.warning}
      </div>
    )}
    {rec.highlight && (
      <div className="mt-2 text-xs text-green-400">
        ★ {rec.highlight}
      </div>
    )}
  </div>
);

// 规避卡片
const AvoidCard = ({ avoid }) => (
  <div className="flex-shrink-0 w-64 p-4 bg-[#0a0e17] rounded-sm border border-red-500/30">
    <div className="flex items-center gap-2 mb-3">
      <AlertTriangle className="w-4 h-4 text-red-500" />
      <span className="text-red-500 font-bold">今日规避</span>
      <span className="text-xs text-[#52525b]">忌神{avoid.wuxing}系</span>
    </div>
    <div className="text-sm text-[#a1a1aa]">
      建议回避: {avoid.sectors.slice(0, 3).join('、')}
    </div>
    <div className="mt-2 text-xs text-red-400">
      {avoid.warning}
    </div>
  </div>
);

// 主组件
export default function TianjiPanel() {
  const navigate = useNavigate();
  const [tianji, setTianji] = useState(null);
  const [loading, setLoading] = useState(true);
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    const loadTianji = async () => {
      try {
        const storedUser = userStorage.getUser();
        setUser(storedUser);
        
        const userId = storedUser?.id;
        const url = userId ? `/tianji/today?user_id=${userId}` : '/tianji/today';
        const response = await api.get(url);
        
        if (response.data.success) {
          setTianji(response.data.tianji);
        }
      } catch (error) {
        console.error('Failed to load tianji:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadTianji();
  }, []);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-8 h-8 animate-spin text-[#f0a500]" />
      </div>
    );
  }
  
  if (!tianji) {
    return null;
  }
  
  const recommendations = tianji.recommendations?.recommendations || [];
  const avoidList = tianji.recommendations?.avoid || [];
  
  return (
    <div className="space-y-4">
      {/* 今日天机横幅 */}
      <TianjiHeader tianji={tianji} />
      
      {/* 命理三要素 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <CaishenCard caishen={tianji.caishen} />
        <ShichenCard shichen={tianji.shichen} />
        <WuxingCard wuxing_strength={tianji.wuxing_strength} />
      </div>
      
      {/* 天机荐股 */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-[#f0a500]" />
              <span className="text-white">天机荐股</span>
              {tianji.user_name && (
                <span className="text-sm text-[#52525b]">· 为{tianji.user_name}专属推荐</span>
              )}
            </CardTitle>
            {!user && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => navigate('/register')}
                className="border-[#f0a500]/50 text-[#f0a500] hover:bg-[#f0a500]/10"
              >
                登录获取个性化推荐
              </Button>
            )}
          </div>
          {tianji.recommendations?.user_xiyong && (
            <p className="text-xs text-[#52525b] mt-1">
              基于您的命盘喜用: 
              <span className="text-green-500 ml-1">{tianji.recommendations.user_xiyong.xi_shen}</span>
              <span className="text-blue-500 ml-1">{tianji.recommendations.user_xiyong.yong_shen}</span>
              · 今日气场叠加
            </p>
          )}
        </CardHeader>
        <CardContent>
          <ScrollArea className="w-full">
            <div className="flex gap-4 pb-2">
              {recommendations.map((rec, i) => (
                <RecommendationCard 
                  key={i} 
                  rec={rec}
                  onClick={() => {
                    // 可以跳转到相关板块
                  }}
                />
              ))}
              {avoidList.map((avoid, i) => (
                <AvoidCard key={i} avoid={avoid} />
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
      
      {/* 查看更多 */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/tianji/calendar')}
          className="text-[#52525b] hover:text-white"
        >
          <Calendar className="w-4 h-4 mr-1" />
          查看月度日历
        </Button>
        {user && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/profile')}
            className="text-[#52525b] hover:text-white"
          >
            查看完整命盘
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        )}
      </div>
      
      {/* 免责声明 */}
      <div className="text-center">
        <p className="text-xs text-[#52525b]">
          ⚠️ {tianji.disclaimer}
        </p>
      </div>
    </div>
  );
}
