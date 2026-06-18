# -*- coding: utf-8 -*-
"""Classify marriage HWP spouse paragraphs into 6 structure axes."""
import json
import re
from pathlib import Path
from collections import Counter

INP = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_marriage_spouse_extract.json")
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_marriage_axis_summary.json")

AXES = {
    "사회": re.compile(r"사회|직장|활동|명예|체面|조직|활동력|명함|사업"),
    "경제": re.compile(r"금전|재성|돈|경제|실속|수입|재물|번영"),
    "가정": re.compile(r"가정|집|동거|처가|시가|일지|육아|가사|손주"),
    "공간": re.compile(r"떨어|별거|분리|출장|각방|주말|거리|이사|분가|역마"),
    "시간": re.compile(r"시간|리듬|주간|야간|평일|주말|저녁|스케줄|등대"),
    "역할": re.compile(r"역할|육아|돈|집|밖|부부|처|남편|아내"),
}

STRUCT_ONLY = re.compile(
    r"구조|모양|패턴|형태|속성|분|12운성|12신살|지장간|천간|지지|"
    r"일지|월지|시|충|형|원진|공망|삼합|입묘|태지|절지|병지|"
    r"금전.*애정.*동거|동거.*건강|허결|이원|위축|기립"
)

SKIP = re.compile(r"시험|합격|버리|하라|해야|도사|공부|고시|운을|대운|세运")


def main():
    data = json.loads(INP.read_text(encoding="utf-8"))
    axis_hits = {k: [] for k in AXES}
    patterns = Counter()

    for item in data["items"]:
        t = item["text"]
        if SKIP.search(t):
            continue
        if not any(STRUCT_ONLY.search(t) or AXES[k].search(t) for k in AXES):
            continue
        matched = [k for k, pat in AXES.items() if pat.search(t)]
        if not matched:
            continue
        rec = {"page": item["page"], "text": t[:200], "axes": matched}
        for k in matched:
            axis_hits[k].append(rec)

        # recurring pattern tags
        if re.search(r"금전.*애정.*동거|동거.*건강", t):
            patterns["사중허결(금·애·거·건)"] += 1
        if re.search(r"떨어져|별거|주말", t):
            patterns["공간·분거"] += 1
        if re.search(r"일지.*충|충.*일지", t):
            patterns["일지충·분거"] += 1
        if re.search(r"지장간", t):
            patterns["지장간·잠복"] += 1
        if re.search(r"12신살", t):
            patterns["12신살·일지"] += 1
        if re.search(r"12운성|태지|절지|입묘", t):
            patterns["12운성"] += 1
        if re.search(r"원진|육해", t):
            patterns["원진·육해"] += 1
        if re.search(r"공망", t):
            patterns["공망·연결"] += 1
        if re.search(r"역마|출장", t):
            patterns["역마·출장"] += 1
        if re.search(r"등대|야간|주간", t):
            patterns["교대·야간"] += 1
        if re.search(r"변화 없|임대|자격증", t):
            patterns["무변화·정착"] += 1
        if re.search(r"동거.*구|붙", t):
            patterns["동거·밀착"] += 1

    summary = {
        "axis_counts": {k: len(v) for k, v in axis_hits.items()},
        "patterns": dict(patterns.most_common()),
        "sample_per_axis": {k: v[:5] for k, v in axis_hits.items()},
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary["axis_counts"], ensure_ascii=False))
    print(json.dumps(summary["patterns"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
