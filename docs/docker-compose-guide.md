# Docker Compose 运行指南

## 1. 一次性构建并启动

```bash
docker compose up --build
```

默认会执行非交互流水线：
1. 按 `REGISTER_COUNT` 注册账号
2. 注册完成后自动探测账号可用性
3. 只把可用账号输出到 `key/kiro_go_credentials_available.json`

## 2. 常用环境变量

在 `docker-compose.yml` 的 `environment` 中调整：

- `REGISTER_COUNT`: 本次注册数量，默认 `1`
- `REGISTER_INTERVAL`: 账号间隔秒数，默认 `30`
- `POST_PROBE`: 注册后是否自动探测，默认 `true`
- `PROBE_TIMEOUT`: 探测接口超时秒数，默认 `25`
- `HEADLESS`: 是否无头，建议 VPS 保持 `true`
- `BROWSER_TYPE`: 容器内请使用 `chrome`
- `DRIVER_STRATEGY`: 容器内建议 `system`
- `USE_UNDETECTED_CHROME`: 容器内建议 `false`

## 3. 输出文件

- `key/accounts.json`: 注册原始账号数据
- `key/kiro_go_credentials_all.json`: 从账号数据提取的导入凭证
- `key/kiro_account_probe_result.json`: 逐账号探测详情
- `key/kiro_go_credentials_available.json`: 可用账号（建议导入）
- `key/kiro_go_credentials_suspended.json`: 封禁账号
- `key/kiro_go_probe_summary.json`: 汇总统计

## 4. 只运行探测（不注册）

把 `REGISTER_COUNT` 改成 `0` 即可跳过注册，直接做探测：

```bash
docker compose run --rm -e REGISTER_COUNT=0 register
```
