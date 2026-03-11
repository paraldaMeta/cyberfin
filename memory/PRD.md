# 全亚洲金融市场智能预测平台 PRD

## 项目概述
全亚洲金融市场智能预测平台，覆盖中国A股、港股、日股、韩股、泰股、期货、外汇七大市场。界面风格对标同花顺交易终端，采用深色主题、数据密集、专业金融UI设计。

## 用户画像
- 中国及亚洲投资者
- 金融分析爱好者
- 对神秘学感兴趣的投资者

## 核心需求
1. 实时行情数据展示（Yahoo Finance API + Alpha Vantage备选）
2. AI智能预测（MiniMax M2.5 API）
3. 占卜推演（Qaida Tarweehat 神谕系统）
4. 股票搜索功能
5. 多市场分类导航
6. 自选股功能
7. 预测历史记录

## 已实现功能 (2026-03-11)

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

### 前端 (React + Tailwind)
- [x] 首页市场总览（涨幅榜/跌幅榜/实时行情）
- [x] 市场分类导航（A股/港股/日股/韩股/泰股/期货/外汇）
- [x] 股票列表页（支持排序）
- [x] 股票详情页（K线图+预测面板+添加自选按钮）
- [x] AI智能预测页面（蓝色科技风）
- [x] 占卜推演页面（金色神秘风）
- [x] 自选股页面（添加/删除/实时行情）
- [x] 预测历史页面（筛选/删除/查看详情）
- [x] 全局搜索功能
- [x] 响应式设计
- [x] 60秒自动刷新

### 数据源集成
- [x] Yahoo Finance API（主数据源）
- [x] Alpha Vantage API（备选数据源，Yahoo失败时自动切换）
- [x] MiniMax M2.5 API（AI预测 + 占卜推演）

### 新增功能 (2026-03-11 更新)
- [x] Alpha Vantage备选数据源
- [x] 自选股功能（LocalStorage客户端ID + MongoDB存储）
- [x] 预测历史记录（MongoDB，保留3个月）

## 技术架构
- 前端: React 19 + Tailwind CSS + Recharts + Shadcn/UI
- 后端: Python FastAPI + Motor (MongoDB)
- 数据源: Yahoo Finance API + Alpha Vantage (backup)
- AI: MiniMax M2.5 API

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

### P1 (待实现)
- K线图更多技术指标（MACD/RSI/布林带）
- 新闻资讯整合
- 预测准确率统计

### P2 (待实现)
- 社区讨论功能
- 价格提醒功能
- 分享预测报告

## 下一步任务
1. 添加更多技术指标到K线图
2. 整合财经新闻API
3. 优化MiniMax API调用获取更准确AI分析
4. 添加预测准确率回测功能

## 免责声明
本平台提供的所有预测内容（包括AI分析和占卜推演）均仅供参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
