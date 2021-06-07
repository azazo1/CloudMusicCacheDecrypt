# coding=utf-8
import os
import sys
from threading import Thread
from typing import Callable

import pyperclip

from decrypt.decrypt import Decrypt, DecryptedFile

out = "./out/"
if len(sys.argv) > 1:
    if sys.argv[1] == "help" or sys.argv[1] == "/?" or sys.argv[1] == "?":
        print(
            """
            StartListener [out_path]
            """
        )
        quit()
    else:
        out = sys.argv[1]


class Listener:
    def __init__(self):
        self.alive = True
        self.decrypter = Decrypt(source_path=r"D:\CloudMusic\缓存\Cache", out_path=out)
        self.readingThread = Thread(target=self.threadRun, daemon=True)

    def threadRun(self):
        while self.alive:
            get = input()
            if get == "open":
                self.openOutPath()
            elif get == "quit":
                self.close()

    def loop(self, stopper: Callable = lambda: False):
        """
        :param stopper: 应返回一个布尔值，为True时停止
        :return:
        """
        print("输出路径为：" + os.path.abspath(self.decrypter.out_path))
        try:
            os.mkdir(out)
            print("输出路径不为空，正在创建...\n输出路径已创建。")
        except FileExistsError:
            pass
        print("输入\"open\" 回车来打开out文件夹")
        print("输入\"quit\" 回车来退出")
        self.readingThread.start()
        print("Listener启动成功。")
        while self.alive and not stopper():
            try:
                pyperclip.waitForNewPaste(1)
                song_id = DecryptedFile.cutIDFromUrl(pyperclip.paste())
                if song_id == -1:
                    continue
                pyperclip.copy("")
                print("检测到来自剪贴板的URL_ID事件。")
                print("解析URL中...")
                print(f"得到ID:{song_id}")
                print("开始解码...")
                get = self.decrypter.decryptID(song_id)
                if get:
                    print("解码成功！")
                    self.openOutPath()
                    get.path = self.decrypter.out_path
                    if os.path.getsize(get.totalPath) < 1024 * 1024:
                        print("目标文件较小，可能为试听文件...请去 https://music.163.com 网站下载正版")
                else:
                    print("解码失败！")
            except pyperclip.PyperclipTimeoutException:
                sys.stdin.isatty()
                pass

    def close(self):
        self.alive = False

    def openOutPath(self):
        os.system(f"start explorer.exe \"{os.path.abspath(self.decrypter.out_path)}\"")


if __name__ == '__main__':
    Listener().loop()
