# Qraft 6.1 TUI 开发规划表（与 TUI6.1 设计方案对齐）

> 原则：小步快跑、零假设开发；严格复用既有 CLI/API/工件；以“SSOT + 单帧直绘 + 统一输入 + 流程编排”为主线。

---

## 里程碑与执行

### M1：框架收口（1–2d）
- 仅保留 Live-only 渲染路径：移除/封装一切 print/clear 型输出，Dashboard 只通过 live.update。
- 统一输入：默认 live.console.input；PT 存在时启用 PromptSession；无 PT 回退 input。
- 固化输入栏：输入不暂停 Live，不影响主帧渲染。
- 交付：Dashboard 不闪屏/不叠加标题，任何时刻都有输入栏。

### M2：SSOT 状态化（1–2d）
- `qraft/tui/state.py`：完善 UIState/RunStore 字段（filters/pagination/tail_offset/active_overlay/workflow_state）。
- `tui_cmd.py`：事件→reducer→render，所有面板只读状态；去除旧 Tab 逻辑残留。
- 交付：选中/刷新/滚动/分页等操作均经由状态生效。

### M3：监控与日志（1–2d）
- Recent Runs：分页/筛选/状态徽章；僵尸检测（pid/host/心跳）。
- Log tail：后台 `LogTailMonitor` + j/k/pgup/pgdn/home/end 滚动；l/x 调整窗口。
- 交付：切换 run 即切尾巴；右栏/底部与状态一致。

### M4：表单与 Tasks 覆盖层（1–2d）
- Tasks/Monitor/Artifacts 作为覆盖层在主帧内显示（取消暂停 Live 的旧做法）。
- 表单：PT（PathCompleter/枚举/历史/步进/日期快捷）；无 PT 回退 input；Dry-run 预览后执行。
- 交付：零盲区（仅暴露已实现）、无模式切换残留、体验一致。

### M5：一键流程编排（2–3d）
- `qraft/tui/workflows.py`：定义 pipeline builder（Data→Search→QuickBT→PreciseBT→Portfolio→Risk→Evidence→Pool→Deploy）。
- 持久化：`artifacts/<pipeline_run>/_pipeline.json`；可干跑/执行/续跑。
- Main 展示“进度条 + 步骤摘要 + 下一步”；右栏/底部联动。
- 交付：一键 Demo 流程可用。

### M6：质量门槛与指标卡（1–2d）
- 指标卡：search/evidence 聚合结果只读展示。
- 质量门槛卡片：两阶段一致性、冷启动复跑、成本敏感性、Top‑N 重叠率（读取既有报表）。
- 交付：Main/右栏给出清晰“是否达标”的可视反馈。

### M7：验收与文档（0.5–1d）
- flake8 改动文件 0 告警；pytest 通过。
- 更新 cookbook：键位/工作流/覆盖层/降级开关；录屏脚本。

---

## 任务清单（可执行项）
1) Live-only 渲染与输入统一化
- Dashboard 仅 live.update；输入使用 live.console.input/PT PromptSession；纯文本兜底开关保留。

2) SSOT 与事件循环
- UIState/RunStore 扩展；tui_cmd 事件→reducer→render；移除旧 Tab 残留。

3) 监控与 Log tail
- Recent Runs 分页/筛选/状态徽章；僵尸检测；Tail 后台刷新 + 键位滚动。

4) 覆盖层子视图
- Tasks/Monitor/Artifacts 以覆盖层方式呈现；返回恢复主帧；不切屏。

5) 一键流程
- workflows.py builder；可干跑/执行/续跑；_pipeline.json 持久化；Main 展示进度。

6) 指标卡与质量门槛
- search/evidence 指标卡；质量门槛状态卡片显示。

7) 文档与验收
- 更新 cookbook 与 examples；flake8/pytest 绿。

---

## 风险与回退
- 终端兼容：默认全屏；异常以环境变量关闭；保留纯文本兜底。
- 文件体量：tail/监控分页与节流；
- 活性误判：保守判断 + 明确“未确认”提示。

---

## 验收标准（TUI 6.1）
- 单屏四区稳定联动；输入栏固定存在；无标题叠加/闪屏/plain 回退。
- 一键流程可用（干跑/执行/续跑）；Main/右栏/底部联动；日志可滚动。
- 代码质量：改动文件 flake8 0 告警；pytest 全量通过。
