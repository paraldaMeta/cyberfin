"""
Jafar Calculator - Qaida Tarweehat Algorithm Implementation
Implements the core Jafar letter calculation algorithm for divination
"""

# Abjad Qumri / Nuhi (28 letters, index 1-28)
ABJAD_QUMRI = {
    'A': 1, 'B': 2, 'G': 3, 'D': 4, 'H': 5, 'W': 6, 'Z': 7, 'HH': 8, 'TT': 9, 'Y': 10,
    'K': 11, 'L': 12, 'M': 13, 'N': 14, 'S': 15, "'A": 16, 'F': 17, 'SS': 18, 'Q': 19, 'R': 20,
    'Sh': 21, 'T': 22, 'Th': 23, 'Kh': 24, 'Dh': 25, 'DD': 26, 'ZZ': 27, 'Gh': 28
}

# Reverse mapping (index to letter)
INDEX_TO_LETTER = {v: k for k, v in ABJAD_QUMRI.items()}

# Abjad Ahtam (Four Elements)
ELEMENTS = {
    'Fire': ['A', 'H', 'TT', 'M', 'F', 'Sh', 'Dh'],  # ↑ Strong breakthrough
    'Air': ['B', 'W', 'Y', 'N', 'SS', 'T', 'DD'],    # → Sideways oscillation
    'Water': ['G', 'Z', 'K', 'S', 'Q', 'Th', 'ZZ'],  # ↓ Pressure pullback
    'Dust': ['D', 'HH', 'L', "'A", 'R', 'Kh', 'Gh']  # ⚓ Bottom consolidation
}

# Chinese mapping for letter transliteration
LETTER_ARABIC = {
    'A': 'أ', 'B': 'ب', 'G': 'ج', 'D': 'د', 'H': 'ه', 'W': 'و', 'Z': 'ز',
    'HH': 'ح', 'TT': 'ط', 'Y': 'ي', 'K': 'ك', 'L': 'ل', 'M': 'م', 'N': 'ن',
    'S': 'س', "'A": 'ع', 'F': 'ف', 'SS': 'ص', 'Q': 'ق', 'R': 'ر', 'Sh': 'ش',
    'T': 'ت', 'Th': 'ث', 'Kh': 'خ', 'Dh': 'ذ', 'DD': 'ض', 'ZZ': 'ظ', 'Gh': 'غ'
}


def text_to_letters(text: str) -> list:
    """Convert text to Abjad letter sequence (simplified mapping)"""
    # Map common characters to Abjad letters
    char_map = {
        'a': 'A', 'b': 'B', 'c': 'G', 'd': 'D', 'e': 'H', 'f': 'F', 'g': 'G',
        'h': 'H', 'i': 'Y', 'j': 'G', 'k': 'K', 'l': 'L', 'm': 'M', 'n': 'N',
        'o': 'W', 'p': 'F', 'q': 'Q', 'r': 'R', 's': 'S', 't': 'T', 'u': 'W',
        'v': 'W', 'w': 'W', 'x': 'Kh', 'y': 'Y', 'z': 'Z',
        # Chinese pinyin common sounds
        '张': 'G', '三': 'S', '李': 'L', '王': 'W', '刘': 'L', '陈': 'Th',
        '贵': 'Q', '州': 'G', '茅': 'M', '台': 'T', '今': 'G', '日': 'R',
        '本': 'B', '周': 'G', '月': 'Y', '季': 'G', '年': 'N'
    }
    
    letters = []
    text_lower = text.lower()
    i = 0
    while i < len(text_lower):
        char = text_lower[i]
        if char in char_map:
            letters.append(char_map[char])
        elif char.isalpha():
            # Default mapping for unmapped characters
            letters.append(INDEX_TO_LETTER[((ord(char) - ord('a')) % 28) + 1])
        i += 1
    
    return letters


def deduplicate_sequence(letters: list) -> list:
    """Remove consecutive duplicates (净化)"""
    if not letters:
        return []
    result = [letters[0]]
    for letter in letters[1:]:
        if letter != result[-1]:
            result.append(letter)
    return result


def maukher_sadr(letters: list) -> list:
    """
    Maukher Sadr (首末交错): Take from right, then left, alternating
    """
    if not letters:
        return []
    
    result = []
    left = 0
    right = len(letters) - 1
    take_right = True
    
    while left <= right:
        if take_right:
            result.append(letters[right])
            right -= 1
        else:
            result.append(letters[left])
            left += 1
        take_right = not take_right
    
    return result


def fasla_adadi(letters1: list, letters2: list) -> list:
    """
    Fasla Adadi (间隔取数): Calculate distance between corresponding letters
    in Abjad Qumri sequence
    """
    min_len = min(len(letters1), len(letters2))
    distances = []
    
    for i in range(min_len):
        l1 = letters1[i]
        l2 = letters2[i]
        
        idx1 = ABJAD_QUMRI.get(l1, 1)
        idx2 = ABJAD_QUMRI.get(l2, 1)
        
        if l1 == l2:
            distance = 28
        else:
            # Forward count from l1 to l2 in circular Abjad sequence
            distance = (idx2 - idx1) % 28
            if distance == 0:
                distance = 28
        
        distances.append(distance)
    
    return distances


def numbers_to_letters(numbers: list) -> list:
    """Convert number sequence back to letters"""
    return [INDEX_TO_LETTER.get(((n - 1) % 28) + 1, 'A') for n in numbers]


def get_element(letter: str) -> str:
    """Get the element for a letter"""
    for element, letters in ELEMENTS.items():
        if letter in letters:
            return element
    return 'Unknown'


def get_dominant_element(letters: list) -> dict:
    """Calculate dominant element from letter sequence"""
    element_counts = {'Fire': 0, 'Air': 0, 'Water': 0, 'Dust': 0}
    
    for letter in letters:
        element = get_element(letter)
        if element in element_counts:
            element_counts[element] += 1
    
    total = sum(element_counts.values())
    if total == 0:
        return {'primary': 'Air', 'secondary': 'Air', 'counts': element_counts}
    
    sorted_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        'primary': sorted_elements[0][0],
        'secondary': sorted_elements[1][0] if len(sorted_elements) > 1 else sorted_elements[0][0],
        'counts': element_counts
    }


def letters_to_transliteration(letters: list) -> str:
    """Convert letters to Arabic-style transliteration"""
    arabic = ''.join([LETTER_ARABIC.get(l, l) for l in letters])
    latin = '-'.join(letters)
    return f"{arabic} ({latin})"


def interpret_element(element_info: dict) -> dict:
    """Interpret elements into financial signals"""
    primary = element_info['primary']
    secondary = element_info['secondary']
    
    element_meanings = {
        'Fire': {'direction': '📈 看涨', 'signal': '强势突破', 'action': '上涨区间、适宜入场'},
        'Air': {'direction': '➡️ 震荡', 'signal': '横盘震荡', 'action': '信号模糊、轻仓谨慎'},
        'Water': {'direction': '📉 看跌', 'signal': '承压回落', 'action': '下跌风险、建议观望'},
        'Dust': {'direction': '⚓ 筑底', 'signal': '筑底蓄力', 'action': '底部蓄势、耐心等待'}
    }
    
    primary_info = element_meanings.get(primary, element_meanings['Air'])
    
    # Calculate signal strength (1-5 stars)
    counts = element_info['counts']
    total = sum(counts.values())
    if total > 0:
        dominance = counts[primary] / total
        if dominance > 0.6:
            strength = 5
        elif dominance > 0.45:
            strength = 4
        elif dominance > 0.35:
            strength = 3
        elif dominance > 0.25:
            strength = 2
        else:
            strength = 1
    else:
        strength = 3
    
    return {
        'direction': primary_info['direction'],
        'signal': primary_info['signal'],
        'action': primary_info['action'],
        'strength': strength,
        'stars': '★' * strength + '☆' * (5 - strength),
        'element_combo': f"{primary}+{secondary}" if primary != secondary else primary
    }


def calculate_jafar(name: str, mother_name: str, question: str, segment_label: str) -> dict:
    """
    Execute complete Qaida Tarweehat algorithm for one segment
    
    Returns dict with all calculation steps and interpretation
    """
    # Step a: Talkhes Sawal (基础行)
    full_input = f"{name}{mother_name}{question}{segment_label}"
    raw_letters = text_to_letters(full_input)
    sitar_asas = deduplicate_sequence(raw_letters)
    
    # Ensure minimum length
    if len(sitar_asas) < 5:
        sitar_asas = sitar_asas + ['A', 'H', 'M', 'D', 'W'][:5-len(sitar_asas)]
    
    # Step b: Maukher Sadr 1
    line_ms1 = maukher_sadr(sitar_asas)
    
    # Step c: Fasla Adadi (间隔取数)
    fasla_numbers = fasla_adadi(sitar_asas, line_ms1)
    
    # Step d: Harufat Mustahisla
    line_mustahisla = numbers_to_letters(fasla_numbers)
    
    # Step e: Final Interlacing (Maukher Sadr × 2)
    ms_temp = maukher_sadr(line_mustahisla)
    final_row = maukher_sadr(ms_temp)
    
    # Get element analysis
    element_info = get_dominant_element(final_row)
    interpretation = interpret_element(element_info)
    
    # Generate transliteration
    transliteration = letters_to_transliteration(final_row)
    
    return {
        'trace': {
            'asas': '-'.join(sitar_asas),
            'ms1': '-'.join(line_ms1),
            'fasla': '-'.join(map(str, fasla_numbers)),
            'mustahisla': '-'.join(line_mustahisla),
            'final_row': '-'.join(final_row)
        },
        'final_row_letters': final_row,
        'transliteration': transliteration,
        'element': element_info,
        'interpretation': interpretation
    }


def generate_divination_report(
    name: str,
    stock_name: str,
    stock_code: str,
    time_period: str,
    segments: list
) -> str:
    """
    Generate complete Jafar divination report with proper algorithm execution
    """
    mother_name = "Hawwa"
    base_question = f"{stock_name}({stock_code})在{time_period}内的行情走势命数如何？"
    
    # Calculate for each segment
    segment_results = []
    for i, segment in enumerate(segments):
        segment_question = f"{stock_name}在{segment}的价格命数裁决"
        result = calculate_jafar(name, mother_name, segment_question, segment)
        segment_results.append({
            'label': segment,
            'index': i + 1,
            **result
        })
    
    # Determine overall trend
    directions = [r['interpretation']['direction'] for r in segment_results]
    bullish_count = sum(1 for d in directions if '涨' in d)
    bearish_count = sum(1 for d in directions if '跌' in d)
    
    if bullish_count > bearish_count:
        overall_trend = "先抑后扬" if directions[0] != '📈 看涨' else "强势上涨"
        overall_stars = "★★★★☆"
    elif bearish_count > bullish_count:
        overall_trend = "先扬后抑" if directions[0] == '📈 看涨' else "弱势下跌"
        overall_stars = "★★☆☆☆"
    else:
        overall_trend = "宽幅震荡"
        overall_stars = "★★★☆☆"
    
    # Find key turning point
    key_segment = segment_results[len(segment_results)//2]['label']
    
    # Build report
    from datetime import datetime, timezone
    current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    report = f"""╔══════════════════════════════════════╗
  🔮 金融天机推演报告
  标的：{stock_name}（{stock_code}）
  推演时段：{time_period}
  求问者：{name}
  推演时刻：{current_time}
╚══════════════════════════════════════╝

━━ 一、行情时段切割 ━━━━━━━━━━━━━━━━━━

* 标的概况：{stock_name} 属亚洲金融市场标的
* 推演跨度：{time_period}
* 切割方案：本次推演将行情时间轴切割为以下 {len(segments)} 个关键阶段：
"""
    
    for seg in segments:
        report += f"  ▸ {seg}\n"
    
    report += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Add each segment
    for result in segment_results:
        interp = result['interpretation']
        trace = result['trace']
        
        report += f"""
┌─────────────────────────────────────┐
│ 阶段 {result['index']}：{result['label']}              │
└─────────────────────────────────────┘

① 推演之问
   「{stock_name}在{result['label']}内，其价格命数是否向阳而升？」

② 神谕裁决（Oracle's Verdict）
   ┌ Final Row（最终字母行）：{trace['final_row']}
   ├ 神谕原文（Transliteration）：{result['transliteration']}
   ├ 中文译意：{interp['signal']}之势
   └ 元素归属：{interp['element_combo']}

③ 行情信号解读
   ┌ 趋势方向：{interp['direction']}
   ├ 信号强度：{interp['stars']}
   ├ 核心行情论断：{interp['signal']}，{interp['action']}
   └ 关键价格行为：{'放量突破关键阻力位' if '涨' in interp['direction'] else '缩量回调寻求支撑' if '跌' in interp['direction'] else '横盘整理等待方向'}

④ 深度行情推演
   此阶段神谕显示{interp['element_combo']}元素主导，对应{interp['signal']}之象。
   从资金动向看，{'主力资金积极入场' if '涨' in interp['direction'] else '主力资金谨慎观望' if '跌' in interp['direction'] else '多空力量相对均衡'}。
   技术面呈现{'突破形态' if '涨' in interp['direction'] else '破位风险' if '跌' in interp['direction'] else '震荡整理'}，
   建议投资者{interp['action']}。

⑤ 算法回溯（Trace）
   ▸ Asas      ：{trace['asas']}
   ▸ MS1       ：{trace['ms1']}
   ▸ Fasla     ：{trace['fasla']}
   ▸ Mustahisla：{trace['mustahisla']}
   ▸ Final Row ：{trace['final_row']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Overall assessment
    report += f"""
━━ 二、全周期综合行情研判 ━━━━━━━━━━━━

▸ 整体趋势判断：
  — 主基调：{overall_trend}
  — 整体信号强度：{overall_stars}

▸ 关键转折时段：{key_segment}

▸ 分时段操作天机：
"""
    
    for result in segment_results:
        action = result['interpretation']['action']
        report += f"  ▹ {result['label']}：{action}\n"
    
    report += f"""
▸ 天机警示（最高风险）：
  需警惕{segments[-1]}阶段的获利回吐压力及突发事件风险

▸ 最佳入场窗口：{segments[0]}
▸ 最佳离场窗口：{segments[-1]}

━━ 三、深化推演邀请 ━━━━━━━━━━━━━━━━━━

本报告已完成【{stock_name}】在【{time_period}】的天机分段推演。
若您需要对某一阶段进行更微观的推演，请提出您的具体指令。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 免责声明：本推演结果由 Ilm al-Jafar 古典算法生成，仅供参考娱乐，
不构成任何投资建议。投资有风险，入市须谨慎。
"""
    
    return report


def get_time_segments(time_period: str) -> list:
    """Get time segments based on period"""
    segments_map = {
        'today': ['早盘（09:30-11:30）', '午盘（13:00-14:00）', '尾盘（14:00-收盘）'],
        '今日': ['早盘（09:30-11:30）', '午盘（13:00-14:00）', '尾盘（14:00-收盘）'],
        'week': ['周一至周二（开局）', '周三（中枢）', '周四至周五（收官）'],
        '本周': ['周一至周二（开局）', '周三（中枢）', '周四至周五（收官）'],
        'month': ['上旬（1-10日）', '中旬（11-20日）', '下旬（21日-月底）'],
        '本月': ['上旬（1-10日）', '中旬（11-20日）', '下旬（21日-月底）'],
        'quarter': ['第一月（开仓期）', '第二月（持仓期）', '第三月（结算期）'],
        '本季度': ['第一月（开仓期）', '第二月（持仓期）', '第三月（结算期）'],
        'year': ['Q1（春季行情）', 'Q2（夏季行情）', 'Q3（秋季行情）', 'Q4（年末行情）'],
        '本年': ['Q1（春季行情）', 'Q2（夏季行情）', 'Q3（秋季行情）', 'Q4（年末行情）']
    }
    return segments_map.get(time_period, segments_map['today'])
