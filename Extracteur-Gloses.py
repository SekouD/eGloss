"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml pour les mots en francais et kalaba.xml pour les mots Kalaba
"""

__author__ = 'Sekou Diao'

import re
import xml.etree.ElementTree as ET
# from xml.dom.minidom import parseString
from bs4 import BeautifulSoup as BS



def generate_xml(dict_list):
    """



    :param dict_list:
    :rtype : bs4 xml object
    """
    doc_xml = BS('<?xml version="1.0" encoding="UTF-8"?>')
    xml_root = doc_xml.new_tag('gloses')
    doc_xml.append(xml_root)
    for mot, reponse in sorted(dict_list.items()):
        word = doc_xml.new_tag('word')
        word['name'] = mot
        xml_root.append(word)
        for dict in reponse:
            answer = doc_xml.new_tag('answer')
            answer['id'] = reponse.index(dict)
            word.append(answer)
            score = doc_xml.new_tag('score')
            score.string = dict['score']
            function = doc_xml.new_tag('function')
            function.string = dict['function']
            comment = doc_xml.new_tag('comment')
            comment.string = dict['comment']
            answer.append(score)
            answer.append(function)
            answer.append(comment)
    return doc_xml


def save_xml(xml_obj, filename):
    """



    :param xml_obj:
    :param filename:
    :rtype :
    """
    xml_file = open('{}.xml'.format(filename), 'w')
    xml_file.write(xml_obj.prettify())
    xml_file.close()
    return


def nettoyer_liste(liste_mot):
    """


    :param liste_mot:
    :rtype : none
    """
    while '\n' in liste_mot: liste_mot.remove('\n')
    for mot in liste_mot:
        if '\n' in mot:
            index = liste_mot.index(mot)
            i = mot.find('\n')
            liste_mot[index] = mot[:i]
    return


def generate_liste_reponse(liste_html):
    """

    :param liste_html:
    :return liste_reponses:
    """
    if liste_html[1].string is None:
        liste_reponses = [td.table.tbody.tr.td.p.string for td in liste_html if td.string != '\n']
    else:
        liste_reponses = [td.p.string if td.string is None else td.string for td in liste_html if td.string != '\n']
    return liste_reponses


def generate_answer_dict(reponse):
    """




    :param reponse:
    :rtype : dict
    """
    if "%" in reponse:
        score = reponse[reponse.find('%') + 1:reponse.rfind('%')]
        function = reponse[4:reponse.find('#')]
    elif "SAC" in reponse:
        score = '100'
        function = reponse[7:reponse.find('#')]
    elif "MC" in reponse:
        score = '100'
        function = reponse[6:reponse.find('#')]
    else:
        score = '0'
        function = reponse[:reponse.find('#')]
    if "#" in reponse:
        comment = reponse[reponse.find('#') + 1:]
    else:
        comment = 'None'
    answer_dict = dict(zip(['score', 'function', 'comment'], [score, function, comment]))
    return answer_dict


def update_dict(dict, zip_mot_reponse):
    """



    :param dict:
    :param zip_mot_reponse:
    :return:
    """
    for mot, raw_reponses in zip_mot_reponse:
        reponses = raw_reponses.split(sep='~')
        answers = []
        for reponse in reponses:
            answers.append(generate_answer_dict(reponse))
        recursive_update(dict, mot, answers)
    return

def recursive_update(dict, key, value):
    """


    :param dict:
    :param key:
    :param value:
    """
    if key not in dict:
        dict[key] = value
    elif dict[key] == value:
        return
    else:
        recursive_update(dict, key + '#', value)
    return



def parse_questiontext_tag(html_obj, kalaba=False):
    """



    :param kalaba:
    :rtype : object
    :param html_obj:
    """
    if kalaba:
        test = html_obj.find_all('table')
        liste_mot = []
        liste_raw_reponses = []
        for table in test:
            liste_mot.extend([td.strong.string for td in table.tbody.tr.contents if td.string != '\n' and td.string is None])
            liste_raw_reponses.extend([tr if len(tr.contents) == 1 else tr.p.string for tr in table.tbody.contents[3].contents if not isinstance(tr, str) and tr.strong is None])
    else:
        liste_mot = [td.string for td in html_obj.tbody.tr.contents]
        liste_raw_reponses = [tr for tr in html_obj.tbody.contents[3].contents]
    nettoyer_liste(liste_mot)
    liste_reponses = generate_liste_reponse(liste_raw_reponses)
    return zip(liste_mot, liste_reponses)


tree = ET.parse('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
root = tree.getroot()
#root1 = BS('quiz-L1-Grammaire-Gloses-20141004-0841.xml')

gloses_dict = {}
kalaba_dict = {}

for question in root.findall('question'):
    if question.attrib['type'] == 'cloze':
        raw_html = question[1][0].text
        parsed_html = BS(raw_html)
        if "KALABA" in question[0][0].text:
            liste_mot_reponse = parse_questiontext_tag(parsed_html, kalaba=True)
            update_dict(kalaba_dict, liste_mot_reponse)
        else:
            liste_mot_reponse = parse_questiontext_tag(parsed_html)
            update_dict(gloses_dict, liste_mot_reponse)

gloses_xml = generate_xml(gloses_dict)
save_xml(gloses_xml, 'gloses')
kalaba_xml = generate_xml(kalaba_dict)
save_xml(kalaba_xml, 'kalaba')
