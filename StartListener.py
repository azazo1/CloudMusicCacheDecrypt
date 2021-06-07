# coding=utf-8
import os
import sys
from threading import Thread
from typing import Callable

import pyperclip
from mutagen.mp3 import MP3

from decrypt.decrypt import Decrypt, DecryptedFile

out = "./out/"
in_ = r"D:\CloudMusic\缓存\Cache"

autoOpen = True
while len(sys.argv) > 1:
    get = sys.argv.pop(-1)
    if get == "help" or get == "/?" or get == "?" or get == "h" or get == "-h" or get == "/h":
        print(
            """
            StartListener [-O"out_path"] [-N]
            -I"": the decrypt source dir, ->"<- is needed. e.g: StartListener -I"C:/"
            -O"out_path": the decrypt output dir, ->"<- is needed. e.g: StartListener -O"D:/"
            -N: don't open explorer after decrypt finished.
            """
        )
        quit()
    elif get == "-noAutoOpen" or get == "-N":
        print("AutoOpen closed.")
        autoOpen = False
    elif "-I" in get:
        in_ = get.replace("-I", "", 1)
    elif "-O" in get:
        out = get.replace("-O", "", 1)
    else:
        print("UnKnow param: " + str(get))
        quit()


class Listener:
    def __init__(self):
        self.alive = True
        self.decrypter = Decrypt(source_path=in_, out_path=out)
        self.readingThread = Thread(target=self.threadRun, daemon=True)

    def threadRun(self):
        while self.alive:
            _get = input()
            if _get == "open":
                self.openOutPath(True)
            elif _get == "quit":
                self.close()

    def loop(self, stopper: Callable = lambda: False):
        """
        :param stopper: 应返回一个布尔值，为True时停止
        :return:
        """
        print("输入路径为：" + os.path.abspath(self.decrypter.in_path))
        print("输出路径为：" + os.path.abspath(self.decrypter.out_path))
        for path in (self.decrypter.in_path, self.decrypter.out_path):
            path = os.path.abspath(path)
            if not os.path.exists(path):
                try:
                    print(f"路径 {path} 不为空，正在创建...")
                    os.mkdir(out)
                    print(f"路径 {path} 已创建。")
                except PermissionError:
                    print(f"路径 {path} 权限不足")
                    self.close()
                except FileNotFoundError:
                    print("请输入正确的路径！")
                    self.close()
        if not self.alive:
            return
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
                decryptFile = self.decrypter.decryptID(song_id)
                decryptFile.path = os.path.abspath(self.decrypter.out_path)
                if decryptFile:
                    print(f"{decryptFile.song.getSongTitle()} - {decryptFile.song.getSongArtist()} 解码成功！\n"
                          f"生成文件 \"{decryptFile.totalPath}\"")
                    self.openOutPath()
                    if not self.checkFile(decryptFile.totalPath):
                        print("目标文件较小，可能为试听文件...请去 https://music.163.com 网站下载正版")
                else:
                    print("解码失败！")
            except pyperclip.PyperclipTimeoutException:
                sys.stdin.isatty()
                pass

    @staticmethod
    def checkFile(filepath: str):
        """判断文件是否正常"""
        mp3 = MP3(filepath)
        if mp3.info.length >= 90:
            return True
        return False

    def close(self):
        self.alive = False

    def openOutPath(self, user: bool = False):
        """
        :param user: 是否是用户发起的
        """
        if not autoOpen and not user:
            return
        os.system(f"start explorer.exe \"{os.path.abspath(self.decrypter.out_path)}\"")


if __name__ == '__main__':
    Listener().loop()
