# model_analysis 调用说明

仅在用户要求模型架构报告、新旧模型比较、参数/KVCache 或量化并行权重估算时使用。普通部署、性能或精度任务继续走原入口；确实需要前期架构分析时才读取本来源。

## 来源与调用

从 [sources.lock.yaml](../../../../upstream/sources.lock.yaml) 的 `model_analysis` 和本机同名配置解析实际路径，核对真实 Git 根与完整 SHA。默认入口是 [原 SKILL](../../../../deps/model-analysis/skills/ascend-model-analysis/SKILL.md)，生成 HTML 时再读取其 [CSS/DFG 模板](../../../../deps/model-analysis/skills/ascend-model-analysis/references/css-template.md)。不复制整份 skill 或建立全局安装副本；外部维护源保持只读。

沿用原结构和计算复核方法，工具名称按当前可用接口解释：Read/Grep 使用实际文件读取与检索，计算通过本地 Python，WebFetch 仅针对用户指定资料或模型文件 API；遵守用户禁止浏览模型厂商主页的要求。需要远程运行时仍用原工作台工具。本来源不要求新身份、provider 或资源系统。

模型分析使用独立目录 `tasks/<模型名>-模型分析/<YYYYMMDD>-<分析序号>/`；同一模型的独立分析序号从 1 连续递增，每次新建模型目录下的同级工作目录，同一次中断恢复沿用原轮次。按[材料规范](../../../../docs/guides/task-records.md#任务目录与唯一入口)在该轮 configs/scripts/results 中分别组织输入配置、计算脚本、报告及生成的 HTML，根目录保留任务说明。大型输入进入 `.workbench-local/`，索引按需在本机解析，向会话仅提供必要摘要并遵守当前环境已确认的传输约束；不上传权重或原仓的大型资料。输入记录实际 config/code/index/card 来源、revision/SHA256，下载核对真实文件名、HTTP 成功及内容可解析性。

## 项目侧边界

- **版本**：记录模型资料、模型实现、vLLM/vLLM-Ascend 的实际 SHA 与影响结论的 dirty 内容。原 skill 的“干净 transformers 自动 pull”在本项目改为使用已确认版本；版本更新由 dependencies 流程处理。
- **架构证据**：config、模型代码、权重索引与模型卡交叉核对。仅索引或单一资料支持的结论标注推断/单源；缺代码不编造算子流，历史报告不替代当前输入。
- **支持与优先级**：对照任务实际 vLLM/vLLM-Ascend/CANN 实现，输出已支持/需适配/缺失/待验证及证据。按任务目标决定 P0/P1/P2，原模板的常见 P0 名称只作需求线索；源码入口存在也不证明全部形状、dtype、图模式或芯片已通过。
- **容量**：显式区分权重估算、每 token KV、每序列固定递归/卷积状态及运行余量。TP/DP/EP/P-D、MTP 与量化覆盖按实际实现记录；量化 scale/zero、激活、通信缓冲、图池等未计项写清。EP 公式不能改名作为 TP 结果，权重能装下不等于可部署。
- **验证**：按原 verification pass 独立重算关键参数、单位、KV 与至少两组权重矩阵，核对章节和 HTML。已有样例有硬编码路径和计算错误，只作参考；专用计算放任务目录，修改数据后重查受影响结果。
- **后续工作**：报告形成适配任务和验证建议；实际改码、部署、精度/性能验收使用已有 execution/review 与领域工具，遵循用户具体授权。

## 当前来源缺口

在固定提交 `b4b1dc1b0f742da29f054c91086aac373134a19d` 中：`Kimi-K3` 与 `transformers` 是 gitlink，却没有 `.gitmodules`；保持未初始化。需要相关实现时复用已确认来源，不猜 URL、不无条件递归。根/skill 的全仓许可未明确，本次用户已授权本机资料引用接入；这不证明可再分发原仓代码、模板或打包发布。许可状态随来源检查记录，不用模型源码的局部许可覆盖整个仓库。

已有样例的参数计数、并行口径与资料一致性按本文容量和验证要求独立复核；样例报告不能代替当前模型输入。普通方法引用无需全量执行原仓脚本或测试。
