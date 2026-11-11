"""실습 자료(채점기준표·수행평가 예시 엑셀)를 HTML이 읽는 assets/kit.js 로 바꾼다.

다른 과목으로 연수할 때:
  1) 구글 시트 '3. 채점기준표'와 '1. 수행평가 예시'를 엑셀(.xlsx)로 내려받아 data/ 에 같은 이름으로 덮어쓴다.
  2) 문제 지문이 바뀌면 data/problem.json 을 고친다.
  3) 아래 명령을 실행한다.
     uv run --no-project --with openpyxl python scripts/build_kit.py
"""
import json
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def clean(v):
    if v is None:
        return ""
    s = str(v).strip()
    s = re.sub(r"[ \t]+", " ", s)
    return s


def num(v):
    s = clean(v)
    try:
        f = float(s)
        return int(f) if f.is_integer() else f
    except ValueError:
        return s


def read_rubric(path):
    ws = openpyxl.load_workbook(path, data_only=True).worksheets[0]
    rows = [[clean(c) for c in r[:3]] for r in ws.iter_rows(values_only=True)]
    kit = {"name": "", "standards": [], "criteria": [], "score": {}, "absent": {}}
    section = None
    for a, b, c in rows:
        if re.match(r"^\d\.\s", a):
            section = a[0]
            continue
        if not (a or b or c):
            continue
        if section == "1" and a == "평가명":
            kit["name"] = b
        elif section == "2":
            if a.startswith("성취기준"):
                kit["standards"].append({"label": a, "direct": b == "직접 입력", "text": c, "levels": []})
            elif b and kit["standards"]:
                kit["standards"][-1]["levels"].append({"level": b, "text": c})
        elif section == "3":
            if a.startswith("채점기준"):
                kit["criteria"].append({"label": a, "name": b, "rows": []})
            elif b and kit["criteria"]:
                kit["criteria"][-1]["rows"].append({"score": num(b), "text": c})
        elif section == "4" and a:
            kit["score"][a] = num(b)
        elif section == "5" and a:
            kit["absent"][a] = num(b)
    return kit


def read_performance(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    out = {"elements": [], "answers": []}
    ws = wb["성취기준 및 평가요소"]
    for r in ws.iter_rows(values_only=True):
        a, b = clean(r[0]), clean(r[1])
        if a in ("지식·이해", "과정·기능", "가치·태도", "평가 요소"):
            items = [re.sub(r"^-\s*", "", x).strip() for x in b.split("\n") if x.strip()]
            out["elements"].append({"category": a, "items": items})
    # [예시답안] 표: '문항 | 내용' 머리줄 다음부터 [평가요소별 채점기준] 전까지
    ws = wb["예시답안 및 채점기준"]
    inside = False
    for r in ws.iter_rows(values_only=True):
        a, b = clean(r[0]), r[1]
        if a.startswith("[예시답안]"):
            inside = True
            continue
        if a.startswith("[평가요소별"):
            break
        if inside and b and a not in ("문항", ""):
            text = "\n".join(re.sub(r"[ \t]+", " ", x).strip() for x in str(b).split("\n") if x.strip())
            out["answers"].append({"no": int(float(a)), "text": text})
    return out


def main():
    kit = read_rubric(DATA / "3-rubric.xlsx")
    kit.update(read_performance(DATA / "1-performance.xlsx"))
    kit["problem"] = json.loads((DATA / "problem.json").read_text(encoding="utf-8"))

    # 붙여 넣기 순서: 평가 설계 화면의 입력칸 순서와 같다
    seq = [{"step": "① 기본 정보", "field": "평가(과제)명", "text": kit["name"]}]
    for s in kit["standards"]:
        seq.append({"step": "② 성취기준", "field": f"{s['label']} (직접 입력 체크)", "text": s["text"]})
        for lv in s["levels"]:
            seq.append({"step": "② 성취기준", "field": f"성취수준 {lv['level']} 내용", "text": lv["text"]})
    for c in kit["criteria"]:
        seq.append({"step": "③ 채점기준", "field": f"{c['label']} · 채점 요소", "text": c["name"]})
        for row in c["rows"]:
            seq.append({"step": "③ 채점기준", "field": f"{c['label']} · {row['score']}점 서술", "text": row["text"]})
    kit["sequence"] = seq

    js = "/* scripts/build_kit.py 로 만든 파일입니다. 직접 고치지 말고 data/ 를 고친 뒤 다시 만드세요. */\n"
    js += "window.KIT = " + json.dumps(kit, ensure_ascii=False, indent=1) + ";\n"
    (ROOT / "assets" / "kit.js").write_text(js, encoding="utf-8")
    print(f"평가명: {kit['name']}")
    print(f"성취기준 {len(kit['standards'])}개, 채점기준 {len(kit['criteria'])}개, 붙여 넣을 칸 {len(seq)}개")
    print(f"평가요소 묶음 {len(kit['elements'])}개, 예시답안 {len(kit['answers'])}개")


if __name__ == "__main__":
    main()
