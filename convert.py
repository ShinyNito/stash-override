#!/usr/bin/python
# -*- coding: UTF-8 -*-

from http.client import responses
import sys
import ruamel.yaml
import urllib.request
import re

def getScript(string):
    Script = {}
    list = re.search(r"(?<=\[(Script)\])(.|\s)*", string, flags=re.MULTILINE)
    if list != None:
        list = (list.group().split("\n"))
        for i in list:
            if i != "":
                i = i.replace(" ", "")
                name = re.search(r"^.+?(?==)", i.replace(" ", ""),flags=re.MULTILINE)
                if name != None:
                    name = name.group()
                    Script[name] = {}
                    l = re.search(r"(?<==).+", i)
                    if i != None:
                        l = l.group().split(",")
                        for v in l:
                            value = re.search(r"(?<==).*", v)
                            key = re.search(r".*(?==)", v)
                            if (value != None) & (key != None): Script[name][key.group()] = value.group()
        return Script

def getMITM(string):
        mitm = []
        list = re.search(r"(?<=\[(MITM)\]\n)((.|\s)*)(?=\[)",
                        string, flags=re.DOTALL)
        if list != None:
            list = list.group()
            list = list.replace(' ', '')
            list = re.search(r"(?<=%INSERT%|%APPEND%).*", list)
            if list != None:
                l = list.group().split(',')
            for v in l:
                mitm.append(v)
        return mitm

def generate_yaml_doc(filename, MITM, Script):
    newScript = []
    typeTable = {
        "http-response": "response"
    }
    scriptProviders = {}
    for (key,value)  in Script.items():
        newScript.append({
            "match": value["pattern"],
            "name": key,
            "type": typeTable[value['type']],
            "require-body": int(value["requires-body"]) == 1,
            "timeout": 120
        })
        scriptProviders[key] = {"url": value["script-path"], "interval": 86400}
    py_object = {'http': {'mitm': MITM, "script": newScript}, "script-providers": scriptProviders}
    file = open(filename, 'w', encoding='utf-8')
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.dump(py_object, file)
    file.close()

url = sys.argv[1]
response = urllib.request.urlopen(url)

if response.getcode() != 200:
    print('获取错误')
    exit()

r = response.read().decode('utf-8')
generate_yaml_doc(getMITM(r), getScript(r))
