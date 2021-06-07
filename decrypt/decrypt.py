# coding=utf-8
import os
import re
import time
import urllib.request as ure
from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Callable

from bs4 import BeautifulSoup

import meyed3
import meyed3.id3.frames
from mfake_useragent import UserAgent


class HTML:
    ua = UserAgent()

    def __init__(self, url: str):
        self.htmlContent = self._request(url)
        self.bs = BeautifulSoup(self.htmlContent, features="lxml")

    def _request(self, url: str):
        req = ure.Request(url, headers={"User-Agent": self.ua.random})
        return ure.urlopen(req).read().decode("utf-8")


class SongDetailGetter:
    @staticmethod
    def songUrl(songID):
        return "http://music.163.com/song?id=" + str(songID)

    @staticmethod
    def albumUrl(albumID):
        return "http://music.163.com/album?id=" + str(albumID)

    def __init__(self, song_id: int):
        self.id = song_id
        self.alive = True
        try:
            self.songHtml = HTML(self.songUrl(self.id))
            self.albumHtml = HTML(self.albumUrl(self.getSongAlbumID()))
        except Exception:
            self.songHtml = None
            self.albumHtml = None
            self.alive = False

    def getSongPicUrl(self) -> str:
        if self.alive:
            imgs = self.songHtml.bs.find_all("img", attrs={"class": "j-img"})
            if imgs:
                return imgs[0]["data-src"]
        return ""

    def getSongTitle(self) -> str:
        if self.alive:
            titDir = self.songHtml.bs.find("div", attrs={"class": "tit"})
            if titDir:
                titEm = titDir.find("em")
                if titEm:
                    return titEm.text
        return ""

    def getSongArtist(self) -> str:
        if self.alive:
            singerP = self.songHtml.bs.find_all("p", attrs={'class': "des s-fc4"})[0]
            if singerP:
                singerA = singerP.find("a")
                if singerA:
                    return singerA.text
        return ""

    def getSongAlbum(self) -> str:
        if self.alive:
            singerP = self.songHtml.bs.find_all("p", attrs={'class': "des s-fc4"})[1]
            if singerP:
                singerA = singerP.find("a")
                if singerA:
                    return singerA.text
        return ""

    def getSongAlbumID(self) -> int:
        if self.alive:
            singerP = self.songHtml.bs.find_all("p", attrs={'class': "des s-fc4"})[1]
            if singerP:
                singerA = singerP.find("a")
                if singerA:
                    return int(singerA["href"].split('?id=')[-1])
        return 0

    def getSongAlbumArtist(self) -> str:
        if self.alive:
            singerA = self.albumHtml.bs.find("a", attrs={"class": 's-fc7'})
            if singerA:
                return singerA.text
        return ""


class AutoShutdownThreadPool(ThreadPoolExecutor):
    def __init__(self, number: int):
        super().__init__(number)
        self.futures = []  # type:List[Future]

    def submit(self, __fn: Callable, *args, **kwargs):
        self.futures.append(super(AutoShutdownThreadPool, self).submit(__fn, *args, **kwargs))

    def __del__(self):
        for i in self.futures:
            i.cancel()
        self.shutdown()


class DecryptedFile:
    UnDecryptedExtra = ".uc"
    DecryptedExtra = ".mp3"
    threadingPool = AutoShutdownThreadPool(10)

    @staticmethod
    def cutIDFromUrl(url: str) -> int:
        match = re.search(r"id=(\d+)", url)
        if match:
            return int(match.group(1))
        return -1

    @staticmethod
    def cutIDFromCacheName(fileName: str) -> int:
        """
        从文件名中取出歌曲id
        :param fileName: 只能是纯文件名字，没后缀，没路径
        :return:
        """
        return int(fileName.split("-")[0])

    def __str__(self):
        return super(DecryptedFile, self).__str__() + f"{{{self.song.getSongTitle()} - {self.song.getSongArtist()}}}"

    def __init__(self, filePath: str, parseInThread=False):
        """
        :param filePath: 要解码的目标文件
        :param parseInThread: 在线程中初始解析
        """
        self.path, self.fileName = os.path.split(filePath)
        self.fileName, self.extra = os.path.splitext(self.fileName)
        # noinspection PyTypeChecker
        self.song = None  # type: SongDetailGetter
        if parseInThread:
            self.threadingPool.submit(self.initSongDetail)
        else:
            self.initSongDetail()

    def initSongDetail(self):
        self.song = SongDetailGetter(self.cutIDFromCacheName(self.fileName))

    def waitSong(self):
        """
        等待线程中self.song的初始化完毕
        :return:
        """
        while True:
            try:
                time.sleep(1 / 60)
                # noinspection PyStatementEffect
                self.song.alive
                break
            except AttributeError:
                pass

    @property
    def decrypted(self):
        return self.extra == self.DecryptedExtra

    def decrypt(self, out_path: str = None):
        """
        解码缓存，结果默认放在缓存文件的位置
        :param out_path: 不用规定文件名
        :return:
        """
        with open(self.totalPath, 'rb') as r:
            get = r.read()
            get = list(get)
            for i in range(len(get)):
                get[i] ^= 0xa3

        self.extra = self.DecryptedExtra

        if self.song.getSongArtist():
            self.fileName = (self.song.getSongTitle() or "UnKnowSong") + " - " + self.song.getSongArtist()
        else:
            self.fileName = self.song.getSongTitle() or "UnKnowSong"

        if out_path is None:
            out_path = self.totalPath
        else:
            out_path += self.fileName + self.extra

        with open(out_path, "wb") as w:
            w.write(bytes(get))
        audio = meyed3.load(out_path)
        audio.initTag()
        audio.tag.artist = self.song.getSongArtist()
        audio.tag.album_artist = self.song.getSongAlbumArtist()
        audio.tag.album = self.song.getSongAlbum()
        audio.tag.title = self.song.getSongTitle()
        url = self.song.getSongPicUrl()
        if url:
            audio.tag.images.set(
                meyed3.id3.frames.ImageFrame.OTHER_ICON,
                None,
                None,
                "The picture of the artist",
                img_url=url
            )
        audio.tag.save()

    @property
    def totalPath(self):
        return os.path.join(self.path, self.fileName + self.extra)


class Decrypt:
    def __init__(self, source_path: str, out_path: str = None):
        """
        :param source_path: 用于默认读取文件的目录
        :param out_path: 用于默认输出文件的目录
        """
        self.in_path = source_path
        self.out_path = out_path

    def scanPath(self, path: str = None, _filter: Callable = lambda fileName: True) \
            -> List[DecryptedFile]:
        """
        找到目标目录下所有的缓存文件及其信息
        如果不想创建实例，self项可填None但此时path必须不为空.
        """

        if not path and self:
            path = self.in_path
        result = []
        for file in os.listdir(path):
            if ".uc" in file and _filter(file):
                result.append(DecryptedFile(os.path.join(path, file), True))
        return result

    def decryptID(self, song_id: int, path: str = None):
        """
        从一个目录解码对应ID的缓存

        如果不想创建实例，self项可填None但此时path必须不为空.
        """

        if not path and self:
            path = self.in_path
        for file in os.listdir(path):
            if ".uc" in file and DecryptedFile.cutIDFromCacheName(file) == song_id:
                dFile = DecryptedFile(os.path.join(path, file))
                self.decryptFile(dFile)
                return dFile
        return None

    def decryptFile(self, targetFile: DecryptedFile):
        targetFile.decrypt(self.out_path)

    def decryptFiles(self, targetFiles: List[DecryptedFile]):
        for file in targetFiles:
            self.decryptFile(file)
