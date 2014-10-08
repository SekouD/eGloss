"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml
"""

__author__ = 'Sekou Diao'

import xml.etree.ElementTree as ET
#from xml.dom.minidom import parseString
from bs4 import BeautifulSoup as BS

tree = ET.parse('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
root = tree.getroot()
#root1 = BS('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
gloses = {}

counter = 0
total = 0
kabala = 0

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
            for mot in liste_mot:
                if '\n' in mot:
                    index = liste_mot.index(mot)
                    i = mot.find('\n')
                    liste_mot[index] = mot[:i]
            print(liste_mot)
            print(question[0][0].text)


print (total)
print(counter)
print(kabala)
