"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml
"""

__author__ = 'Sekou Diao'

import xml.etree.ElementTree as ET
from xml.dom.minidom import parseString

tree = ET.parse('quiz-L1-Grammaire-Gloses-20141004-0841.xml')
root = tree.getroot()

gloses = {}

counter = 0
total = 0
kabala = 0

for question in root.findall('question'):
    if question.attrib['type'] == 'cloze':
        questiontext = question.get('questiontext')
        total += 1
        if "KALABA" in question[0][0].text: kabala += 1
        else:
            raw_html = question[1][0].text
            parsed_html = parseString(raw_html)
            counter += 1
            print(parsed_html.toxml())
            print(question[0][0].text)

print (total)
print(counter)
print(kabala)