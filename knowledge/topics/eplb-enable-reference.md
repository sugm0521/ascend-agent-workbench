---
id: eplb-enable-reference
title: MRV2下EPLB启用的版本化参考与验证边界
status: candidate
updated_at: '2026-10-15T19:23:21+08:00'
verified_at: '2026-10-15T17:39:04+08:00'
tags:
- EPLB
- MRV2
- STAIR
- KimiK3
- 启用参考
applies_to: 2026-10-15所核对A5/KimiK3 W4A8-MXFP、D TP8/DP4/EP32与P TP8/PP4；vLLM-Ascend0.30.0rc2.dev10+g6d4339aa1.d20261012加EPLB补丁，历史补丁实现未公开，当前适用性待复核
sources: []
observed_at: '2026-10-15'
evidence_scope: 历史调查摘要；原始材料未发布，不能由本仓库独立复验当前部署或实现
---

# MRV2下EPLB启用的版本化参考与验证边界

## 适用范围与已有证据

这是2026-10-15一次历史已运行配置的参考片段，不是任意模型/量化/版本的默认部署方案。原始材料与补丁未发布，状态为 candidate，当前适用性待复核。历史配置限定D侧4个TP8/DP4实例、总EP32，P侧TP8/PP4。版本为vLLM-Ascend 0.30.0rc2.dev10+g6d4339aa1.d20261012、vLLM0.30.0+empty、Mooncake0.3.11.post1、torch-npu2.10.0.post7；历史核对的CANN版本为9.2.0/V100R001C12SPC001B234安装信息，不冒充每个历史进程动态库映射。

原基线加补丁不能用包版本完整表示。对应补丁没有公开的完整复现来源，目标环境必须重新确认模型、量化与EPLB接口支持；不能用文件存在证明所有分支都被执行。

## 启用前置判断

确认当前模型/MoE登记、量化方法、冗余专家及权重视图支持EPLB，并与实际vLLM runner接口匹配。本任务曾补充量化/EPLB、Kimi/MTP和HIXL配套；这些支持条件不能靠添加CLI绕过，也不能把历史六笔PR变成未来版本无条件cherry-pick清单。先检查所用分支实际实现，有遗漏再定点核对对应补丁。

仅计划启用EPLB时读取本条。保留用户已确认的拓扑、KV连接器和模型参数，不因参考示例自动切换模型、并行、量化、环境或停止/重启服务。

## 历史D侧参数片段

以下保留历史D侧参数及当时 `enable_eplb=True` 的观察。它不是完整P/D启动命令，也不能独立复现原部署；使用前先核对目标版本支持，再与实际D启动参数组合，TP/DP/rank/端点等按实际部署填写。

```bash
export VLLM_USE_V2_MODEL_RUNNER=1

eplb_args=(
  --enable-expert-parallel
  --enable-eplb
  --eplb-config.window_size 600
  --eplb-config.step_interval 50
  --eplb-config.num_redundant_experts 32
  --eplb-config.use_async true
  --eplb-config.policy stair
)
# 已有D侧vllm serve命令追加 "${eplb_args[@]}"；这里只定义片段，不启动服务。
```

window_size/step_interval按引擎step计，不是秒；冗余32为该样例每MoE层的副本槽位配置，需满足当前模型和并行约束，不是32个新逻辑专家。样例采用自动选择出的HIXL通信器，不能据此保证所有环境相同。

历史P侧未设置enable-eplb；不要为了“八机一致”将上述D参数复制到PP4的P侧。草稿模型EPLB关闭而target保持开启符合本样例。该历史MRV2实现不能补DYNAMIC_EPLB=true，判断边界见[运行阶段判读](eplb-runtime-evidence.md)。

## 超时配套与初始化修改单独记录

该历史配置另有ASCEND_CONNECT_TIMEOUT=60000（毫秒）、ASCEND_TRANSFER_TIMEOUT=180000（毫秒）、MC_TRANSFER_TIMEOUT=300（秒），属于Mooncake KV预算，作用/读取时机见[分层超时](mooncake-nested-timeout.md)。这是样例选用环境；脚本值与组件实际解析是不同证据，不能只靠export证明存量进程生效。

历史通信器实现另有初始化同步300→1200秒修改；单次connect/运行传输/cleanup仍300秒。它是本任务代码调整，不是上述环境变量的效果，不向其他版本承诺同名开关。历史成功轮没有耗尽原预算，不能将1200秒写成启动的普遍必要条件或已修复加载停滞。

## 真实运行与精度边界

历史调查摘要记录该部署完成通信器初始化，并在评测负载下发生布局提交；当时观测窗口未见此前KV/batch失败。原始运行材料未发布，这不构成仓库可独立复验的功能验收。停止信号后的API错误应与评测窗口内的自发故障分开，不能仅看日志末尾异常判断精度测试失败。

历史评测观察用于限定这份配置的验证层级：它进入过GPQA评测，但不同并发的结果不是同条件重复；保存输出仍有缺有效最终选项、reserved字面量、工具协议或异常字符。没有原始逐请求finish_reason/完整推理和小算子或严格EPLB开关A/B，不能认定精度完全通过、截断机制已定位或融合算子无问题。本条仅保留可复用设置与历史观察的验收边界，不发布逐轮任务进度或私有材料索引。

## 复核、访问与失效条件

原证据日期为2026-10-15，历史运行/评分窗口为11:39–14:38；`verified_at` 保留原离线复核时间。本次仅清理发布内容，没有重新验证部署或刷新原实验时间。配置与运行结论均为历史摘要，原始材料及补丁未公开；使用者只能按上述边界参考，不能宣称从本仓库独立复验当前部署。

runner、CLI字段、模型/量化、并行拓扑、冗余专家约束、策略或通信实现变化时重新核对对应项；未使用EPLB的普通服务不触发本参考。初始化与日志字段验证参阅已有运行证据条目，输出质量沿原精度流程检查，不为本条自动发推理或打流。
