"""
八字命理计算引擎
完整实现四柱八字计算、五行统计、喜忌神判断、大运流年计算
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from .constants import (
    TIANGAN, DIZHI, TIANGAN_WUXING, DIZHI_WUXING,
    TIANGAN_YINYANG, DIZHI_SHENGXIAO, DIZHI_CANGGAN,
    LIUSHIJIAZI, WUHU_DUN, WUSHU_DUN, MONTH_ZHI_ORDER,
    WUXING_SHENG, WUXING_KE, XIANGCHONG, XIANGHAI,
    ZODIAC_FORTUNE_2026, MONTHLY_FORTUNE_2026,
    WUXING_SECTOR_MAPPING, INVESTMENT_STYLE, WUXING_NAMES
)
from .solar_terms import (
    get_month_zhi_for_date, is_before_lichun,
    get_solar_terms_for_year, get_lichun_for_year
)
from .city_coordinates import (
    get_city_coordinates, calculate_true_solar_time,
    get_shichen_from_hour
)


class BaziCalculator:
    """八字命理计算器"""
    
    def __init__(
        self,
        birth_year: int,
        birth_month: int,
        birth_day: int,
        birth_hour: Optional[int] = None,
        birth_minute: int = 0,
        gender: str = '男',
        province: str = None,
        city: str = None,
        name: str = ''
    ):
        """
        初始化八字计算器
        
        Args:
            birth_year: 出生年份（公历）
            birth_month: 出生月份（公历）
            birth_day: 出生日期（公历）
            birth_hour: 出生小时（北京时间，0-23），None表示不知道
            birth_minute: 出生分钟
            gender: 性别（男/女）
            province: 出生省份（用于真太阳时校正）
            city: 出生城市
            name: 姓名
        """
        self.birth_year = birth_year
        self.birth_month = birth_month
        self.birth_day = birth_day
        self.birth_hour = birth_hour
        self.birth_minute = birth_minute
        self.gender = gender
        self.province = province
        self.city = city
        self.name = name
        
        # 创建出生日期时间对象
        self.birth_datetime = datetime(birth_year, birth_month, birth_day)
        
        # 真太阳时校正
        self.true_solar_hour = birth_hour
        self.true_solar_minute = birth_minute
        self.longitude = None
        
        if birth_hour is not None and province and city:
            coords = get_city_coordinates(province, city)
            if coords:
                self.longitude = coords[0]
                self.true_solar_hour, self.true_solar_minute = calculate_true_solar_time(
                    birth_hour, birth_minute, self.longitude
                )
        
        # 计算四柱
        self.year_pillar = self._calculate_year_pillar()
        self.month_pillar = self._calculate_month_pillar()
        self.day_pillar = self._calculate_day_pillar()
        self.hour_pillar = self._calculate_hour_pillar() if birth_hour is not None else None
        
        # 计算五行统计
        self.wuxing_count = self._calculate_wuxing_count()
        
        # 计算喜忌神
        self.xiyong = self._calculate_xiyong()
    
    def _calculate_year_pillar(self) -> Dict:
        """
        计算年柱
        
        算法：
        1. 以公历年份计算天干：(年份 - 4) % 10 → 对应天干索引
        2. 以公历年份计算地支：(年份 - 4) % 12 → 对应地支索引
        3. 注意：以「立春」为界（通常为2月3-5日），立春前出生者，年柱取上一年
        """
        year = self.birth_year
        
        # 检查是否在立春之前
        if is_before_lichun(self.birth_datetime):
            year -= 1
        
        gan_index = (year - 4) % 10
        zhi_index = (year - 4) % 12
        
        gan = TIANGAN[gan_index]
        zhi = DIZHI[zhi_index]
        
        return {
            'gan': gan,
            'zhi': zhi,
            'ganzhi': gan + zhi,
            'wuxing_gan': TIANGAN_WUXING[gan],
            'wuxing_zhi': DIZHI_WUXING[zhi],
            'yinyang': TIANGAN_YINYANG[gan],
            'shengxiao': DIZHI_SHENGXIAO[zhi],
        }
    
    def _calculate_month_pillar(self) -> Dict:
        """
        计算月柱
        
        月柱地支以节气为界，月柱天干根据五虎遁年起月法推算
        """
        # 获取月柱地支
        zhi = get_month_zhi_for_date(self.birth_datetime)
        
        # 根据五虎遁年起月法计算月柱天干
        year_gan = self.year_pillar['gan']
        yin_gan_index = WUHU_DUN[year_gan]  # 寅月天干起始索引
        
        # 计算目标月支在月支序列中的位置
        zhi_offset = MONTH_ZHI_ORDER.index(zhi)
        
        # 计算天干索引
        gan_index = (yin_gan_index + zhi_offset) % 10
        gan = TIANGAN[gan_index]
        
        return {
            'gan': gan,
            'zhi': zhi,
            'ganzhi': gan + zhi,
            'wuxing_gan': TIANGAN_WUXING[gan],
            'wuxing_zhi': DIZHI_WUXING[zhi],
            'yinyang': TIANGAN_YINYANG[gan],
        }
    
    def _calculate_day_pillar(self) -> Dict:
        """
        计算日柱
        
        使用儒略日计算法，基准点：2000年1月1日 = 甲子日（序号0）
        实际上2000年1月1日是戊辰日，需要修正
        """
        # 基准日：1900年1月31日是甲子日
        base_date = datetime(1900, 1, 31)
        
        # 计算与基准日的天数差
        delta = (self.birth_datetime - base_date).days
        
        # 对60取模，得到六十甲子序号
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
            'yinyang': TIANGAN_YINYANG[gan],
            'is_rizhu': True,  # 标记这是日柱（日主）
        }
    
    def _calculate_hour_pillar(self) -> Optional[Dict]:
        """
        计算时柱
        
        时柱地支由出生时辰直接对应
        时柱天干根据五鼠遁日起时法推算
        """
        if self.true_solar_hour is None:
            return None
        
        # 获取时辰地支
        zhi = get_shichen_from_hour(self.true_solar_hour)
        
        # 根据五鼠遁日起时法计算时柱天干
        day_gan = self.day_pillar['gan']
        zi_gan_index = WUSHU_DUN[day_gan]  # 子时天干起始索引
        
        # 计算时支在地支序列中的位置
        zhi_index = DIZHI.index(zhi)
        
        # 计算天干索引
        gan_index = (zi_gan_index + zhi_index) % 10
        gan = TIANGAN[gan_index]
        
        return {
            'gan': gan,
            'zhi': zhi,
            'ganzhi': gan + zhi,
            'wuxing_gan': TIANGAN_WUXING[gan],
            'wuxing_zhi': DIZHI_WUXING[zhi],
            'yinyang': TIANGAN_YINYANG[gan],
        }
    
    def _calculate_wuxing_count(self) -> Dict[str, float]:
        """
        统计八字五行分布
        
        计分规则：
        - 天干每个计1分
        - 地支主气计1分
        """
        count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        
        pillars = [self.year_pillar, self.month_pillar, self.day_pillar]
        if self.hour_pillar:
            pillars.append(self.hour_pillar)
        
        for pillar in pillars:
            # 天干五行
            gan_wuxing = pillar['wuxing_gan']
            count[gan_wuxing] += 1
            
            # 地支藏干主气五行
            zhi = pillar['zhi']
            canggan_list = DIZHI_CANGGAN[zhi]
            main_canggan = canggan_list[0]  # 主气
            main_wuxing = TIANGAN_WUXING[main_canggan]
            count[main_wuxing] += 1
        
        return count
    
    def _calculate_xiyong(self) -> Dict:
        """
        计算喜用神和忌神
        
        简化版算法：
        - 日主（日柱天干）代表命主本人
        - 判断日主强弱：月令对日主的影响最大
        - 日主强 → 喜见克我之神（官杀）或泄我之神（食伤）
        - 日主弱 → 喜见生我之神（印绶）或同类（比劫）
        """
        day_gan = self.day_pillar['gan']
        day_wuxing = TIANGAN_WUXING[day_gan]
        month_zhi = self.month_pillar['zhi']
        month_wuxing = DIZHI_WUXING[month_zhi]
        
        # 判断日主强弱
        # 简化判断：如果月令与日主同五行或生日主，则日主强
        is_strong = False
        
        if month_wuxing == day_wuxing:
            is_strong = True
        elif WUXING_SHENG.get(month_wuxing) == day_wuxing:
            is_strong = True
        
        # 也参考五行统计
        same_wuxing_count = self.wuxing_count[day_wuxing]
        sheng_wuxing = [k for k, v in WUXING_SHENG.items() if v == day_wuxing]
        if sheng_wuxing:
            same_wuxing_count += self.wuxing_count[sheng_wuxing[0]]
        
        if same_wuxing_count >= 4:
            is_strong = True
        elif same_wuxing_count <= 2:
            is_strong = False
        
        # 确定喜用神和忌神
        if is_strong:
            # 日主强，喜克泄
            xi_shen = WUXING_KE[day_wuxing]  # 我克之物（财星）
            yong_shen = [k for k, v in WUXING_KE.items() if v == day_wuxing][0]  # 克我之物（官杀）
            ji_shen = day_wuxing  # 同类（比劫）为忌
        else:
            # 日主弱，喜生扶
            xi_shen = [k for k, v in WUXING_SHENG.items() if v == day_wuxing][0]  # 生我之物（印绶）
            yong_shen = day_wuxing  # 同类（比劫）
            ji_shen = [k for k, v in WUXING_KE.items() if v == day_wuxing][0]  # 克我之物为忌
        
        # 找出命局中最缺的五行
        min_wuxing = min(self.wuxing_count, key=self.wuxing_count.get)
        max_wuxing = max(self.wuxing_count, key=self.wuxing_count.get)
        
        return {
            'day_master': day_gan,
            'day_master_wuxing': day_wuxing,
            'is_strong': is_strong,
            'strength_desc': '身强' if is_strong else '身弱',
            'xi_shen': xi_shen,  # 喜神
            'yong_shen': yong_shen,  # 用神
            'ji_shen': ji_shen,  # 忌神
            'lacking': min_wuxing,  # 最缺的五行
            'excess': max_wuxing,  # 最多的五行
        }
    
    def calculate_dayun(self, start_year: int = None) -> List[Dict]:
        """
        计算大运
        
        大运起运方向：
        - 阳年生男、阴年生女 → 顺排
        - 阳年生女、阴年生男 → 逆排
        
        起运岁数计算：
        - 从出生日到下一个/上一个节气的天数 ÷ 3
        """
        year_gan = self.year_pillar['gan']
        is_yang_year = TIANGAN_YINYANG[year_gan] == '阳'
        is_male = self.gender == '男'
        
        # 确定顺逆
        is_forward = (is_yang_year and is_male) or (not is_yang_year and not is_male)
        
        # 计算起运岁数（简化：固定为3岁起运）
        qiyun_age = 3
        
        # 获取月柱在六十甲子中的位置
        month_ganzhi = self.month_pillar['ganzhi']
        month_index = LIUSHIJIAZI.index(month_ganzhi)
        
        # 生成8步大运
        dayun_list = []
        if start_year is None:
            start_year = self.birth_year + qiyun_age
        
        for i in range(8):
            if is_forward:
                index = (month_index + i + 1) % 60
            else:
                index = (month_index - i - 1) % 60
            
            ganzhi = LIUSHIJIAZI[index]
            gan = ganzhi[0]
            zhi = ganzhi[1]
            
            age_start = qiyun_age + i * 10
            age_end = age_start + 9
            year_start = self.birth_year + age_start
            year_end = self.birth_year + age_end
            
            dayun_list.append({
                'index': i + 1,
                'ganzhi': ganzhi,
                'gan': gan,
                'zhi': zhi,
                'wuxing_gan': TIANGAN_WUXING[gan],
                'wuxing_zhi': DIZHI_WUXING[zhi],
                'age_range': f'{age_start}-{age_end}岁',
                'year_range': f'{year_start}-{year_end}年',
                'is_current': year_start <= datetime.now().year <= year_end,
            })
        
        return dayun_list
    
    def analyze_liunian(self, year: int = 2026) -> Dict:
        """
        分析流年运势
        
        Args:
            year: 要分析的年份，默认2026年
        """
        # 计算流年干支
        gan_index = (year - 4) % 10
        zhi_index = (year - 4) % 12
        
        liunian_gan = TIANGAN[gan_index]
        liunian_zhi = DIZHI[zhi_index]
        liunian_ganzhi = liunian_gan + liunian_zhi
        liunian_shengxiao = DIZHI_SHENGXIAO[liunian_zhi]
        
        # 获取命主生肖
        birth_shengxiao = self.year_pillar['shengxiao']
        
        # 获取生肖运势
        zodiac_fortune = ZODIAC_FORTUNE_2026.get(birth_shengxiao, {
            'rating': '中',
            'advice': '稳健操作'
        })
        
        # 分析流年天干与日主的关系
        day_wuxing = self.day_pillar['wuxing_gan']
        liunian_wuxing = TIANGAN_WUXING[liunian_gan]
        
        relation = self._get_wuxing_relation(day_wuxing, liunian_wuxing)
        
        # 分析流年地支与命局地支的关系
        zhi_relations = []
        for pillar in [self.year_pillar, self.month_pillar, self.day_pillar]:
            zhi = pillar['zhi']
            if XIANGCHONG.get(zhi) == liunian_zhi:
                zhi_relations.append(f'{zhi}与{liunian_zhi}相冲')
            if XIANGHAI.get(zhi) == liunian_zhi:
                zhi_relations.append(f'{zhi}与{liunian_zhi}相害')
        
        # 获取喜用神与流年的关系
        xiyong_match = liunian_wuxing == self.xiyong['xi_shen'] or liunian_wuxing == self.xiyong['yong_shen']
        
        return {
            'year': year,
            'ganzhi': liunian_ganzhi,
            'gan': liunian_gan,
            'zhi': liunian_zhi,
            'wuxing': TIANGAN_WUXING[liunian_gan],
            'shengxiao': liunian_shengxiao,
            'birth_shengxiao': birth_shengxiao,
            'zodiac_fortune': zodiac_fortune,
            'day_master_relation': relation,
            'zhi_relations': zhi_relations,
            'xiyong_match': xiyong_match,
            'xiyong_desc': '流年五行利于命主' if xiyong_match else '流年五行不利于命主，需谨慎',
            'monthly_fortune': MONTHLY_FORTUNE_2026,
        }
    
    def _get_wuxing_relation(self, my_wuxing: str, other_wuxing: str) -> Dict:
        """获取两个五行之间的关系"""
        if my_wuxing == other_wuxing:
            return {'type': '比劫', 'desc': '竞争、平分', 'nature': '中性'}
        if WUXING_SHENG.get(other_wuxing) == my_wuxing:
            return {'type': '印绶', 'desc': '资源、贵人', 'nature': '吉'}
        if WUXING_SHENG.get(my_wuxing) == other_wuxing:
            return {'type': '食伤', 'desc': '输出、创造', 'nature': '泄'}
        if WUXING_KE.get(other_wuxing) == my_wuxing:
            return {'type': '官杀', 'desc': '压力、规范', 'nature': '凶'}
        if WUXING_KE.get(my_wuxing) == other_wuxing:
            return {'type': '财星', 'desc': '财运、获益', 'nature': '吉'}
        return {'type': '未知', 'desc': '', 'nature': '中性'}
    
    def get_sector_recommendations(self) -> Dict:
        """
        获取股票板块推荐
        
        基于喜用神和流年运势推荐
        """
        xi_shen = self.xiyong['xi_shen']
        yong_shen = self.xiyong['yong_shen']
        ji_shen = self.xiyong['ji_shen']
        
        # 推荐板块（喜用神对应）
        recommended = []
        if xi_shen in WUXING_SECTOR_MAPPING:
            recommended.append({
                'wuxing': xi_shen,
                'reason': '喜神',
                **WUXING_SECTOR_MAPPING[xi_shen]
            })
        if yong_shen != xi_shen and yong_shen in WUXING_SECTOR_MAPPING:
            recommended.append({
                'wuxing': yong_shen,
                'reason': '用神',
                **WUXING_SECTOR_MAPPING[yong_shen]
            })
        
        # 规避板块（忌神对应）
        avoid = []
        if ji_shen in WUXING_SECTOR_MAPPING:
            avoid.append({
                'wuxing': ji_shen,
                'reason': '忌神',
                **WUXING_SECTOR_MAPPING[ji_shen]
            })
        
        # 获取投资风格
        day_wuxing = self.day_pillar['wuxing_gan']
        investment_style = INVESTMENT_STYLE.get(day_wuxing, {
            'style': '综合型投资者',
            'description': '根据市场情况灵活调整',
            'risk_preference': '中风险',
        })
        
        # 获取最佳入场/离场月份
        best_entry = [6, 8, 11]  # 根据CLSA 2026预测
        best_exit = [7, 12]
        
        return {
            'recommended_sectors': recommended,
            'avoid_sectors': avoid,
            'investment_style': investment_style,
            'best_entry_months': best_entry,
            'best_exit_months': best_exit,
            'position_advice': self.xiyong['strength_desc'] + '，' + (
                '可适当积极配置' if self.xiyong['is_strong'] else '建议稳健防守配置'
            ),
        }
    
    def get_full_bazi_analysis(self) -> Dict:
        """获取完整的八字分析结果"""
        liunian = self.analyze_liunian(2026)
        dayun = self.calculate_dayun()
        sectors = self.get_sector_recommendations()
        
        # 构建命盘四柱数据
        sizhu = {
            'year': {
                **self.year_pillar,
                'label': '年柱',
            },
            'month': {
                **self.month_pillar,
                'label': '月柱',
            },
            'day': {
                **self.day_pillar,
                'label': '日柱',
                'note': '(日主)',
            },
        }
        if self.hour_pillar:
            sizhu['hour'] = {
                **self.hour_pillar,
                'label': '时柱',
            }
        
        return {
            'name': self.name,
            'gender': self.gender,
            'birth_info': {
                'year': self.birth_year,
                'month': self.birth_month,
                'day': self.birth_day,
                'hour': self.birth_hour,
                'minute': self.birth_minute,
                'province': self.province,
                'city': self.city,
                'longitude': self.longitude,
                'true_solar_hour': self.true_solar_hour,
                'true_solar_minute': self.true_solar_minute,
            },
            'sizhu': sizhu,
            'wuxing_count': self.wuxing_count,
            'wuxing_chart': [
                {'name': '木', 'value': self.wuxing_count['木'], 'color': '#22c55e'},
                {'name': '火', 'value': self.wuxing_count['火'], 'color': '#ef4444'},
                {'name': '土', 'value': self.wuxing_count['土'], 'color': '#eab308'},
                {'name': '金', 'value': self.wuxing_count['金'], 'color': '#f0a500'},
                {'name': '水', 'value': self.wuxing_count['水'], 'color': '#3b82f6'},
            ],
            'xiyong': self.xiyong,
            'dayun': dayun,
            'liunian_2026': liunian,
            'sector_recommendations': sectors,
            'disclaimer': '以上内容基于传统命理推算，仅供娱乐参考，不构成投资建议。',
        }
