"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml
"""

__author__ = 'Sekou Diao'

import re
import xml.etree.ElementTree as ET
#from xml.dom.minidom import parseString
from bs4 import BeautifulSoup as BS

tree = ET.parse('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
root = tree.getroot()
#root1 = BS('quiz-L1-Grammaire-Gloses-20141004-0841.xml')

"""
variables de debogage
"""
counter = 0
total = 0
kabala = 0

gloses = {}

for question in root.findall('question'):
    if question.attrib['type'] == 'cloze':
        questiontext = question.get('questiontext')
        total += 1
        #liste_mots = []
        if "KALABA" in question[0][0].text: kabala += 1
        else:
            raw_html = question[1][0].text
            parsed_html = BS(raw_html)
            counter += 1
            liste_mot = [td.string for td in parsed_html.tbody.tr.contents]
            while '\n' in liste_mot: liste_mot.remove('\n')
            #test = parsed_html.find_all_next(text=True)
            for mot in liste_mot:
                if '\n' in mot:
                    index = liste_mot.index(mot)
                    i_l = mot.find('\n')
                    liste_mot[index] = mot[:i_l]
            contents = [tr for tr in parsed_html.tbody.contents[3].contents]
            if contents[1].string is None:
                liste_reponses = [td.table.tbody.tr.td.p.string for td in contents if td.string != '\n']
            else : liste_reponses = [td.string for td in contents if td.string != '\n']
            for mot, raw_reponses in zip(liste_mot, liste_reponses):
                reponses = raw_reponses.split(sep='~')
                answers = []
                for reponse in reponses:
                    if not reponse.startswith('%'):
                        score = '0'
                        function = reponse[:reponse.find('#')]
                    else:
                        if "SAC" in reponse: score = '100'
                        else:
                            score = reponse[reponse.find('%') + 1:reponse.rfind('%')]
                        function = reponse[4:reponse.find('#')]
                    comment = reponse[reponse.find('#') + 1:]
                    answers.append(dict(zip(['score','function','comment'], [score, function, comment])))
                if mot in gloses:
                    if gloses == answers: pass
                    else: gloses[mot + '#'] = answers
                gloses[mot] = answers

gloses_xml = BS('<?xml version="1.0" encoding="UTF-8"?>')

for mot, reponse in sorted(gloses.items()):
    word = gloses_xml.new_tag('word')
    word['name'] = mot
    gloses_xml.append(word)
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

xml_file = open('gloses.xml', 'w')
xml_file.write(gloses_xml.prettify())
xml_file.close()
