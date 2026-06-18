# -*- coding: utf-8 -*-
import re
from hwp5.binmodel import Hwp5File, Paragraph, ParaText

HWP = r"C:\Users\Lenovo\Desktop\명리pdf - 백업\기타\새 폴더\배우자 보는 법(탈).hwp"

PAT = re.compile(
    r"(배우자|남편|아내|부인|부부|배필|일지|월지|년지|시지).{0,80}(조직|직장|직업|권한|사회|활동|명예|공공|실력|직장형태|조직형)|"
    r"(조직|직장|직업|권한|사회적|활동|명예).{0,80}(배우자|남편|아내|부인|배필)|"
    r"(천간|지지).{0,40}(관성|정관|편관)|"
    r"(관성|정관|편관).{0,40}(천간|지지|뿌리|기립)|"
    r"(배우자|남편|정관|편관|관성).{0,60}(12운성|운성|입묘|양지|병지|관대|목욕|태|양)|"
    r"(12운성|운성).{0,60}(배우자|남편|정관|편관)|"
    r"(배우자|남편|일지).{0,60}(신살|양인|원진|공망|역마)|"
    r"(신살|양인|원진|공망|역마).{0,60}(배우자|남편|부인)|"
    r"(배우자|남편|일지).{0,60}(형|충|파|해|삼합|육합)|"
    r"(형|충|파|해).{0,60}(배우자|남편|부인|일지)|"
    r"뿌리.{0,40}(기립|두)|"
    r"기립.{0,40}(배우자|정관|편관)|"
    r"지장간.{0,40}(배우자|정관|편관)|"
    r"명예속성|유명속성|공공속성|실력속성|실속속성|사익속성|직업환경|직장형태|조직속|관인소통|역마속성"
)


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def collect():
    h = Hwp5File(HWP)
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


def context(rows, i):
    lines = []
    for j in range(max(0, i - 2), min(len(rows), i + 3)):
        pg, t = rows[j]
        mark = ">>>" if j == i else "   "
        lines.append(f"{mark} p{pg} | {t}")
    return "\n".join(lines)


def main():
    rows = collect()
    seen = set()
    n = 0
    for i, (pg, t) in enumerate(rows):
        if not PAT.search(t):
            continue
        key = (pg, t)
        if key in seen:
            continue
        seen.add(key)
        n += 1
        print("=" * 60)
        print(f"p{pg}")
        print(t)
        print("--- 문맥 ---")
        print(context(rows, i))
        print()
    print("COUNT", n)


if __name__ == "__main__":
    main()
