# coding=utf-8
import os
import sys
from os.path import join

package_needs = ["pip", "lxml", "beautifulsoup4", "eyed3", "fake_useragent", "mutagen"]
while package_needs:
    package = package_needs.pop(0)
    pip = join(join(sys.exec_prefix, "Scripts"), "pip.exe")
    if os.system(f"\"{sys.executable}\" -m pip install {package} --upgrade -i https://pypi.douban.com/simple"):
        package_needs.append(package)

#
# class Reporter:
#     def __init__(self):
#         self.lastReport = (0, 0)  # size, time
#
#     def __call__(self, *args, **kwargs):
#         a, b, t = args
#         nowTime = time.time()
#         if a % 20 == 0:
#             length = 10
#             first = "■" * int(a * b / t * length)
#             second = "□" * (length - len(first))
#             # MB/s
#             speed = ((a * b) - self.lastReport[0]) / (nowTime - self.lastReport[1]) / 1024 / 1024
#             print(f'\r|{first}{second}| '
#                   f'{a * b / t:.2%} '
#                   f'{speed:.2f} MB/s',
#                   end="")
#             self.lastReport = (a * b, nowTime)


# file_needs = [('ffmpeg.7z', 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z')]
# while file_needs:
#     file = file_needs.pop(0)
#     try:
#         print('Downloading: ' + file[0])
#         ure.urlretrieve(file[1], file[0], reporthook=Reporter())
#         print("Download" + file[0] + " Over.")
#     except Exception:
#         file_needs.append(file)


input("Setup-OK!")
