---
id: container-environment-network-lifecycle
title: 容器SSH、环境继承和管理网络入口的生命周期核验
status: candidate
updated_at: '2026-10-26T14:40:16.513692+08:00'
verified_at: '2026-10-26T14:40:16.513692+08:00'
observed_at: '2026-10-23'
tags: [容器, SSH, CANN, NetworkManager, DNS, systemd, 转发]
applies_to: 手工Docker容器、Linux宿主及已安装NetworkManager/systemd的历史环境；具体入口、unit与网卡由使用者核对
evidence_scope: 已保存命令与运行摘要，以及仓内既有环境规范；未公开完整环境，不由本仓独立复验；未补做容器重启或网络实验
sources: []
---

# 从保存时可用到重启后仍可用

## SSH与CANN入口

独立启动sshd可以让当前容器可登录；若PID1只是`tail`，该事实不能保证容器重启后sshd自动恢复。需要另查入口、进程监督和重启验证。容器同名重建时以实际container ID和新SSH核验为准，不沿用旧ID交付结论。

显式`source`CANN成功是对照，不能代替真实SSH默认环境、`docker exec`方式、服务脚本及已启动进程继承的检查。文件存在、环境变量有值、解释器能导入、实际设备调用分别记录。具体执行规范复用[容器创建后的环境入口验收](../../.agents/skills/ascend-agent-workflow/references/service-deployment.md#容器创建后的环境入口验收)，不重复维护第二套初始化流程。

## DNS的分层验收

在使用NetworkManager的目标上，分别检查连接配置中的持久DNS、活动连接的DNS、实际域名解析与HTTPS访问；保留默认路由前后值。某次registry返回401可支持解析、TCP/TLS和认证入口可达，不表示镜像拉取、其他外网源或代理都可用。

历史DNS操作保存了命令结果，但原侧会话的人类实施授权不能完整取得；该缺口限制对原操作权限的回溯，不影响“不能把401当拉取成功”的判读方法。不能仅凭本条自动修改DNS或覆盖其他会话配置。

## 管理网到PD业务入口

评测机可能能访问宿主管理IP，却无法路由到容器业务网IP。先分别测试服务端自身、评测宿主和评测容器；P侧8000可达不等于它可以替代PD代理。

历史在不重启P/D与原代理的条件下，复用宿主已有`systemd-socket-proxyd`增加管理IP转发。参数化示意：

```bash
# 先确认该管理地址/端口属于本任务且未被其他入口占用。
systemd-run --unit=pool-eval-forward \
  --socket-property=ListenStream=192.0.2.20:1999 \
  --property=Restart=on-failure \
  /usr/lib/systemd/systemd-socket-proxyd 192.0.2.10:1999
```

实际路径和systemd能力需在目标核对，API客户端及egress白名单必须同步使用新入口。先健康/模型列表，再以原评测真实POST及Agent步骤确认模型交互；健康200不是生成成功。

上述为运行期transient unit，宿主重启后不保证保留；原模型/业务代理退出也不保证转发unit随之退出。历史残留socket占用调度端口，需核对unit、绑定地址、后端目标和所有权后只撤销本任务转发；不能按端口杀所有进程。恢复也须确认新后端，避免转发到旧实例。

## 证据边界与复查

进程无PID、NPU显存未清零和新服务已被用户重拉可能同时出现。旧空闲快照不能授权清理新PID；结合容器ID、PID/starttime、设备持有者和任务owner。首次容器筛选及后续实际使用按[服务器记录规范](../../docs/task-records.md#服务器可达性总表)，不把宿主全部容器视作用户所有。

更换容器入口、网络namespace、系统服务管理或认证方式后复验。本文不给出永久DNS/防火墙/SSH配置，也不授权停止服务。
