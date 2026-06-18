# -*- coding: utf-8 -*-
import win32com.client
from pathlib import Path

HWP = Path(
    r"C:\Users\Lenovo\Desktop\박청화_분자료\박청화 애정운 결혼운 + 처자인연법 (일부 채워쓸 것, 복사해 넣을 것).hwp"
)

hwp = win32com.client.Dispatch("HWPFrame.HwpObject")
hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
hwp.Open(str(HWP), "HWP", "forceopen:true")
doc = hwp.XHwpDocuments.Item(0)
print("PageCount", doc.XHwpDocumentInfo.PageCount)
hwp.Quit()
