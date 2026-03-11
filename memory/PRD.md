# 全亚洲金融市场智能预测平台 PRD

## 项目概述
全亚洲金融市场智能预测平台，覆盖中国A股、港股、日股、韩股、泰股、期货、外汇七大市场。界面风格对标同花顺交易终端，采用深色主题、数据密集、专业金融UI设计。

## 用户画像
- 中国及亚洲投资者
- 金融分析爱好者
- 对神秘学感兴趣的投资者

## 核心需求
1. 实时行情数据展示（Yahoo Finance API + Alpha Vantage备选）
2. AI智能预测（MiniMax M2.5 API - 博士级金融分析）
3. 占卜推演（Qaida Tarweehat 神谕系统）
4. 股票搜索功能
5. 多市场分类导航（含美股市场）
6. 自选股功能
7. 预测历史记录
8. **多语言支持（8种语言）**
9. **金融新闻集成**
10. **K线图技术指标（MACD/RSI/布林带）**

## 已实现功能 (2026-03-11 更新)

### 后端 (FastAPI)
- [x] /api/markets - 获取所有市场列表
- [x] /api/market/{type} - 获取特定市场股票列表
- [x] /api/stock/{symbol} - 获取股票详情和历史数据
- [x] /api/search - 股票搜索
- [x] /api/overview - 市场总览（涨跌幅榜）
- [x] /api/predict/ai - AI智能预测
- [x] /api/predict/divination - 占卜推演
- [x] /api/watchlist/{client_id} - 自选股CRUD
- [x] /api/watchlist/{client_id}/data - 带行情的自选股
- [x] /api/history/save - 保存预测历史
- [x] /api/history - 查询预测历史（支持筛选）
- [x] /api/history/{id} - 删除历史记录
- [x] /api/news - 金融新闻API

### 前端 (React + Tailwind)
- [x] 首页市场总览（涨幅榜/跌幅榜/实时行情）
- [x] 市场分类导航（A股/美股/港股/日股/韩股/泰股/期货/外汇）
- [x] 股票列表页（支持排序）
- [x] 股票详情页（K线图+预测面板+添加自选按钮）
- [x] AI智能预测页面（博士级分析，蓝色科技风）
- [x] 占卜推演页面（金色神秘风）
- [x] 自选股页面（添加/删除/实时行情）
- [x] 预测历史页面（筛选/删除/查看详情）
- [x] 全局搜索功能
- [x] 响应式设计
- [x] 60秒自动刷新
- [x] **多语言支持（8种语言）**
- [x] **首页金融新闻组件**
- [x] **K线图技术指标（MACD/RSI/布林带）**

### 多语言支持 (2026-03-11 新增)
- [x] i18n框架集成（i18next风格自定义实现）
- [x] 支持8种语言：中文、英文、日文、韩文、泰文、马来文、印地文、阿拉伯文
- [x] 语言选择器组件（Header顶部）
- [x] RTL方向支持（阿拉伯语）
- [x] 翻译覆盖所有UI文本

### 金融新闻集成 (2026-03-11 新增)
- [x] /api/news 后端端点（支持Yahoo Finance RSS）
- [x] FinancialNews组件（首页右侧显示）
- [x] 支持多地区新闻（中国/日本/香港/韩国/亚洲）
- [x] 5分钟自动刷新

### K线图技术指标 (2026-03-11 新增)
- [x] TechnicalIndicatorsChart组件
- [x] MACD指标（DIF/DEA/柱状图）
- [x] RSI指标（带70/30超买超卖线）
- [x] 布林带（上轨/中轨/下轨）
- [x] 指标切换按钮（可独立开关每个指标）
- [x] 技术指标面板显示/隐藏控制

### 数据源集成
- [x] Yahoo Finance API（主数据源）
- [x] Alpha Vantage API（备选数据源，Yahoo失败时自动切换）
- [x] MiniMax M2.5 API（AI预测 + 占卜推演）

### 新增功能 (2026-03-11 更新)
- [x] Alpha Vantage备选数据源
- [x] 自选股功能（LocalStorage客户端ID + MongoDB存储）
- [x] 预测历史记录（MongoDB，保留3个月）
- [x] 博士级AI分析提示词（CFA+FRM+PhD级别量化分析框架）
- [x] 美股市场支持（AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, BRK-B, JPM, V）
- [x] 修复空搜索返回422错误的bug（现返回空数组）

### AI解读模块优化 (2026-03-11 新增)
- [x] 全新博士级System Prompt - 包含7大市场专项框架
- [x] 前端技术指标计算 - calculateAllIndicators()在调用AI前执行
- [x] 技术指标快照卡片 - 显示价格、涨跌幅、均线排列、MACD、RSI、技术评分等
- [x] 新增volume_price_analysis - 量价分析（成交量趋势、量价关系、机构行为）
- [x] 新增bollinger_analysis - 布林带分析（带宽状态、挤压预警）
- [x] 新增idiosyncratic_risks - 标的特有风险（区别于系统性风险）
- [x] 可折叠详细分析面板 - 趋势/动量/量价/布林带分析
- [x] 5段式专业叙述报告 - opening/technical/fundamental/synthesis/forward_guidance
- [x] 看多/看空概率校验 - 两者之和必须等于100%

## 技术架构
- 前端: React 19 + Tailwind CSS + Recharts + Shadcn/UI
- 后端: Python FastAPI + Motor (MongoDB)
- 数据源: Yahoo Finance API + Alpha Vantage (backup)
- AI: MiniMax M2.5 API
- 前端计算: 技术指标计算器 (technicalIndicators.js)
- 国际化: 自定义i18n系统 (8种语言)

## 关键文件
- /app/backend/server.py - 主后端服务
- /app/backend/services/ai_prediction_prompts.py - 博士级AI提示词模块
- /app/frontend/src/pages/AIPredictionPage.jsx - AI预测页面
- /app/frontend/src/pages/StockDetailPage.jsx - 股票详情页（含技术指标）
- /app/frontend/src/utils/technicalIndicators.js - 技术指标计算器
- /app/frontend/src/i18n/translations.js - 多语言翻译配置
- /app/frontend/src/i18n/LanguageSwitcher.jsx - 语言选择器
- /app/frontend/src/components/FinancialNews.jsx - 金融新闻组件
- /app/frontend/src/components/TechnicalIndicatorsChart.jsx - 技术指标图表组件

## 优先级功能列表

### P0 (已完成)
- 实时行情展示
- 市场分类导航
- AI智能预测
- 占卜推演
- 股票搜索
- 自选股功能
- 预测历史记录
- 备选数据源
- **多语言支持（8种语言）**
- **金融新闻集成**
- **K线图技术指标（MACD/RSI/布林带）**

### P1 (命理系统 - 阶段1已完成 2026-03-11)
- ✅ 命理计算引擎（四柱八字、五行统计、喜忌神判断、大运流年）
- ✅ 真太阳时校正（基于出生地经纬度）
- ✅ 节气精确时刻计算
- ✅ 用户注册系统（收集生辰八字信息）
- ✅ 用户登录系统
- ✅ 注册页面（三步骤：账户信息→生辰信息→命盘预览）
- ✅ 命盘展示页面（八字表格、五行雷达图、流年运势、投资建议）
- ✅ 股票板块映射（基于喜用神+CLSA风水指数推荐行业）
- ✅ 侧边栏命理中心入口

### P1 (命理系统 - 阶段2&3待实现)
- 首页个性化推荐（基于喜用神置顶对应板块）
- AI预测联动（命盘匹配度分析）
- 占卜联动（自动填入用户信息）
- 用户主页月度吉凶日历

### P2 (待实现)
- 预测准确率统计
- 社区讨论功能
- 价格提醒功能
- 分享预测报告

## 命理系统架构 (2026-03-11 新增)

### 后端API
- `/api/bazi/provinces` - 获取省份列表（34个省市自治区）
- `/api/bazi/cities/{province}` - 获取城市列表
- `/api/bazi/shichen` - 获取时辰选项（13个，含"不知道"）
- `/api/bazi/calculate` - 计算八字命盘
- `/api/auth/register` - 用户注册（自动计算命盘）
- `/api/auth/login` - 用户登录
- `/api/user/{user_id}` - 获取用户资料
- `/api/user/{user_id}/bazi` - 获取用户命盘
- `/api/user/{user_id}/bazi/refresh` - 刷新用户命盘

### 命理计算模块
- `/app/backend/services/bazi/calculator.py` - 八字计算器核心
- `/app/backend/services/bazi/constants.py` - 天干地支/五行/生肖常量
- `/app/backend/services/bazi/solar_terms.py` - 节气精确时刻计算
- `/app/backend/services/bazi/city_coordinates.py` - 城市经纬度数据库

### 前端页面
- `/register` - 注册页面（三步骤表单）
- `/login` - 登录页面
- `/profile` - 命盘展示页面

## 下一步任务
1. **阶段2&3**: 命理系统与App其他模块联动
   - 首页个性化推荐
   - AI预测命盘匹配度
   - 占卜自动填入用户信息
2. 用户头像上传功能
3. 预测准确率回测

## 免责声明
本平台提供的所有预测内容（包括AI分析、占卜推演和命理分析）均仅供娱乐参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
