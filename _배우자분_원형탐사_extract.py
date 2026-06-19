# -*- coding: utf-8 -*-
"""Extract conclusion-first entries from 결혼_관련 A-grade HWP files."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from hwp5.binmodel import Hwp5File, Paragraph, ParaText

ROOT = Path(r"C:\Users\Lenovo\Desktop\결혼_관련")
OUT_DIR = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료")

A_GRADE_PATTERNS = [
    r"^결혼운\.hwp$",
    r"박청화.*애정운.*결혼운.*처자인연법",
    r"배우자\s*보는\s*법.*탈",
    r"배우자운\s*요점정리",
    r"^사주와\s*이성운",
    r"역학살롱\s*인연법",
    r"탈원\s*일간별\s*부부",
]

CONCLUSION = re.compile(
    r"(결혼|배우자|남편|아내|부부|처|재혼|이혼|별거|동거|시집|장가|혼인|배필|인연)"
    r".{0,40}"
    r"(늦|빨|지연|조기|덕|고생|불리|유리|안정|불안|반복|이별|열리|닫|"
    r"활동|가정|직장|사회|재혼|이혼|행복|갈등|싸|화|원|맞|틀|좋|나쁘|"
    r"강|약|없|있|많|적|쉽|어렵|가능|불가|해야|하면|된다|안\s*된다|"
    r"보면|보인|나타|형성|만남|인연|운이|운을|운은|운에|운으로)",
    re.I,
)

CONCLUSION_SHORT = re.compile(
    r"(결혼을?\s*(늦|빨|조|지)|배우자\s*(덕|고생|로|와|와서|에게|가)|"
    r"재혼|이혼\s*(가능|반복|많|쉽|어렵)|별거|동거|"
    r"결혼\s*후\s*(안정|불안|행복|갈등)|"
    r"배우자\s*(가\s*)?(사회|직장|가정|활동|지키|돌봄)|"
    r"운이\s*(열|닫|좋|나쁘)|불리|유리|덕을\s*보|고생을\s*하)",
    re.I,
)

SAJU = re.compile(
    r"(년주|월주|일주|시주|천간|지지|지장간|일지|월지|시지|년지|"
    r"관성|재성|비겁|식상|인성|편관|정관|편재|정재|"
    r"배우자(?:성|궁|운|상)?|남편(?:성|궁)?|아내(?:성|궁)?|"
    r"합|충|형|파|해|공망|원진|삼합|육합|"
    r"대운|세운|12운성|12신살|역마|도화|홍염|"
    r"갑|을|병|정|무|기|경|辛|壬|癸|"
    r"子|丑|寅|卯|辰|巳|午|未|申|酉|戌|亥|"
    r"입묘|절지|태지|병지|장생|목욕|관대|건록|제왕|쇠|병|사|묘|절|태|양)",
    re.I,
)

EVENT = re.compile(
    r"(늦게\s*결혼|빨리\s*결혼|조혼|지연\s*결혼|"
    r"재혼|이혼|별거|동거|출장|이사|분가|"
    r"싸움|갈등|화해|이별|만남|인연|"
    r"직장|사업|가사|육아|처가|시가|"
    r"덕\s*보|고생|운\s*열|불리|유리|안정|불안)",
    re.I,
)

SKIP = re.compile(
    r"^Q\.|^A\.|시험|합격|고시|공부를\s*해|표를\s*만들|"
    r"논리의\s*확장|귀신\s*명도|방향성을\s*제시|설명하기\s*나름",
    re.I,
)


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def extract_binmodel(path: Path):
    rows = []
    try:
        h = Hwp5File(str(path))
        page = 1
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
    except Exception as e:
        return [(-1, f"[EXTRACT_FAIL: {e}]")]
    return rows


def find_a_grade_files():
    all_hwp = list(ROOT.rglob("*.hwp"))
    found = []
    for pat in A_GRADE_PATTERNS:
        rx = re.compile(pat, re.I)
        match = next((p for p in all_hwp if rx.search(p.name)), None)
        if match:
            found.append(match)
        else:
            found.append(None)
    return found


def summarize(text, max_len=120):
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= max_len else t[: max_len - 1] + "…"


def extract_saju_spans(text):
    hits = SAJU.findall(text)
    uniq = []
    seen = set()
    for h in hits:
        k = h.lower() if isinstance(h, str) else str(h)
        if k not in seen:
            seen.add(k)
            uniq.append(h)
    return uniq[:12]


def extract_events(text):
    return list(dict.fromkeys(EVENT.findall(text)))[:8]


def is_conclusion(text):
    if len(text) < 12 or len(text) > 500:
        return False
    if SKIP.search(text):
        return False
    return bool(CONCLUSION.search(text) or CONCLUSION_SHORT.search(text))


def normalize_conclusion(text):
    t = re.sub(r"\s+", " ", text).strip()
    t = re.sub(r"[「」\"'""''\[\]()]", "", t)
    return t[:100]


def process_file(path: Path):
    rows = extract_binmodel(path)
    entries = []
    for pg, text in rows:
        if not is_conclusion(text):
            continue
        saju = extract_saju_spans(text)
        events = extract_events(text)
        entries.append(
            {
                "page": pg,
                "summary": summarize(text, 150),
                "conclusion": text,
                "saju": saju,
                "events": events,
            }
        )
    return {"file": path.name, "path": str(path), "pages": max((p for p, _ in rows if p > 0), default=0), "entries": entries}


def build_pattern_tags(entries_all):
    tags = Counter()
    tag_rules = [
        ("늦게_결혼", re.compile(r"늦.*결혼|결혼.*늦|지연.*결혼|늦게\s*해야", re.I)),
        ("빨리_결혼_불리", re.compile(r"빨.*결혼|조혼|일찍.*결혼|빨리.*불리", re.I)),
        ("배우자_덕", re.compile(r"배우자.*덕|덕.*보|덕을\s*보", re.I)),
        ("배우자_고생", re.compile(r"배우자.*고생|고생.*배우자|처.*고생", re.I)),
        ("운_열림", re.compile(r"운.*열|열리|운이\s*좋", re.I)),
        ("재혼_가능", re.compile(r"재혼", re.I)),
        ("이별_반복", re.compile(r"이별.*반복|반복.*이별|이혼.*반복|재혼.*많", re.I)),
        ("결혼후_안정", re.compile(r"결혼\s*후.*안정|안정.*결혼\s*후|결혼.*안정", re.I)),
        ("배우자_사회활동", re.compile(r"배우자.*(사회|직장|활동|사업|일)", re.I)),
        ("배우자_가정", re.compile(r"배우자.*(가정|집|가사|육아|지키)", re.I)),
        ("별거_분리", re.compile(r"별거|떨어|분리|각방|주말\s*부부", re.I)),
        ("일지_충", re.compile(r"일지.*충|충.*일지", re.I)),
        ("배우자궁_공망", re.compile(r"배우자궁.*공망|공망.*배우자|일지.*공망", re.I)),
        ("재성_관성", re.compile(r"재성|관성|편재|정재|편관|정관", re.I)),
        ("지장간", re.compile(r"지장간", re.I)),
        ("12운성", re.compile(r"12운성|입묘|절지|태지|병지", re.I)),
        ("12신살", re.compile(r"12신살", re.I)),
        ("원진_육해", re.compile(r"원진|육해", re.I)),
        ("역마_출장", re.compile(r"역마|출장", re.I)),
        ("대운_세운", re.compile(r"대운|세운", re.I)),
    ]
    for e in entries_all:
        t = e["conclusion"]
        for name, rx in tag_rules:
            if rx.search(t):
                tags[name] += 1
    return tags


def main():
    files = find_a_grade_files()
    results = []
    all_entries = []
    missing = []

    for i, path in enumerate(files):
        if path is None:
            missing.append(A_GRADE_PATTERNS[i])
            continue
        print(f"Processing: {path.name}")
        r = process_file(path)
        results.append(r)
        for e in r["entries"]:
            e["source"] = path.name
            all_entries.append(e)

    patterns = build_pattern_tags(all_entries)
    conc_norm = Counter(normalize_conclusion(e["conclusion"]) for e in all_entries)
    top50 = conc_norm.most_common(50)

    # structure recurrence from saju tokens
    struct_counter = Counter()
    for e in all_entries:
        for s in e["saju"]:
            struct_counter[s] += 1

    event_counter = Counter()
    for e in all_entries:
        for ev in e["events"]:
            event_counter[ev] += 1

    # archetype candidates: co-occurring pattern pairs
    cooc = Counter()
    tag_rules = [
        ("늦게_결혼", re.compile(r"늦.*결혼|결혼.*늦", re.I)),
        ("배우자_덕", re.compile(r"덕", re.I)),
        ("일지_충", re.compile(r"일지.*충", re.I)),
        ("재성", re.compile(r"재성|편재|정재", re.I)),
        ("관성", re.compile(r"관성|편관|정관", re.I)),
        ("별거", re.compile(r"별거|떨어", re.I)),
        ("재혼", re.compile(r"재혼", re.I)),
        ("지장간", re.compile(r"지장간", re.I)),
    ]

    def tags_for(text):
        return [n for n, rx in tag_rules if rx.search(text)]

    for e in all_entries:
        ts = tags_for(e["conclusion"])
        for i in range(len(ts)):
            for j in range(i + 1, len(ts)):
                cooc[(ts[i], ts[j])] += 1

    payload = {
        "missing_patterns": missing,
        "files": [{k: v for k, v in r.items() if k != "entries"} | {"entry_count": len(r["entries"])} for r in results],
        "total_entries": len(all_entries),
        "patterns": dict(patterns.most_common()),
        "top50_conclusions": [{"text": t, "count": c} for t, c in top50],
        "top_structures": dict(struct_counter.most_common(40)),
        "top_events": dict(event_counter.most_common(30)),
        "cooccurrence": {f"{a}+{b}": c for (a, b), c in cooc.most_common(25)},
        "entries_sample": all_entries[:80],
    }

    json_path = OUT_DIR / "_배우자분_원형탐사_A급_raw.json"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    jsonl_path = OUT_DIR / "_배우자분_원형탐사_A급_entries.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for e in all_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # markdown report
    md = []
    md.append("# 배우자의 분 · 원형 탐사 · A급 수집 v1\n")
    md.append("> **단계:** 반복 구조 · 반복 사건 · 반복 원형 **수집** (분 생성 ✗)\n")
    md.append(f"> **대상:** `{ROOT}` · A급 7종\n")
    md.append(f"> **추출 건수:** {len(all_entries)} · **일자:** 2026-06-18\n")
    md.append("\n---\n")

    md.append("\n## 1. A급 파일 처리 현황\n\n")
    md.append("| # | 파일 | 페이지 | 추출 |\n")
    md.append("|---|------|:------:|:----:|\n")
    for i, r in enumerate(results, 1):
        md.append(f"| {i} | {r['file']} | {r['pages']} | {len(r['entries'])} |\n")
    if missing:
        md.append(f"\n**미발견:** {', '.join(missing)}\n")

    md.append("\n---\n\n## 2. 반복 구조 목록\n\n")
    md.append("| 구조 태그 | 빈도 |\n|----------|:----:|\n")
    struct_tags = [
        ("일지_충", patterns.get("일지_충", 0)),
        ("배우자궁_공망", patterns.get("배우자궁_공망", 0)),
        ("재성_관성", patterns.get("재성_관성", 0)),
        ("지장간", patterns.get("지장간", 0)),
        ("12운성", patterns.get("12운성", 0)),
        ("12신살", patterns.get("12신살", 0)),
        ("원진_육해", patterns.get("원진_육해", 0)),
        ("역마_출장", patterns.get("역마_출장", 0)),
        ("대운_세운", patterns.get("대운_세운", 0)),
    ]
    struct_tags.sort(key=lambda x: -x[1])
    for name, cnt in struct_tags:
        if cnt:
            md.append(f"| {name} | {cnt} |\n")

    md.append("\n**토큰 빈도 (사주 구조어):**\n\n")
    for s, c in struct_counter.most_common(25):
        md.append(f"- **{s}** × {c}\n")

    md.append("\n---\n\n## 3. 반복 사건 목록\n\n")
    md.append("| 사건 태그 | 빈도 |\n|----------|:----:|\n")
    event_tags = [
        ("늦게_결혼", patterns.get("늦게_결혼", 0)),
        ("빨리_결혼_불리", patterns.get("빨리_결혼_불리", 0)),
        ("배우자_덕", patterns.get("배우자_덕", 0)),
        ("배우자_고생", patterns.get("배우자_고생", 0)),
        ("운_열림", patterns.get("운_열림", 0)),
        ("재혼_가능", patterns.get("재혼_가능", 0)),
        ("이별_반복", patterns.get("이별_반복", 0)),
        ("결혼후_안정", patterns.get("결혼후_안정", 0)),
        ("배우자_사회활동", patterns.get("배우자_사회활동", 0)),
        ("배우자_가정", patterns.get("배우자_가정", 0)),
        ("별거_분리", patterns.get("별거_분리", 0)),
    ]
    event_tags.sort(key=lambda x: -x[1])
    for name, cnt in event_tags:
        if cnt:
            md.append(f"| {name} | {cnt} |\n")

    md.append("\n**사건어 빈도:**\n\n")
    for ev, c in event_counter.most_common(20):
        md.append(f"- {ev} × {c}\n")

    md.append("\n---\n\n## 4. 공통 원형 후보\n\n")
    md.append("> 결론 문장 **공동 출현** 태그 기준\n\n")
    for pair, c in cooc.most_common(15):
        md.append(f"- **{pair[0]}** + **{pair[1]}** × {c}\n")

    md.append("\n| 후보 | 근거 |\n|------|------|\n")
    candidates = [
        ("원형-A · 일지충→별거·갈등", patterns.get("일지_충", 0) + patterns.get("별거_분리", 0)),
        ("원형-B · 재성→배우자 덕·경제", patterns.get("재성_관성", 0) + patterns.get("배우자_덕", 0)),
        ("원형-C · 늦은 결혼→안정", patterns.get("늦게_결혼", 0) + patterns.get("결혼후_안정", 0)),
        ("원형-D · 재혼·이별 반복", patterns.get("재혼_가능", 0) + patterns.get("이별_반복", 0)),
        ("원형-E · 지장간·잠복 배우자", patterns.get("지장간", 0)),
        ("원형-F · 역마·사회활동 배우자", patterns.get("역마_출장", 0) + patterns.get("배우자_사회활동", 0)),
        ("원형-G · 12운성·관계 온도", patterns.get("12운성", 0)),
        ("원형-H · 공망·인연 공백", patterns.get("배우자궁_공망", 0)),
    ]
    candidates.sort(key=lambda x: -x[1])
    for name, score in candidates:
        if score:
            md.append(f"| {name} | 공동 빈도 {score} |\n")

    md.append("\n---\n\n## 5. 새롭게 발견한 구조 (A급 교차)\n\n")
    novel = []
    if patterns.get("12운성", 0) and patterns.get("별거_분리", 0):
        novel.append("12운성(입묘·절지·병지) + 별거/주말부부 — **온도·거리** 동시 서술")
    if patterns.get("지장간", 0) and patterns.get("배우자_가정", 0):
        novel.append("지장간 + 가정역할 — **겉·속 이원** 배우자")
    if patterns.get("원진_육해", 0):
        novel.append("원진·육해 — **미세 갈등·누적 이별** 축")
    if patterns.get("대운_세운", 0) and patterns.get("재혼_가능", 0):
        novel.append("대운·세운 전환 + 재혼 — **시간축** 배우자 교체")
    for n in novel:
        md.append(f"- {n}\n")
    if not novel:
        md.append("- (A급 교차 분석 후 보강)\n")

    md.append("\n---\n\n## 6. 결론 문장 빈도 TOP 50\n\n")
    md.append("| # | 빈도 | 결론 문장 |\n")
    md.append("|---|:----:|----------|\n")
    for i, (t, c) in enumerate(top50, 1):
        safe = t.replace("|", "\\|")
        md.append(f"| {i} | {c} | {safe} |\n")

    md.append("\n---\n\n## 7. 추출 샘플 (결론→구조→사건 역추적)\n\n")
    shown = 0
    for e in all_entries:
        if shown >= 25:
            break
        if len(e["saju"]) < 1 and len(e["events"]) < 1:
            continue
        md.append(f"### [{e['source']}] p.{e['page']}\n\n")
        md.append(f"**[원문 요약]** {e['summary']}\n\n")
        md.append(f"**[결론]** {e['conclusion'][:300]}{'…' if len(e['conclusion'])>300 else ''}\n\n")
        md.append(f"**[사주 구조]** {', '.join(e['saju']) if e['saju'] else '—'}\n\n")
        md.append(f"**[반복 사건]** {', '.join(e['events']) if e['events'] else '—'}\n\n")
        md.append("---\n\n")
        shown += 1

    md.append("\n*배우자분_원형탐사_A급 / 수집단계 / B급 대기*\n")

    md_path = OUT_DIR / "배우자분_원형탐사_A급_v1.md"
    md_path.write_text("".join(md), encoding="utf-8")

    print("entries", len(all_entries))
    print("written", md_path)
    print("written", json_path)


if __name__ == "__main__":
    main()
