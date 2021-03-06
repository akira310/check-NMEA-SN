#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import copy
import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pdb


def add_timediff(dt, tdiff):
    return datetime.datetime.fromtimestamp(int(time.mktime(dt.timetuple())) + tdiff)


def check_thr(gps, thr, show, timewidth, tdiff):
    poplist = list()
    for k, v in gps["sv"].items():
        if (np.average(v["sn"]) < thr["sn"]) or \
           (show["gsamode"] and np.average(v["el"]) < thr["el"]):
            poplist.append(k)
    for k in poplist:
        gps["sv"].pop(k)

    print(timewidth)
    if timewidth[0]:    # start time
        start = add_timediff(timewidth[0], -1*tdiff)
        for i, t in enumerate(gps["time"]):
            try:
                dt = datetime.datetime.combine(t[0], t[1])
                if start <= dt:
                    gps["time"] = gps["time"][i:]
                    for v in gps["sv"].values():
                        for k in ["sn", "el", "az"]:
                            v[k] = v[k][i:]
                    break
            except TypeError:
                pass

    if timewidth[1]:    # end time
        end = add_timediff(timewidth[1], -1*tdiff)
        for i, t in enumerate(reversed(gps["time"])):
            dt = datetime.datetime.combine(t[0], t[1])
            if end >= dt:
                end = len(gps["time"])-i
                gps["time"] = gps["time"][:end]
                for v in gps["sv"].values():
                    for k in ["sn", "el", "az"]:
                        v[k] = v[k][:end]
                break

    return gps


def make_timestr(t, tdiff):
    if t:
        t_mod = add_timediff(datetime.datetime.combine(t[0], t[1]), tdiff)
        return "{}/{} {}".format(t_mod.date().month, t_mod.date().day, t_mod.time())
    return "----"


def add_gsadata(gsasv, sv, gsa):
    # check SV No.
    for used in gsasv:
        if used not in gsa["sv"]:
            gsa["sv"][used] = copy.deepcopy(gsa["sv"]["dummy"])

    # add gsv data
    if sv["no"] in gsa["sv"]:
        gsa["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
        gsa["sv"][sv["no"]]["el"].append(int(sv["el"] if sv["el"] else -1))
        gsa["sv"][sv["no"]]["az"].append(int(sv["az"] if sv["az"] else -1))


def add_gsvdata(gps, gsv, gsa):
    if "GSV" in gps:
        for sv in gps["GSV"]["sv"]:
            # check SV No.
            if sv["no"] not in gsv["sv"]:
                gsv["sv"][sv["no"]] = copy.deepcopy(gsv["sv"]["dummy"])

            gsv["sv"][sv["no"]]["sn"].append(int(sv["sn"] if sv["sn"] else 0))
            gsv["sv"][sv["no"]]["el"].append(int(sv["el"] if sv["el"] else -1))
            gsv["sv"][sv["no"]]["az"].append(int(sv["az"] if sv["az"] else -1))

            if "GSA" in gps:
                add_gsadata(gps["GSA"]["sv"], sv, gsa)

    gsv["sv"]["dummy"]["sn"].append(0)
    gsv["sv"]["dummy"]["el"].append(0)
    if "GSA" in gps:
        gsa["sv"]["dummy"]["sn"].append(0)
        gsa["sv"]["dummy"]["el"].append(0)


def create_gpsdata(gpsinput):
    base = {"sv": {"dummy": {"sn": [], "el": [], "az": []}}, "time": [], "hdop": []}
    gsa = copy.deepcopy(base)
    gsv = copy.deepcopy(base)

    for gps in gpsinput:
        rmc = gps["RMC"]
        now = (rmc.datestamp, rmc.timestamp) if rmc.datestamp and rmc.timestamp else None
        gsv["time"].append(now)
        gsv["hdop"].append(float(gps["GGA"]["hdop"]) if "GGA" in gps else 99)
        if "GSA" in gps:
            gsa["time"].append(now)
            gsa["hdop"].append(float(gps["GGA"]["hdop"]) if "GGA" in gps else 99)

        add_gsvdata(gps, gsv, gsa)

    gsa["sv"].pop("dummy")
    gsv["sv"].pop("dummy")

    return gsv, gsa


class NMEAGraph(object):
    u""" NMEAパース結果描画クラス

    パースされたデータを元にグラフを描画する
    """

    def __init__(self, tid, gpsinput, tz):
        self._log = logging.getLogger(__name__)
        self._tid = tid
        self._tz = tz
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

        for k, v_tmp in gps["sv"].items():
            v = {"az":[], "el":[]}
            for i in range(len(v_tmp["az"])):
                if v_tmp["az"][i] > 0:
                    v["az"].append(v_tmp["az"][i])
                if v_tmp["el"][i] > 0:
                    v["el"].append(v_tmp["el"][i])

            if len(v["az"]) > 0 and np.min(v["az"]) > 0 and \
               len(v["el"]) > 0 and np.min(v["el"]) > 0:
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

    def _create_linegraph(self, gps, thr, tdiff, ax):
        ax.set_title("fixed SN")
        ax.set_ylabel("CN")
        ax.set_ylim(thr["sn"], 50)

        if len(gps) < 1 or len(gps["time"]) < 3:
            return

        for k, v in sorted(gps["sv"].items(), key=lambda x: int(x[0])):
            ax.plot(v["sn"], label=k)

        timespan = self._get_linegraph_timesplit(gps["time"])
        ax.set_xticks(timespan)
        ax.set_xticklabels(map(lambda i: make_timestr(gps["time"][i], tdiff), timespan),
                           rotation=15, fontsize="small")
        ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)

    def _create_hdop(self, gps, thr, tdiff, ax):
        ax.set_title("dop")
        ax.set_ylabel("hdop")
        ax.set_ylim(0, 15)

        if len(gps) < 1 or len(gps["time"]) < 3:
            return

        ax.plot(gps["hdop"], label="hdop")
        timespan = self._get_linegraph_timesplit(gps["time"])
        ax.set_xticks(timespan)
        ax.set_xticklabels(map(lambda i: make_timestr(gps["time"][i], tdiff), timespan),
                           rotation=15, fontsize="small")
        # ax.legend(bbox_to_anchor=(1, 1), loc=2, frameon=True)

    @staticmethod
    def _get_linegraph_timesplit(time):
        l = [0]
        timelen = len(time)
        splt = 5 if timelen > 5 else timelen-1
        l = [i for i in range(0, timelen-1, (timelen-1)//splt)]
        # 分割した最後の値が終端に近すぎるとグラフ描画時に文字が重なるため削除
        if (timelen-1)-l[-1] < (l[1]-l[0])/3:
            l.pop(-1)

        return l + [timelen-1]

    def draw(self, thr, show, timewidth):
        u""" グラフ描画 """

        # sns.set(palette='colorblind')
        sns.set_style("white")
        fig = plt.figure()
        fig.suptitle("tid [{}]".format(self._tid))
        gsamode = True if show["gsamode"] and len(self._gsa["sv"]) else False
        gps = copy.deepcopy(self._gsa if gsamode else self._gsv)

        gps = check_thr(gps, thr, show, timewidth, self._tz)

        # First row setting
        rownum = 2 if show["sn"] or show["hdop"] else 1
        clmnum = 2 if show["pos"] else 1
        if show["pos"]:
            self._create_polargraph(gps, gsamode, fig.add_subplot(rownum, 2, 2, polar=True))
        self._create_bargraph(gps, thr, fig.add_subplot(rownum, clmnum, 1))

        # second row setting
        if rownum == 2:
            clmnum = 2 if show["sn"] and show["hdop"] else 1
            if show["hdop"]:
                self._create_hdop(gps, thr, self._tz, fig.add_subplot(rownum, clmnum, 3 if clmnum == 2 else 2))
            if show["sn"]:
                self._create_linegraph(gps, thr, self._tz, fig.add_subplot(rownum, clmnum,  4 if clmnum == 2 else 2))

        plt.show()


if __name__ == '__main__':
    print("WARN: this file is not entry point !!", file=sys.stderr)
