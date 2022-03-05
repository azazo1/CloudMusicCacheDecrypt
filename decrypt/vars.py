# coding=utf-8
import configparser
import os


class Vars:
    session = "vars"
    default = {"autoOpen": "1",
               "translate": "1",
               "out": "./out/",
               "in": r"./cacheSource/"}
    now = {}


class ReadConfig:
    """读取配置文件"""
    configFile = "./config.ini"

    @classmethod
    def init(cls):
        try:
            cls.create()
            print("正在读取配置...")
            parser = configparser.ConfigParser()
            parser.read(cls.configFile, encoding="utf-8")
            for option in Vars.default.keys():
                Vars.now.update({option: parser.get(Vars.session, option)})
            print("配置加载完毕.")
        except Exception:
            print(f"读取配置文件出现错误，请删除原有的配置文件:{cls.configFile}")

    @classmethod
    def create(cls):
        """若不存在则创建"""
        if not os.path.isfile(cls.configFile):
            print("配置文件缺失，正在创建新默认配置...")
            with open(cls.configFile, "w") as w:
                parser = configparser.ConfigParser()
                parser.add_section(Vars.session)
                for option in Vars.default.keys():
                    parser.set(Vars.session, option, Vars.default[option])
                parser.write(w)
