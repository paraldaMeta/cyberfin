"""
每日天机计算模块
包含：日柱计算、财神方位、时辰吉凶、五行强度、天机荐股
"""
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from .constants import (
    TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    DIZHI_SHENGXIAO, DIZHI_CANGGAN, LIUSHIJIAZI,
    WUXING_SHENG, WUXING_KE, WUXING_SECTOR_MAPPING,
    MONTHLY_FORTUNE_2026
)

# ============ 财神方位数据 ============

# 阳贵人方位（正财神）
YANG_GUIREN = {
    '甲': {'direction': '东北', 'fangwei': '艮方'},
    '乙': {'direction': '东南', 'fangwei': '巽方'},
    '丙': {'direction': '正南', 'fangwei': '离方'},
    '丁': {'direction': '正南', 'fangwei': '离方'},
    '戊': {'direction': '正东', 'fangwei': '震方'},
    '己': {'direction': '正东', 'fangwei': '震方'},
    '庚': {'direction': '西北', 'fangwei': '乾方'},
    '辛': {'direction': '西北', 'fangwei': '乾方'},
    '壬': {'direction': '正北', 'fangwei': '坎方'},
    '癸': {'direction': '正北', 'fangwei': '坎方'},
}

# 阴贵人方位（偏财神）
YIN_GUIREN = {
    '甲': {'direction': '正西', 'fangwei': '兑方'},
    '乙': {'direction': '正北', 'fangwei': '坎方'},
    '丙': {'direction': '西北', 'fangwei': '乾方'},
    '丁': {'direction': '西北', 'fangwei': '乾方'},
    '戊': {'direction': '西南', 'fangwei': '坤方'},
    '己': {'direction': '东北', 'fangwei': '艮方'},
    '庚': {'direction': '正南', 'fangwei': '离方'},
    '辛': {'direction': '东南', 'fangwei': '巽方'},
    '壬': {'direction': '东北', 'fangwei': '艮方'},
    '癸': {'direction': '东南', 'fangwei': '巽方'},
}

# 2026年流年飞星方位警示
FEIXING_2026 = {
    '正东': {'star': '8白财星', 'effect': 'good', 'note': '财运增益'},
    '东南': {'star': '9紫吉星', 'effect': 'good', 'note': '桃花人脉'},
    '正南': {'star': '5黄+太岁', 'effect': 'bad', 'note': '今年全年慎用'},
    '正北': {'star': '三煞', 'effect': 'bad', 'note': '今年全年慎入'},
    '西北': {'star': '2黑', 'effect': 'bad', 'note': '今年全年慎用'},
}

# ============ 时辰吉凶数据 ============

# 日干对应最佳/忌时辰
SHICHEN_JIXIONG = {
    '甲': {'best': ['巳', '午'], 'avoid': ['申', '酉'], 'best_stars': [5, 4]},
    '乙': {'best': ['午', '巳'], 'avoid': ['申', '酉'], 'best_stars': [5, 4]},
    '丙': {'best': ['寅', '卯'], 'avoid': ['亥', '子'], 'best_stars': [5, 4]},
    '丁': {'best': ['卯', '寅'], 'avoid': ['亥', '子'], 'best_stars': [5, 4]},
    '戊': {'best': ['巳', '午'], 'avoid': ['寅', '卯'], 'best_stars': [5, 4]},
    '己': {'best': ['午', '巳'], 'avoid': ['寅', '卯'], 'best_stars': [5, 4]},
    '庚': {'best': ['丑', '子'], 'avoid': ['寅', '卯'], 'best_stars': [5, 4]},
    '辛': {'best': ['子', '丑'], 'avoid': ['巳', '午'], 'best_stars': [5, 4]},
    '壬': {'best': ['申', '酉'], 'avoid': ['戌', '未'], 'best_stars': [5, 4]},
    '癸': {'best': ['酉', '申'], 'avoid': ['辰', '丑'], 'best_stars': [5, 4]},
}

# 时辰与交易时段对应
SHICHEN_MARKET = {
    '子': {'range': '23:00-01:00', 'market': '夜盘期货'},
    '丑': {'range': '01:00-03:00', 'market': '夜盘期货'},
    '寅': {'range': '03:00-05:00', 'market': '欧洲早盘外汇'},
    '卯': {'range': '05:00-07:00', 'market': '欧洲外汇开盘'},
    '辰': {'range': '07:00-09:00', 'market': 'A股港股盘前'},
    '巳': {'range': '09:00-11:00', 'market': 'A股/港股早盘'},
    '午': {'range': '11:00-13:00', 'market': 'A股/港股午盘'},
    '未': {'range': '13:00-15:00', 'market': 'A股下午盘'},
    '申': {'range': '15:00-17:00', 'market': '港股尾盘+美股盘前'},
    '酉': {'range': '17:00-19:00', 'market': '美股开盘'},
    '戌': {'range': '19:00-21:00', 'market': '美股主要时段'},
    '亥': {'range': '21:00-23:00', 'market': '美股+夜盘期货'},
}

# ============ 特殊日期 ============

# 2026年奔驰骏马日（大吉）
BENCHI_JUNMA_DATES = [
    (2, 9), (3, 17), (3, 18), (3, 25),
    (4, 10), (5, 13), (6, 17), (7, 14),
    (8, 5), (8, 7), (8, 21), (9, 16),
    (10, 8), (10, 9), (11, 2), (11, 3),
    (11, 26), (12, 10), (12, 22),
    (1, 15), (1, 28), (1, 29),  # 2027年1月
]

# 2026年跛行之马日（凶）
BOXING_ZHIMA_DATES = [
    (2, 5), (2, 27), (3, 24), (4, 30), (7, 3),
]

# ============ 五行板块详细映射 ============

WUXING_STOCKS = {
    '木': {
        'name': '木系',
        'icon': '🌿',
        'color': '#22c55e',
        'a_stock': {
            'sectors': ['医药生物', '农林牧渔', '家居家装', '互联网科技'],
            'stocks': ['片仔癀', '恒瑞医药', '药明康德', '隆基绿能', '中国中免'],
        },
        'hk_stock': {
            'sectors': ['互联网科技', '医疗健康'],
            'stocks': ['腾讯', '阿里', '美团', '京东健康'],
        },
        'futures': ['豆粕', '玉米', '棉花', '木材'],
        'forex': ['新兴市场货币'],
        'logic': '木代表生长扩张，利科技成长',
    },
    '火': {
        'name': '火系',
        'icon': '🔥',
        'color': '#ef4444',
        'a_stock': {
            'sectors': ['能源', '新能源', '通信', '传媒娱乐', '军工'],
            'stocks': ['中国石油', '隆基绿能', '宁德时代', '中国移动', '芒果超媒'],
        },
        'hk_stock': {
            'sectors': ['能源', '电信'],
            'stocks': ['中海油', '中国移动', '中国电信'],
        },
        'futures': ['原油', '天然气', '动力煤'],
        'forex': ['石油货币(加元/挪威克朗)'],
        'logic': '火代表能量爆发，利能源传媒',
    },
    '土': {
        'name': '土系',
        'icon': '🏔️',
        'color': '#eab308',
        'a_stock': {
            'sectors': ['建材', '基建', '房地产', '酒店旅游'],
            'stocks': ['海螺水泥', '中国建筑', '万科A', '华住集团'],
        },
        'hk_stock': {
            'sectors': ['地产', '建材'],
            'stocks': ['中国恒大', '碧桂园', '华润置地'],
        },
        'futures': ['螺纹钢', '铁矿石', '铜'],
        'forex': ['稳定货币'],
        'logic': '土代表稳定储存，利基建地产',
        'warning': '2026年土行承压，秋季一个月强势',
    },
    '金': {
        'name': '金系',
        'icon': '🥇',
        'color': '#f0a500',
        'a_stock': {
            'sectors': ['机械制造', '钢铁有色', '军工', '金融'],
            'stocks': ['三一重工', '紫金矿业', '中航沈飞', '招商银行', '中信证券'],
        },
        'hk_stock': {
            'sectors': ['工业', '金融'],
            'stocks': ['中国平安', '汇丰控股', '工商银行'],
        },
        'futures': ['黄金', '白银', '铜', '铁矿石'],
        'forex': ['美元', '瑞士法郎'],
        'logic': '金代表坚硬价值，利金融军工',
        'highlight': '2026年金行最旺，全年关注',
    },
    '水': {
        'name': '水系',
        'icon': '💧',
        'color': '#3b82f6',
        'a_stock': {
            'sectors': ['航运港口', '渔业水产', '饮料', '跨境贸易'],
            'stocks': ['中远海控', '国联水产', '农夫山泉', '跨境通'],
        },
        'hk_stock': {
            'sectors': ['航运'],
            'stocks': ['东方海外', '中远海控'],
        },
        'futures': ['船运指数'],
        'forex': ['日元', '人民币离岸'],
        'logic': '水代表流动贸易，利航运消费',
        'warning': '2026年水运最衰，降低配置权重30%',
    },
}


class DailyTianjiCalculator:
    """每日天机计算器"""
    
    def __init__(self, target_date: date = None):
        """
        初始化每日天机计算器
        
        Args:
            target_date: 目标日期，默认为今天
        """
        self.target_date = target_date or date.today()
        self.day_pillar = self._calculate_day_pillar()
        self.day_gan = self.day_pillar['gan']
        self.day_zhi = self.day_pillar['zhi']
    
    def _calculate_day_pillar(self) -> Dict:
        """计算当日日柱"""
        # 基准日：1900年1月31日是甲子日
        base_date = date(1900, 1, 31)
        delta = (self.target_date - base_date).days
        jiazi_index = delta % 60
        
        ganzhi = LIUSHIJIAZI[jiazi_index]
        gan = ganzhi[0]
        zhi = ganzhi[1]
        
        return {
            'gan': gan,
            'zhi': zhi,
            'ganzhi': ganzhi,
            'wuxing_gan': TIANGAN_WUXING[gan],
            'wuxing_zhi': DIZHI_WUXING[zhi],
        }
    
    def get_wuxing_strength(self) -> Dict:
        """
        计算今日五行强度
        
        天干地支同五行 → 双旺 ★★★★★
        天干地支相生 → 旺 ★★★★
        中性 → 平 ★★★
        天干地支相克 → 衰 ★★
        """
        gan_wx = TIANGAN_WUXING[self.day_gan]
        zhi_wx = DIZHI_WUXING[self.day_zhi]
        
        # 计算各五行强度
        strength = {'木': 2, '火': 2, '土': 2, '金': 2, '水': 2}
        
        # 天干五行加成
        strength[gan_wx] += 2
        
        # 地支五行加成
        strength[zhi_wx] += 1
        
        # 相生关系加成
        if WUXING_SHENG.get(zhi_wx) == gan_wx:
            strength[gan_wx] += 1  # 地支生天干
        if WUXING_SHENG.get(gan_wx) == zhi_wx:
            strength[zhi_wx] += 1  # 天干生地支
        
        # 相克关系减弱
        for wx in strength:
            if WUXING_KE.get(gan_wx) == wx:
                strength[wx] -= 1
            if WUXING_KE.get(zhi_wx) == wx:
                strength[wx] -= 1
        
        # 转换为星级
        result = {}
        for wx, val in strength.items():
            stars = min(5, max(1, val))
            if gan_wx == zhi_wx == wx:
                level = '双旺'
                stars = 5
            elif stars >= 4:
                level = '旺'
            elif stars == 3:
                level = '平'
            elif stars == 2:
                level = '衰'
            else:
                level = '极衰'
            
            result[wx] = {
                'stars': stars,
                'level': level,
                'is_main': wx == gan_wx,
            }
        
        return {
            'main_wuxing': gan_wx,
            'sub_wuxing': zhi_wx,
            'strength': result,
            'description': f'{gan_wx}气当令' if gan_wx == zhi_wx else f'{gan_wx}气主导，{zhi_wx}气辅助',
        }
    
    def get_caishen_direction(self) -> Dict:
        """获取今日财神方位"""
        yang = YANG_GUIREN[self.day_gan]
        yin = YIN_GUIREN[self.day_gan]
        
        # 检查流年飞星叠加
        yang_feixing = FEIXING_2026.get(yang['direction'])
        yin_feixing = FEIXING_2026.get(yin['direction'])
        
        return {
            'zhengcai': {
                'direction': yang['direction'],
                'fangwei': yang['fangwei'],
                'type': '正财神',
                'description': '主动求财方向',
                'feixing': yang_feixing,
            },
            'piancai': {
                'direction': yin['direction'],
                'fangwei': yin['fangwei'],
                'type': '偏财神',
                'description': '意外之财方向',
                'feixing': yin_feixing,
            },
            'avoid': [d for d, info in FEIXING_2026.items() if info['effect'] == 'bad'],
            'tip': f'今日财神坐{yang["direction"]}，面朝{yang["direction"]}操盘可增旺财运',
        }
    
    def get_shichen_ranking(self) -> List[Dict]:
        """获取今日时辰吉凶排序"""
        jixiong = SHICHEN_JIXIONG[self.day_gan]
        best = jixiong['best']
        avoid = jixiong['avoid']
        best_stars = jixiong['best_stars']
        
        result = []
        for i, zhi in enumerate(DIZHI):
            market_info = SHICHEN_MARKET[zhi]
            
            if zhi in best:
                idx = best.index(zhi)
                stars = best_stars[idx] if idx < len(best_stars) else 4
                level = '大吉' if stars == 5 else '吉'
                color = 'green'
            elif zhi in avoid:
                stars = 1
                level = '凶'
                color = 'red'
            else:
                stars = 3
                level = '平'
                color = 'gray'
            
            result.append({
                'zhi': zhi,
                'name': f'{zhi}时',
                'range': market_info['range'],
                'market': market_info['market'],
                'stars': stars,
                'level': level,
                'color': color,
                'is_best': zhi == best[0] if best else False,
                'is_avoid': zhi in avoid,
            })
        
        return result
    
    def get_special_day_status(self) -> Dict:
        """检查是否为特殊日期"""
        month = self.target_date.month
        day = self.target_date.day
        
        is_benchi = (month, day) in BENCHI_JUNMA_DATES
        is_boxing = (month, day) in BOXING_ZHIMA_DATES
        
        if is_benchi:
            return {
                'type': 'benchi_junma',
                'name': '奔驰骏马',
                'level': '大吉',
                'icon': '🐎',
                'color': 'gold',
                'message': '今日天机大吉日 · 奔驰骏马 · 宜关注突破行情',
                'multiplier': 1.2,
            }
        elif is_boxing:
            return {
                'type': 'boxing_zhima',
                'name': '跛行之马',
                'level': '凶',
                'icon': '🐴',
                'color': 'gray',
                'message': '今日天机凶日 · 跛行之马 · 宜控仓观望',
                'multiplier': 0.7,
            }
        else:
            return {
                'type': 'normal',
                'name': '普通日',
                'level': '平',
                'icon': '📅',
                'color': 'normal',
                'message': None,
                'multiplier': 1.0,
            }
    
    def get_monthly_fortune(self) -> Dict:
        """获取当月运势评级"""
        month = str(self.target_date.month)
        fortune = MONTHLY_FORTUNE_2026.get(month, {'trend': '平稳', 'advice': '稳健操作'})
        
        # 月份评级映射
        month_signals = {
            '2': {'signal': '⚠️', 'color': 'red', 'action': '本月慎入，可观望'},
            '3': {'signal': '↗', 'color': 'yellow', 'action': '本月轻仓试探'},
            '4': {'signal': '↑', 'color': 'green', 'action': '本月可建仓'},
            '5': {'signal': '↑', 'color': 'green', 'action': '继续持有'},
            '6': {'signal': '🚀', 'color': 'gold', 'action': '本月最佳持仓月'},
            '7': {'signal': '🔴', 'color': 'red', 'action': '本月高危，减仓/止损'},
            '8': {'signal': '↑', 'color': 'green', 'action': '低位布局窗口'},
            '9': {'signal': '↗', 'color': 'yellow', 'action': '持仓'},
            '10': {'signal': '→', 'color': 'gray', 'action': '等待方向'},
            '11': {'signal': '↑', 'color': 'green', 'action': '持仓'},
            '12': {'signal': '↓', 'color': 'orange', 'action': '减仓'},
            '1': {'signal': '🏁', 'color': 'blue', 'action': '把握尾段'},
        }
        
        signal_info = month_signals.get(month, {'signal': '→', 'color': 'gray', 'action': '稳健操作'})
        
        return {
            'month': self.target_date.month,
            'trend': fortune['trend'],
            'advice': fortune['advice'],
            **signal_info,
        }
    
    def get_tianji_recommendations(self, user_xiyong: Dict = None) -> Dict:
        """
        获取天机荐股推荐
        
        Args:
            user_xiyong: 用户的喜忌神信息，格式 {'xi_shen': '木', 'yong_shen': '火', 'ji_shen': '金'}
        """
        wuxing_strength = self.get_wuxing_strength()
        monthly = self.get_monthly_fortune()
        special_day = self.get_special_day_status()
        
        recommendations = []
        avoid_list = []
        
        # 默认喜用神（未登录用户）
        if not user_xiyong:
            user_xiyong = {'xi_shen': '金', 'yong_shen': '木', 'ji_shen': '水'}
        
        xi_shen = user_xiyong.get('xi_shen', '金')
        yong_shen = user_xiyong.get('yong_shen', '木')
        ji_shen = user_xiyong.get('ji_shen', '水')
        
        # 计算推荐
        for wuxing in [xi_shen, yong_shen]:
            if wuxing not in WUXING_STOCKS:
                continue
                
            stock_info = WUXING_STOCKS[wuxing]
            strength = wuxing_strength['strength'].get(wuxing, {})
            
            # 计算推荐强度
            base_stars = strength.get('stars', 3)
            final_stars = min(5, int(base_stars * special_day['multiplier']))
            
            rec = {
                'wuxing': wuxing,
                'name': stock_info['name'],
                'icon': stock_info['icon'],
                'color': stock_info['color'],
                'stars': final_stars,
                'strength_level': strength.get('level', '平'),
                'reason': '喜神' if wuxing == xi_shen else '用神',
                'a_stock': stock_info['a_stock'],
                'hk_stock': stock_info['hk_stock'],
                'futures': stock_info['futures'],
                'logic': stock_info['logic'],
                'monthly_signal': monthly['signal'],
                'monthly_action': monthly['action'],
                'warning': stock_info.get('warning'),
                'highlight': stock_info.get('highlight'),
            }
            recommendations.append(rec)
        
        # 计算规避
        if ji_shen in WUXING_STOCKS:
            ji_info = WUXING_STOCKS[ji_shen]
            ji_strength = wuxing_strength['strength'].get(ji_shen, {})
            
            avoid_list.append({
                'wuxing': ji_shen,
                'name': ji_info['name'],
                'icon': ji_info['icon'],
                'color': ji_info['color'],
                'reason': '忌神',
                'strength_level': ji_strength.get('level', '平'),
                'sectors': ji_info['a_stock']['sectors'],
                'warning': f'忌神{ji_shen}今日{ji_strength.get("level", "平")}，逆势操作风险提升',
            })
        
        return {
            'date': self.target_date.isoformat(),
            'day_pillar': self.day_pillar,
            'recommendations': recommendations,
            'avoid': avoid_list,
            'user_xiyong': user_xiyong,
        }
    
    def get_full_tianji(self, user_xiyong: Dict = None, user_name: str = None) -> Dict:
        """获取完整的每日天机数据"""
        wuxing_strength = self.get_wuxing_strength()
        caishen = self.get_caishen_direction()
        shichen = self.get_shichen_ranking()
        special_day = self.get_special_day_status()
        monthly = self.get_monthly_fortune()
        recommendations = self.get_tianji_recommendations(user_xiyong)
        
        # 找出最佳和次佳时辰
        sorted_shichen = sorted(shichen, key=lambda x: x['stars'], reverse=True)
        best_shichen = sorted_shichen[0] if sorted_shichen else None
        second_shichen = sorted_shichen[1] if len(sorted_shichen) > 1 else None
        avoid_shichen = [s for s in shichen if s['is_avoid']]
        
        # 农历日期（简化显示）
        lunar_display = f'{self.day_pillar["ganzhi"]}日'
        
        return {
            'date': self.target_date.isoformat(),
            'date_display': self.target_date.strftime('%Y年%m月%d日'),
            'lunar_display': lunar_display,
            'day_pillar': self.day_pillar,
            'year_info': {
                'ganzhi': '丙午',
                'shengxiao': '马',
                'wuxing': '火',
                'description': '丙午火马年',
            },
            'wuxing_strength': wuxing_strength,
            'caishen': caishen,
            'shichen': {
                'all': shichen,
                'best': best_shichen,
                'second': second_shichen,
                'avoid': avoid_shichen,
            },
            'special_day': special_day,
            'monthly_fortune': monthly,
            'recommendations': recommendations,
            'user_name': user_name,
            'disclaimer': '天机荐股基于命理推演，仅供参考娱乐，不构成任何投资建议。',
        }


def get_month_calendar(year: int, month: int) -> List[Dict]:
    """获取指定月份的天机日历"""
    import calendar
    
    cal = calendar.Calendar()
    days = []
    
    for day in cal.itermonthdays(year, month):
        if day == 0:
            days.append(None)
            continue
        
        target_date = date(year, month, day)
        calculator = DailyTianjiCalculator(target_date)
        special = calculator.get_special_day_status()
        
        days.append({
            'day': day,
            'date': target_date.isoformat(),
            'ganzhi': calculator.day_pillar['ganzhi'],
            'special_type': special['type'],
            'special_name': special['name'] if special['type'] != 'normal' else None,
            'color': special['color'],
        })
    
    return days
