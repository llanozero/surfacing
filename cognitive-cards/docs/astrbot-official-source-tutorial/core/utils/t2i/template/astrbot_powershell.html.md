# 文件教程：core/utils/t2i/template/astrbot_powershell.html

## 文件定位

- 官方路径：`C:\Users\llano\AppData\Local\AstrBot\backend\app\astrbot\core\utils\t2i\template\astrbot_powershell.html`
- 文件类型：`.html`
- 文件大小：`5762` 字节
- 所属目录教程：[core/utils/t2i/template](README.md)

## 它是做什么的

<

## 角色判断

这个文件位于核心实现层，通常承载底层机制、抽象或运行时行为。

## 文件内容摘要

以下是文件前 30 行的截断预览，便于快速判断内容：

```text
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <title>Astrbot PowerShell {{ version }}</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css" integrity="sha384-wcIxkf4k558AjM3Yz3BBFQUbk/zgIYC2R0QpeeYb+TwlBVMrlgLqwRjRtGZiK7ww" crossorigin="anonymous">
  <style>
    :root {
        --bg-color: #010409;
        --text-color: #e6edf3;
        --title-bar-color: #161b22;
        --title-text-color: #e6edf3;
        --font-family: "Consolas", "Microsoft YaHei Mono", "Dengxian Mono", "Courier New", monospace;
        --glow-color: rgba(200, 220, 255, 0.7);
    }

    @keyframes scanline {
        0% {
            background-position: 0 0;
        }
        100% {
            background-position: 0 100%;
        }
    }

    body {
        background-color: var(--bg-color);
        color: var(--text-color);
        font-family: var(--font-family);
        margin: 0;
```

## 阅读建议

- 建议结合同目录 Python 文件一起看，确认这个文件在运行时如何被加载。

## 同目录相关文件

- [astrbot_vitepress.html](astrbot_vitepress.html.md)
- [base.html](base.html.md)
- [shiki_runtime.iife.js](shiki_runtime.iife.js.md)

## 维护提示

- 这份文件教程是基于当前 AstrBot 官方源码快照自动生成的摘要。
- 如果你准备修改当前文件，建议先同步阅读它的所属目录教程，再搜索它在全项目中的引用位置。