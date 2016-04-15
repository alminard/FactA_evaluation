#!/usr/bin/python2.7

#usage: python CAT_to_evaluation_formats.py [CAT files or folder] [output_folder] [file rules FV] 
#version 5: add option language

import os 
import re
import sys 
import math
import commands
import codecs
from xml.dom import minidom


markable_id = "m_id"
relation_id = "r_id"
token_id = "t_id"

def get_arg(index):
    return sys.argv[index]


# take input from command line and give error messages 
# call appropriate functions to evaluate 
def input_and_evaluate():
    global file_rules

    invalid = 'false' 
    arg1 = get_arg(1) 
    global directory_path 
    directory_path = get_directory_path(sys.argv[0])

    file_rules = get_arg(3)

    # both arguments are directories 
    if os.path.isdir(arg1):
        evaluate_folder(arg1)
    elif os.path.isfile(arg1):
        read_CAT_file(arg1)

     
def evaluate_folder(repName):
    if repName[-1] != '/': 
        repName += '/' 
    for file in os.listdir(repName):
        if os.path.isdir(repName+file):
            subdir = file+'/'
            evaluate_folder(repName+subdir)
        else:
            fileName = repName +  file
            if not re.search('DS_Store', file): 
                read_CAT_file(fileName)

def extract_name(filename):
    parts = re.split('/', filename)
    length = len(parts)
    return parts[length-1]

def get_directory_path(path): 
    name = extract_name(path)
    dir = re.sub(name, '', path) 
    if dir == '': 
        dir = './'
    return dir 


class markable():
    "defining markable class"
    def __init__(self):
        self.eid = ''
        self.tokenAnchor = []
        self.att = {}


def get_element_value(elt):
    "get the list of token ids that composed the extent of the markable"
    tokenAnchorList = elt.getElementsByTagName('token_anchor') 
    tokenId = []
    for tokA in tokenAnchorList:
        tokenId.append(tokA.attributes[token_id].value)
    return tokenId


def get_element_feat(elt, nameFeat):
    if elt.hasAttribute(nameFeat):
        return elt.getAttribute(nameFeat)
    else:
        return ""


def get_all_element_value(elements, eltName, objectEval):
    "build a list of markable object"
    entityList = []
    entityTokenList = []
    elementsList = elements.getElementsByTagName(eltName)
    for elt in elementsList:
        e = markable()

        e.tokenAnchor = get_element_value(elt)
        e.eid = get_element_feat(elt, markable_id)
        
        for objE in objectEval:
            e.att[objE] = get_element_feat(elt, objE)
            if e.att[objE] == "" and get_arg(3) == "factuality":
                e.att[objE] = "O"
            
        if len(e.tokenAnchor) > 0:
            entityList.append(e)

    return entityList



def convertFact_multicol(list_token, list_event_ment, dict_FV):
    global nb_per
    global nb_loc
    global nb_org
    numSent = "0"
    content = []
    j = 0
    first_tok_sent = 0
    
    prev_ent = ""

    list_event_token_id = {}
    for ev in list_event_ment:
        for tokan in ev.tokenAnchor:
            if tokan in list_event_token_id:
                #don't keep CONJ
                if len(ev.tokenAnchor) < len(list_event_token_id[tokan].tokenAnchor):
                    list_event_token_id[tokan] = ev

            else:
                list_event_token_id[tokan] = ev

    for tok in list_token:
        if tok.firstChild:
            if tok.getAttribute('sentence') != numSent:
                content.insert(j,[""])
                j+=1
            
            content.insert(j,[tok.firstChild.nodeValue,"t"+tok.getAttribute(token_id)])
            #content.insert(j,[tok.firstChild.nodeValue])

            if tok.getAttribute(token_id) in list_event_token_id:
                ev = list_event_token_id[tok.getAttribute(token_id)]
                if j > 0 and len(content[j]) < len(content[j-1]) and re.search("-EVENT",content[j-1][len(content[j])]) and len(ev.tokenAnchor) > 1:
                    pref = "I-"
                else:
                    pref = "B-"
                        
                        
                prev_ent = ev.eid
                content[j].append(pref+"EVENT")

                polarity = ev.att["polarity"]
                certainty = ev.att["certainty"]
                time = ev.att["time"]
                comment = ev.att["comment"]

                if "no attribution" in comment or "no factuality" in comment:
                    polarity = "O"
                    certainty = "O"
                    time = "O"
                
                content[j].append(polarity)
                content[j].append(certainty)
                content[j].append(time)

                combin_factuality = polarity+"#"+certainty+"#"+time

                if "no attribution" in comment or "no factuality" in comment:
                    content[j].append("no_factuality_annotation")
                elif combin_factuality in dict_FV:
                    content[j].append(dict_FV[combin_factuality])
                else:
                    content[j].append("underspecified")

                
            else:
                prev_ent = ""
                content[j].append("O")
                content[j].append("O")
                content[j].append("O")
                content[j].append("O")
                content[j].append("O")
                
            numSent = tok.getAttribute("sentence")

            j += 1

    return content




def build_col_format_text(fileName, content):
    content_toprint = ""
    for k in range(0,len(content)):
        for c in range(0,len(content[k])):
            if c == len(content[k])-1:
                content_toprint += content[k][c]
            else:
                content_toprint += content[k][c]+"\t"
        content_toprint += "\n"
    
    content_toprint += "\n"
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    
    if len(sys.argv) > 3:
        extent = ".naf.conll"
        if get_arg(3) == "NER":
            extent = ".naf.conll"
        fileOut = extract_name(fileName)
        fileOut = fileOut.replace(".txt.xml",extent)
        fileOut = fileOut.replace(".xml",extent)
        f = codecs.open(get_arg(2)+fileOut,"w",encoding="utf-8")
        f.write(content_toprint)
        #sys.stdout = f
        
    #sys.stdout.write(content_toprint)



def read_FV_rules(fileRules):
    dict_FV = {}

    f = open(fileRules,"r")
    p = re.compile("^[^\#]+.*=")
    for line in f:
        if p.match(line):
            elt = line.split(" = ")
            dict_FV[elt[0]] = elt[1]
    f.close()

    return dict_FV


def read_CAT_file(fileName): 
    global markable_id
    global relation_id
    global token_id
    global layer

    #parse the file
    xmldoc = minidom.parse(fileName)

    #get elements 'Markables'
    markables = xmldoc.getElementsByTagName('Markables')[0] 

    #get tokens
    list_token = xmldoc.getElementsByTagName('token')

    if list_token[0].hasAttribute("id") :
        markable_id = "id"
        token_id = "id"
        relation_id = "id"

    list_event_mention = get_all_element_value(markables,'EVENT',['certainty','time','polarity','comment'])

    
    content_to_write = []
    
 
    dict_FV = read_FV_rules(get_arg(3))
    content_to_write = convertFact_multicol(list_token, list_event_mention, dict_FV)

    build_col_format_text(fileName, content_to_write)
    

input_and_evaluate()
