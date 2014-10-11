"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml
"""

__author__ = 'Sekou Diao'

import re
import xml.etree.ElementTree as ET
# from xml.dom.minidom import parseString
from bs4 import BeautifulSoup as BS


"""
variables de debogage
"""
counter = 0
total = 0
kabala = 0


def generate_gloses_xml(gloses_dict):
    """


    :param gloses_dict:
    :rtype : bs4 xml object
    """
    gloses_xml = BS('<?xml version="1.0" encoding="UTF-8"?>')
    xml_root = gloses_xml.new_tag('gloses')
    gloses_xml.append(xml_root)
    for mot, reponse in sorted(gloses_dict.items()):
        word = gloses_xml.new_tag('word')
        word['name'] = mot
        xml_root.append(word)
        for dict in reponse:
            answer = gloses_xml.new_tag('answer')
            answer['id'] = reponse.index(dict)
            word.append(answer)
            score = gloses_xml.new_tag('score')
            score.string = dict['score']
            function = gloses_xml.new_tag('function')
            function.string = dict['function']
            comment = gloses_xml.new_tag('comment')
            comment.string = dict['comment']
            answer.append(score)
            answer.append(function)
            answer.append(comment)
    return gloses_xml


def save_xml(xml_obj):
    """


    :param xml_obj:
    :rtype :
    """
    xml_file = open('gloses.xml', 'w')
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
        liste_reponses = [td.string for td in liste_html if td.string != '\n']
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
        function = reponse[8:reponse.find('#')]
    else:
        score = '0'
        function = reponse[:reponse.find('#')]
    if "#" in reponse:
        comment = reponse[reponse.find('#') + 1:]
    else:
        comment = 'None'
    answer_dict = dict(zip(['score', 'function', 'comment'], [score, function, comment]))
    return answer_dict


def update_glose_dict(glose_dict, zip_mot_reponse):
    """


    :param liste_mot_reponse:
    :param glose_dict:
    :return:
    """
    for mot, raw_reponses in zip_mot_reponse:
        reponses = raw_reponses.split(sep='~')
        answers = []
        for reponse in reponses:
            answers.append(generate_answer_dict(reponse))
        if mot in glose_dict:
            if glose_dict == answers:
                pass
            else:
                glose_dict[mot + '#'] = answers
        glose_dict[mot] = answers
    return


def parse_questiontext_tag(html_obj):
    """

    :param html_obj:
    """
    liste_mot = [td.string for td in parsed_html.tbody.tr.contents]
    nettoyer_liste(liste_mot)
    liste_raw_reponses = [tr for tr in parsed_html.tbody.contents[3].contents]
    liste_reponses = generate_liste_reponse(liste_raw_reponses)
    return zip(liste_mot, liste_reponses)


tree = ET.parse('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
root = tree.getroot()
#root1 = BS('quiz-L1-Grammaire-Gloses-20141004-0841.xml')

gloses = {}

for question in root.findall('question'):
    if question.attrib['type'] == 'cloze':
        if "KALABA" in question[0][0].text:
            pass
        else:
            raw_html = question[1][0].text
            parsed_html = BS(raw_html)
            liste_mot_reponse = parse_questiontext_tag(raw_html)
            update_glose_dict(gloses, liste_mot_reponse)

gloses_xml = generate_gloses_xml(gloses)
save_xml(gloses_xml)
