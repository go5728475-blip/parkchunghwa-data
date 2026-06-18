# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

from hwp5.binmodel import Hwp5File, Paragraph, ParaText

HWP = Path(
    r"C:\Users\Lenovo\Desktop\박청화_분자료\박청화 애정운 결혼운 + 처자인연법 (일부 채워쓸 것, 복사해 넣을 것).hwp"
)

REL = re.compile(
    r"애정|결혼|배우자|남편|아내|처|부부|배우자상|처자|인연|연애|시집|장가|"
    r"혼인|조혼|이혼|재혼|미혼|처녀|총각|배필|배우자\s*운|결혼\s*운|애정\s*운"
)


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def collect_paras():
    h = Hwp5File(str(HWP))
    page = 1
    rows = []
    for section in h.bodytext.sections:
        cur = ""
        pg = page
        for model in section.models():
            if model["type"] is Paragraph:
                if cur.strip():
                    rows.append((pg, cur.strip()))
                cur = ""
                split = model["content"].get("split")
                if split is not None and getattr(split, "new_page", False):
                    page += 1
                pg = page
            elif model["type"] is ParaText:
                cur += para_text(model)
        if cur.strip():
            rows.append((page, cur.strip()))
    return rows


def main():
    rows = collect_paras()
    gangs = []
    subs = []
    rel_toc = []

    for pg, text in rows:
        if re.match(r"^제\d+강", text):
            gangs.append({"page": pg, "title": text})
        if text.startswith("■"):
            subs.append({"page": pg, "title": text.lstrip("■ ").strip()})
        # 목차 후보: 짧은 줄 + 관련 키워드, 또는 ■/제N강/번호 목록
        if REL.search(text):
            is_toc = (
                text.startswith("■")
                or re.match(r"^제\d+강", text)
                or re.match(r"^\d+[\.)]\s", text)
                or len(text) <= 120
            )
            if is_toc:
                rel_toc.append({"page": pg, "line": text})

    out = {
        "filename": HWP.name,
        "gangs": gangs,
        "subs": subs,
        "rel_toc": rel_toc,
    }
    Path(HWP.parent / "_hwp_marriage_outline.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("gangs", len(gangs))
    print("subs", len(subs))
    print("rel_toc", len(rel_toc))


if __name__ == "__main__":
    main()
