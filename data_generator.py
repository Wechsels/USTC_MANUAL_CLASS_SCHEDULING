import json
import os
import pandas as pd
import re
import glob

output_file = 'data.js'

unitTimeRange = {
    1: (7*60+50, 8*60+35),
    2: (8*60+40, 9*60+25),
    3: (9*60+45, 10*60+30),
    4: (10*60+35, 11*60+20),
    5: (11*60+25, 12*60+10),
    6: (14*60+0, 14*60+45),
    7: (14*60+50, 15*60+35),
    8: (15*60+55, 16*60+40),
    9: (16*60+45, 17*60+30),
    10: (17*60+35, 18*60+20),
    11: (19*60+30, 20*60+15),
    12: (20*60+20, 21*60+5),
    13: (21*60+10, 21*60+55),
}

# 根据实际列名自动映射到内部统一字段名
COL_MAP = {
    '课堂号': 'code',
    '课程名': 'courseName',
    '课程名称': 'courseName',
    '授课教师': 'teacher',
    '授课老师': 'teacher',
    '时间地点': 'timePlace',
    '日期时间地点人员': 'timePlace',
    '学分': 'credit',
    '选课人数': 'selected',
    '已选人数': 'selected',
    '限选人数': 'capacity',
    '选课人数上限': 'capacity',
    '课堂类型': 'classType',
}

# 自动查找当前目录下所有 .xlsx 文件（跳过 _ 开头的临时文件）
xlsx_files = [f for f in sorted(glob.glob('*.xlsx')) if not f.startswith('_')]
if not xlsx_files:
    raise FileNotFoundError('当前目录未找到 .xlsx 文件')

def extract_semester(filename):
    """从文件名提取学期信息"""
    m = re.search(r'(\d{4}年[春夏秋]季学期)', filename)
    return m.group(1) if m else '未知学期'

def unify_columns(df):
    """把原始列名映射到内部统一字段名，缺失字段用 NaN 填充"""
    unified = {}
    for raw_col in df.columns:
        if raw_col in COL_MAP:
            unified[COL_MAP[raw_col]] = df[raw_col]
    for key in ('code', 'courseName', 'teacher', 'timePlace', 'credit', 'selected', 'capacity', 'classType'):
        if key not in unified:
            unified[key] = pd.Series([None] * len(df), dtype=object)
    return pd.DataFrame(unified)

def clean_time_place(info):
    """
    清理时间地点字段，使其兼容 dealTime 的 place: token 格式。
    新格式示例: "2~18周 慕课 :5(11,12) 冯红艳"
    旧格式示例: "1~8周 1201: 2(8,9) 4(3,4,5)"
    dealTime 期望地点是一个以 ':' 结尾的独立 token，时段形如 "1(3,4,5)"。
    """
    if pd.isna(info) or info == '':
        return ''
    info = str(info)
    info = re.sub(r'_x000d_', '\n', info)
    # 去掉末尾教师名：最后一个 ')' 之后的文本（新格式会附带授课教师姓名）
    last_paren = info.rfind(')')
    if last_paren != -1:
        info = info[:last_paren + 1]
    # 新格式 "地点 :N(...)" → "地点: N(...)"，让地点成为以 ':' 结尾的 token
    info = re.sub(r' :', ': ', info)
    return info

def dealTime(info):
    result = 0
    place = None
    plwt = {}
    if info == "":
        return (0, "")
    info = re.sub(r'_x000d_', '\n', info)
    info = re.split(r'[\x00-\x20]', info)
    for x in info:
        x = str(x)
        if x == "":
            continue
        if x[-1] == ':':
            place = x
        if x[-1] != ')':
            continue
        if not place in plwt:
            plwt[place] = [0, 0, 0, 0, 0, 0, 0]
        day = int(x[0]) - 1
        x = x[2:-1]
        if '~' in x:
            units = []
            st0, ed0 = map(lambda x: int(x[:2]) * 60 + int(x[3:]), x.split('~'))
            for unit in unitTimeRange:
                st1, ed1 = unitTimeRange[unit]
                if max(st0, st1) < min(ed0, ed1):
                    units.append(unit)
        else:
            units = list(map(int, x.split(',')))
        for i in units:
            plwt[place][day] |= 1 << i
        if 1 in units or 2 in units:
            result |= 1 << (day * 6 + 0)
        if 3 in units or 4 in units or 5 in units:
            result |= 1 << (day * 6 + 1)
        if 6 in units or 7 in units:
            result |= 1 << (day * 6 + 2)
        if 8 in units:
            result |= 1 << (day * 6 + 3)
        if 9 in units or 10 in units:
            result |= 1 << (day * 6 + 4)
        if 11 in units or 12 in units or 13 in units:
            result |= 1 << (day * 6 + 5)
    st = ""
    for k, v in plwt.items():
        for i in range(1, 8):
            r = v[i - 1]
            if r:
                u = ""
                for j in range(1, 14):
                    if (r >> j) & 1:
                        u = u + str(j) + ','
                st = st + k + str(i) + '(' + u[:-1] + ');'
        if not v:
            st = st + k + ";"
    return (result, st[:-1])

def dealWeek(info):
    result = 0
    if pd.isna(info):
        return 0
    for period in str(info).split('\n'):
        if '周 ' not in period:
            continue
        period = period.split('周 ')[0]
        for x in period.split(','):
            if '~' not in x and str(int(x)) == x:
                result |= 1 << int(x)
                continue
            special = ''
            if x.endswith('(单)'):
                special = 'Odd'
                x = x[:-3]
            if x.endswith('(双)'):
                special = 'Even'
                x = x[:-3]
            t = x.split('~')
            assert len(t) == 2, t
            if special == 'Odd':
                for week in range(int(t[0]), int(t[1]) + 1):
                    if week % 2 == 1:
                        result |= 1 << week
            elif special == 'Even':
                for week in range(int(t[0]), int(t[1]) + 1):
                    if week % 2 == 0:
                        result |= 1 << week
            else:
                for week in range(int(t[0]), int(t[1]) + 1):
                    result |= 1 << week
    result >>= 1
    return result

def extract_locations(info):
    """
    从时间地点字段提取所有地点标识，复用 clean_time_place 的规整逻辑。
    规整后地点是以 ':' 结尾的独立 token（如 "2409:"、"TH-C101:"、"管理楼三楼机房:"），
    去掉末尾冒号即为地点名。dealTime 用同样的方式识别地点，保持一致。
    """
    cleaned = clean_time_place(info)
    if not cleaned:
        return []
    locs = []
    for tok in re.split(r'[\x00-\x20]', cleaned):
        tok = str(tok)
        if len(tok) > 1 and tok.endswith(':'):
            locs.append(tok[:-1])
    return locs

def merge_continuation_rows(df):
    """
    把 code=NaN 的延续行合并到正确的主行。

    新格式中，同一课堂的不同时段可能拆成多行。延续行只有 timePlace 有值，
    其余元数据列（code, courseName, teacher 等）均为 NaN。延续行的 timePlace
    末尾会附带该时段的授课教师姓名。

    匹配策略：先用 (教师, 地点) 全局索引定位主行，回退到前一个主行。
    简单 ffill 会把延续行错配给相邻的前一行主行——当某个课堂的主行在文件
    后段、而延续行散在前段时（新教务导出常见），就会把别课堂的时段并进来。
    元数据也只从主行取（按 code 映射），不用位置 ffill，避免延续行继承相邻
    别课堂的 courseName/teacher。
    """
    code = 'code'
    teacher = 'teacher'
    time_place = 'timePlace'
    meta_cols = ('courseName', 'teacher', 'credit', 'selected', 'capacity', 'classType')

    is_main = df[code].notna()  # 原始主行标记（赋值 code 前先记录）

    # 构建 (教师, 地点) -> [(row_idx, code), ...] 全局索引（只看主行）。
    # 同一 (教师, 地点) 可能被多个课堂共享（同课程的不同小班，教师和教室相同、
    # 只是上课节次不同），所以保留全部候选，匹配时再就近选。
    tl_map = {}
    main_idx = df.index[is_main]
    for i in main_idx:
        r = df.loc[i]
        locs = extract_locations(r[time_place])
        tlist = [t.strip() for t in str(r[teacher]).split(',')] if pd.notna(r[teacher]) else []
        for t in tlist:
            for loc in locs:
                tl_map.setdefault((t, loc), []).append((i, r[code]))

    # 为每个 NaN code 行分配正确的课堂号
    assigned = df[code].copy()
    for i in range(len(df)):
        if pd.notna(assigned.iloc[i]):
            continue
        tv = str(df.iloc[i][time_place])
        # 提取教师名（最后一个 ')' 之后的部分）
        lp = tv.rfind(')')
        time_teacher = tv[lp + 1:].strip() if lp != -1 and lp + 1 < len(tv) else None
        locs = extract_locations(tv)

        # 策略1: (教师, 地点) 匹配。
        # - 若该 (教师, 地点) 只被一个课堂拥有（唯一匹配），直接取它——即使主行
        #   在文件后段（如 MSEN6406P.01 的延续行散在前段、主行在后段）。
        # - 若被多个课堂共享（同课程不同小班，教师/教室相同仅节次不同），取离当前
        #   行最近的前一个主行——延续行通常紧跟主行，就近能正确区分小班。
        found_code = None
        if time_teacher and locs:
            # 汇总所有 loc 下的候选主行
            seen_codes = {}
            for loc in locs:
                for (midx, mcode) in tl_map.get((time_teacher, loc), []):
                    seen_codes.setdefault(mcode, []).append(midx)
            if len(seen_codes) == 1:
                found_code = next(iter(seen_codes))
            elif len(seen_codes) > 1:
                # 多课堂共享：取当前位置之前、行号最大的主行
                prior = [(max(idx_list), mcode)
                         for mcode, idx_list in seen_codes.items()
                         if min(idx_list) < i]
                if prior:
                    found_code = max(prior, key=lambda x: x[0])[1]

        # 策略2: 回退到前一个已分配的 code
        if not found_code:
            for j in range(i - 1, -1, -1):
                if pd.notna(assigned.iloc[j]):
                    found_code = assigned.iloc[j]
                    break

        if found_code:
            assigned.iloc[i] = found_code

    # 丢弃仍然没有 code 的行（文件开头的孤行）
    valid_mask = assigned.notna()
    df = df[valid_mask].copy()
    df[code] = assigned[valid_mask].values
    is_main = is_main[valid_mask].values

    # 元数据只从主行取：构建 code -> 主行元数据 映射，再回填到所有同 code 行。
    # 这样延续行不会因位置相邻而继承别课堂的 courseName/teacher。
    meta_lookup = {}
    for _, r in df[is_main].iterrows():
        meta_lookup[r[code]] = {col: r[col] for col in meta_cols}
    for col in meta_cols:
        df[col] = df[code].map(lambda c: meta_lookup.get(c, {}).get(col))

    # 按课堂号分组合并
    grouped = df.groupby(code, sort=False).agg({
        'courseName': 'first',
        'teacher': 'first',
        'credit': 'first',
        'selected': 'first',
        'capacity': 'first',
        'classType': 'first',
        'timePlace': lambda s: '\n'.join(str(v) for v in s if pd.notna(v) and str(v).strip()),
    }).reset_index()

    return grouped


# 可选加载评课社区评分
try:
    from icourse_spider import lesson_match
    HAS_ICOURSE = True
except ImportError:
    HAS_ICOURSE = False

output = []
total_rows = 0

for xlsx in xlsx_files:
    print(f'Processing: {xlsx}')
    df = pd.read_excel(xlsx)
    df = unify_columns(df)
    semester = extract_semester(os.path.basename(xlsx))

    grouped = merge_continuation_rows(df)

    for i in grouped.index:
        tm = clean_time_place(grouped['timePlace'][i])
        time, plwt = dealTime(tm)
        if time == 0 and plwt == '':
            continue

        teachers_raw = grouped['teacher'][i]
        if pd.isna(teachers_raw):
            teachers = []
        else:
            teachers = [t for t in teachers_raw.split(',') if t]
        teacher = teachers
        if len(teacher) >= 3:
            teacher = teacher[:2] + ['...']
        teacher = ','.join(teacher)

        week = dealWeek(tm)
        if week == 0 and time != 0:
            week = (1 << 18) - 1

        sim_course = {
            'code': grouped['code'][i],
            'courseName': grouped['courseName'][i],
            'teacher': teacher,
            'teachers': teachers,
            'weekType': week,
            'timeType0': time & ((1 << 30) - 1),
            'placeDayTime': plwt,
            'credit': grouped['credit'][i],
            'volume': f"{grouped['selected'][i]}/{grouped['capacity'][i]}"
        }
        if time >> 30:
            sim_course['timeType1'] = time >> 30
        class_type = grouped['classType'][i]
        # 旧格式用 "通识"，新格式用 "公选课" 标记通识/公共选修课
        if isinstance(class_type, str) and ('通识' in class_type or '公选' in class_type):
            sim_course['tongshi'] = 1

        if HAS_ICOURSE:
            course_name = sim_course['courseName']
            if isinstance(course_name, str):
                icourseRating = lesson_match.get_icourseRating(course_name, teachers)
                if icourseRating != '暂无评分':
                    sim_course['icourseRating'] = icourseRating

        sim_course.pop('teachers')
        output.append(sim_course)
        total_rows += 1

output.sort(key=lambda x: x['code'])
final_data = json.dumps(output, ensure_ascii=False, separators=(',', ':'))

# 把键名引号去掉，保持原有 data.js 格式
for key in ['code', 'courseName', 'teacher', 'weekType', 'timeType0', 'timeType1',
            'tongshi', 'placeDayTime', 'icourseRating', 'credit', 'volume']:
    final_data = final_data.replace(f'"{key}"', key)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f'var version="260716";var semester="{semester}";var allLesson=' + final_data + ';')

print(f'Done. {total_rows} lessons written to {output_file}')
print(f'Semester: {semester}')