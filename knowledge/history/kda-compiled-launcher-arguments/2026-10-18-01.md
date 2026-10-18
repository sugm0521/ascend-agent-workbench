---
id: kda-compiled-launcher-arguments
title: KDA预编译直接调用须区分编译期绑定与运行时参数
status: candidate
updated_at: '2026-10-17T10:23:40+08:00'
verified_at: '2026-10-17T10:23:40+08:00'
observed_at: '2026-10-16'
evidence_scope: 固定公开源码的两处调用已核对；参数报错、安装launcher签名及修改后请求仅有历史运行记录，本轮未重新运行；运行环境完整构建来源未公开，当前其他组合适用性待确认
tags: [KDA, Triton, CompiledKernel, constexpr, A5, 参数签名]
applies_to: vLLM-Ascend 7759ceecee1c3ea21a4d47d55f93545fca895088的KDAStateCopyPlan直接预编译调用，以及2026-10-16 A5运行摘要；须另核对实际Triton Ascend launcher ABI，不外推所有Triton后端或版本
sources:
  - id: kda-plan-source
    path: https://github.com/vllm-project/vllm-ascend/blob/7759ceecee1c3ea21a4d47d55f93545fca895088/vllm_ascend/ops/kda_state_copy_plan.py
    revision: 7759ceecee1c3ea21a4d47d55f93545fca895088
    locator: KDAStateCopyPlan.prepare的TO_CACHE/HAS_FLAGS/BLOCK_SIZE绑定；KDAStateCopyPlan._launch的直接CompiledKernel调用
    observed_at: '2026-10-17T10:23:40+08:00'
    evidence: source
    access: published
---

# KDA预编译直接调用的参数边界

## 结论与触发条件

预热能够编译、服务健康检查通过，仍可能在首次真实KDA请求中出现直接launcher参数数量错误。遇到这种错误，应对照编译时绑定、直接调用实参和实际生成launcher签名；不要仅凭Python kernel声明或旧注释重传编译期常量。

本条保留的是特定实现的失败路径和复核方法。`candidate`表示历史运行无法由公开仓库独立复验，实际安装后端仍须核对；不是要求所有CompiledKernel调用统一删参数。

## 公开源码与历史运行分别支持什么

- **公开source事实**：固定源码的`prepare`将三个常量作为JIT关键字绑定，`_launch`又把对应值作为位置参数传入预编译对象。源码能证明这两处传参不同，不能单独证明任何后端生成的ABI。
- **2026-10-16历史runtime摘要**：在A5的KDA prefill/gather路径中，launcher报接收18项却传入21项；当时安装实现为9项固定启动信息加9项kernel运行时参数。多出的3项对应上述已绑定常量。首次请求失败发生在此调用，不是退出清理异常。
- **历史修改与验证范围**：只去掉直接调用末尾的3项，保留prepare绑定、kernel数学实现与其他配置后，后续真实PD请求及一轮120请求输出1024 tokens的性能负载通过。没有独立算子精度矩阵、全部变体覆盖或全面语言精度验收，不能据此宣布所有状态拷贝语义已验证。

历史安装包、实际launcher及运行原件未发布；上述运行与恢复摘要不是公开source条目提供的证明。公开基线也不代表叠加补丁和安装组件的完整复现条件。

## 遇到同类错误时的复核方法

1. 先定位首个参数错误的调用栈，区分初始化JIT入口与请求期直接预编译入口；HTTP健康不替代执行该分支的真实请求。
2. 在当前安装版本中逐项对照固定启动信息、指针/标量实参和已绑定常量，检查参数数量、顺序及类型。以实际launcher为准，不能把历史的18/21项当作新版本标准。
3. 已有修复授权时，只处理已定位的不匹配；沿当前任务要求验证实际gather/scatter、相关dtype和索引变体。保留原失败，未跑的必需项继续列缺口。

## 限制与复查触发

本条不证明当前main仍存在相同错误，不涵盖其他CompiledKernel后端、fallback或不同ABI。更换Triton/Ascend后端、调整JIT绑定或直接调用路径、修改缓存布局/索引类型时，重新对照实际生成签名及相应执行路径。新增可公开复验的运行证据前保持候选。
