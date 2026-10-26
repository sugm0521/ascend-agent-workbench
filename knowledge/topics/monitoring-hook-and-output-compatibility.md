---
id: monitoring-hook-and-output-compatibility
title: 监控hook与NPU命令输出变化的证据边界
status: candidate
updated_at: '2026-10-26T14:40:16.513692+08:00'
verified_at: '2026-10-26T14:40:16.513692+08:00'
observed_at: '2026-10-23'
tags: [监控, profile_memory, v1_metrics, npu-smi, unknown]
applies_to: 历史监控适配26.0.0与Ascend f8750b59相关入口；npu-smi26.2新输出观察，不代表所有CLI版本
evidence_scope: 保存的日志、配置和源码观察；完整运行构建未公开，尚无跨版本公共工具验收；本条不实施工具修复
sources: []
---

# 监控失败与业务失败分别定位

历史hook配置引用不存在的`profile_memory`，加载异常被捕获后跳过。日志出现ERROR说明该hook没生效，不足以认定模型已经退出。需要核对配置项、目标模块/类的实际符号、异常处理与进程状态；用户随后手动停止业务，不能反推hook导致退出。

npu-smi26.2表格变化可能使只识别旧格式的解析器找不到设备或进程。未识别应保留unknown、原命令退出码和有界stdout/stderr，不能将解析空结果解释成0设备或空闲。先分设备列表、进程持有者、API与模型状态；一条格式变更不能支持重启或清理。

这类候选已确认收录为诊断知识，不等于授权修改/发布旧NPU查询工具或扩大其支持范围。未来实现应使用不同版本的真实保存样本验证，并明确旧/新格式及未知分支；本次不增加解析器或skill规则。

更换监控插件、Python接口、CANN或npu-smi版本时重新核对。复用[执行流程](../../.agents/skills/ascend-task-execution/SKILL.md)与[运行快照](../../.agents/skills/ascend-runtime-snapshot/SKILL.md)记录当时实现，不把历史unknown改写成通过。
