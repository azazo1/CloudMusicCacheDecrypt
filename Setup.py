# coding=utf-8
import os
import sys
from os.path import join

needs = ["pip", "lxml"]
failed = []
while needs:
    for package in needs:
        pip = join(join(sys.exec_prefix, "Scripts"), "pip.exe")
        if os.system(f"\"{sys.executable}\" -m pip install {package} --upgrade -i https://pypi.douban.com/simple"):
            failed.append(package)
    needs = failed.copy()
input("Setup-OK!")
