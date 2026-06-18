# -*- coding: utf-8 -*-
import re
from pathlib import Path

from hwp5.binmodel import Hwp5File, Paragraph, ParaText

HWP = Path(
    r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp"
)

FAIL = re.compile(
    r"성격|기질|심리|적응력|충동|연애|배우자|결혼|애정|"
    r"공부\s*방법|MBTI|처세|운이\s*좋|운세|"
    r"가라\.|가라는|해야\s*되|언급해\s*주|좋아\s*보|가장\s*좋|"
    r"안\s*된다|포기|노력|겁이|의심|화끈|입을\s*무겁|"
    r"동물|띠를|생태|생리|노린내|미혼|亡身|개화"
)

STRUCT = re.compile(
    r"조직(으로|성|생활|무늬|속성|중심|계통)|"
    r"사업(으로|성|인)|직장(으로|생활|환경|전변)|"
    r"자격(증|속성|쓰임)|유통(업)?|교육(자|속성|사업|관련)?|"
    r"법조|법무|의료|전문|공직|공무원|"
    r"납품|제조|생산|대리점|매장|프랜차|자릿세|"
    r"부동산|중개|임대|금융|펀드|회계|세무|"
    r"월지.*직업|직업.*월지|월간.*속성|월간.*형태|"
    r"正財.*조직|偏財.*사업|조직성\s*중심|사회적\s*중심|"
    r"조직\(납품|커피숍|학원|군인|경찰|변호|판사|검사|"
    r"테이블|take\s*out|브랜드\s*카펴|내근|외근|"
    r"역마|항공|해운|무역|건설|통신|"
    r"조직과\s*서로\s*이익|조직성과\s*사업성"
)


def para_text(model):
    parts = []
    for item in model.get("content", {}).get("chunks", []):
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[1], str):
            parts.append(item[1])
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def split_sents(text):
    parts = re.split(
        r"(?<=[\.!?…])\s+|(?<=다\.)\s+|(?<=니다\.)\s+|(?<=본다\.)\s+|(?<=된다\.)\s+",
        text.strip(),
    )
    return [p.strip() for p in parts if len(p.strip()) >= 15]


def candidate_name(s):
    rules = [
        (r"월지.*직업|직업.*월지|월지.*행위", "월지 반복행위 직업 구조"),
        (r"월간.*속성|월간.*형태|겉무늬", "월간 속성(겉무늬) 직업 구조"),
        (r"正財.*조직|조직성\s*중심|조직성중심", "조직형(正財) 직업 구조"),
        (r"偏財.*사업|사회적\s*중심|사업성|사업으로", "사업형(偏財) 직업 구조"),
        (r"유통|납품|대리점|매장|프랜차|도매|소매", "유통·납품 사업 구조"),
        (r"자릿세|테이블|take\s*out|브랜드\s*카페|커피숍", "자릿세·매장 사업 구조"),
        (r"제조|생산", "제조·생산 사업 구조"),
        (r"법조|법무|변호|판사|검사|공증|행정사", "법무·법조 자격 전문직 구조"),
        (r"의료|병원|간호|치과", "의료 자격 전문직 구조"),
        (r"교육|학원|교사|컨설턴트", "교육·컨설팅 전문직 구조"),
        (r"부동산|중개|임대", "부동산·중개 구조"),
        (r"금융|펀드|은행|보험|회계|세무", "금융·회계 전문직 구조"),
        (r"군인|경찰|특수행정|물리력", "군·경 조직 전문직 구조"),
        (r"공직|공무원|행정|재정", "공직·행정 조직 구조"),
        (r"역마|항공|해운|무역|건설|통신|외교|언론", "역마·대외 조직 구조"),
        (r"역술|종교", "종교·역술 전문 서비스 구조"),
        (r"조직생활|직장전변|조직에서\s*조직", "조직생활·전환 구조"),
        (r"자격증|자격\s*속성|면허", "자격·면허 전문직 구조"),
        (r"神殺|충|刑|파|해", "신살·형충 기반 직업 구조"),
    ]
    for pat, name in rules:
        if re.search(pat, s, re.I):
            return name
    return "직업 채널 구조"


def why_line(s, name):
    if "正財" in s or "조직성" in s:
        return "正財·조직성 중심으로 직장·조직 채널인지 사업 채널인지를 가르는 구조 선언이다."
    if "偏財" in s or "사업" in s:
        return "偏財·사업성 중심으로 사업·조직을 나누는 직업 채널 구조를 말한다."
    if "월지" in s:
        return "월지를 직업의 본체(반복행위·직장환경)로 보는 직업 구조 판단 기준이다."
    if "월간" in s:
        return "월간을 직업의 겉속성·형태로 보는 구조 판단 기준이다."
    if "유통" in s or "납품" in s or "매장" in s:
        return "유통·납품·매장 등 돈이 붙는 사업 채널 구조를 직접 명시한다."
    if "자격" in s or "법조" in s or "의료" in s:
        return "자격·면허 기반 전문직 채널(법조·의료 등)을 직업 구조로 규정한다."
    if "자릿세" in s or "커피" in s or "테이블" in s:
        return "자릿세 vs 유통 등 매장·사업 형태를 가르는 구조를 말한다."
    if "교육" in s or "학원" in s:
        return "교육·컨설팅 등 전문 서비스 채널을 직업 구조로 규정한다."
    if "부동산" in s or "중개" in s:
        return "부동산·중개 업종과 자격(印星) 요건을 직업 구조로 연결한다."
    if "공직" in s or "공무원" in s:
        return "공직·행정 조직 계통을 직업 구조로 규정한다."
    if "조직" in s:
        return "조직·직장 채널을 중심으로 한 직업 구조(조직형)를 말한다."
    return f"「{name}」에 해당하는 직업·역할·채널이 문장에 직접 드러난다."


def ok(s):
    if len(s) > 260 or FAIL.search(s):
        return False
    return bool(STRUCT.search(s))


def collect():
    h = Hwp5File(str(HWP))
    page = 1
    gang = ""
    subtitle = ""
    seq = 0
    out = []

    for section in h.bodytext.sections:
        cur = ""
        pg = page
        for model in section.models():
            if model["type"] is Paragraph:
                if cur.strip():
                    if re.match(r"^제\d+강", cur):
                        gang = cur
                    if cur.startswith("■"):
                        subtitle = cur.lstrip("■ ").strip()
                    for sent in split_sents(cur):
                        if ok(sent):
                            seq += 1
                            out.append(
                                dict(
                                    seq=seq,
                                    text=sent,
                                    gang=gang,
                                    subtitle=subtitle,
                                    page=pg,
                                )
                            )
                cur = ""
                split = model["content"].get("split")
                if split is not None and getattr(split, "new_page", False):
                    page += 1
                pg = page
            elif model["type"] is ParaText:
                cur += para_text(model)
        if cur.strip():
            if re.match(r"^제\d+강", cur):
                gang = cur
            if cur.startswith("■"):
                subtitle = cur.lstrip("■ ").strip()
            for sent in split_sents(cur):
                if ok(sent):
                    seq += 1
                    out.append(
                        dict(
                            seq=seq,
                            text=sent,
                            gang=gang,
                            subtitle=subtitle,
                            page=page,
                        )
                    )
    return out


def pick30(items):
    # priority: 탈도사 numbered rules, 正財/偏財 split, 월지/월간, job category bullets
    pri = []
    rest = []
    for it in items:
        t = it["text"]
        score = 0
        if "탈도사" in (it["subtitle"] or "") or re.match(r"^\d+\.", t):
            score += 2
        if re.search(r"월지|월간|正財|偏財|조직성|사업성|자격|유통|자릿세|법조|의료|교육|부동산|금융|군|경찰", t):
            score += 2
        if re.search(r"으로\s*(본|보|가)|쓰기도|종사|구조", t):
            score += 1
        if score >= 3:
            pri.append(it)
        else:
            rest.append(it)

    chosen = []
    seen_text = set()
    seen_name = set()

    for pool in (pri, rest):
        for it in pool:
            if len(chosen) >= 30:
                break
            if it["text"] in seen_text:
                continue
            name = candidate_name(it["text"])
            if name in seen_name and len(chosen) > 15:
                continue
            seen_text.add(it["text"])
            seen_name.add(name)
            it["name"] = name
            it["why"] = why_line(it["text"], name)
            chosen.append(it)
    if len(chosen) < 30:
        for it in items:
            if len(chosen) >= 30:
                break
            if it["text"] not in seen_text:
                it["name"] = candidate_name(it["text"])
                it["why"] = why_line(it["text"], it["name"])
                chosen.append(it)
                seen_text.add(it["text"])
    chosen.sort(key=lambda x: x["seq"])
    return chosen[:30]


def main():
    items = collect()
    picked = pick30(items)
    lines = []
    for i, c in enumerate(picked, 1):
        lines += [
            "---",
            "",
            f"### {i}",
            "",
            "**[원문]**",
            c["text"],
            "",
            "**[직업의 분 후보명]**",
            c["name"],
            "",
            "**[왜 직업의 분 후보인가]**",
            c["why"],
            "",
            "**[출처]**",
            f"{c['gang'] or '(강의명 미표기)'} / {c['subtitle'] or '(소제목 미표기)'} / p.{c['page']} (추정)",
            "",
        ]
    out = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업의분_후보_30_v1.md")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(len(picked), "written", out)


if __name__ == "__main__":
    main()
