#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import os
import matplotlib.pyplot as plt
import seaborn as sns


class NMEAData(object):
    u""" NMEAデータ確認用クラス

    指定ｳれたNORMALディレクトリ内のNMEAデータからSN等を算出する
    """

    def __init__(self):
        pass

    def concat_trip(self, path):
        u""" 各ファイルをtrip idごとにまとめる

        Args:
            path: sd root path

        Returns:
            dict_trip: tripIDごとにファイルをまとめたdict
                 * key1: tripID, value(list): 対応tripIDのファイルフルパス
        """

        path += "\\SYSTEM\\NMEA\\NORMAL\\"
        files = os.listdir(path)
        files.sort()
        dict_trip = {}

        for file in files:
            file = path + file
            with open(file, "r") as f:
                key = f.readline().split(",")[-1]
                if key not in dict_trip:
                    dict_trip[key] = list()
                dict_trip[key].append(file)

        return dict_trip

    def check(self, dict_trip):
        u""" tripIDごとのTTFF,SN等を調べる

        Args:
            dict_trip: self.concat_trip()で得れるdict

        Returns:
            trip: tripIDごとのチェック結果dict
                 * key1: tripID, value(list): 対応tripIDのチェック結果dict
                    * key1: "ttff"
                    * key2: "ttffnmea"
                    * key3: "sn", value(list): SNリスト
                        * key1:"time"
                        * key2:"num"
                        * key3:"sn"
        """

        data = dict()
        trip = dict()

        for k, v in dict_trip.items():
            data[k] = self.__get_lines(v)

        for k, v in data.items():
            pack = list()
            p = list()
            r = re.compile("^\$GPRMC")
            for d in v:
                if r.search(d) and len(p) > 0:
                    pack.append(p[:])
                    p.clear()
                p.append(d)
            trip[k] = self.__check_trip(pack)
        return (trip)

    def __check_trip(self, pack):
        trip = {"ttff": "", "ttffnmea": "", "sn": []}

        for i, p in enumerate(pack):
            stnum = list()
            snlist = list()
            sn_dict = dict((x, list()) for x in ["time", "num", "sn"])

            for s in p:
                sentence = s.replace("*", ",").split(",")

                if sentence[0] == "$GPRMC":
                    stnum.clear()
                    if sentence[2] == 'A' and sentence[3]:
                        sn_dict["time"] = sentence[1] + "-" + sentence[9]
                        if not trip["ttff"]:
                            trip["ttff"] = str(int(i/2))
                            trip["ttffnmea"] = sn_dict["time"]
                elif trip["ttff"] and sentence[0] == "$GPGSA":
                    if sentence[2] != 1:
                        stnum = sentence[3:3+12]
                    while "" in stnum:
                        del stnum[stnum.index("")]
                elif trip["ttff"] and len(stnum) and sentence[0] == "$GPGSV":
                    pos = 4
                    while(pos < len(sentence)):
                        if sentence[pos] in stnum:
                            snlist.append(sentence[pos+3])
                        pos += 4

            if snlist:
                sn_dict["num"] = len(stnum)
                sn_dict["sn"] = self.__average_sn(snlist)
                trip["sn"].append(sn_dict)
        return trip

    def __average_sn(self, snlist):
        sn = ""
        try:
            sn = str(sum(list(map(int, snlist))) / len(snlist))
        except Exception as e:
            os.sys.stderr(e)

        return sn

    def __get_lines(self, files):
        lines = list()
        r = re.compile("^\$GP")
        for file in files:
            with open(file, "r") as f:
                for l in f:
                    if r.search(l):
                        lines.append(l)
        return lines

if __name__ == '__main__':
    pass