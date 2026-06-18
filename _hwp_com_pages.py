# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

import win32com.client

HWP = Path(r"C:\Users\Lenovo\Desktop\박청화_분자료\직업론 (박청화 직업 + 탈도사 직업) 20250110 기묘일.hwp")

hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.Open(str(HWP), "HWP", "forceopen:true")

doc = hwp.XHwpDocuments.Item(0)
info = doc.XHwpDocumentInfo
print("PageCount", info.PageCount)
print("ParaCount", info.ParaCount)
print("SectionCount", info.SectionCount)
print("Title", info.Title)
print("Subject", info.Subject)

hwp.Quit()
