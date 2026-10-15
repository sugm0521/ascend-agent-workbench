---
id: eplb-enable-reference
title: MRV2下EPLB启用的版本化参考与验证边界
status: verified
updated_at: '2026-10-15T17:39:04+08:00'
verified_at: '2026-10-15T17:39:04+08:00'
tags:
- EPLB
- MRV2
- STAIR
- KimiK3
- 启用参考
applies_to: 2026-10-15所核对A5/KimiK3 W4A8-MXFP、D TP8/DP4/EP32与P TP8/PP4；vLLM-Ascend0.30.0rc2.dev10+g6d4339aa1.d20261012加EPLB补丁，实际代码以所列指纹限定
sources:
- id: launch-config
  path: tasks/eplb/results/accuracy-runs-review-20261015-1726/effective-eplb-config.json
  revision: sha256:ce245bf1eb23f4580038c6fb7c867206bb63138f9af5ce3636221a103227dd7f
  locator: roles.d0_0..d0_3.eplb_flags/environment/logged_enable_eplb/logged_enable_expert_parallel；P侧flags为空
  observed_at: '2026-10-15T09:26:27.848908+00:00'
  evidence: source
  access: local-only
- id: installed-code
  path: tasks/eplb/results/accuracy-runs-review-20261015-1726/effective-eplb-config.json
  revision: sha256:ce245bf1eb23f4580038c6fb7c867206bb63138f9af5ce3636221a103227dd7f
  locator: roles.*.source_fingerprints及versions；原读取source-state记录在同目录
  observed_at: '2026-10-15T17:30:55+08:00'
  evidence: source
  access: local-only
- id: evaluated-runs
  path: tasks/eplb/results/accuracy-runs-review-20261015-1726/accuracy-summary.json
  revision: sha256:153546abc810b53041fdd139a98892daee455a273ead2cd2bfa1072faa95e689
  locator: current_service_round=true的4组：20261015_115441/123440/130007/133309；官方逐题与保存文本核验
  observed_at: '2026-10-15T09:28:16.551045+00:00'
  evidence: runtime
  access: local-only
- id: service-window
  path: tasks/eplb/results/accuracy-runs-review-20261015-1726/service-analysis.json
  revision: sha256:e2d09356319ac4b75786b328990095899b14393a9b0faaea64bad6cd435f9aef
  locator: 当前四D角色的commits/first_errors/signals/kv_error_count，原日志11:39–14:38
  observed_at: '2026-10-15T09:26:27.848908+00:00'
  evidence: runtime
  access: local-only
- id: installed-cann
  path: tasks/eplb/results/accuracy-runs-review-20261015-1726/cann-current.json
  revision: sha256:918aead439ce923a3671b93698ad8b811dfac57b24d68ef43cbd3df034c7f7b5
  locator: ascend_toolkit_install.info.version/innerversion；本轮仅复核一个D节点安装信息
  observed_at: '2026-10-15T17:33:58+08:00'
  evidence: source
  access: local-only
---

# MRV2下EPLB启用的版本化参考与验证边界

## 适用范围与已有证据

这是一次已运行配置的参考片段，不是任意模型/量化/版本的默认部署方案。launch-config限定D侧4个TP8/DP4实例、总EP32，P侧TP8/PP4。版本为vLLM-Ascend 0.30.0rc2.dev10+g6d4339aa1.d20261012、vLLM0.30.0+empty、Mooncake0.3.11.post1、torch-npu2.10.0.post7；installed-cann为9.2.0/V100R001C12SPC001B234安装信息，不冒充每个历史进程动态库映射。

原基线加本地补丁不能用包版本完整表示。installed-code记录的实际关键文件SHA256：w4a8_mxfp4.py=`d33d1ee97c93d6b9fdb9193455aef6558c67efcd3af797e08e113acae1cb462f`；patch_eplb.py=`3605c7337f45b80ccda874850ba7575288f3c688d04e821c8ae67681beb32c68`；stair.py=`f340c5b95404c65d3da6e67242aa9499212d6a6e7ede2279dec2dcb9ef68d708`；eplb_communicator.py=`3597a8bd0b6c730169c846d5c384fcc687c85d63569143d480b4645c63429bf3`。八机当前回读一致，与本轮原有补丁记录相符；没有算子trace，不用文件存在证明所有分支都被执行。

## 启用前置判断

确认当前模型/MoE登记、量化方法、冗余专家及权重视图支持EPLB，并与实际vLLM runner接口匹配。本任务曾补充量化/EPLB、Kimi/MTP和HIXL配套；这些支持条件不能靠添加CLI绕过，也不能把历史六笔PR变成未来版本无条件cherry-pick清单。先检查所用分支实际实现，有遗漏再定点核对对应补丁。

仅计划启用EPLB时读取本条。保留用户已确认的拓扑、KV连接器和模型参数，不因参考示例自动切换模型、并行、量化、环境或停止/重启服务。

## 当前D侧参数片段

以下来自launch-config的4个D启动脚本，且当前启动日志记录enable_eplb=True。并非完整P/D启动命令；追加到本任务已核对的D启动参数，TP/DP/rank/端点等按实际部署填写。

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

本次P侧未设置enable-eplb；不要为了“八机一致”将上述D参数复制到PP4的P侧。草稿模型EPLB关闭而target保持开启符合本样例。当前MRV2不能补DYNAMIC_EPLB=true，具体实现和日志证据见[运行阶段判读](eplb-runtime-evidence.md)。

## 超时配套与初始化修改单独记录

launch-config的启动脚本另有ASCEND_CONNECT_TIMEOUT=60000（毫秒）、ASCEND_TRANSFER_TIMEOUT=180000（毫秒）、MC_TRANSFER_TIMEOUT=300（秒），属于Mooncake KV预算，作用/读取时机见[分层超时](mooncake-nested-timeout.md)。这是样例选用环境；脚本值与组件实际解析是不同证据，不能只靠export证明存量进程生效。

当前eplb_communicator.py另有本地初始化同步300→1200秒修改；单次connect/运行传输/cleanup仍300秒。它是本任务代码调整，不是上述环境变量的效果，不向其他版本承诺同名开关。历史成功轮没有耗尽原预算，不能将1200秒写成启动的普遍必要条件或已修复加载停滞。

## 真实运行与精度边界

service-window证实所列部署完成通信器初始化，并在评测负载下发生真实布局提交；应用日志的已归档观测窗口未见此前KV/batch失败。停止信号后的API错误应与评测窗口内的自发故障分开，不能仅看日志末尾异常判断精度测试失败。

evaluated-runs用于限定这份配置的验证层级：它进入过GPQA评测，但不同并发的结果不是同条件重复；保存输出仍有缺有效最终选项、reserved字面量、工具协议或异常字符。没有原始逐请求finish_reason/完整推理和小算子或严格EPLB开关A/B，不能认定精度完全通过、截断机制已定位或融合算子无问题。个人逐轮得分与进度保留在本机任务报告，本条仅保留可复用的设置、实际执行依据与验收边界。

## 复核、访问与失效条件

各source id对应相应段落。原日志/客户端快照于17:26/17:27采集，实际运行/评分在11:39–14:38；本次verified_at是离线复核时间。launch-config为已保存脚本与实际文件指纹，evaluated-runs/service-window来自明确轮次的历史运行材料。本机source为local-only，其他agent无原材料时只能参考已发布的限定结论，不能称独立复验当前部署。

runner、CLI字段、模型/量化、并行拓扑、冗余专家约束、策略或通信实现变化时重新核对对应项；未使用EPLB的普通服务不触发本参考。初始化与日志字段验证参阅已有运行证据条目，输出质量沿原精度流程检查，不为本条自动发推理或打流。
