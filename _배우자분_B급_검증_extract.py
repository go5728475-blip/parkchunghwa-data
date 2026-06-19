# -*- coding: utf-8
"""B-grade HWP: validate A-grade archetypes 02/04/06/07/10 — evidence accumulation."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from hwp5.binmodel import Hwp5File, Paragraph, ParaText

ROOT = Path(r"C:\Users\Lenovo\Desktop\결혼_관련")
OUT_DIR = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료")
A_GRADE = [
    re.compile(r"^결혼운\.hwp$", re.I),
    re.compile(r"박청화.*애정운.*결혼운.*처자인연법", re.I),
    re.compile(r"배우자\s*보는\s*법.*탈", re.I),
    re.compile(r"배우자운\s*요점정리", re.I),
    re.compile(r"^사주와\s*이성운", re.I),
    re.compile(r"역학살롱\s*인연법", re.I),
    re.compile(r"탈원\s*일간별\s*부부", re.I),
]

TARGET_ARCH = {
    "원형-02": {
        "name": "정관·정재=만족 / 편관·편재=허결",
        "match": re.compile(
            r"정관|정재|편관|편재|만족도|허결|올바른\s*배우자|금전.*애정.*동거",
            re.I,
        ),
    },
    "원형-04": {
        "name": "형충파해 → 거리·갈등",
        "match": re.compile(
            r"형충|충.*일지|일지.*충|파破|형성|미워|깨지|부부궁.*손상|"
            r"거리.*두|떨어져|별거|적당히.*사",
            re.I,
        ),
    },
    "원형-06": {
        "name": "배우자 덕·복",
        "match": re.compile(
            r"배우자.*(덕|복)|덕.*보|덕을\s*보|참\s*배우자덕|귀인.*배우자|"
            r"배우자의\s*복|복과\s*덕|남편덕|처덕",
            re.I,
        ),
    },
    "원형-07": {
        "name": "밖=사회 / 집=가정",
        "match": re.compile(
            r"밖에\s*있|집안|가정|월주.*활동|직장|사업|사회.*활동|대외|"
            r"역마|출장|동거.*해도|가사|육아|시댁|처가|활동력",
            re.I,
        ),
    },
    "원형-10": {
        "name": "년주·대운·시주=시기",
        "match": re.compile(
            r"년주.*(인연|만나|열)|이른\s*나이|대운|세운|시주|"
            r"늦게\s*만나|적령|만혼|지연.*결혼|결혼\s*적령|조혼|일찍\s*결혼",
            re.I,
        ),
    },
}

FOCUS = {
    "만혼": re.compile(
        r"만혼|늦.*결혼|늦게\s*만나|적령.*넘|지연.*결혼|"
        r"결혼.*늦|해외\s*인연|절지|고개\s*숙|나이.*먹.*결혼",
        re.I,
    ),
    "조혼": re.compile(
        r"조혼|빨.*결혼|일찍\s*결혼|이른\s*결혼|18세.*결혼|"
        r"일찍\s*해서|적령\s*전|너무\s*일찍",
        re.I,
    ),
    "재혼": re.compile(
        r"재혼|거쳐간|한번\s*거쳐|두\s*번째\s*배우자|이혼.*후|"
        r"겁재.*배우자|비견.*배우자|이혼하자마자|전\s*배우자",
        re.I,
    ),
    "배우자_덕": re.compile(
        r"배우자\s*덕|남편덕|처덕|덕을\s*보|덕.*보|참\s*배우자덕|"
        r"배우자의\s*복|복과\s*덕",
        re.I,
    ),
    "배우자_사회활동": re.compile(
        r"사회.*활동|사회.*역량|사회.*명예|직장|사업|대외|"
        r"활동력|능력자|명함|밖에서",
        re.I,
    ),
    "거리형_배우자": re.compile(
        r"별거|떨어져\s*살|거리.*두|몸이\s*떨어|각방|주말\s*부부|"
        r"적당히\s*거리|떨어져\s*있어야|역마.*남편|먼\s*곳",
        re.I,
    ),
    "결혼_후_안정": re.compile(
        r"결혼\s*후.*안정|안정.*결혼|가정\s*안정|안정적.*남편|"
        r"만족도.*높|조화|무난|큰\s*불만\s*없|오래\s*가",
        re.I,
    ),
}

REL = re.compile(
    r"배우자|남편|아내|부부|처|결혼|재혼|이혼|인연|배필|일지|정관|정재|편관|편재",
    re.I,
)
SKIP = re.compile(r"^Q\.|^A\.|시험|합격|고시", re.I)


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def extract_file(path: Path):
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
        return {"file": path.name, "error": str(e), "entries": []}
    return {"file": path.name, "pages": max((p for p, _ in rows), default=0), "entries": []}


def is_evidence(text):
    if len(text) < 18 or SKIP.search(text):
        return False
    if not REL.search(text):
        return False
    arch = any(spec["match"].search(text) for spec in TARGET_ARCH.values())
    focus = any(rx.search(text) for rx in FOCUS.values())
    return arch or focus


def classify(text):
    arches = [k for k, s in TARGET_ARCH.items() if s["match"].search(text)]
    themes = [k for k, rx in FOCUS.items() if rx.search(text)]
    return arches, themes


def extract_phrase(text, rx):
    m = rx.search(text)
    if not m:
        return None
    start = max(0, m.start() - 30)
    end = min(len(text), m.end() + 50)
    return text[start:end].strip()


def b_grade_files():
    out = []
    for p in sorted(ROOT.rglob("*.hwp")):
        if any(pat.search(p.name) for pat in A_GRADE):
            continue
        out.append(p)
    return out


def load_a_baseline():
    p = OUT_DIR / "_배우자분_원형01-10_추가수집.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def main():
    files = b_grade_files()
    all_entries = []
    file_stats = []

    for path in files:
        print("B:", path.name)
        h = Hwp5File(str(path))
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

        hits = 0
        for pg, text in rows:
            if not is_evidence(text):
                continue
            arches, themes = classify(text)
            if not arches and not themes:
                continue
            e = {
                "source": path.name,
                "page": pg,
                "conclusion": text,
                "archetypes": arches,
                "themes": themes,
            }
            all_entries.append(e)
            hits += 1
        file_stats.append({"file": path.name, "pages": max((p for p, _ in rows), default=0), "hits": hits})

    # cross counts
    arch_c = Counter()
    theme_c = Counter()
    cross = Counter()  # (arch, theme)
    for e in all_entries:
        for a in e["archetypes"]:
            arch_c[a] += 1
        for t in e["themes"]:
            theme_c[t] += 1
        for a in e["archetypes"]:
            for t in e["themes"]:
                cross[(a, t)] += 1

    # save jsonl
    jsonl = OUT_DIR / "_배우자분_B급_검증_entries.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for e in all_entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    # A-grade baseline from B-grade entries in A files - use focus counts from A doc
    A_FOCUS = {
        "만혼": 10, "조혼": 1, "재혼": 22, "배우자_덕": 23,
        "배우자_사회활동": 69, "거리형_배우자": 28, "결혼_후_안정": 22,
    }
    A_ARCH = {
        "원형-02": 107, "원형-04": 36, "원형-06": 21,
        "원형-07": 90, "원형-10": 17,
    }

    md = []
    md.append("# 배우자의 분 · B급 · 원형 5종 검증 v1\n\n")
    md.append("> **목표:** 새 원형 ✗ · **증거 누적** ●\n")
    md.append("> **검증 대상:** 원형-02 · 04 · 06 · 07 · 10 (A급 발견)\n")
    md.append(f"> **B급 파일:** {len(files)}종 · **증거 건수:** {len(all_entries)} · 2026-06-18\n\n")
    md.append("---\n\n")

    md.append("## 1. B급 파일 처리\n\n")
    md.append("| 파일 | 페이지 | 증거 |\n|------|:------:|:----:|\n")
    for s in sorted(file_stats, key=lambda x: -x["hits"]):
        if s["hits"]:
            md.append(f"| {s['file']} | {s['pages']} | {s['hits']} |\n")
    zero = [s for s in file_stats if s["hits"] == 0]
    if zero:
        md.append(f"\n**증거 0:** {len(zero)}종\n")

    md.append("\n---\n\n## 2. A급 vs B급 · 원형 매칭 (누적)\n\n")
    md.append("| 원형 | A급 | B급 | 합계 | 검증 |\n|------|:---:|:---:|:----:|:----:|\n")
    for aid in ["원형-02", "원형-04", "원형-06", "원형-07", "원형-10"]:
        a = A_ARCH.get(aid, 0)
        b = arch_c.get(aid, 0)
        total = a + b
        verdict = "● 누적" if b >= 5 else ("△ 보강" if b else "✗ 미확인")
        md.append(f"| {aid} {TARGET_ARCH[aid]['name'][:20]}… | {a} | {b} | {total} | {verdict} |\n")

    md.append("\n---\n\n## 3. 집중 7테마 · A vs B 증거\n\n")
    md.append("| 테마 | A급 | B급 | 합계 | 판정 |\n|------|:---:|:---:|:----:|:----:|\n")
    for fk in FOCUS:
        a = A_FOCUS.get(fk, 0)
        b = theme_c.get(fk, 0)
        total = a + b
        if b >= a * 0.3 or b >= 10:
            v = "● 교차확인"
        elif b >= 3:
            v = "△ 부분확인"
        else:
            v = "△ 희소"
        md.append(f"| {fk.replace('_', ' ')} | {a} | {b} | {total} | {v} |\n")

    md.append("\n---\n\n## 4. 원형 × 테마 교차 (B급)\n\n")
    md.append("| 원형 | 테마 | B건수 |\n|------|------|:-----:|\n")
    for (a, t), c in cross.most_common(40):
        md.append(f"| {a} | {t.replace('_', ' ')} | {c} |\n")

    md.append("\n---\n\n## 5. 원형별 B급 증거 수집\n\n")
    for aid in ["원형-02", "원형-04", "원형-06", "원형-07", "원형-10"]:
        spec = TARGET_ARCH[aid]
        items = [e for e in all_entries if aid in e["archetypes"]]
        md.append(f"### {aid} · {spec['name']}\n\n")
        md.append(f"**B급 건수:** {len(items)} · **A급:** {A_ARCH.get(aid, 0)} · **합:** {len(items) + A_ARCH.get(aid, 0)}\n\n")

        # theme breakdown within archetype
        tc = Counter()
        for e in items:
            for t in e["themes"]:
                tc[t] += 1
        if tc:
            md.append("**집중 테마 (B):** " + " · ".join(f"{k}({v})" for k, v in tc.most_common()) + "\n\n")

        md.append("#### 증거 문장\n\n")
        shown = 0
        for e in items:
            if shown >= 12:
                break
            themes = ", ".join(e["themes"]) if e["themes"] else "—"
            txt = e["conclusion"]
            if len(txt) > 200:
                txt = txt[:200] + "…"
            md.append(f"- **[{e['source']}]** p.{e['page']} · *{themes}*\n")
            md.append(f"  {txt}\n\n")
            shown += 1
        md.append("---\n\n")

    md.append("## 6. 집중 7테마 · B급 문장 수집\n\n")
    for fk, rx in FOCUS.items():
        items = [e for e in all_entries if fk in e["themes"]]
        md.append(f"### {fk.replace('_', ' ')}\n\n")
        md.append(f"**B급:** {len(items)} · **A급:** {A_FOCUS.get(fk, 0)} · **합:** {len(items) + A_FOCUS.get(fk, 0)}\n\n")

        # which archetypes support this theme in B
        ac = Counter()
        for e in items:
            for a in e["archetypes"]:
                ac[a] += 1
        if ac:
            md.append("**연결 원형:** " + " · ".join(f"{k}({v})" for k, v in ac.most_common()) + "\n\n")

        md.append("**구절:**\n\n")
        for e in items[:15]:
            ph = extract_phrase(e["conclusion"], FOCUS[fk])
            if ph:
                md.append(f"- [{e['source']}] {ph}\n")
        md.append("\n---\n\n")

    md.append("## 7. 검증 판정 (증거 누적)\n\n")
    md.append("| 원형 | B≥5 | 7테마 교차 | 종합 |\n|------|:---:|:----------:|:----:|\n")
    theme_by_arch = defaultdict(set)
    for (a, t), c in cross.items():
        if c >= 2:
            theme_by_arch[a].add(t)
    for aid in ["원형-02", "원형-04", "원형-06", "원형-07", "원형-10"]:
        b = arch_c.get(aid, 0)
        tc = len(theme_by_arch.get(aid, set()))
        if b >= 20 and tc >= 3:
            v = "● PASS"
        elif b >= 5:
            v = "△ 누적중"
        else:
            v = "△ 희소"
        md.append(f"| {aid} | {'Y' if b >= 5 else 'N'} | {tc} | {v} |\n")

    md.append("\n**한 줄:** B급 = A급 5원형 **교차 검증** · 원형 신규 생성 ✗ · **次 = 동일 원형 실고객 실측**\n\n")
    md.append("*배우자분_B급_원형검증_v1 / 확定 ✗*\n")

    out_path = OUT_DIR / "배우자분_B급_원형검증_v1.md"
    out_path.write_text("".join(md), encoding="utf-8")

    summary = {
        "b_files": len(files),
        "b_entries": len(all_entries),
        "arch_counts": dict(arch_c),
        "theme_counts": dict(theme_c),
        "cross_top": {f"{a}+{t}": c for (a, t), c in cross.most_common(30)},
    }
    (OUT_DIR / "_배우자분_B급_검증_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("entries", len(all_entries))
    print("written", out_path)


if __name__ == "__main__":
    main()
