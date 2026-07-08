# USTC Course Scheduling Tool

USTC Course Scheduling Tool is a static web app for planning course timetables. It helps students search courses, choose preferred sections, adjust scheduling preferences, and generate timetable plans directly in the browser.

This project is part of Woke 365, a Gold Award winner at USTC's Yuqing Cup Campus Software Design Competition.

## Tech Stack

- HTML, CSS, JavaScript
- jQuery
- Layui
- Python

## Directory Structure

```text
.
├── index.html              # Page entry
├── js.js                   # Main business logic and scheduling algorithm
├── table.css               # Page and timetable styles
├── data.js                 # Generated course data
├── data_generator.py       # Generates data.js from class.xlsx
├── class.xlsx              # Course data exported from the academic system
├── icourse_spider/         # Course rating crawler and matcher
├── layui/                  # Layui dependency
├── jquery.js               # jQuery dependency
├── filesaver.js            # File export dependency
├── README.md
└── LICENSE
```

## Quick Start

This project is a static site with no build step. You can open `index.html` directly, or start a local static server from the project root:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/`.

For the development guide, see [开发说明.md](./开发说明.md).

## Contributors

Xulei Sun, Brealid, Determinant

## License

This project is licensed under the [GNU Affero General Public License v3.0 (AGPL-3.0)](./LICENSE).
