"""
Extracteur de mots depuis un fichier xml moodle quiz.
Le script lit le fichier et en extrait les mots ainsi que les questions associees a chaque mot puis enregistre le
resultat dans un fichier gloses_francais.xml pour les mots en francais et gloses_kalaba.xml pour les mots Kalaba.
"""

__author__ = 'Sekou Diao'

import argparse
import codecs
from bs4 import BeautifulSoup as BS, NavigableString
import sqlite3
from os.path import isfile, getsize


def extract_gloses(xml_file):
    """
    Reads the specified file and extracts gloss information.

    It incrementally updates gloses_francais_dict and gloses_kalaba_dict.

    :param xml_file: file
    :return:
    """
    xml_doc = BS(xml_file)

    for question in xml_doc.find_all('question'):
        if question['type'] == 'cloze':
            name_tag = question.find('name')
            raw_html = question.questiontext.text
            clean_html = clean_raw_html(raw_html)
            parsed_html = BS(clean_html)
            if "KALABA" in name_tag.text:
                liste_mot_reponse = parse_questiontext_tag(parsed_html, kalaba=True)
                update_dict(gloses_kalaba_dict, liste_mot_reponse)
            else:
                liste_mot_reponse = parse_questiontext_tag(parsed_html)
                update_dict(gloses_francais_dict, liste_mot_reponse)
    liste_doublons = []
    for key, values in gloses_francais_dict['unique'].items():
        if key in gloses_francais_dict['duplicates']:
            gloses_francais_dict['duplicates'][key + "$"] = values
            liste_doublons.append(key)
    for elt in liste_doublons:
        gloses_francais_dict['unique'].pop(elt)
    return


def parse_questiontext_tag(html_obj, kalaba=False):
    """
    Parses an a html object containing the exercice and extracts a list of words and a list of unprocessed answers.

    The parsing part had to be tweaked to handle the many variations in question structure.

    :param kalaba: bool
    :param html_obj: bs4 html object
    :rtype zip: zip
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

    :param liste_mot: list
    :rtype : none
    """
    while '\n' in liste_mot:
        liste_mot.remove('\n')
    for mot in liste_mot:
        index = liste_mot.index(mot)
        liste_mot[index] = mot.rstrip()
    return


def generate_liste_reponse(liste_html):
    """
    Generates a list of raw answers from the parsed Html.

    :param liste_html: list
    :return liste_reponses:
    """
    while '\n' in liste_html:
        liste_html.remove('\n')
    liste_reponses = [td if isinstance(td, NavigableString) else td.text.replace('\n', '') for td in liste_html]
    return liste_reponses


def generate_answer_dict(reponse):
    """
    Generates a dictionary with keys 'score', 'content', 'comment'.

    :param reponse: str
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
    if content.startswith(':'):
        content = content[1:]
    answer_dict = dict(zip(['score', 'content', 'comment'], [score, content, comment]))
    return answer_dict


def update_dict(dic, zip_mot_reponses):
    """
    Updates dict with the entries in zip_mot_reponse.

    Calls recursive_update to update the dictionary.

    :param dic: dic
    :param zip_mot_reponses: zip
    :return:
    """
    for mot, raw_reponses in zip_mot_reponses:
        answers = []
        reponses = raw_reponses.split(sep='~')
        if reponses[0] == '{1:MC:':
            reponses[0:2] = [''.join(reponses[0:2])]
        for reponse in reponses:
            answers.append(generate_answer_dict(reponse))
        recursive_update(dic, mot.lower(), answers)
    return

def update_db(dbname, dic):
    """

    :param dbname:
    :param dic:
    :return:
    """
    glosesdb = sqlite3.connect(dbname)
    gloses = glosesdb.cursor()
    compteur_mot = {}
    for key in dic:
        for mot in dic[key]:
            if "$" in mot:
                mot_nu = mot.rstrip("$")
            elif "#" in mot:
                mot_nu = mot.rstrip("#")
            else:
                mot_nu = mot
            if not mot_nu in compteur_mot:
                compteur_mot[mot_nu] = 1
            else:
                compteur_mot[mot_nu] += 1
            gloses.execute("INSERT into words values (?,?) ", (mot_nu, compteur_mot[mot_nu]))
            for reponse in dic[key][mot]:
                gloses.execute("INSERT into answers values (?,?,?,?,?) ", (mot_nu, compteur_mot[mot_nu], reponse['score'], reponse['content'], reponse['comment']))
    glosesdb.commit()
    return


def create_db(dbname):
    """

    :param dbname:
    :return:
    """
    if not _isSQLite3(dbname):
        glosesdb = sqlite3.connect(dbname)
        gloses = glosesdb.cursor()
        gloses.execute("""PRAGMA foreign_keys = ON """)
        create_words_table = '''CREATE TABLE `words` (
                `word`	TEXT,
                `id`	INT,
                PRIMARY KEY(`word`, `id`)
            )'''
        create_answers_table = '''CREATE TABLE `answers` (
                `word`	TEXT,
                `id`	INT,
                `score`	INT,
                `content`	TEXT,
                `comment`	TEXT,
                FOREIGN KEY(`word`, `id`) REFERENCES words(`word`, `id`)
            )'''
        gloses.execute(create_words_table)
        gloses.execute(create_answers_table)
        glosesdb.commit()
    return

def recursive_update(dic, key, value):
    """
    Recursively checks if key is in dic.

    If key is not in dic, it updates the dic with {key : value}.
    If key is in dic, it appends '#' to the key and recursively try to update dic.

    :param dic: dic
    :param key: str
    :param value: list
    """

    if "#" not in key and key not in dic['unique']:
        dic['unique'][key] = value
        return
    elif "#" not in key and dic['unique'][key] == value:
        return
    if key not in dic['duplicates']:
        dic['duplicates'][key] = value
    elif dic['duplicates'][key] == value:
        return
    else:
        key = key + "#"
        recursive_update(dic, key, value)

    return


def generate_xml(dict_list):
    """
    Takes a list of dictionaries and returns a bs4 xml object.

    Each entry of the list is a dictionary of the form {syntagm: answer list}.

    :param dict_list: list
    :rtype : bs4 xml object
    """
    doc_xml = BS('<?xml version="1.0" encoding="UTF-8"?>')
    xml_root = doc_xml.new_tag('glosses')
    doc_xml.append(xml_root)
    for mot, reponses in sorted(dict_list.items()):
        syntagm = doc_xml.new_tag('word')
        syntagm['name'] = mot
        xml_root.append(syntagm)
        for dic in reponses:
            answer = doc_xml.new_tag('answer')
            answer['id'] = reponses.index(dic)
            syntagm.append(answer)
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

    :param xml_obj: bs4 xml object
    :param filename: str
    :rtype :
    """
    with codecs.open('{}.xml'.format(filename), 'w', encoding='utf8') as xml_file:
        xml_file.write(xml_obj.prettify())
        xml_file.close()
    return

def _isSQLite3(filename):
    """

    :param filename:
    :return: bool
    """
    if not isfile(filename):
        return False
    if getsize(filename) < 100:  # SQLite database file header is 100 bytes
        return False
    else:
        fd = open(filename, 'rb')
        header = fd.read(100)
        fd.close()
        if header[0:16] == b'SQLite format 3\000':
            return True
        else:
            return False

if __name__ == "__main__":
    # Creates the 2 dictionary objects that will hold the results of the words/answers extraction process
    gloses_francais_dict = {'unique': {}, 'duplicates': {}}
    gloses_kalaba_dict = {'unique': {}, 'duplicates': {}}

    # Creates parser object to hold arguments
    parser = argparse.ArgumentParser()
    # parser.add_argument('file', type=argparse.FileType('r'))
    parser.add_argument('file_name')
    args = parser.parse_args()
    # file_obj = args.file
    # extract_gloses(file_obj)

    file_name = args.file_name
    with codecs.open(file_name, 'r', encoding='utf8') as file_obj:
        extract_gloses(file_obj)



    # [(key, key + "$") for key in gloses_francais_dict['duplicates'] if (key + "$") in gloses_francais_dict['duplicates']]
    #
    # [(elt[0], gloses_francais_dict['duplicates'][elt[0]][i], elt[1], gloses_francais_dict['duplicates'][elt[1]][i]) if
    # gloses_francais_dict['duplicates'][elt[0]][i] != gloses_francais_dict['duplicates'][elt[1]][i] for elt in
    #  liste_doublons for i in range(len(gloses_francais_dict['duplicates'][key]))]

    liste_doublons = [(key, key + "$") for key in gloses_francais_dict['duplicates'] if
                      (key + "$") in gloses_francais_dict['duplicates'] and len(gloses_francais_dict['duplicates'][key]) == len(gloses_francais_dict['duplicates'][key + "$"])]
    champsdifferents = {}
    for elt in liste_doublons:
        champsdifferents[elt] = []
        if elt[0] in gloses_francais_dict['duplicates']:
            for i in range(len(gloses_francais_dict['duplicates'][elt[0]])):
                if gloses_francais_dict['duplicates'][elt[0]][i] != gloses_francais_dict['duplicates'][elt[1]][i]:
                    champsdifferents[elt].append((
                        gloses_francais_dict['duplicates'][elt[0]][i], gloses_francais_dict['duplicates'][elt[1]][i]))

    dbname1 = "gloses_francais.db"
    create_db(dbname1)
    update_db(dbname1, gloses_francais_dict)



    gloses_francais_xml = generate_xml(gloses_francais_dict['unique'])
    save_xml(gloses_francais_xml, 'Gloses Francais Xml/gloses_francais_unique-v4')

    gloses_francais_xml = generate_xml(gloses_francais_dict['duplicates'])
    save_xml(gloses_francais_xml, 'Gloses Francais Xml/gloses_francais_duplicates-v4')

    gloses_kalaba_xml = generate_xml(gloses_kalaba_dict['unique'])
    save_xml(gloses_kalaba_xml, 'Gloses Kalaba Xml/gloses_kalaba_unique-v4')

    gloses_kalaba_xml = generate_xml(gloses_kalaba_dict['duplicates'])
    save_xml(gloses_kalaba_xml, 'Gloses Kalaba Xml/gloses_kalaba_duplicates-v4')