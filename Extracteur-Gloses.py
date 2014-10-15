"""
Extracteur de mots depuis quiz-L1-Grammaire-Gloses-20141004-0841.xml
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses.xml pour les mots en francais et kalaba.xml pour les mots Kalaba.
"""

__author__ = 'Sekou Diao'

from bs4 import BeautifulSoup as BS

def clean_raw_html(raw_html):
    """
    Takes a raw html string and removes <span> and <br /> tags.

    :param raw_html: str
    :return: str
    """
    for tag in ('<br />', '<span>', '</span>'):
        raw_html = raw_html.replace(tag, '')
    return raw_html


def nettoyer_liste(liste_mot):
    """
    Cleans a list of words by removing '\n' entries.

    :param liste_mot:
    :rtype : none
    """
    while '\n' in liste_mot:
        liste_mot.remove('\n')
    for mot in liste_mot:
        if '\n' in mot:
            index = liste_mot.index(mot)
            i = mot.find('\n')
            liste_mot[index] = mot[:i]
    return


def generate_liste_reponse(liste_html):
    """
    Generates a list of raw answers from the parsed Html.

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
    Generates a dictionary with keys 'score', 'content', 'comment'.

    :param reponse:
    :rtype : dict
    """
    if "%" in reponse:
        score = reponse[reponse.find('%') + 1:reponse.rfind('%')]
        content = reponse[4:reponse.find('#')]
    elif "SAC" in reponse:
        score = '100'
        content = reponse[7:reponse.find('#')]
    elif "MC" in reponse:
        score = '100'
        content = reponse[6:reponse.find('#')]
    elif reponse.startswith('='):
        score = '100'
        content = reponse[:reponse.find('#')]
    else:
        score = '0'
        content = reponse[:reponse.find('#')]
    if "#" in reponse:
        comment = reponse[reponse.find('#') + 1:]
    else:
        comment = 'None'
    answer_dict = dict(zip(['score', 'content', 'comment'], [score, content, comment]))
    return answer_dict


def update_dict(dic, zip_mot_reponse):
    """
    Updates dict with the entries in zip_mot_reponse.

    Calls recursive_update to update the dictionary.

    :param dic:
    :param zip_mot_reponse:
    :return:
    """
    for mot, raw_reponses in zip_mot_reponse:
        answers = []
        reponses = raw_reponses.split(sep='~')
        if reponses[0] == '{1:MC:':
            reponses[0:2] = [''.join(reponses[0:2])]
        for reponse in reponses:
            answers.append(generate_answer_dict(reponse))
        recursive_update(dic, mot.lower(), answers)
    return


def recursive_update(dic, key, value):
    """
    Recursively Checks if key is in dic.

    If key is not in dic, it updates the dic with {key : value}.
    If key is in dic, it appends '#' to the key and recursively try to update dic.

    :param dic:
    :param key:
    :param value:
    """
    if key not in dic:
        dic[key] = value
    elif dic[key] == value:
        return
    else:
        recursive_update(dic, key + '#', value)
    return


def parse_questiontext_tag(html_obj, kalaba=False):
    """
    Parses an a html object containing the exercice and extracts a list of words and a list of unprocessed answers.

    The parsing part had to be tweaked to handle the many variations in question structure.

    :param kalaba:
    :rtype zip: object
    :param html_obj:
    """
    if kalaba:
        table_list = html_obj.find_all('table')
        liste_mot = []
        liste_raw_reponses = []
        for table in table_list:
            liste_mot.extend(
                [td.strong.string for td in table.tbody.tr.contents if td.string != '\n' and td.string is None])
            liste_raw_reponses.extend(
                [tr if len(tr.contents) == 1 else tr.p.string for tr in table.tbody.contents[3].contents if
                 not isinstance(tr, str) and tr.strong is None])
    else:
        liste_mot = [td.string for td in html_obj.tbody.tr.contents]
        liste_raw_reponses = [tr for tr in html_obj.tbody.contents[3].contents]
    nettoyer_liste(liste_mot)
    liste_reponses = generate_liste_reponse(liste_raw_reponses)
    return zip(liste_mot, liste_reponses)


def generate_xml(dict_list):
    """
    Takes a list of dictionaries and returns a bs4 xml object.

    Each entry of the list is a dictionary of the form {lexeme: answer list}
    :param dict_list:
    :rtype : bs4 xml object
    """
    doc_xml = BS('<?xml version="1.0" encoding="UTF-8"?>')
    xml_root = doc_xml.new_tag('gloses')
    doc_xml.append(xml_root)
    for mot, reponses in sorted(dict_list.items()):
        lexeme = doc_xml.new_tag('lexeme')
        lexeme['name'] = mot
        xml_root.append(lexeme)
        for dic in reponses:
            answer = doc_xml.new_tag('answer')
            answer['id'] = reponses.index(dic)
            lexeme.append(answer)
            tag_list = [('score', 'num'), ('content', 'text'), ('comment', 'text')]
            for tag_name, tag_type in tag_list:
                tag = doc_xml.new_tag(tag_name)
                tag['type'] = tag_type
                tag.string = dic[tag_name]
                answer.append(tag)
    return doc_xml


def save_xml(xml_obj, filename):
    """
    Takes a bs4 xml object and saves it to a file called 'filename'.

    :param xml_obj:
    :param filename:
    :rtype :
    """
    xml_file = open('{}.xml'.format(filename), 'w')
    xml_file.write(xml_obj.prettify())
    xml_file.close()
    return


# Creates the 2 dictionary objects that will hold the results of the words/answers extraction process
gloses_dict = {}
kalaba_dict = {}

root = BS(open('quiz-L1-Grammaire-Gloses-20141004-0841.xml', 'r'))

for question in root.find_all('question'):
    if question['type'] == 'cloze':
        name_tag = question.find('name')
        raw_html = question.questiontext.text
        clean_html = clean_raw_html(raw_html)
        parsed_html = BS(clean_html)
        if "KALABA" in name_tag.text:
            liste_mot_reponse = parse_questiontext_tag(parsed_html, kalaba=True)
            update_dict(kalaba_dict, liste_mot_reponse)
        else:
            liste_mot_reponse = parse_questiontext_tag(parsed_html)
            update_dict(gloses_dict, liste_mot_reponse)

gloses_xml = generate_xml(gloses_dict)
save_xml(gloses_xml, 'gloses')
kalaba_xml = generate_xml(kalaba_dict)
save_xml(kalaba_xml, 'kalaba')
