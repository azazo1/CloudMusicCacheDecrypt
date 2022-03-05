# coding=utf-8
import json
import os
import re
import time
import traceback
import urllib.request as ure
from asyncio import Future
from concurrent.futures.thread import ThreadPoolExecutor
from typing import List, Callable

import eyed3
import eyed3.id3.frames
from bs4 import BeautifulSoup

import decrypt.vars as mVars


class HTML:
    ua = "Mozilla x86"

    def __init__(self, url: str):
        self.htmlContent = self.request(url).decode("utf-8")
        self.bs = BeautifulSoup(self.htmlContent, features="html.parser")

    @classmethod
    def request(cls, url: str) -> bytes:
        req = ure.Request(url, headers={"User-Agent": cls.ua})
        return ure.urlopen(req).read()


class SongDetailGetter:
    @staticmethod
    def songUrl(songID):
        return "http://music.163.com/song?id=" + str(songID)

    @staticmethod
    def albumUrl(albumID):
        return "http://music.163.com/album?id=" + str(albumID)

    @staticmethod
    def lyricsUrl(songID):
        return "http://music.163.com/api/song/lyric?id=" + str(songID) + "&lv=-1&tv=-1"

    def __init__(self, song_id: int):
        self.id = song_id
        self.alive = True
        self.lyrics = None  # type:str
        try:
            self.songHtml = HTML(self.songUrl(self.id))
            self.albumHtml = HTML(self.albumUrl(self.getSongAlbumID()))
        except Exception:
            traceback.print_exc()
            self.songHtml = None
            self.albumHtml = None
            self.alive = False

    def getSongLyrics(self, translation: bool = None) -> str:
        """
        :param translation: 只是一个请求，不一定真的翻译（因为可能没有翻译版本歌词）,默认使用config中的值
        """
        if self.alive:
            if translation is None:
                translation = mVars.Vars.now["translate"] == "1"
            if self.lyrics is not None:
                return self.lyrics
            obj = json.loads(HTML.request(self.lyricsUrl(self.id)))  # type:dict
            prime_keys = list(obj.keys())
            if "nolyric" in prime_keys and obj["nolyric"] is True:  # 没有歌词
                self.lyrics = ""
                return self.lyrics
            if "tlyric" in prime_keys and translation and obj['tlyric']['lyric']:  # 翻译版本
                return obj['tlyric']['lyric']
            if "lrc" in prime_keys:  # 初始版本
                return obj['lrc']['lyric']
        return ""

    def getSongPicUrl(self, size=(1000, 1000)) -> str:
        if self.alive:
            imgs = self.songHtml.bs.find_all("img", attrs={"class": "j-img"})
            if imgs:
                img_noSize = imgs[0]["src"].split('?param=')[0]  # type:str
                img = img_noSize + "?param={}y{}".format(*size)
                return img
        return ""

    def getSongPicData(self) -> bytes:
        if self.alive:
            picUrl = self.getSongPicUrl()
            try:
                return HTML.request(picUrl)
            except Exception:
                traceback.print_exc()
                return b""
        return b""

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
                singerSpan = singerP.find("span")
                if singerSpan:
                    return singerSpan['title']
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
            singerPs = self.songHtml.bs.find_all("p", attrs={'class': "des s-fc4"})
            if singerPs and singerPs[1]:
                singerA = singerPs[1].find("a")
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
        match = re.search(r"\?id=(\d+)", url) or re.search(r'song/(\d+)', url)
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

        title = self.song.getSongTitle() or "UnKnowSong"
        artist = self.song.getSongArtist()

        if artist and not artist.isspace():
            self.fileName = title + " - " + artist.replace('/', "&")
        else:
            self.fileName = title
        self.fileName = re.sub(r'["\\/:?*<>|]', "", self.fileName)
        if out_path is None:
            out_path = self.totalPath
        else:
            out_path += self.fileName + self.extra

        with open(out_path, "wb") as w:
            w.write(bytes(get))
        audio = eyed3.load(out_path)
        audio.initTag()
        audio.tag.artist = artist
        audio.tag.album_artist = self.song.getSongAlbumArtist()
        audio.tag.album = self.song.getSongAlbum()
        audio.tag.title = title
        audio.tag.audio_file_url = self.song.songUrl(self.song.id)
        audio.tag.lyrics.set(self.song.getSongLyrics())
        data = self.song.getSongPicData()
        if data:
            audio.tag.images.set(
                eyed3.id3.frames.ImageFrame.FRONT_COVER,
                data,
                "image/jpeg",
                "The picture of the artist",
            )
        audio.tag.save()

    @property
    def totalPath(self):
        return os.path.join(self.path, self.fileName + self.extra)


class Decrypt:
    @property
    def in_path(self) -> str:
        if self._in_path is None:
            return mVars.Vars.now["in"]
        return self.in_path

    @in_path.setter
    def in_path(self, val: str):
        self._in_path = val

    @property
    def out_path(self) -> str:
        if self._out_path is None:
            return mVars.Vars.now["out"]
        return self.out_path

    @out_path.setter
    def out_path(self, val: str):
        self._out_path = val

    def __init__(self, source_path: str = None, out_path: str = None):
        """
        :param source_path: 用于默认读取文件的目录
        :param out_path: 用于默认输出文件的目录
        """
        # 以下两者都有默认值(property)
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
