# -*- coding: utf-8 -*-
"""Extract HWP metadata: readability, page count, heading outline."""
import json
import re
import sys
from pathlib import Path

from hwp5.binmodel import Hwp5File, Paragraph, ParaText, Style, ControlChar
from hwp5.filestructure import Hwp5File as FsHwp5File

HWP = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp")
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_hwp_outline.json")


def text_from_paratext(model):
    chunks = model.get("content", {}).get("chunks", [])
    parts = []
    for item in chunks:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            val = item[1]
            if isinstance(val, str):
                parts.append(val)
            elif isinstance(val, dict) and val.get("name") == "CHAR":
                # page/section break controls
                chid = val.get("chid")
                if chid:
                    parts.append(f"[{chid}]")
    return "".join(parts).strip()


def main():
    result = {
        "requested_name": "천론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp",
        "actual_filename": HWP.name,
        "readable": False,
        "page_count_summary": None,
        "page_break_count": 0,
        "section_count": 0,
        "paragraph_count": 0,
        "styles": [],
        "headings": [],
        "errors": [],
    }

    try:
        fs = FsHwp5File(str(HWP))
        summary = fs.summaryinfo
        result["page_count_summary"] = summary.numberOfPages
        result["title_meta"] = summary.title
        result["subject_meta"] = summary.subject
    except Exception as e:
        result["errors"].append(f"summary: {e}")

    styles = {}
    paragraphs = []
    page_breaks = 0
    new_sections = 0

    try:
        h = Hwp5File(str(HWP))
        docinfo = h.docinfo
        for model in docinfo.models():
            if model["type"] is Style:
                c = model["content"]
                sid = len(styles)
                flags = c.get("flags")
                kind = getattr(flags, "kind", None) if flags is not None else None
                styles[sid] = {
                    "id": sid,
                    "local_name": c.get("local_name", ""),
                    "name": c.get("name", ""),
                    "kind": kind,
                }

        sec_idx = 0
        for section in h.bodytext.sections:
            result["section_count"] += 1
            current_para = None
            for model in section.models():
                if model["type"] is Paragraph:
                    split = model["content"].get("split")
                    split_dict = {}
                    if split is not None:
                        for attr in ("new_page", "new_section", "new_column", "new_columnsdef"):
                            split_dict[attr] = bool(getattr(split, attr, False))
                    current_para = {
                        "section": sec_idx,
                        "style_id": model["content"].get("style_id"),
                        "parashape_id": model["content"].get("parashape_id"),
                        "split": split_dict,
                        "text": "",
                    }
                    if split_dict.get("new_page"):
                        page_breaks += 1
                    if split_dict.get("new_section"):
                        new_sections += 1
                    paragraphs.append(current_para)
                elif model["type"] is ParaText and current_para is not None:
                    current_para["text"] += text_from_paratext(model)
            sec_idx += 1

        result["readable"] = True
        result["page_break_count"] = page_breaks
        result["paragraph_count"] = len(paragraphs)
        result["styles"] = list(styles.values())

        # heading candidates: style name/local_name or short standalone lines
        heading_style_ids = set()
        for sid, st in styles.items():
            names = (st.get("local_name") or "") + " " + (st.get("name") or "")
            if re.search(r"제목|Heading|개요|Outline|차\s*제|대\s*제", names, re.I):
                heading_style_ids.add(sid)

        for p in paragraphs:
            txt = re.sub(r"\s+", " ", p["text"]).strip()
            if not txt or txt.startswith("["):
                continue
            sid = p["style_id"]
            st = styles.get(sid, {})
            st_name = (st.get("local_name") or st.get("name") or "").strip()
            is_heading = sid in heading_style_ids
            # heuristic: numbered section headings like "1.", "1)", "■", "◆", roman numerals
            if not is_heading:
                if re.match(r"^(\d+[\.)]\s*|[■◆●▶▷▪]\s*|[IVXLC]+\.\s*)", txt) and len(txt) <= 120:
                    is_heading = True
            if is_heading:
                result["headings"].append(
                    {
                        "level": "style" if sid in heading_style_ids else "heuristic",
                        "style_id": sid,
                        "style_name": st_name,
                        "text": txt,
                    }
                )

        # fallback headings if style-based empty: first lines + numbered lines
        if len(result["headings"]) < 3:
            seen = set()
            for p in paragraphs:
                txt = re.sub(r"\s+", " ", p["text"]).strip()
                if not txt or len(txt) > 150:
                    continue
                if re.match(r"^(\d+[\.)]\s*|[■◆●▶▷▪]\s*|[가-힣]\.\s)", txt):
                    if txt not in seen:
                        seen.add(txt)
                        result["headings"].append(
                            {"level": "pattern", "style_id": p["style_id"], "style_name": "", "text": txt}
                        )

    except Exception as e:
        result["errors"].append(f"body: {e}")
        import traceback
        result["traceback"] = traceback.format_exc()

    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in result if k != "traceback"}, ensure_ascii=False, indent=2))
    if result.get("traceback"):
        print(result["traceback"], file=sys.stderr)


if __name__ == "__main__":
    main()
