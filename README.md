# 中科大排课工具

纯手动前端排课网页应用。搜索课程、选择课堂、调整排课偏好，浏览器内直接生成课表。基于 Xulei Sun 现有项目改编用，解决了原有排课不能手动识别的痛点。

## 快速开始

直接用浏览器打开 `index.html` 即可。

也可启动本地服务：

```bash
python -m http.server 8000
```

## 课程数据更新

从教务系统导出 Excel，放到项目根目录，运行生成脚本：

```bash
python -m pip install pandas openpyxl
python data_generator.py
```

脚本会自动扫描当前目录下所有 `.xlsx` 文件，兼容新旧两种教务导出格式，无需手动指定文件名或列名。

## 贡献者

Xulei Sun, Brealid, Determinant

## 许可证

[GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE)
