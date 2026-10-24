# 千问办公绿皮书 2.0 · Skill

面向零基础读者的绿色图文办公手册，也是一份可复用的本地 Skill：可按任务查阅办公方法、设计模拟练习，或维护并重新生成绿皮书。包含完整正文、配图、练习答案、分章源稿及构建检查工具。

- [直接在线阅读绿皮书](https://paul090515.github.io/qianwen-office-greenbook/)
- [下载 Skill 完整 ZIP](https://paul090515.github.io/qianwen-office-greenbook/qianwen-office-greenbook-skill.zip)
- [下载完整图文阅读资料包](https://paul090515.github.io/qianwen-office-greenbook/千问办公绿皮书2.0_完整图文资料包.zip)
- [查看 Skill 指令](SKILL.md) · [可编辑文稿](千问办公绿皮书.md)

当前书稿为2.0版，含23篇正文、26幅正文配图（封面另有官方图标）、33段可复制示例与要求，两套原创模拟练习。产品资料核查日为2026年10月24日；本次封装 Skill 沿用该书稿。

## 安装与调用

下载 Skill ZIP 并解压，把其中完整的 `qianwen-office-greenbook` 文件夹放到本地 Codex 的 `~/.codex/skills/` 目录，保留文件夹内所有文件；已存在同名文件夹时先保留旧版，避免直接覆盖。Skill 名为 `$qianwen-office-greenbook`。

示例请求：

```text
使用 $qianwen-office-greenbook，教我用千问办公核对一张表。
使用 $qianwen-office-greenbook，更新绿皮书的材料管理章节，保持绿色图文风格，并交付网页、文稿和ZIP。
```

只阅读和使用知识资料，不需要安装 Node.js 或 Python；只有重新构建、核验或打包时才需要相应工具。Skill 本身不连接千问办公账号，不提供账号权限。

## 阅读与编辑

解压后用浏览器打开 `千问办公绿皮书.html` 或 `index.html`，即可离线阅读；官方来源和产品功能仍需联网。`千问办公绿皮书.md` 是合并文稿，编辑或转交时与 `assets/` 配图一起保留。

持续维护时编辑 `chapters/` 分章源稿，使用 `book.json` 管理顺序、标题、分组、版本与核查日期；构建会重新生成合并文稿，不能只修改生成文件。建议先复制完整目录到工作区，再在副本中修改。

## 重新构建与检查

在项目副本中运行。要求 Node.js 20以上、Python 3.9以上；构建唯一依赖为已锁定版本的 `marked`。有可用依赖环境就复用，否则先运行 `npm install --ignore-scripts`。

```sh
node scripts/build.mjs
python3 scripts/verify_book.py
python3 scripts/package_book.py --output ../千问办公绿皮书_完整资料包.zip
```

三个脚本也接受项目目录作为位置参数。构建不改写分章原稿；核验会检查目录、图片、内嵌下载及两套模拟数据；打包只输出供读者使用的材料，默认拒绝覆盖已有ZIP。结构检查不代替实际浏览器排版检查或产品账号实测。

## 配套资料

- `practice/`：活动报名、共享工具借还两套CSV与JSON核对答案，均为模拟数据。
- `图片来源.md`、`sources.json`：图标、官方示例图片和正文来源。
- `references/editorial-rules.md`：原创性、事实核查、教学与发布要求。
- `agents/openai.yaml`：Skill显示信息。

本书不是官方出版物。功能、界面、套餐与权限随版本和账号变化；不要把官方帮助页图片或模拟答案当成真实账号执行证明。
