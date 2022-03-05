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

try:
    from playsound import playsound as _playsound


    def playsound(*a):
        try:
            _ = sys.stderr
            with open('nul', 'w') as w:
                sys.stderr = w
                rst = _playsound(*a)
            sys.stderr = _
            return rst
        except Exception as e:
            pass
except ModuleNotFoundError:
    playsound = lambda *a: None

mVars.ReadConfig.init()


def handleCommand(command: str, doOnQuit: Callable = sys.exit):
    if not command or command.isspace():
        return
    if command == "help" or command == "/?" or command == "?" or command == "h" or command == "-h" or command == "/h":
        # 中英文两个版本
        print(
            ["""
Command line arguments:
> {this} [-I"source_path"] [-O"out_path"] [-(n|y)Open] [-(n|y)T] [quit]

-I"source_path": Set the decrypted source dir, ->"<- is needed. e.g: {this} -I"C:/"

-O"out_path": Set the decrypt output dir, ->"<- is needed. e.g: {this} -O"D:/"

-(n|y)Open: Don't auto open explorer after decrypt finished. e.g: {this} -nOpen

-(n|y)T: Whether use the translated lyrics instead of original one. e.g: {this} -yT

help: Get help.

Above can be used in this script's input stream.

Interacting command:
open: Open decrypted output directory.
""",
             """
命令行参数:
> {this} [-I"source_path"] [-O"out_path"] [-(n|y)Open] [-(n|y)T] [quit]

-I"source_path": 设置待解码文件所在夹, 即网易云缓存文件夹. ->"<- source_path 两边的英文双引号是必要的. 示例: {this} -I"C:/"

-O"out_path": 解码输出文件夹, 即mp3存放文件夹, ->"<- out_path 两边的英文双引号是必要的. 示例: {this} -O"D:/"

-(n|y)Open: 设置是否在解码完成后打开解码输出文件夹, n为否, y为是. 示例: {this} -nOpen

-(n|y)T: 是否选用翻译过的歌词(若有). 示例: {this} -yT

help: 获取帮助.

以上选项可以同时在脚本运行时使用

交互命令:
open: 打开解码输出文件夹.
"""
             ][1].format(this=__file__)
        )
        doOnQuit()
    elif command == "-noAutoOpen" or command == "-nOpen":
        print("AutoOpen disabled.")
        mVars.Vars.now["autoOpen"] = "0"
    elif command == "-autoOpen" or command == "-yOpen":
        print("AutoOpen enabled.")
        mVars.Vars.now["autoOpen"] = "1"
    elif command == "-noTranslate" or command == "-nT":
        print("TranslateLyrics disabled.")
        mVars.Vars.now["translate"] = "0"
    elif command == "-translate" or command == "-yT":
        print("TranslateLyrics enabled.")
        mVars.Vars.now["translate"] = "1"
    elif "-I\"" in command:
        mVars.Vars.now["in"] = os.path.abspath(command.replace("-I", "", 1).strip('"'))
        print('Source input dir changed: ' + mVars.Vars.now["in"])
    elif "-O\"" in command:
        mVars.Vars.now["out"] = os.path.abspath(command.replace("-O", "", 1).strip('"'))
        print('Output dir changed: ' + mVars.Vars.now["out"])
    else:
        # 部分命令实现在 threadRun
        print("UnKnow param: " + str(command))
        doOnQuit()


while len(sys.argv) > 1:
    handleCommand(sys.argv.pop(-1))


class Listener:
    error_mp3 = "./sound/error.mp3"
    startDecrypt_mp3 = "./sound/startDecrypt.mp3"
    finish_mp3 = "./sound/finish.mp3"

    def __init__(self):
        self.alive = True
        self.decrypter = Decrypt()  # 使用 config 路径(默认)
        self.readingThread = Thread(target=self.threadRun, daemon=True)

    def threadRun(self):
        try:
            while self.alive:
                _get = input()
                if _get == "open":
                    self.openOutPath(True)
                elif _get == "quit":
                    self.close()
                elif re.search(r"id:\s*?(\d+)", _get):
                    song_id = int(re.search(r"id:\s*?(\d+)", _get).group(1))
                    pyperclip.copy(SongDetailGetter.songUrl(song_id))
                elif DecryptedFile.cutIDFromUrl(_get) != -1:
                    pyperclip.copy(SongDetailGetter.songUrl(DecryptedFile.cutIDFromUrl(_get)))
                else:
                    handleCommand(_get, lambda: None)
        except (KeyboardInterrupt, EOFError):
            return

    def loop(self, stopper: Callable = lambda: False):
        """
        :param stopper: 应返回一个布尔值，为True时停止
        :return:
        """
        print("输入路径为：" + os.path.abspath(self.decrypter.in_path))
        print("输出路径为：" + os.path.abspath(self.decrypter.out_path))
        for path in (self.decrypter.in_path, self.decrypter.out_path):
            path = os.path.abspath(path)
            if not os.path.isdir(path):
                try:
                    print(f"路径 {path} 不存在，正在创建...")
                    os.mkdir(path)
                    print(f"路径 {path} 已创建。")
                except PermissionError:
                    print(f"路径 {path} 权限不足")
                    self.close()
                except FileNotFoundError:
                    print("请输入正确的路径！")
                    self.close()
                    playsound(self.error_mp3)
        if not self.alive:
            return
        print("输入 \"open\" 回车来打开out文件夹")
        print("输入 \"quit\" 回车来退出")
        print("输入 \"id:歌曲id\" 回车来解码对应id")
        print("输入 \"help\" 回车来获得更多帮助")
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
                print("检测到来自剪贴板的URL_ID事件。")
                print("解析URL中...")
                self.decrypt(song_id)
            except pyperclip.PyperclipTimeoutException:
                pass

    def decrypt(self, song_id):
        print(f"得到ID:{song_id}")
        print("开始解码...")
        playsound(self.startDecrypt_mp3)
        decryptFile = self.decrypter.decryptID(song_id)
        if decryptFile:
            decryptFile.path = os.path.abspath(self.decrypter.out_path)
            print(f"{decryptFile.song.getSongTitle()} - {decryptFile.song.getSongArtist()} 解码成功！\n"
                  f"生成文件 \"{decryptFile.totalPath}\"")
            playsound(self.finish_mp3)
            self.openOutPath()
            if not self.checkFile(decryptFile.totalPath):
                print("目标文件较小，可能为试听文件...请去 https://music.163.com 网站下载正版")
        else:
            print('解码失败，ID:{} 没有对应缓存文件。'.format(song_id))
            playsound(self.error_mp3)

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
        if not mVars.Vars.now["autoOpen"] == "1" and not user:
            return
        os.system(f"start explorer.exe \"{os.path.abspath(self.decrypter.out_path)}\"")


if __name__ == '__main__':
    listener = Listener()
    try:
        listener.loop()
    finally:
        listener.close()
        input(">回车退出>")
