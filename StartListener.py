# coding=utf-8
import os
import re
import sys
from threading import Thread
from typing import Callable

import pyperclip
from mutagen.mp3 import MP3

import decrypt.vars as mVars
from decrypt.decrypt import Decrypt, DecryptedFile, SongDetailGetter


def handleCommand(command: str, doOnQuit: Callable = quit):
    if not command or command.isspace():
        return
    if command == "help" or command == "/?" or command == "?" or command == "h" or command == "-h" or command == "/h":
        print(
            """
            {this} [-I"source_path"] [-O"out_path"] [-(n|y)Open] [-(n|y)T]
            -I"source_path": the decrypt source dir, ->"<- is needed. e.g: {this} -I"C:/"
            -O"out_path": the decrypt output dir, ->"<- is needed. e.g: {this} -O"D:/"
            -(n|y)Open: don't auto open explorer after decrypt finished. e.g: {this} -nOpen
            -(n|y)T: Whether use the translated lyrics instead of original one. e.g: {this} -yT
            """
        )
        doOnQuit()
    elif command == "-noAutoOpen" or command == "-nOpen":
        print("AutoOpen disabled.")
        mVars.autoOpen = False
    elif command == "-autoOpen" or command == "-yOpen":
        print("AutoOpen enabled.")
        mVars.autoOpen = True
    elif command == "-noTranslate" or command == "-nT":
        print("TranslateLyrics disabled.")
        mVars.translate = False
    elif command == "-translate" or command == "-yT":
        print("TranslateLyrics enabled.")
        mVars.translate = True
    elif "-I\"" in command:
        mVars.in_ = os.path.abspath(command.replace("-I", "", 1))
    elif "-O\"" in command:
        mVars.out = os.path.abspath(command.replace("-O", "", 1))
    else:
        print("UnKnow param: " + str(command))
        doOnQuit()


while len(sys.argv) > 1:
    handleCommand(sys.argv.pop(-1))


class Listener:
    def __init__(self):
        self.alive = True
        self.decrypter = Decrypt(source_path=mVars.in_, out_path=mVars.out)
        self.readingThread = Thread(target=self.threadRun, daemon=True)

    def threadRun(self):
        while self.alive:
            _get = input()
            if _get == "open":
                self.openOutPath(True)
            elif _get == "quit":
                self.close()
            elif re.search(r"id:(\d+)", _get):
                song_id = (re.search(r"id:(\d+)", _get).group(1))
                pyperclip.copy(SongDetailGetter.songUrl(song_id))
            else:
                handleCommand(_get, lambda: None)

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
                    os.mkdir(mVars.out)
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
        print("输入\"id:歌曲id\" 回车来解码对应id")
        self.readingThread.start()
        print("Listener启动成功。")
        while self.alive and not stopper():
            try:
                pyperclip.waitForNewPaste(1)
                pasted = pyperclip.paste()
                song_id = DecryptedFile.cutIDFromUrl(pasted)
                if song_id == -1:
                    continue
                print("剪贴板：" + pasted)
                pyperclip.copy("")
                print("\a检测到来自剪贴板的URL_ID事件。")
                print("解析URL中...")
                print(f"得到ID:{song_id}")
                print("开始解码...")
                decryptFile = self.decrypter.decryptID(song_id)
                if decryptFile:
                    decryptFile.path = os.path.abspath(self.decrypter.out_path)
                    print(f"{decryptFile.song.getSongTitle()} - {decryptFile.song.getSongArtist()} 解码成功！\n"
                          f"生成文件 \"{decryptFile.totalPath}\"")
                    self.openOutPath()
                    if not self.checkFile(decryptFile.totalPath):
                        print("目标文件较小，可能为试听文件...请去 https://music.163.com 网站下载正版")
                else:
                    print('解码失败，ID:{} 没有对应缓存文件。'.format(song_id))
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
        if not mVars.autoOpen and not user:
            return
        os.system(f"start explorer.exe \"{os.path.abspath(self.decrypter.out_path)}\"")


if __name__ == '__main__':
    listener = Listener()
    try:
        listener.loop()
    finally:
        listener.close()
