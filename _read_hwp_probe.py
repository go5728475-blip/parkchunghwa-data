# -*- coding: utf-8 -*-
import olefile
from pathlib import Path

p = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp")
ole = olefile.OleFileIO(str(p))
print("streams:")
for s in ole.listdir():
    print("/".join(s))
ole.close()
