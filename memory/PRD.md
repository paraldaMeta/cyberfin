# 全亚洲金融市场智能预测平台 PRD

## 项目概述
全亚洲金融市场智能预测平台，覆盖中国A股、港股、日股、韩股、泰股、期货、外汇七大市场。界面风格对标同花顺交易终端，采用深色主题、数据密集、专业金融UI设计。

## 用户画像
- 中国及亚洲投资者
- 金融分析爱好者
- 对神秘学感兴趣的投资者

## 核心需求
1. 实时行情数据展示（Yahoo Finance API）
2. AI智能预测（MiniMax M2.5 API）
3. 占卜推演（Qaida Tarweehat 神谕系统）
4. 股票搜索功能
5. 多市场分类导航

## 已实现功能 (2026-03-11)

### 后端 (FastAPI)
- [x] /api/markets - 获取所有市场列表
- [x] /api/market/{type} - 获取特定市场股票列表
- [x] /api/stock/{symbol} - 获取股票详情和历史数据
- [x] /api/search - 股票搜索
- [x] /api/overview - 市场总览（涨跌幅榜）
- [x] /api/predict/ai - AI智能预测
- [x] /api/predict/divination - 占卜推演

### 前端 (React + Tailwind)
- [x] 首页市场总览（涨幅榜/跌幅榜/实时行情）
- [x] 市场分类导航（A股/港股/日股/韩股/泰股/期货/外汇）
- [x] 股票列表页（支持排序）
- [x] 股票详情页（K线图+预测面板）
- [x] AI智能预测页面（蓝色科技风）
- [x] 占卜推演页面（金色神秘风）
- [x] 全局搜索功能
- [x] 响应式设计
- [x] 60秒自动刷新

### 集成
- [x] Yahoo Finance API（实时行情）
- [x] MiniMax M2.5 API（AI预测 + 占卜推演）

## 技术架构
- 前端: React 19 + Tailwind CSS + Recharts + Shadcn/UI
- 后端: Python FastAPI + Motor (MongoDB)
- 数据源: Yahoo Finance API
- AI: MiniMax M2.5 API

## 优先级功能列表

### P0 (已完成)
- 实时行情展示
- 市场分类导航
- AI智能预测
- 占卜推演
- 股票搜索

### P1 (待实现)
- 自选股功能
- 预测历史记录
- 用户收藏功能

### P2 (待实现)
- K线图更多指标（MACD/RSI/布林带）
- 新闻资讯整合
- 社区讨论功能

## 下一步任务
1. 增加更多技术指标到K线图
2. 实现自选股功能
3. 添加预测历史记录存储
4. 优化MiniMax API响应（真实AI分析）
5. 添加更多市场数据源备选（Alpha Vantage）

## 免责声明
本平台提供的所有预测内容（包括AI分析和占卜推演）均仅供参考研究，不构成任何投资建议。投资有风险，入市须谨慎。
