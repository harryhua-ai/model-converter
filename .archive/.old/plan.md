# Sprint 1 计划：前端设计优化（简约科技风）与组件化重构

## 核心目标
1. 彻底解决 `HomePage.tsx` 庞大且未组件化的问题。
2. 依据用户提供的参考图（CamThink AI Tools），将整体 UI 重构为“简约科技风”。
3. 替换低级的交互体验（用 Toast 替换原生 \`alert()\`）。

## 执行路径
- [ ] **样式底座更新**：调整 Tailwind 主题色，注入品牌橙红色，移除冗余的圆角和背景光晕。
- [ ] **组件切分抽取**：
  - [ ] 上传区块 (`FileUploadArea`)
  - [ ] 预设选项卡 (`PresetCard`)
  - [ ] 配置信息确认 (`ConfigSummaryBox`)
- [ ] **HomePage 重装**：应用深色顶部 Hero 区，排版整体扁平化、规整化。
- [ ] **交互补充**：接入 Toast 弹窗反馈机制。
