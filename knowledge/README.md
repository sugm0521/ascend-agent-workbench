# 私有工程知识库接入与维护协议

公开工作台只保存通用接入方法、skill 和证据规范。工程知识正文、主题索引与历史保存在开发者自行选择的外部私有目录，不再放入本仓库。

## 目录绑定与检索

初始化由 [ascend-workbench-init](../.agents/skills/ascend-workbench-init/SKILL.md) 将“是否接入知识库、本机目录、远端不使用/复用/新建、定时维护及同步策略”纳入集中确认；已有明确选择复用。确认后仅在被 Git 忽略的 `config/workbench.local.yaml` 保存 `paths.knowledge_root`。提交的 [配置示例](../config/workbench.example.yaml) 保持 null；不预设用户名、盘符、笔记软件或私有仓库 URL。

- 缺字段、null 或空值：未配置，不以 shell 当前目录或公开 `knowledge/` 代替。
- 非空值：绝对路径直接解析，相对路径相对实际工作台根解析；解析符号链接后的真实目录必须在工作台之外。仅使用本机目录，不将远程路径当本地路径。
- 目录不存在、不可读或位于工作台内：说明具体缺口，暂停依赖它的知识写入；其他独立工作继续。接入/修复绑定走初始化的定向步骤，普通任务不运行完整初始化。
- 先读私有根 `AGENTS.md`、`README.md` 及相关分类规则，按实际布局定位正文和历史；默认布局见模板。按下文[分类检索与归档](#分类检索与归档)定位条目；默认排除历史，只按需追溯。写前重读目标、核对指纹与 owner，活动写入或基线变化时保留并报告。

该目录可为任意私有知识库的项目子目录，不要求 Git。本机存储、远端同步与定时维护独立选择，完整分支见[初始化接入约定](../.agents/skills/ascend-workbench-init/references/operations.md#私有知识目录接入)；仅本地也可定时整理，远端存在也可手动维护/同步。若使用 Git，另行核对实际仓根、私有可见性、作者/DCO、认证与发布授权；路径可读不表示已完成这些检查，也不触发建仓或同步。工程知识不能随公开工作台发布；在工作台内被忽略的副本也不能成为默认正文位置。

agent 先读取本机 YAML，再可调用已有验证器做只读检查（参数值由调用方解析，脚本不解析配置）：

```sh
python scripts/validate_workbench.py --knowledge-root <已确认目录> --knowledge-only
python scripts/validate_workbench.py --knowledge-root <已确认目录> --knowledge-path <库内实际相对条目路径> --knowledge-only
```

检查不创建目录或文件；ready 仅证明目录可读，`target_exists` 表示指定条目是否存在。所有知识读写都在解析后的私有根；缺配置时正常公开仓验证仍可运行，业务候选可留本机任务等待接入。

自动归档遵循 [每日同步说明](../docs/guides/daily-sync.md)，检索和维护使用 [ascend-knowledge-curation](../.agents/skills/ascend-knowledge-curation/SKILL.md)。个人日报、任务状态与原始日志留本机任务/忽略目录，不包装成知识；知识库不替代任务当前状态。没有新知识不凑条目。

## 规则分工与初始模板

本目录保存公共接入协议与通用模板，不保存实际工程知识。知识根路径、远端、同步及调度选择留调用方本机配置；目标库 AGENTS.md 维护目录、检索、更新、字段与历史规则，README.md 维护导航。skill 负责解析绑定、读取库内规范、核对授权和证据并交付结果。

新建知识库先取得并核对实际目标目录，再将 [初始操作规范](templates/AGENTS.example.md) 按已确认布局调整后保存为知识根 AGENTS.md，并由最小首页链接；首页说明用途及正文/历史位置，其他目录按首次需要创建。远端尚未克隆时不提前生成文件，执行顺序和验收以[初始化接入约定](../.agents/skills/ascend-workbench-init/references/operations.md#私有知识目录接入)为准；这是可编辑的初始副本，后续以目标库维护的版本为准，不自动从模板覆盖。接入已有库先复用其规范与分类，不为模板迁移正文或全量补字段。工作台更新后可通过[增量检查与补齐](../.agents/skills/ascend-workbench-init/references/operations.md#增量检查与补齐)发现相关缺项，先给差异，再按授权补齐。缺规范或规范不可读时说明缺口，可只读检索；写入前先明确维护约定，补规范本身也须在授权范围内。相关子目录规则只按访问范围读取，不全库加载。

库内规则不能扩大用户授权、泄露私有内容或突破调用方安全边界；冲突时说明具体差异，不静默覆盖。公共工作台保留查询只读、具体收录与发布分别授权、证据不夸大、旧文可追溯及不擅自运行实验的底线；目录和字段细节只由目标库维护。

验证器 --knowledge-root 仅检查外部绑定可读，--knowledge-path 检查调用方提供的相对路径及越界；不解析库内规则、不限制 topics 布局，也不证明写权限或知识已验证。公开链接检查仅放行本 README 和明确的模板文件，不允许借模板目录发布知识正文。

## 分类检索与归档

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#分类检索与归档)。

## 收录与更新

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#收录与更新)。

## 统一证据流程

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#统一证据流程)。

### 状态复核

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#状态复核)。

### 乱序归纳与结论替代

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#乱序归纳与结论替代)。

## 条目最小结构

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#条目最小结构)。

## 过期与历史保留

具体规则由目标库 AGENTS.md 维护；初始约定见[模板对应章节](templates/AGENTS.example.md#过期与历史保留)。
