/**
 * 用户命盘展示页面
 * 显示八字命盘、五行分布、流年运势、投资建议
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, RefreshCw, LogOut, Loader2, TrendingUp, TrendingDown, Calendar, Star, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Progress } from '../components/ui/progress';
import { ScrollArea } from '../components/ui/scroll-area';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { toast } from 'sonner';
import { authService, userStorage } from '../services/authService';

// 五行颜色
const WUXING_COLORS = {
  '木': '#22c55e',
  '火': '#ef4444',
  '土': '#eab308',
  '金': '#f0a500',
  '水': '#3b82f6',
};

export default function ProfilePage() {
  const navigate = useNavigate();
  
  const [user, setUser] = useState(null);
  const [bazi, setBazi] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    const loadUserData = async () => {
      const storedUser = userStorage.getUser();
      if (!storedUser) {
        navigate('/login');
        return;
      }
      
      setUser(storedUser);
      setBazi(storedUser.bazi_data);
      setLoading(false);
    };
    
    loadUserData();
  }, [navigate]);
  
  const handleRefreshBazi = async () => {
    if (!user?.id) return;
    
    setRefreshing(true);
    try {
      const res = await authService.refreshBazi(user.id);
      if (res.success) {
        setBazi(res.bazi);
        const updatedUser = { ...user, bazi_data: res.bazi };
        userStorage.setUser(updatedUser);
        setUser(updatedUser);
        toast.success('命盘已刷新');
      }
    } catch (error) {
      toast.error('刷新失败');
    } finally {
      setRefreshing(false);
    }
  };
  
  const handleLogout = () => {
    userStorage.clearUser();
    navigate('/');
    toast.success('已退出登录');
  };
  
  if (loading) {
    return (
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#f0a500]" />
      </div>
    );
  }
  
  if (!bazi) {
    return (
      <div className="min-h-screen bg-[#0a0e17] flex items-center justify-center">
        <Card className="bg-[#141824] border-[#2a2f3e] p-8 text-center">
          <p className="text-[#a1a1aa] mb-4">暂无命盘数据</p>
          <Button onClick={handleRefreshBazi} className="bg-[#f0a500] text-black">
            生成命盘
          </Button>
        </Card>
      </div>
    );
  }
  
  // 准备雷达图数据
  const radarData = bazi.wuxing_chart.map(item => ({
    subject: item.name,
    value: item.value,
    fullMark: 4,
  }));
  
  return (
    <div className="space-y-6">
      {/* 用户头部 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#f0a500] to-[#c0392b] flex items-center justify-center">
            <User className="w-8 h-8 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{bazi.name}</h1>
            <p className="text-[#a1a1aa]">
              {bazi.sizhu.year.shengxiao}年生 · {bazi.gender} · {bazi.xiyong.strength_desc}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefreshBazi}
            disabled={refreshing}
            className="border-[#2a2f3e] text-[#a1a1aa]"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleLogout}
            className="border-[#2a2f3e] text-[#a1a1aa]"
          >
            <LogOut className="w-4 h-4 mr-1" />
            退出
          </Button>
        </div>
      </div>
      
      {/* 命盘内容 */}
      <Tabs defaultValue="bazi" className="space-y-4">
        <TabsList className="bg-[#141824] border border-[#2a2f3e]">
          <TabsTrigger value="bazi" className="data-[state=active]:bg-[#f0a500] data-[state=active]:text-black">
            八字命盘
          </TabsTrigger>
          <TabsTrigger value="fortune" className="data-[state=active]:bg-[#f0a500] data-[state=active]:text-black">
            流年运势
          </TabsTrigger>
          <TabsTrigger value="investment" className="data-[state=active]:bg-[#f0a500] data-[state=active]:text-black">
            投资建议
          </TabsTrigger>
        </TabsList>
        
        {/* 八字命盘 Tab */}
        <TabsContent value="bazi" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 四柱八字 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500]">四柱八字</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-2 text-center">
                  {['hour', 'day', 'month', 'year'].map((pillar) => {
                    const data = bazi.sizhu[pillar];
                    return (
                      <div key={pillar} className="bg-[#0a0e17] rounded-sm p-3 border border-[#2a2f3e]">
                        <div className="text-xs text-[#52525b] mb-2">
                          {pillar === 'year' ? '年柱' : pillar === 'month' ? '月柱' : pillar === 'day' ? '日柱' : '时柱'}
                          {pillar === 'day' && <span className="text-[#f0a500]"> (日主)</span>}
                        </div>
                        {data ? (
                          <>
                            <div className="text-2xl font-bold text-[#f0a500]">{data.gan}</div>
                            <div className="text-xs text-[#a1a1aa]">{data.wuxing_gan}</div>
                            <div className="text-2xl font-bold text-[#c0392b] mt-2">{data.zhi}</div>
                            <div className="text-xs text-[#a1a1aa]">{data.wuxing_zhi}</div>
                            {data.shengxiao && (
                              <div className="text-sm text-white mt-2">{data.shengxiao}</div>
                            )}
                          </>
                        ) : (
                          <div className="text-[#52525b]">
                            <div className="text-2xl">—</div>
                            <div className="text-2xl mt-2">—</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
            
            {/* 五行能量雷达图 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500]">五行能量分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={radarData}>
                      <PolarGrid stroke="#2a2f3e" />
                      <PolarAngleAxis dataKey="subject" stroke="#a1a1aa" />
                      <PolarRadiusAxis angle={90} domain={[0, 4]} stroke="#52525b" />
                      <Radar
                        name="五行"
                        dataKey="value"
                        stroke="#f0a500"
                        fill="#f0a500"
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-4 mt-4">
                  {bazi.wuxing_chart.map(item => (
                    <div key={item.name} className="text-center">
                      <div className="text-xl font-bold" style={{ color: item.color }}>
                        {item.value}
                      </div>
                      <div className="text-xs text-[#a1a1aa]">{item.name}</div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* 喜忌神 */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-[#f0a500]">喜忌神分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="bg-[#0a0e17] rounded-sm p-4 border border-[#2a2f3e] text-center">
                  <div className="text-xs text-[#52525b] mb-2">日主</div>
                  <div className="text-2xl font-bold" style={{ color: WUXING_COLORS[bazi.xiyong.day_master_wuxing] }}>
                    {bazi.xiyong.day_master}
                  </div>
                  <div className="text-xs text-[#a1a1aa]">{bazi.xiyong.day_master_wuxing} · {bazi.xiyong.strength_desc}</div>
                </div>
                <div className="bg-[#0a0e17] rounded-sm p-4 border border-green-500/30 text-center">
                  <div className="text-xs text-[#52525b] mb-2">喜神</div>
                  <div className="text-2xl font-bold text-green-500">{bazi.xiyong.xi_shen}</div>
                  <div className="text-xs text-[#a1a1aa]">有利五行</div>
                </div>
                <div className="bg-[#0a0e17] rounded-sm p-4 border border-blue-500/30 text-center">
                  <div className="text-xs text-[#52525b] mb-2">用神</div>
                  <div className="text-2xl font-bold text-blue-500">{bazi.xiyong.yong_shen}</div>
                  <div className="text-xs text-[#a1a1aa]">调候五行</div>
                </div>
                <div className="bg-[#0a0e17] rounded-sm p-4 border border-red-500/30 text-center">
                  <div className="text-xs text-[#52525b] mb-2">忌神</div>
                  <div className="text-2xl font-bold text-red-500">{bazi.xiyong.ji_shen}</div>
                  <div className="text-xs text-[#a1a1aa]">不利五行</div>
                </div>
                <div className="bg-[#0a0e17] rounded-sm p-4 border border-purple-500/30 text-center">
                  <div className="text-xs text-[#52525b] mb-2">缺失</div>
                  <div className="text-2xl font-bold text-purple-500">{bazi.xiyong.lacking}</div>
                  <div className="text-xs text-[#a1a1aa]">需补充</div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          {/* 大运 */}
          <Card className="bg-[#141824] border-[#2a2f3e]">
            <CardHeader>
              <CardTitle className="text-[#f0a500]">大运排列</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex overflow-x-auto gap-2 pb-2">
                {bazi.dayun.map((dy) => (
                  <div
                    key={dy.index}
                    className={`flex-shrink-0 w-24 p-3 rounded-sm border text-center ${
                      dy.is_current
                        ? 'bg-[#f0a500]/10 border-[#f0a500]'
                        : 'bg-[#0a0e17] border-[#2a2f3e]'
                    }`}
                  >
                    <div className="text-lg font-bold text-white">{dy.ganzhi}</div>
                    <div className="text-xs text-[#a1a1aa]">{dy.age_range}</div>
                    <div className="text-xs text-[#52525b]">{dy.year_range}</div>
                    {dy.is_current && (
                      <div className="text-xs text-[#f0a500] mt-1">当前</div>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        {/* 流年运势 Tab */}
        <TabsContent value="fortune" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 2026年运势 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500] flex items-center gap-2">
                  <Calendar className="w-5 h-5" />
                  2026年流年运势
                </CardTitle>
                <CardDescription className="text-[#a1a1aa]">
                  丙午年 · 火马年
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between p-4 bg-[#0a0e17] rounded-sm border border-[#2a2f3e]">
                  <div>
                    <div className="text-sm text-[#52525b]">您的生肖</div>
                    <div className="text-2xl font-bold text-white">{bazi.liunian_2026.birth_shengxiao}</div>
                  </div>
                  <div className={`px-4 py-2 rounded-full text-lg font-bold ${
                    bazi.liunian_2026.zodiac_fortune.rating === '大吉' ? 'bg-green-500/20 text-green-500' :
                    bazi.liunian_2026.zodiac_fortune.rating === '吉' ? 'bg-blue-500/20 text-blue-500' :
                    bazi.liunian_2026.zodiac_fortune.rating === '凶' ? 'bg-red-500/20 text-red-500' :
                    bazi.liunian_2026.zodiac_fortune.rating === '太岁' ? 'bg-orange-500/20 text-orange-500' :
                    'bg-yellow-500/20 text-yellow-500'
                  }`}>
                    {bazi.liunian_2026.zodiac_fortune.rating}
                  </div>
                </div>
                
                <div className="p-4 bg-[#0a0e17] rounded-sm border border-[#2a2f3e]">
                  <div className="text-sm text-[#52525b] mb-2">投资建议</div>
                  <p className="text-white">{bazi.liunian_2026.zodiac_fortune.advice}</p>
                </div>
                
                <div className="p-4 bg-[#0a0e17] rounded-sm border border-[#2a2f3e]">
                  <div className="text-sm text-[#52525b] mb-2">日主与流年关系</div>
                  <div className="flex items-center gap-2">
                    <span className="text-[#f0a500]">{bazi.liunian_2026.day_master_relation.type}</span>
                    <span className="text-[#a1a1aa]">·</span>
                    <span className="text-white">{bazi.liunian_2026.day_master_relation.desc}</span>
                  </div>
                </div>
                
                {bazi.liunian_2026.zhi_relations.length > 0 && (
                  <div className="p-4 bg-[#0a0e17] rounded-sm border border-orange-500/30">
                    <div className="text-sm text-orange-500 mb-2 flex items-center gap-1">
                      <AlertTriangle className="w-4 h-4" />
                      地支冲害提示
                    </div>
                    {bazi.liunian_2026.zhi_relations.map((rel, i) => (
                      <p key={i} className="text-[#a1a1aa]">{rel}</p>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* 月度吉凶 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500]">2026年月度走势</CardTitle>
                <CardDescription className="text-[#a1a1aa]">
                  基于流年运势预测
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-80">
                  <div className="space-y-2">
                    {Object.entries(bazi.liunian_2026.monthly_fortune).map(([month, data]) => (
                      <div
                        key={month}
                        className="flex items-center justify-between p-3 bg-[#0a0e17] rounded-sm border border-[#2a2f3e]"
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-[#1e2330] flex items-center justify-center text-[#f0a500] font-bold">
                            {month}
                          </div>
                          <div>
                            <div className="text-white text-sm">{data.trend}</div>
                            <div className="text-xs text-[#52525b]">{month}月</div>
                          </div>
                        </div>
                        <div className="text-xs text-[#a1a1aa] max-w-[150px] text-right">
                          {data.advice}
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        {/* 投资建议 Tab */}
        <TabsContent value="investment" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* 投资风格 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500] flex items-center gap-2">
                  <User className="w-5 h-5" />
                  投资性格分析
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-[#0a0e17] rounded-sm border border-[#f0a500]/30">
                  <div className="text-xl font-bold text-[#f0a500] mb-2">
                    {bazi.sector_recommendations.investment_style.style}
                  </div>
                  <p className="text-[#a1a1aa]">
                    {bazi.sector_recommendations.investment_style.description}
                  </p>
                  <div className="mt-3 flex items-center gap-2">
                    <span className="text-sm text-[#52525b]">风险偏好:</span>
                    <span className="text-white">{bazi.sector_recommendations.investment_style.risk_preference}</span>
                  </div>
                </div>
                
                <div className="p-4 bg-[#0a0e17] rounded-sm border border-[#2a2f3e]">
                  <div className="text-sm text-[#52525b] mb-2">仓位建议</div>
                  <p className="text-white">{bazi.sector_recommendations.position_advice}</p>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-[#0a0e17] rounded-sm border border-green-500/30">
                    <div className="text-sm text-green-500 mb-2 flex items-center gap-1">
                      <TrendingUp className="w-4 h-4" />
                      最佳入场月份
                    </div>
                    <div className="text-white">
                      {bazi.sector_recommendations.best_entry_months.map(m => `${m}月`).join('、')}
                    </div>
                  </div>
                  <div className="p-4 bg-[#0a0e17] rounded-sm border border-red-500/30">
                    <div className="text-sm text-red-500 mb-2 flex items-center gap-1">
                      <TrendingDown className="w-4 h-4" />
                      建议离场月份
                    </div>
                    <div className="text-white">
                      {bazi.sector_recommendations.best_exit_months.map(m => `${m}月`).join('、')}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* 板块推荐 */}
            <Card className="bg-[#141824] border-[#2a2f3e]">
              <CardHeader>
                <CardTitle className="text-[#f0a500] flex items-center gap-2">
                  <Star className="w-5 h-5" />
                  2026年板块选股建议
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 推荐板块 */}
                <div>
                  <div className="text-sm text-green-500 mb-2">推荐关注板块（基于喜用神）</div>
                  {bazi.sector_recommendations.recommended_sectors.map((sector, i) => (
                    <div key={i} className="p-3 bg-[#0a0e17] rounded-sm border border-green-500/30 mb-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-lg font-bold" style={{ color: WUXING_COLORS[sector.wuxing] }}>
                          {sector.wuxing}行
                        </span>
                        <span className="text-xs text-green-500 px-2 py-1 bg-green-500/10 rounded">
                          {sector.reason}
                        </span>
                      </div>
                      <div className="text-sm text-[#a1a1aa] mb-1">
                        {sector.sectors.slice(0, 3).join('、')}
                      </div>
                      <div className="text-xs text-[#52525b]">
                        {sector.forecast_2026}
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* 规避板块 */}
                <div>
                  <div className="text-sm text-red-500 mb-2">建议规避板块（基于忌神）</div>
                  {bazi.sector_recommendations.avoid_sectors.map((sector, i) => (
                    <div key={i} className="p-3 bg-[#0a0e17] rounded-sm border border-red-500/30 mb-2">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-lg font-bold" style={{ color: WUXING_COLORS[sector.wuxing] }}>
                          {sector.wuxing}行
                        </span>
                        <span className="text-xs text-red-500 px-2 py-1 bg-red-500/10 rounded">
                          {sector.reason}
                        </span>
                      </div>
                      <div className="text-sm text-[#a1a1aa] mb-1">
                        {sector.sectors.slice(0, 3).join('、')}
                      </div>
                      {sector.warning && (
                        <div className="text-xs text-red-400 flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          {sector.warning}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* 免责声明 */}
          <div className="bg-[#1e2330] border border-[#2a2f3e] rounded-sm p-4">
            <p className="text-xs text-[#52525b] text-center">
              ⚠️ {bazi.disclaimer}
            </p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
