# 中科大排课工具

中科大排课工具是一个纯前端的排课网页应用。学生可在浏览器中搜索课程、选择课堂、调整排课偏好，并直接生成课表方案。

本项目为 Woke 365 的一部分，曾获中科大瑜杯校园软件设计竞赛金奖。

## 功能概览

- **课程搜索** — 按课程名、教师名模糊检索
- **课堂选择** — 查看时间、地点、学分、选课人数等详细信息
- **智能排课** — 自动检测时间冲突，生成不冲突的排课方案
- **多套方案** — 同时保存、切换多套排课方案
- **评课社区评分** — 集成 icourse 评课社区评分，辅助选课决策
- **课表导出** — 导出课表文件

## 技术栈

- 前端：HTML / CSS / JavaScript、jQuery、Layui
- 数据处理：Python（pandas、openpyxl）

## 目录结构

```text
.
├── index.html              # 页面入口
├── js.js                   # 主要业务逻辑和排课算法
├── table.css               # 页面和课表样式
├── data.js                 # 生成的课程数据
├── data_generator.py       # 从 Excel 生成 data.js
├── 中国科大2026年秋季学期*.xlsx   # 教务系统导出的课程数据
├── icourse_spider/         # 评课社区评分抓取和匹配
├── layui/                  # Layui 依赖
├── jquery.js               # jQuery 依赖
├── filesaver.js            # 导出文件依赖
├── 开发说明.md
├── README.md
└── LICENSE
```

## 快速开始

本项目为纯静态网站，无需构建。直接用浏览器打开 `index.html` 即可使用。

也可在本地启动 HTTP 服务：

```bash
python -m http.server 8000
```

访问 `http://localhost:8000/`。

## 课程数据更新

每次选课系统开放新学期的选课后，需要更新课程数据：

1. 从 `https://catalog.ustc.edu.cn/query/lesson` 下载 Excel，放到项目根目录（脚本会自动扫描所有 `.xlsx` 文件）。
2. 安装依赖：

   ```bash
   python -m pip install pandas openpyxl
   ```

3. 生成课程数据：

   ```bash
   python data_generator.py
   ```

4. 在浏览器中刷新页面，验证搜索、选课和排课功能。

> 学期信息会从 Excel 文件名自动提取（匹配 `XXXX年X季学期` 模式）。

## 评课社区评分更新

通常无需频繁更新。如需刷新：

```bash
cd icourse_spider
python -m pip install requests tqdm
python spider.py
cd ..
python data_generator.py
```

## 更新日志

- **2026-07-18** — 修复延续行合并逻辑：新教务系统导出将同一课堂的不同时段拆分为多行，现通过 (教师, 地点) 索引精确匹配，消除跨课堂时段污染
- **2026-07-18** — 兼容新旧两种教务系统导出格式，列名自动映射
- **2026-07-18** — 修复空间前冒号（`地点 :1(...)`）识别问题

## 贡献者

Xulei Sun, Brealid, Determinant

## 许可证

[GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE)