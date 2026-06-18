# -*- coding: utf-8 -*-
import io
import re
import sys
from pathlib import Path

from hwp5.hwp5txt import TextTransform
from hwp5.xmlmodel import Hwp5File

HWP = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp")
OUT = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\_extracted.txt")

text_transform = TextTransform()
buf = io.StringIO()
with Hwp5File(str(HWP)) as hwp5file:
    text_transform.transform_hwp5_to_text(hwp5file, buf)
text = buf.getvalue()
OUT.write_text(text, encoding="utf-8")
print("chars", len(text))
print("lines", text.count("\n") + 1)
# form feed often marks page breaks in plaintext export
ff = text.count("\f")
print("form_feed_pages", ff + 1 if ff else "none")
print("--- preview ---")
print(text[:2000])
