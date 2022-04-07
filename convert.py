#!/usr/bin/python
# -*- coding: UTF-8 -*-

from cmath import log
from ctypes.wintypes import PINT
from distutils.log import Log
from http.client import responses
import sys
import ruamel.yaml
import urllib.request
import re


def getScript(string):
    Script = {}
    list = re.search(r"(?<=\[(Script)\]\s)([^\[])*",
                     string, flags=re.MULTILINE)
    if list != None:
        list = (list.group().split("\n"))
        for i in list:
            if i != "":
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

def getRewrite(string):
    rewrite = []
    list = re.search(r"(?<=\[(URL Rewrite)\]\s)([^\[])*",
                     string, flags=re.MULTILINE)
    if list != None:
        for l in list.group().split("\n"):
            if l != "": rewrite.append(l.replace('"', ''))
    return rewrite


def getMITM(string):
    mitm = []
    list = re.search(r"(?<=\[(MITM)\]\s).*$", string, flags=re.MULTILINE)
    if list != None:
        l = list.group()
        l = l.replace(' ', '')
        l = re.search(r"(?<=%INSERT%|%APPEND%).*", l)
        if l != None:
            l = l.group().split(',')
        for v in l:
            mitm.append(v)
    return mitm


def generate_yaml_doc(filename, r):
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
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(py_object, file)
    file.close()


urls = {
    "./General.stoverride": "https://raw.githubusercontent.com/DivineEngine/Profiles/master/Surge/Module/General.sgmodule",
    "./ad.stoverride": "https://raw.githubusercontent.com/app2smile/rules/master/module/ad.sgmodule",
    "./AdvertisingScript.stoverride": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rewrite/Surge/AdvertisingScript/AdvertisingScript.sgmodule"
}
for (key, u) in urls.items():
    response = urllib.request.urlopen(u)
    if response.getcode() != 200:
        print('获取错误')
    else:
        r = response.read().decode('utf-8')
        generate_yaml_doc(key, r)
