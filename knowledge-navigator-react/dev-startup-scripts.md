# 开发启动脚本 · start-dev.bat / start-dev.ps1

> 一键启动 FastAPI 后端（8171）+ Vite 前端（7100），启动前自动清理端口占用。

## 一、使用方式

| 脚本 | 启动方式 | 特点 |
|------|----------|------|
| `start-dev.bat` | 资源管理器双击，或 `cmd /c start-dev.bat` | 纯 ASCII，任何代码页下安全 |
| `start-dev.ps1` | `powershell -ExecutionPolicy Bypass -File .\start-dev.ps1` | 中文输出、后端健康检查、更友好的提示 |

启动后访问：

- 轻量模式（lite）：`http://localhost:7100/`
- 完整模式（pro）：`http://localhost:7100/?backend_mode=pro`（或管理界面 ⚙ 切换）

## 二、编码问题排查记录（2026-07-26）

**现象**：运行初版 `start-dev.bat` 后满屏 `'湇鍔″櫒' 不是内部或外部命令`，后端未启动。

**原因**：初版 bat 以 UTF-8（无 BOM）保存且含中文，而 cmd.exe 按系统代码页
（GBK / CP936）解析批处理文件——中文字节被按 GBK 误读后，命令行结构被破坏
（`rem` 注释、引号配对、`start "标题"` 均失效），后端启动行随之丢失。
`chcp 65001` 无法挽救：cmd 对批处理逐行用当前代码页解析，切换时机已晚。

**修复**：

1. `start-dev.bat` 改为**纯 ASCII + CRLF**——ASCII 在任何代码页下字节含义一致；
2. 中文提示移入 `start-dev.ps1`，并以 **UTF-8 with BOM** 保存
   （Windows PowerShell 5.1 依靠 BOM 识别 UTF-8，无 BOM 时按 GBK 误读）；
3. 顺带修正初版文档中的前端端口笔误（5173 → 7100）。

**另一个坑**：ps1 中直接 `npm run dev` 在输出被重定向的非交互场景下，
npm 的 cmd shim 会挂起（vite 横幅后无 ready、端口不监听）。
改为 `cmd /c "npm run dev"` 后解决——与 bat 的进程环境一致。

**注意**：从 Git Bash 用完整 Windows 路径调用 bat 时，路径中的中文（如 `龙虾`）
会以 UTF-8 传给按 GBK 解析的 cmd 导致找不到文件；在 cmd / 资源管理器中
直接运行不受影响。ps1 无此问题（PowerShell 原生 Unicode）。

## 三、端口占用自动清理

两个脚本启动前都会结束占用 8171 / 7100 的进程，避免重复启动失败：

- bat：`netstat -ano | findstr LISTENING` 提取 PID → `taskkill /F`
- ps1：`Get-NetTCPConnection -State Listen -LocalPort <port>` → `Stop-Process -Force`

实测：先手动启动一个后端占用 8171，再运行脚本 → 旧进程被结束，
新后端 + 前端正常启动（ps1 输出 `端口 8171 -> 已结束 PID xxxxx`）。

## 四、验证结果（2026-07-26）

| 测试 | 结果 |
|------|------|
| bat：占用状态下清理 + 启动 | 后端 health 37 卡片 / 25 节点 ✓，前端 HTTP 200 ✓ |
| ps1：清理 bat 启动的实例并重启 | 端口清理提示正确 ✓，健康检查通过 ✓，前端 HTTP 200 ✓ |
| ps1 中文输出 | 真实控制台正常；重定向到文件时按 OEM 编码（仅测试场景，不影响使用） |

## 五、常用排障

```bash
# 查看端口占用
netstat -ano | findstr "LISTENING" | findstr ":8171 :7100"

# 手动结束后端 / 前端
taskkill /PID <pid> /F

# 后端健康检查
curl http://localhost:8171/api/health
```
