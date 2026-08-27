# 掘金签到 · GitHub Actions 部署说明

用 GitHub 的服务器帮你每天定时签到，电脑关机也不影响。全程免费（私有仓库每月 2000 分钟额度，本任务一天约 1 分钟）。

需要准备：一个 GitHub 账号，以及每个掘金账号的 Cookie。

---

## 第一步：创建私有仓库

1. 打开 https://github.com/new 并登录
2. Repository name 填 `juejin-checkin`（可随意改）
3. **Privacy 必须选 Private（私有）**
4. 点 Create repository 创建

## 第二步：把本目录的文件上传到仓库

方式 A：网页上传（最简单）
1. 在仓库首页点 Add file → Upload files
2. 把本目录下的 `juejin_checkin.py`、`requirements.txt`、`.github` 文件夹整体拖进去
3. 点 Commit changes

方式 B：git 命令行（推荐，方便以后更新）

```bash
cd 本目录（github-actions）
git init
git add .
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/juejin-checkin.git
git push -u origin main
```

## 第三步：配置 Cookie（仓库 Secret）

1. 仓库页 → Settings → Secrets and variables → Actions → New repository secret
2. Name 填：`JUEJIN_COOKIES`
3. Value 里填所有账号的 Cookie，**每行一个账号**：

```
账号1=第一段的Cookie整串
账号2=第二段的Cookie整串
```

也可以不写名字，每行直接放 Cookie（脚本会自动命名为 账号1、账号2、…）。

> 注意：Cookie 里如果含有 `=` 号（很常见），不影响，脚本只按每行第一个 `=` 分隔，`=` 前面是名字、后面整串都是 Cookie。

4. 点 Add secret 保存

## 第四步：手动测试一次

1. 仓库页 → Actions 标签 → 左侧点 Juejin Check-in
2. 右侧点 Run workflow → 绿色按钮运行
3. 点进这次运行的日志，能看到每个账号的签到结果和抽奖结果

## 第五步：坐等自动运行

- 默认**每天 00:00 UTC（北京时间 08:00）**自动签到，无需任何操作
- 想改时间：编辑 `.github/workflows/checkin.yml` 里的 `cron`，注意 Actions 用 UTC 时区（北京时间 = UTC + 8，例如想北京 9 点跑就写 `0 1 * * *`）

---

## 日常维护

| 场景 | 做法 |
| --- | --- |
| 加账号 | Settings → Secrets → 编辑 JUEJIN_COOKIES，加一行 |
| 减账号 | 同上，删掉对应一行 |
| Cookie 过期（日志报错） | 重新抓取该账号 Cookie，更新 Secret |
| 手动补签 | Actions 页 → Run workflow 手动触发 |

## 安全提醒

- 仓库务必保持 Private，不要把 Cookie 写进代码或提交记录
- Cookie 是你的登录凭证，只用 Secret 传递（日志里会自动打码，不会明文显示）
- 万一泄露：立即重新登录掘金，旧的 Cookie 会失效
