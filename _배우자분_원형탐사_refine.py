# -*- coding: utf-8 -*-
"""Refine A-grade extraction: theme clustering + quality filter."""
import json
import re
from collections import Counter
from pathlib import Path

RAW = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_배우자분_원형탐사_A급_raw.json")
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\배우자분_원형탐사_A급_v1.md")

THEMES = [
    ("늦게_결혼_유리", re.compile(r"늦.*결혼|결혼.*늦|지연|늦게\s*해야|적령.*넘", re.I)),
    ("빨리_결혼_불리", re.compile(r"빨.*결혼|조혼|일찍.*결혼|이른\s*결혼.*불", re.I)),
    ("배우자_덕", re.compile(r"배우자.*덕|덕.*보|덕이\s*좋|참\s*배우자덕", re.I)),
    ("배우자_고생", re.compile(r"배우자.*고생|고생.*하|처.*고생|불만족|만족도.*떨|허결", re.I)),
    ("운_열림", re.compile(r"인연.*열|운.*열|이른\s*나이.*인연", re.I)),
    ("재혼_이혼", re.compile(r"재혼|이혼|거쳐|한번\s*더", re.I)),
    ("이별_갈등_반복", re.compile(r"다툼|싸우|갈등|미워|깨지|파破|형충", re.I)),
    ("결혼후_안정", re.compile(r"안정.*남편|안정.*배우자|결혼.*안정|만족도.*높", re.I)),
    ("배우자_사회활동", re.compile(r"사회.*명예|사회.*역량|직장|사업|밖에\s*있|대외", re.I)),
    ("배우자_가정", re.compile(r"가정|집안|가사|육아|지키|먹이고\s*기르", re.I)),
    ("별거_거리", re.compile(r"별거|거리.*두|떨어|적당히.*사|주말", re.I)),
    ("가까이_살면_악화", re.compile(r"가까이\s*살|너무\s*가까|건강.*악화|시름시름", re.I)),
    ("일지_정재정관_최상", re.compile(r"일지.*정재|일지.*정관|가장\s*좋", re.I)),
    ("지장간_배우자", re.compile(r"지장간.*배우자|배우자.*지장간", re.I)),
    ("12운성_역량", re.compile(r"12운성|입묘|절지|태지|병지|장생|제왕", re.I)),
    ("원진_귀문", re.compile(r"원진|귀문|육해", re.I)),
    ("공망_격각", re.compile(r"공망|격각|불안정|위축", re.I)),
    ("양인_겁재_손상", re.compile(r"양인|겁재.*배우자|좌불안", re.I)),
    ("식신_자녀우선", re.compile(r"식신.*배우자|자식.*우선|자녀.*걱정", re.I)),
    ("천간_명예_지지_실력", re.compile(r"천간.*명예|지지.*경제|지지.*실력", re.I)),
]

ASSERTIVE = re.compile(r"(된다|됩니다|되오|되니|것이오|것이지|입니다|이오|하오|하니|보면|보아|판단|유추|의미|형태|모양|속하|갖춘|발생|나타)", re.I)
QUESTION = re.compile(r"\?\s*$|까요|습니까|인가요|무엇|어떻|언제|왜\s", re.I)
NOISE = re.compile(r"^제?\d+편_|^Q\.|^A\.|^■|수업시간|다음\s*시간", re.I)


def main():
    data = json.loads(RAW.read_text(encoding="utf-8"))
    entries = []
    for item in data.get("entries_sample", []):
        entries.append(item)
    # full entries not in sample - reload from files by re-reading raw isn't complete
    # use patterns + top50 from raw; refine themes from all via second extract stored

    # Re-parse: raw only has sample 80 - need full list. Run quick merge from re-extract file
    full_path = RAW.parent / "_배우자분_원형탐사_A급_entries.jsonl"
    if not full_path.exists():
        print("entries jsonl missing - theme pass on sample only")
        all_e = data.get("entries_sample", [])
    else:
        all_e = [json.loads(l) for l in full_path.read_text(encoding="utf-8").splitlines() if l.strip()]

    theme_counter = Counter()
    theme_examples = {}
    quality = []

    for e in all_e:
        t = e["conclusion"]
        if QUESTION.search(t) or NOISE.search(t):
            continue
        if len(t) < 25:
            continue
        if not ASSERTIVE.search(t):
            continue
        quality.append(e)
        matched = []
        for name, rx in THEMES:
            if rx.search(t):
                theme_counter[name] += 1
                matched.append(name)
                theme_examples.setdefault(name, []).append(
                    {"source": e.get("source", ""), "page": e.get("page"), "text": t[:180]}
                )

    # structural recurrence from quality set
    struct_pat = [
        ("연월일시_궁위", re.compile(r"년주|월지|일지|시지|시주|연월일시", re.I)),
        ("천간지지_지장간_3층", re.compile(r"천간.*지지|지장간", re.I)),
        ("배우자궁_형충파해", re.compile(r"일지.*(충|형|파|해|합)|형충파해", re.I)),
        ("정재정관_편재편관", re.compile(r"정재|정관|편재|편관", re.I)),
        ("12운성_일지", re.compile(r"일지.*12운성|12운성.*일지", re.I)),
        ("대운_시주_전환", re.compile(r"대운|시주|61~80", re.I)),
        ("삼합_역마", re.compile(r"삼합|역마|巳酉丑", re.I)),
        ("12신살_천을", re.compile(r"12신살|천을귀인|백호|괴강", re.I)),
    ]
    struct_c = Counter()
    struct_ex = {}
    for e in quality:
        t = e["conclusion"]
        for name, rx in struct_pat:
            if rx.search(t):
                struct_c[name] += 1
                struct_ex.setdefault(name, t[:120])

    md = []
    md.append("# 배우자의 분 · 원형 탐사 · A급 수집 v1\n\n")
    md.append("> **단계:** 반복 구조 · 반복 사건 · 반복 원형 **수집** (분 생성 ✗ · 상담문 ✗)\n")
    md.append("> **방식:** 결론 문장 → 반복 사건 → 사주 구조 (역추적)\n")
    md.append("> **대상:** `C:\\Users\\Lenovo\\Desktop\\결혼_관련` · A급 7종 · **2026-06-18**\n\n")
    md.append("---\n\n")

    md.append("## 1. A급 파일 처리\n\n")
    md.append("| # | 파일 | 페이지 | 원시 추출 | 품질 필터 후 |\n")
    md.append("|---|------|:------:|:---------:|:------------:|\n")
    by_file = Counter(e.get("source") for e in quality)
    raw_by = {f["file"]: f["entry_count"] for f in data["files"]}
    for i, f in enumerate(data["files"], 1):
        md.append(f"| {i} | {f['file']} | {f['pages']} | {f['entry_count']} | {by_file.get(f['file'], 0)} |\n")
    md.append(f"\n**전체:** 원시 {data['total_entries']} → 품질 {len(quality)} (질문·목차·단문 제외)\n\n")

    md.append("---\n\n## 2. 반복 구조 목록\n\n")
    md.append("| 구조 | 빈도 | 대표 결론 |\n|------|:----:|----------|\n")
    for name, cnt in struct_c.most_common():
        ex = struct_ex.get(name, "—")
        md.append(f"| {name} | {cnt} | {ex}… |\n")

    md.append("\n---\n\n## 3. 반복 사건 목록 (결론 테마)\n\n")
    md.append("| 사건/결론 테마 | 빈도 | 예시 |\n|---------------|:----:|------|\n")
    for name, cnt in theme_counter.most_common():
        ex = theme_examples.get(name, [{}])[0].get("text", "—")[:80]
        md.append(f"| {name} | {cnt} | {ex}… |\n")

    md.append("\n---\n\n## 4. 공통 원형 후보\n\n")
    candidates = [
        ("원형-01 · 천간명예/지지실력/지장간잠복", struct_c.get("천간지지_지장간_3층", 0), "배우자를 연·월·일·시 **3층**으로 읽는 공통 틀"),
        ("원형-02 · 정관정재=만족 / 편관편재=허결", theme_counter.get("결혼후_안정", 0) + theme_counter.get("배우자_고생", 0), "육신별 **만족도·허결** 이원"),
        ("원형-03 · 일지=관계 / 지지12운성=사회역량", struct_c.get("12운성_일지", 0) + theme_counter.get("12운성_역량", 0), "일지=나↔배우자 · 지지=배우자 사회면"),
        ("원형-04 · 형충파해→거리·갈등", theme_counter.get("이별_갈등_반복", 0) + theme_counter.get("별거_거리", 0), "부부궁 손상 → **미움·파破·적당한 거리**"),
        ("원형-05 · 가까이 살면 악화", theme_counter.get("가까이_살면_악화", 0), "양인·충·격각 → **근접 거주 불리**"),
        ("원형-06 · 배우자 덕·복", theme_counter.get("배우자_덕", 0), "정재 일지 · 상생 · 귀인"),
        ("원형-07 · 밖=사회 / 집=가정 역할", theme_counter.get("배우자_사회활동", 0) + theme_counter.get("배우자_가정", 0), "월주·역마·식신=**공간 분리**"),
        ("원형-08 · 원진·귀문=잦은 다툼", theme_counter.get("원진_귀문", 0), "싫지 않으나 **자주 다툼**"),
        ("원형-09 · 식신=자녀우선·배우자 후순위", theme_counter.get("식신_자녀우선", 0), "일지 식신 → **기르는** 배우자"),
        ("원형-10 · 년주=이른 인연 / 대운=시기", theme_counter.get("운_열림", 0) + struct_c.get("대운_시주_전환", 0), "궁위=**시간·인연 열림**"),
    ]
    md.append("| 후보 | 점수 | 핵심 |\n|------|:----:|------|\n")
    for name, score, core in sorted(candidates, key=lambda x: -x[1]):
        if score:
            md.append(f"| {name} | {score} | {core} |\n")

    md.append("\n---\n\n## 5. 새롭게 발견한 구조 (A급 교차)\n\n")
    novel = [
        "**설계도 은유** — 배우자성이 없어도 병화 정관 등 **대체 읽기** (탈원)",
        "**동정(動靜) 읽기** — 배우자궁 멀쩡해도 **대운·동정**으로 관계 변형",
        "**월주=직업공간=배우자 활동력** — 젊은 날·사회활동 축",
        "**격각=임대·역마=배우자 자리 불안정**",
        "**충=움직임 완충 → 적당한 거리** (탈원 9편)",
        "**辰未 겁재중 배우자 → 한번 거쳐야** (재혼·지연 암시)",
    ]
    for n in novel:
        md.append(f"- {n}\n")

    md.append("\n---\n\n## 6. 결론 문장 빈도 TOP 50 (테마)\n\n")
    md.append("| # | 빈도 | 결론 테마 |\n|---|:----:|----------|\n")
    for i, (name, cnt) in enumerate(theme_counter.most_common(50), 1):
        md.append(f"| {i} | {cnt} | {name} |\n")

    md.append("\n---\n\n## 7. 역추적 샘플 (고품질 15건)\n\n")
    shown = 0
    priority_themes = [t for t, _ in theme_counter.most_common(10)]
    for theme in priority_themes:
        for ex in theme_examples.get(theme, [])[:2]:
            if shown >= 15:
                break
            md.append(f"### {theme} · [{ex['source']}] p.{ex['page']}\n\n")
            md.append(f"**[원문 요약]** {ex['text'][:120]}…\n\n")
            md.append(f"**[결론]** {ex['text']}\n\n")
            md.append("**[사주 구조]** (역추적) — ")
            if "정관" in ex["text"] or "정재" in ex["text"]:
                md.append("정관/정재 · ")
            if "편관" in ex["text"] or "편재" in ex["text"]:
                md.append("편관/편재 · ")
            if "일지" in ex["text"]:
                md.append("일지(배우자궁) · ")
            if "지장간" in ex["text"]:
                md.append("지장간 · ")
            if "12운성" in ex["text"] or "입묘" in ex["text"] or "절지" in ex["text"]:
                md.append("12운성 · ")
            if "원진" in ex["text"] or "귀문" in ex["text"]:
                md.append("원진/귀문 · ")
            if "충" in ex["text"] or "파" in ex["text"] or "형" in ex["text"]:
                md.append("형충파해 · ")
            md.append("\n\n")
            md.append("**[반복 사건]** — ")
            ev = []
            if theme_counter.get("별거_거리") and "거리" in ex["text"]:
                ev.append("적당한 거리")
            if "다툼" in ex["text"] or "싸우" in ex["text"]:
                ev.append("잦은 다툼")
            if "덕" in ex["text"]:
                ev.append("배우자 덕")
            if "불만족" in ex["text"] or "허결" in ex["text"]:
                ev.append("만족도 저하")
            if "사회" in ex["text"] or "명예" in ex["text"]:
                ev.append("사회적 역량")
            if "가정" in ex["text"] or "집" in ex["text"]:
                ev.append("가정 역할")
            md.append(", ".join(ev) if ev else theme.replace("_", " "))
            md.append("\n\n---\n\n")
            shown += 1

    md.append("\n---\n\n## 8. B급 대기\n\n")
    md.append("A급 7종 완료 · **次 = B급** `*.hwp` 나머지 31종 교차 검증\n\n")
    md.append("*배우자분_원형탐사_A급_v1 / 원형 DB 수집 / 확定 ✗*\n")

    OUT.write_text("".join(md), encoding="utf-8")
    print("quality", len(quality))
    print("themes", len(theme_counter))
    print("written", OUT)


if __name__ == "__main__":
    main()
