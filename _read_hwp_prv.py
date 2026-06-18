# -*- coding: utf-8 -*-
import olefile
from pathlib import Path

p = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp")
ole = olefile.OleFileIO(str(p))
for name in [("PrvText",), ("DocInfo",), ("FileHeader",)]:
    if ole.exists(name):
        data = ole.openstream(name).read()
        print(f"=== {'/'.join(name)} size={len(data)} ===")
        # PrvText is often UTF-16LE
        if name[0] == "PrvText":
            for enc in ("utf-16-le", "utf-8", "cp949"):
                try:
                    txt = data.decode(enc, errors="ignore")
                    if txt.strip():
                        print(txt[:5000])
                        break
                except Exception:
                    pass
ole.close()
