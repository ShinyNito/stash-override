#!/usr/bin/python
# -*- coding: UTF-8 -*-

from http.client import responses
import sys
import ruamel.yaml
import urllib.request
import re


def checkSection(string):
    return re.search(r"^\[.*\]$", string) != None

def getScript(string):
    Script = {}
    list = re.search(r"(?<=\[(Script)\]\s)(.|\s)*",
                     string, flags=re.MULTILINE)
    if list != None:
        list = (list.group().split("\n"))
        for i in list:
            if i != "":
                if checkSection(i):
                    break
                i = i.replace(" ", "")
                name = re.search(
                    r"^.+?(?==)", i.replace(" ", ""), flags=re.MULTILINE)
                if name != None:
                    name = name.group()
                    Script[name] = {}
                    l = re.search(r"(?<==).+", i)
                    if i != None:
                        l = l.group().split(",")
                        for v in l:
                            value = re.search(r"(?<==).*", v)
                            key = re.search(r"^.+?(?==)", v)
                            if (value != None) & (key != None):
                                Script[name][key.group()] = value.group()
        return Script


def getGeneral(string):
    general = {"fake-ip-filter": []}
    list = re.search(r"(?<=\[(General)\]\s)([^\[])*", string, flags=re.MULTILINE)
    if list != None:
            rel = re.search(r"^always-real-ip.*", list.group(), flags=re.MULTILINE)
            if rel != None:
                r = re.search(r"(?<=(%INSERT%|%APPEND%)).*", rel.group())
                if r != None:
                    for i in r.group().split(","):
                        general["fake-ip-filter"].append(i)
            # if rel != None:

    else:
        return []
    return general


def getName(string):
    list = re.search(r"(?<=^#!name=).*\n", string, flags=re.MULTILINE)
    if list != None:
        return list.group()
    return ""

def getDesc(string):
    list = re.search(r"(?<=^#!desc=).*\n", string, flags=re.MULTILINE)
    if list != None:
        return list.group()
    return ""

def getRewrite(string):
    rewrite = []
    list = re.search(r"(?<=\[(URL Rewrite)\]\s)(.|\s)*",
                     string, flags=re.MULTILINE)
    if list != None:
        for l in list.group().split("\n"):
            if checkSection(l):
                break
            if (l != "") & (re.search(r"^#.*", l) == None):
                if re.search(r'\s.*\$\d', l) != None:
                    l =re.sub(r"\sheader$", " 302", l)
                rewrite.append(l.replace('"', ''))
    return rewrite


def getMITM(string):
    mitm = []
    list = re.search(r"(?<=\[(MITM)\]\s)(.|\s)*", string, flags=re.MULTILINE)
    if list != None:
        l = list.group()
        l = l.replace(' ', '')
        l1 = re.search(r"(?<=%INSERT%|%APPEND%).*", l)
        if l1 != None:
            l = l1.group().split(',')
        else: 
            l = re.search(r"(?<==).*", l)
            if l != None:
                l = l.group().split(',')
        for v in l:
            mitm.append(v)
    return mitm


def generate_yaml_doc(filename, r, source):
    name = getName(r)
    desc = getDesc(r)
    mtim = getMITM(r)
    general = getGeneral(r)
    if mtim == []:
        print('mitm为空')
        exit()
    Script = getScript(r)
    rewrite = getRewrite(r)
    newScript = []
    typeTable = {
        "http-response": "response",
        "http-request": "request"
    }
    scriptProviders = {}
    if Script != None:
        for (key, value) in Script.items():
            if value != {}:
                newScript.append({
                    "match": value["pattern"],
                    "name": key,
                    "type": typeTable[value['type']],
                    "require-body": int(value["requires-body"]) == 1,
                    "timeout": 120
                })
                scriptProviders[key] = {
                    "url": value["script-path"], "interval": 86400}
    py_object = {'http': {'mitm': mtim}}
    if newScript != []:
        py_object["http"]["script"] = newScript
        py_object["script-providers"] = scriptProviders
    if rewrite != []:
        py_object["http"]['rewrite'] = rewrite
    if general:
        if general['fake-ip-filter']:
            if (py_object.__contains__("dns")) != True:
                py_object["dns"] = {
                    "fake-ip-filter": []
                }
            py_object["dns"]['fake-ip-filter'] = general["fake-ip-filter"]
    file = open(filename, 'w', encoding='utf-8')
    file.write("# modify from " + source)
    if name != "":
        file.write("name: " + name)
    if desc != "":
        file.write("desc: " + desc + "\n")
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(py_object, file)
    file.close()


urls = {
    # "weibo-ad": "https://raw.githubusercontent.com/zmqcherish/proxy-script/main/weibo.sgmodule", 不可用
    "jd_price2": "https://raw.githubusercontent.com/githubdulong/Script/master/jd_price2.sgmodule",
    "xiaohongshu.ad": "https://raw.githubusercontent.com/chouchoui/QuanX/master/Scripts/xiaohongshu/xiaohongshu.ad.sgmodule",
    "weibo": "https://raw.githubusercontent.com/ShinyNito/Rule-Snippet/main/weibo.sgmodule",
    "General": "https://raw.githubusercontent.com/DivineEngine/Profiles/master/Surge/Module/General.sgmodule",
    "ad": "https://raw.githubusercontent.com/app2smile/rules/master/module/ad.sgmodule",
    "AdvertisingScript": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Surge/AdvertisingScript/AdvertisingScript.sgmodule",
    "bilibili_plus": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/script/bilibili/bilibili_plus.sgmodule",
    "bilibili-test": "https://raw.githubusercontent.com/app2smile/rules/master/module/bilibili-test.sgmodule",
    "TestFlightDownload": "https://raw.githubusercontent.com/NobyDa/Script/master/Surge/Module/TestFlightDownload.sgmodule",
    "AdvertisingLite_Classical": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Surge/AdvertisingLite/AdvertisingLite_Classical.sgmodule"
}
for (key, u) in urls.items():
    response = urllib.request.urlopen(u)
    if response.getcode() != 200:
        print('获取错误')
    else:
        r = response.read().decode('utf-8')
        generate_yaml_doc( "./" +key + ".stoverride", r, u)
        print("https://raw.githubusercontent.com/ShinyNito/stash-override/main/" + key + ".stoverride" + "\n")
