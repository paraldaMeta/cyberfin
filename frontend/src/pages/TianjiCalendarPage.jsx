/**
 * 天机日历页面
 * 展示月度天机日历，标注奔驰骏马日/跛行之马日
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Calendar, Star, AlertTriangle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import api from '../services/api';
import { userStorage } from '../services/authService';

const WEEKDAYS = ['日', '一', '二', '三', '四', '五', '六'];
const MONTHS = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一月', '十二月'];

// 月度趋势
const MONTHLY_TRENDS = {
  1: { signal: '🏁', trend: '冲刺', color: 'blue' },
  2: { signal: '⚠️', trend: '下跌', color: 'red' },
  3: { signal: '↗', trend: '小涨', color: 'yellow' },
  4: { signal: '↑', trend: '上涨', color: 'green' },
  5: { signal: '↑', trend: '上涨', color: 'green' },
  6: { signal: '🚀', trend: '最强月', color: 'gold' },
  7: { signal: '🔴', trend: '急跌', color: 'red' },
  8: { signal: '↑', trend: '反弹', color: 'green' },
  9: { signal: '↗', trend: '小涨', color: 'yellow' },
  10: { signal: '→', trend: '横盘', color: 'gray' },
  11: { signal: '↑', trend: '上涨', color: 'green' },
  12: { signal: '↓', trend: '回落', color: 'orange' },
};

export default function TianjiCalendarPage() {
  const navigate = useNavigate();
  const today = new Date();
  
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [calendar, setCalendar] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);
  const [dayDetail, setDayDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  
  // 加载月度日历
  useEffect(() => {
    const loadCalendar = async () => {
      setLoading(true);
      try {
        const response = await api.get(`/tianji/calendar/${year}/${month}`);
        if (response.data.success) {
          setCalendar(response.data.calendar);
        }
      } catch (error) {
        console.error('Failed to load calendar:', error);
      } finally {
        setLoading(false);
      }
    };
    loadCalendar();
  }, [year, month]);
  
  // 加载日期详情
  const loadDayDetail = async (dateStr) => {
    setDetailLoading(true);
    try {
      const user = userStorage.getUser();
      const url = user?.id 
        ? `/tianji/date/${dateStr}?user_id=${user.id}`
        : `/tianji/date/${dateStr}`;
      const response = await api.get(url);
      if (response.data.success) {
        setDayDetail(response.data.tianji);
      }
    } catch (error) {
      console.error('Failed to load day detail:', error);
    } finally {
      setDetailLoading(false);
    }
  };
  
  const handleDayClick = (day) => {
    if (!day) return;
    setSelectedDate(day);
    loadDayDetail(day.date);
  };
  
  const prevMonth = () => {
    if (month === 1) {
      setYear(year - 1);
      setMonth(12);
    } else {
      setMonth(month - 1);
    }
  };
  
  const nextMonth = () => {
    if (month === 12) {
      setYear(year + 1);
      setMonth(1);
    } else {
      setMonth(month + 1);
    }
  };
  
  const monthTrend = MONTHLY_TRENDS[month];
  
  // 计算日历网格
  const firstDayOfMonth = new Date(year, month - 1, 1).getDay();
  const calendarGrid = [];
  for (let i = 0; i < firstDayOfMonth; i++) {
    calendarGrid.push(null);
  }
  calendar.forEach(day => calendarGrid.push(day));
  
  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Calendar className="w-6 h-6 text-[#f0a500]" />
            天机日历
          </h1>
          <p className="text-[#a1a1aa] text-sm mt-1">
            2026丙午火马年 · 查看每日天机吉凶
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => navigate('/')}
          className="border-[#2a2f3e] text-[#a1a1aa]"
        >
          返回首页
        </Button>
      </div>
      
      {/* 月份导航 */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={prevMonth}
              className="text-[#a1a1aa] hover:text-white"
            >
              <ChevronLeft className="w-5 h-5" />
            </Button>
            
            <div className="text-center">
              <div className="text-xl font-bold text-white">
                {year}年 {MONTHS[month - 1]}
              </div>
              {monthTrend && (
                <div className={`text-sm mt-1 ${
                  monthTrend.color === 'gold' ? 'text-[#f0a500]' :
                  monthTrend.color === 'green' ? 'text-green-500' :
                  monthTrend.color === 'red' ? 'text-red-500' :
                  monthTrend.color === 'orange' ? 'text-orange-500' :
                  'text-[#a1a1aa]'
                }`}>
                  {monthTrend.signal} 本月趋势: {monthTrend.trend}
                </div>
              )}
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={nextMonth}
              className="text-[#a1a1aa] hover:text-white"
            >
              <ChevronRight className="w-5 h-5" />
            </Button>
          </div>
        </CardContent>
      </Card>
      
      {/* 图例 */}
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-[#f0a500]" />
          <span className="text-[#a1a1aa]">🐎 奔驰骏马 (大吉)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded bg-[#52525b]" />
          <span className="text-[#a1a1aa]">🐴 跛行之马 (凶)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded border border-[#f0a500]" />
          <span className="text-[#a1a1aa]">今日</span>
        </div>
      </div>
      
      {/* 日历网格 */}
      <Card className="bg-[#141824] border-[#2a2f3e]">
        <CardContent className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-[#f0a500]" />
            </div>
          ) : (
            <>
              {/* 星期标题 */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {WEEKDAYS.map(day => (
                  <div key={day} className="text-center text-sm text-[#52525b] py-2">
                    {day}
                  </div>
                ))}
              </div>
              
              {/* 日期网格 */}
              <div className="grid grid-cols-7 gap-1">
                {calendarGrid.map((day, index) => {
                  if (!day) {
                    return <div key={`empty-${index}`} className="aspect-square" />;
                  }
                  
                  const isToday = day.date === today.toISOString().split('T')[0];
                  const isSpecial = day.special_type !== 'normal';
                  const isBenchi = day.special_type === 'benchi_junma';
                  const isBoxing = day.special_type === 'boxing_zhima';
                  
                  return (
                    <div
                      key={day.date}
                      onClick={() => handleDayClick(day)}
                      className={`aspect-square p-1 rounded-sm cursor-pointer transition-colors ${
                        isToday ? 'ring-2 ring-[#f0a500]' : ''
                      } ${
                        isBenchi ? 'bg-[#f0a500]/20 hover:bg-[#f0a500]/30' :
                        isBoxing ? 'bg-[#52525b]/20 hover:bg-[#52525b]/30' :
                        'hover:bg-[#1e2330]'
                      }`}
                    >
                      <div className="h-full flex flex-col items-center justify-center">
                        <span className={`text-lg font-medium ${
                          isBenchi ? 'text-[#f0a500]' :
                          isBoxing ? 'text-[#52525b]' :
                          isToday ? 'text-white' :
                          'text-[#a1a1aa]'
                        }`}>
                          {day.day}
                        </span>
                        <span className="text-xs text-[#52525b]">{day.ganzhi}</span>
                        {isSpecial && (
                          <span className="text-xs mt-0.5">
                            {isBenchi ? '🐎' : '🐴'}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </CardContent>
      </Card>
      
      {/* 本月特殊日期列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-[#141824] border-[#f0a500]/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-[#f0a500] flex items-center gap-2">
              <Star className="w-4 h-4" />
              本月奔驰骏马日 (大吉)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {calendar.filter(d => d?.special_type === 'benchi_junma').map(day => (
                <div
                  key={day.date}
                  onClick={() => handleDayClick(day)}
                  className="px-3 py-1.5 bg-[#f0a500]/10 rounded-sm cursor-pointer hover:bg-[#f0a500]/20"
                >
                  <span className="text-[#f0a500]">{day.day}日</span>
                  <span className="text-[#52525b] text-xs ml-1">{day.ganzhi}</span>
                </div>
              ))}
              {calendar.filter(d => d?.special_type === 'benchi_junma').length === 0 && (
                <span className="text-[#52525b]">本月无</span>
              )}
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-[#141824] border-[#52525b]/30">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-[#52525b] flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              本月跛行之马日 (凶)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {calendar.filter(d => d?.special_type === 'boxing_zhima').map(day => (
                <div
                  key={day.date}
                  onClick={() => handleDayClick(day)}
                  className="px-3 py-1.5 bg-[#52525b]/10 rounded-sm cursor-pointer hover:bg-[#52525b]/20"
                >
                  <span className="text-[#a1a1aa]">{day.day}日</span>
                  <span className="text-[#52525b] text-xs ml-1">{day.ganzhi}</span>
                </div>
              ))}
              {calendar.filter(d => d?.special_type === 'boxing_zhima').length === 0 && (
                <span className="text-[#52525b]">本月无</span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* 日期详情弹窗 */}
      <Dialog open={!!selectedDate} onOpenChange={() => setSelectedDate(null)}>
        <DialogContent className="bg-[#141824] border-[#2a2f3e] max-w-lg">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              {selectedDate?.special_type === 'benchi_junma' && '🐎'}
              {selectedDate?.special_type === 'boxing_zhima' && '🐴'}
              {selectedDate?.date} 天机详情
            </DialogTitle>
          </DialogHeader>
          
          {detailLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-[#f0a500]" />
            </div>
          ) : dayDetail && (
            <div className="space-y-4">
              {/* 日柱信息 */}
              <div className="p-3 bg-[#0a0e17] rounded-sm">
                <div className="flex items-center justify-between">
                  <span className="text-[#52525b]">日柱</span>
                  <span className="text-white font-bold text-lg">{dayDetail.day_pillar.ganzhi}</span>
                </div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-[#52525b]">五行主导</span>
                  <span className="text-[#a1a1aa]">{dayDetail.wuxing_strength.description}</span>
                </div>
              </div>
              
              {/* 财神方位 */}
              <div className="p-3 bg-[#0a0e17] rounded-sm">
                <div className="text-[#f0a500] text-sm mb-2">财神方位</div>
                <div className="flex items-center justify-between">
                  <span className="text-[#52525b]">正财神</span>
                  <span className="text-white">{dayDetail.caishen.zhengcai.direction}</span>
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[#52525b]">偏财神</span>
                  <span className="text-[#a1a1aa]">{dayDetail.caishen.piancai.direction}</span>
                </div>
              </div>
              
              {/* 最佳时辰 */}
              <div className="p-3 bg-[#0a0e17] rounded-sm">
                <div className="text-[#f0a500] text-sm mb-2">最佳入市时辰</div>
                {dayDetail.shichen.best && (
                  <div className="flex items-center justify-between">
                    <span className="text-green-500">{dayDetail.shichen.best.name} {dayDetail.shichen.best.range}</span>
                    <span className="text-[#52525b]">{dayDetail.shichen.best.market}</span>
                  </div>
                )}
                {dayDetail.shichen.avoid.length > 0 && (
                  <div className="mt-2 text-red-400 text-sm">
                    忌: {dayDetail.shichen.avoid.map(s => s.name).join('、')}
                  </div>
                )}
              </div>
              
              {/* 特殊日提示 */}
              {dayDetail.special_day.type !== 'normal' && (
                <div className={`p-3 rounded-sm ${
                  dayDetail.special_day.type === 'benchi_junma' 
                    ? 'bg-[#f0a500]/10 border border-[#f0a500]/30'
                    : 'bg-[#52525b]/10 border border-[#52525b]/30'
                }`}>
                  <div className={`font-bold ${
                    dayDetail.special_day.type === 'benchi_junma' ? 'text-[#f0a500]' : 'text-[#52525b]'
                  }`}>
                    {dayDetail.special_day.icon} {dayDetail.special_day.name}
                  </div>
                  <div className="text-sm text-[#a1a1aa] mt-1">
                    {dayDetail.special_day.message}
                  </div>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* 免责声明 */}
      <div className="text-center">
        <p className="text-xs text-[#52525b]">
          ⚠️ 天机日历基于命理推演，仅供参考娱乐，不构成任何投资建议。
        </p>
      </div>
    </div>
  );
}
