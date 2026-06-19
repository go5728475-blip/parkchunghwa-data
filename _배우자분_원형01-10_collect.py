# -*- coding: utf-8 -*-
"""Per-archetype (원형-01~10) event/outcome/sentence collection from A-grade entries."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ENTRIES = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_배우자분_원형탐사_A급_entries.jsonl")
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\배우자분_원형01-10_추가수집_v1.md")

ASSERTIVE = re.compile(r"(된다|됩니다|되오|되니|것이오|것이지|입니다|이오|하오|하니|보면|보아|판단|유추|의미|형태|모양|속하|갖춘|발생|나타|것이다|된다\.|됩니다\.)", re.I)
QUESTION = re.compile(r"\?\s*$|까요|습니까|인가요", re.I)
NOISE = re.compile(r"^제?\d+편_|^Q\.|^A\.|^■|수업시간|다음\s*시간", re.I)

ARCHETYPES = {
    "원형-01": {
        "name": "천간명예 / 지지실력 / 지장간잠복",
        "match": re.compile(
            r"천간.*(명예|사회)|지지.*(경제|실력|내실)|지장간.*(배우자|두드러|잠복)|"
            r"천간은.*바라보|지지는.*내실|지장간은",
            re.I,
        ),
    },
    "원형-02": {
        "name": "정관·정재=만족 / 편관·편재=허결",
        "match": re.compile(
            r"정관|정재|편관|편재|만족도|허결|올바른\s*배우자|금전.*애정.*동거",
            re.I,
        ),
    },
    "원형-03": {
        "name": "일지=관계 / 지지12운성=사회역량",
        "match": re.compile(
            r"12운성|일지.*12운성|지지.*12운성|입묘|절지|태지|병지|장생|제왕|"
            r"사회적.*역량|배우자와\s*나와의\s*관계",
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
    "원형-05": {
        "name": "가까이 살면 악화",
        "match": re.compile(
            r"가까이\s*살|너무\s*가까|건강.*악화|시름시림|수술|양인살.*일지|"
            r"좌불안|칼.*놓",
            re.I,
        ),
    },
    "원형-06": {
        "name": "배우자 덕·복",
        "match": re.compile(
            r"배우자.*(덕|복)|덕.*보|덕을\s*보|참\s*배우자덕|귀인.*배우자|"
            r"배우자의\s*복|복과\s*덕",
            re.I,
        ),
    },
    "원형-07": {
        "name": "밖=사회 / 집=가정",
        "match": re.compile(
            r"밖에\s*있|집안|가정|월주.*활동|직장|사업|사회.*활동|대외|"
            r"역마|출장|동거.*해도|가사|육아|시댁|처가",
            re.I,
        ),
    },
    "원형-08": {
        "name": "원진·귀문=잦은 다툼",
        "match": re.compile(
            r"원진|귀문|육해|다툼|싸우|갈등|미워|맞추.*살|깎.*다듬",
            re.I,
        ),
    },
    "원형-09": {
        "name": "식신=자녀우선·배우자 후순위",
        "match": re.compile(
            r"식신.*배우자|식상.*자식|자식.*우선|자녀.*걱정|먹이고\s*기르|"
            r"배우자.*뒷전|일지.*식신",
            re.I,
        ),
    },
    "원형-10": {
        "name": "년주=이른 인연 / 대운·시주=시기",
        "match": re.compile(
            r"년주.*(인연|만나|열)|이른\s*나이|대운|세운|시주|61~80|"
            r"늦게\s*만나|적령|만혼|지연.*결혼|결혼\s*적령",
            re.I,
        ),
    },
}

# Event extraction patterns
EVENT_PATTERNS = [
    ("별거·거리두기", re.compile(r"별거|떨어져|거리.*두|각방|주말\s*부부|분가", re.I)),
    ("동거·한집", re.compile(r"동거|한\s*집|같이\s*살|붙어", re.I)),
    ("출장·이동", re.compile(r"출장|이사|역마|떠나|머무", re.I)),
    ("다툼·싸움", re.compile(r"다툼|싸우|갈등|미워|깨지", re.I)),
    ("이혼·별거", re.compile(r"이혼|헤어|파혼", re.I)),
    ("재혼·거쳐감", re.compile(r"재혼|거쳐|한번\s*더|두\s*번째", re.I)),
    ("만남·인연", re.compile(r"만나|인연.*열|처연|장가|시집", re.I)),
    ("직장·사업", re.compile(r"직장|사업|사회.*활동|명예|체面", re.I)),
    ("가사·육아", re.compile(r"가사|육아|집안|돌봄|기르", re.I)),
    ("건강·수술", re.compile(r"건강|수술|시름|아프", re.I)),
    ("처가·시댁", re.compile(r"처가|시댁|시가|장인|시부", re.I)),
    ("금전·경제", re.compile(r"금전|돈|경제|재물|실속", re.I)),
]

OUTCOME_PATTERNS = [
    ("결혼후_안정", re.compile(r"안정|만족도.*높|조화|평온|무난|큰\s*불만\s*없", re.I)),
    ("결혼후_불안·허결", re.compile(r"불안|허결|불만족|만족도.*떨|언발|시소", re.I)),
    ("만혼·늦은결혼", re.compile(r"늦.*결혼|늦게\s*만나|만혼|적령.*넘|지연|해외\s*인연", re.I)),
    ("조혼·이른결혼", re.compile(r"빨.*결혼|조혼|일찍\s*결혼|이른\s*나이.*결혼|18세", re.I)),
    ("재혼·이혼경험", re.compile(r"재혼|이혼.*후|거쳐간", re.I)),
    ("배우자_덕", re.compile(r"덕.*보|덕을\s*보|배우자\s*덕|참\s*배우자덕", re.I)),
    ("배우자_고생", re.compile(r"고생|불행|좌불안|악화", re.I)),
    ("운_열림", re.compile(r"운.*열|인연.*열|열릴", re.I)),
    ("별거_필요", re.compile(r"떨어져\s*있어야|별거|거리.*두.*사", re.I)),
    ("사회적_성공", re.compile(r"명예|사회.*역량|폼\s*잡|능력자", re.I)),
    ("가정_중심", re.compile(r"가정.*안정|집.*지키|가사|육아", re.I)),
]

FOCUS = {
    "결혼_후_안정": re.compile(
        r"결혼\s*후.*안정|안정.*결혼|가정\s*안정|안정적.*남편|안정적.*배우자|"
        r"만족도.*높|조화.*가|무난.*인연|큰\s*불만\s*없",
        re.I,
    ),
    "별거": re.compile(
        r"별거|떨어져\s*살|거리.*두|몸이\s*떨어|각방|주말\s*부부|"
        r"적당히\s*거리|떨어져\s*있어야",
        re.I,
    ),
    "만혼": re.compile(
        r"만혼|늦.*결혼|늦게\s*만나|적령.*넘|지연.*결혼|"
        r"늦게\s*해야|결혼.*늦|해외\s*인연|적령기\s*에\s*적당|"
        r"절지|고개\s*숙|늦게\s*만나든|나이.*먹.*결혼|"
        r"결혼\s*시기.*늦|인연.*늦",
        re.I,
    ),
    "재혼": re.compile(
        r"재혼|거쳐간|한번\s*거쳐|두\s*번째\s*배우자|이혼.*후|"
        r"거쳐\s*간|겁재.*배우자|비견.*배우자|한번\s*더|"
        r"이혼하자마자|거쳐야|전\s*배우자",
        re.I,
    ),
    "배우자_덕": re.compile(
        r"배우자\s*덕|덕을\s*보|덕.*보|참\s*배우자덕|"
        r"배우자의\s*복|귀인.*배우자",
        re.I,
    ),
    "배우자_갈등": re.compile(
        r"갈등|다툼|싸우|미워|깨지|불화|불만|허결|불만족|"
        r"파破|형충|원진|귀문",
        re.I,
    ),
    "배우자_사회활동": re.compile(
        r"사회.*활동|사회.*역량|사회.*명예|직장|사업|대외|"
        r"밖에\s*있|활동력|능력자|명함",
        re.I,
    ),
}


def load_all():
    rows = []
    for line in ENTRIES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        e = json.loads(line)
        t = e["conclusion"]
        if QUESTION.search(t) and len(t) < 40:
            continue
        if NOISE.search(t):
            continue
        rows.append(e)
    return rows


def load_quality():
    return [e for e in load_all() if len(e["conclusion"]) >= 20 and ASSERTIVE.search(e["conclusion"])]


def norm_sentence(t, n=90):
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"[「」\"'""''\[\]()]", "", t)
    return t[:n]


def extract_tags(text, patterns):
    return [name for name, rx in patterns if rx.search(text)]


def top_sentences(items, n=12):
    c = Counter(norm_sentence(x["conclusion"]) for x in items)
    return c.most_common(n)


def md_table(rows, headers):
    lines = ["| " + " | ".join(headers) + " |\n"]
    lines.append("|" + "|".join([":---:" if i == 1 else "---" for i in range(len(headers))]) + "|\n")
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |\n")
    return "".join(lines)


def main():
    entries = load_quality()
    all_entries = load_all()
    by_arch = defaultdict(list)
    for e in entries:
        t = e["conclusion"]
        for aid, spec in ARCHETYPES.items():
            if spec["match"].search(t):
                by_arch[aid].append(e)

    focus_hits = {k: [] for k in FOCUS}
    for e in all_entries:
        t = e["conclusion"]
        if len(t) < 15:
            continue
        for fk, rx in FOCUS.items():
            if rx.search(t):
                focus_hits[fk].append(e)

    md = []
    md.append("# 배우자의 분 · 원형-01~10 · 추가 수집 v1\n\n")
    md.append("> **근거:** A급 7종 · 품질 필터 317건 · **결론→사건→결과** 역추적\n")
    md.append("> **단계:** 원형 DB 수집 (분 생성 ✗) · **2026-06-18**\n\n")
    md.append("---\n\n")

    md.append("## 집중 수집 7테마 (전 원형 교차)\n\n")
    for fk in [
        "결혼_후_안정", "별거", "만혼", "재혼",
        "배우자_덕", "배우자_갈등", "배우자_사회활동",
    ]:
        hits = focus_hits[fk]
        md.append(f"### {fk.replace('_', ' ')}\n\n")
        md.append(f"**건수:** {len(hits)}\n\n")
        ev_c = Counter()
        out_c = Counter()
        for e in hits:
            for ev in extract_tags(e["conclusion"], EVENT_PATTERNS):
                ev_c[ev] += 1
            for o in extract_tags(e["conclusion"], OUTCOME_PATTERNS):
                out_c[o] += 1
        if ev_c:
            md.append("**반복 사건:** " + " · ".join(f"{k}({v})" for k, v in ev_c.most_common(8)) + "\n\n")
        if out_c:
            md.append("**반복 결과:** " + " · ".join(f"{k}({v})" for k, v in out_c.most_common(8)) + "\n\n")
        md.append("**대표 문장:**\n\n")
        for sent, cnt in top_sentences(hits, 15):
            md.append(f"- ({cnt}) {sent}\n")
        # phrase-level hits
        phrases = []
        phrase_rx = {
            "결혼_후_안정": re.compile(r"[^。\.!?]{8,60}(?:안정|만족도.*높|조화)[^。\.!?]{0,30}", re.I),
            "별거": re.compile(r"[^。\.!?]{8,60}(?:별거|떨어져|거리.*두)[^。\.!?]{0,30}", re.I),
            "만혼": re.compile(r"[^。\.!?]{8,60}(?:늦|적령|만혼|절지|고개\s*숙)[^。\.!?]{0,30}", re.I),
            "재혼": re.compile(r"[^。\.!?]{8,60}(?:재혼|거쳐|이혼)[^。\.!?]{0,30}", re.I),
            "배우자_덕": re.compile(r"[^。\.!?]{8,60}(?:덕|복)[^。\.!?]{0,30}", re.I),
            "배우자_갈등": re.compile(r"[^。\.!?]{8,60}(?:다툼|싸우|갈등|미워|불만족)[^。\.!?]{0,30}", re.I),
            "배우자_사회활동": re.compile(r"[^。\.!?]{8,60}(?:사회|직장|활동|명예)[^。\.!?]{0,30}", re.I),
        }
        if fk in phrase_rx:
            pc = Counter()
            for e in hits:
                for m in phrase_rx[fk].findall(e["conclusion"]):
                    pc[m.strip()] += 1
            if pc:
                md.append("\n**구절 단위:**\n\n")
                for ph, c in pc.most_common(10):
                    md.append(f"- ({c}) {ph.strip()}\n")
        md.append("\n---\n\n")

    md.append("## 원형별 상세 (01~10)\n\n")
    for aid in sorted(ARCHETYPES.keys()):
        spec = ARCHETYPES[aid]
        items = by_arch[aid]
        md.append(f"### {aid} · {spec['name']}\n\n")
        md.append(f"**매칭 건수:** {len(items)}\n\n")

        ev_c = Counter()
        out_c = Counter()
        for e in items:
            for ev in extract_tags(e["conclusion"], EVENT_PATTERNS):
                ev_c[ev] += 1
            for o in extract_tags(e["conclusion"], OUTCOME_PATTERNS):
                out_c[o] += 1

        md.append("#### 1. 반복 사건\n\n")
        if ev_c:
            for k, v in ev_c.most_common(12):
                md.append(f"- **{k}** × {v}\n")
        else:
            md.append("- (매칭 없음)\n")
        md.append("\n")

        md.append("#### 2. 반복 결혼 결과\n\n")
        if out_c:
            for k, v in out_c.most_common(12):
                md.append(f"- **{k}** × {v}\n")
        else:
            md.append("- (매칭 없음)\n")
        md.append("\n")

        md.append("#### 3. 반복 문장\n\n")
        md.append("| 빈도 | 문장 |\n|:---:|:----|\n")
        for sent, cnt in top_sentences(items, 10):
            safe = sent.replace("|", "\\|")
            md.append(f"| {cnt} | {safe} |\n")
        md.append("\n")

        # cross with focus themes
        cross = []
        for fk, rx in FOCUS.items():
            n = sum(1 for e in items if rx.search(e["conclusion"]))
            if n:
                cross.append((fk.replace("_", " "), n))
        if cross:
            md.append("#### 집중 테마 교차\n\n")
            md.append("| 테마 | 건수 |\n|------|:----:|\n")
            for name, n in sorted(cross, key=lambda x: -x[1]):
                md.append(f"| {name} | {n} |\n")
            md.append("\n")

        # one reverse-trace sample
        sample = next((e for e in items if len(extract_tags(e["conclusion"], EVENT_PATTERNS)) >= 1), None)
        if sample:
            md.append("#### 역추적 샘플 1건\n\n")
            md.append(f"**[결론]** {sample['conclusion'][:250]}…\n\n")
            md.append(f"**[사건]** {', '.join(extract_tags(sample['conclusion'], EVENT_PATTERNS))}\n\n")
            md.append(f"**[결과]** {', '.join(extract_tags(sample['conclusion'], OUTCOME_PATTERNS))}\n\n")
            md.append(f"**[출처]** {sample['source']} p.{sample['page']}\n\n")

        md.append("---\n\n")

    md.append("*배우자분_원형01-10_추가수집_v1 / A급 / 확定 ✗*\n")
    OUT.write_text("".join(md), encoding="utf-8")

    payload = {
        "by_archetype_counts": {k: len(v) for k, v in by_arch.items()},
        "focus_counts": {k: len(v) for k, v in focus_hits.items()},
    }
    (OUT.parent / "_배우자분_원형01-10_추가수집.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("written", OUT)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
