#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import logging
import copy
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np


def check_thr(gps, thr, show):
    poplist = list()
    for k, v in gps["sv"].items():
        if (np.average(v["sn"]) < thr["sn"]) or \
           (show["gsamode"] and np.average(v["el"]) < thr["el"]):
            poplist.append(k)
    for k in poplist:
        gps["sv"].pop(k)
    return gps


def make_timestr(rmc):
    if rmc.datestamp and rmc.timestamp:
        return "{}/{} {}".format(rmc.datestamp.month, rmc.datestamp.day, rmc.timestamp)
    return "----"


def add_gsadata(gsasv, sv, gsa):
    # check SV No.
    for used in gsasv:
        if used not in gsa["sv"]:
            gsa["sv"][used] = copy.deepcopy(gsa["sv"]["dummy"])

    # add gsv data
    if sv["no"] in gsa["sv"]:
        gsa["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
        if sv["el"]:
            gsa["sv"][sv["no"]]["el"].append(int(sv["el"]))
        if sv["az"]:
            gsa["sv"][sv["no"]]["az"].append(int(sv["az"]))

    gsa["sv"]["dummy"]["sn"].append(0)
    gsa["sv"]["dummy"]["el"].append(0)


def add_gsvdata(gps, gsv, gsa):
    if "GSV" in gps:
        for sv in gps["GSV"]["sv"]:
            # check SV No.
            if sv["no"] not in gsv["sv"]:
                gsv["sv"][sv["no"]] = copy.deepcopy(gsv["sv"]["dummy"])

            gsv["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
            if sv["el"]:
                gsv["sv"][sv["no"]]["el"].append(int(sv["el"]))
            if sv["az"]:
                gsv["sv"][sv["no"]]["az"].append(int(sv["az"]))

            if "GSA" in gps:
                add_gsadata(gps["GSA"]["sv"], sv, gsa)

    gsv["sv"]["dummy"]["sn"].append(0)
    gsv["sv"]["dummy"]["el"].append(0)


def create_gpsdata(gpsinput):
    dummy = {"sv": {"dummy": {"sn": [], "el": [], "az": []}}, "time": []}
    gsa = copy.deepcopy(dummy)
    gsv = copy.deepcopy(dummy)

    for gps in gpsinput:
        now = make_timestr(gps["RMC"])
        gsv["time"].append(now)
        if "GSA" in gps:
            gsa["time"].append(now)

        add_gsvdata(gps, gsv, gsa)

    gsa["sv"].pop("dummy")
    gsv["sv"].pop("dummy")

    return gsv, gsa


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gpsinput):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._gsv, self._gsa = create_gpsdata(gpsinput)

    @staticmethod
    def _create_bargraph(gps, thr, ax):
        ax.set_ylim(thr["sn"], 50)
        x = list()
        y = list()
        if len(gps) < 1:
            return
        for k, v in sorted(gps["sv"].items(), key=lambda x: int(x[0])):
            x.append(k)
            y.append(np.average(v["sn"]))
        rects = ax.bar(left=[x for x in range(len(x))], height=y, tick_label=x)

        svnum = len(y)
        avrg = np.average(sorted(y, reverse=True)[:3]) if svnum >= 3 else 0
        print(["{:.2f}".format(top3) for top3 in sorted(y, reverse=True)[:3]])
        ax.set_title("num:{}   top3 avrg.{:.1f}".format(svnum, avrg))
        for rect in rects:
            h = rect.get_height()
            ax.text(rect.get_x()+0.3, h, "{:.1f}".format(h),
                    ha='center', va='bottom')

    @staticmethod
    def _create_polargraph(gps, gsamode, ax):
        sv = list()
        theta = list()
        r = list()

        if gsamode:
            for k, v in gps["sv"].items():
                sv.append(k)
                theta.append(np.radians(np.average(v["az"])))
                r.append(90 - np.average(v["el"]))
        ax.set_rlim(0, 90)
        ax.set_yticklabels([])
        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_thetagrids([i*45 for i in range(8)],
                          ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.plot(theta, r, 'o')

        for s, t, v in zip(sv, theta, r):
            ax.text(t, v, s)

    @staticmethod
    def _create_linegraph(gps, thr, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(thr["sn"], 50)
        if len(gps) < 1:
            return
        for k, v in sorted(gps["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v["sn"], label=k)
        ax.set_xticks([0, len(gps["time"])//2, len(gps["time"])-1])
        ax.set_xticklabels([gps["time"][0], gps["time"][len(gps["time"])//2], gps["time"][-1]],
                           rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)

    def draw(self, thr, show):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")
        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        gsamode = True if show["gsamode"] and len(self._gsa["sv"]) else False
        gps = copy.deepcopy(self._gsa if gsamode else self._gsv)

        gps = check_thr(gps, thr, show)
        row = 2 if show["avrg"] or show["pos"] else 1
        col = 2 if show["avrg"] and show["pos"] else 1
        if show["avrg"]:
            self._create_bargraph(gps, thr, fig.add_subplot(row, col, 1))
        if show["pos"]:
            self._create_polargraph(gps, gsamode, fig.add_subplot(row, col, col, polar=True))
        self._create_linegraph(gps, thr, fig.add_subplot(row, 1, row))
        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
