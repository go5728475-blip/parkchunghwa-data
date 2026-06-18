# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path
from hwp5.binmodel import Hwp5File, Paragraph, ParaText

HWP = Path(
    r"C:\Users\Lenovo\Desktop\박청화_분자료\박청화 애정운 결혼운 + 처자인연법 (일부 채워쓸 것, 복사해 넣을 것).hwp"
)
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_marriage_spouse_extract.json")


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def collect():
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


STRUCT = re.compile(
    r"배우자|남편|아내|부부|처|부인|배필|일지|관성|재성|지장간|12신살|12운성|"
    r"원진|공망|충|형|삼합|역마|동거|떨어|분리|직장|활동|금전|애정|건강|가정|처가|역할"
)
SKIP = re.compile(
    r"^Q\.|^A\.|대운|세运|해야|하라|하면 된|좋다고|나쁘|방향성을 제시|설명하기 나름|"
    r"공부를 해 보면|표를 만들|논리의 확장|귀신 명도"
)


def main():
    rows = collect()
    hits = []
    seen = set()
    for pg, t in rows:
        if not STRUCT.search(t) or len(t) < 20:
            continue
        if SKIP.search(t):
            continue
        key = t[:80]
        if key in seen:
            continue
        seen.add(key)
        hits.append({"page": pg, "text": t})

    OUT.write_text(json.dumps({"total_pages": max(p for p, _ in rows), "count": len(hits), "items": hits}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("pages", max(p for p, _ in rows), "hits", len(hits))


if __name__ == "__main__":
    main()
