from os import sep
from typing import List, Tuple
from bs4 import BeautifulSoup
import requests
import re
import time
import os.path
import spacy


def error_page(soup) -> bool:
    content_box = soup.find('div', id_='contingut')
    if content_box == None:
        return False
    error_messsage = content_box.find('h2')
    if error_messsage == None:
        return False
    return True


def extract_title(soup) -> str:
    title_box = soup.find('h3')
    if title_box == None:
        return ''
    title = title_box.text.strip()
    return title


def extract_subtitle(soup) -> str:
    subtitle_box = soup.find('h4', class_='subtitol')
    if subtitle_box == None:
        return ''
    # retourne si la chaine de caractère est un lien
    if subtitle_box.text.find('http') != -1:
        return ''
    # certaines phrases ne retournent qu'un chiffre ou des caractères spéciaux
    if len(subtitle_box.text) < 10:
        return ''
    subtitle = subtitle_box.text.strip()
    return subtitle


def extract_whole_article(soup) -> str:
    article_box = soup.find('p', class_='contingut')
    # clean text
    article = article_box.text.replace('<br>', '')
    article = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', article)
    return article


def split_article_in_sentences(article: str) -> List[str]:
    sentences = article.split('.')
    sentences = [sentence for sentence in sentences if sentence]
    sentences = [sentence.strip() for sentence in sentences]
    return sentences


def count_word_by_sentence(sentence: str) -> int:
    return sentence.count(' ') + 1


def count_sentences(sentences: List[str]) -> int:
    return len(sentences)


def create_new_file(for_counter: int,  index_filename: int) -> Tuple[str, int]:
    if (for_counter % 1000) == 0:
        index_filename += 1
    filename = 'jornalet_{0}.txt'.format(index_filename)
    return filename, index_filename


def display_informations(for_counter: int, total_words: int, total_sentences: int) -> None:
    if (for_counter % 1000) == 0:
        print(f'##{time.strftime("%Y-%m-%d %H:%M:%S")}##')
        print(f'Nombre total de mots: {total_words} .....')
        print(f'Nombre total de phrases: {total_sentences} .....')


def fetch_last_article_nb_checked() -> int:
    if os.path.exists('nb_jornalet_articles.txt'):
        with open('nb_jornalet_articles.txt', 'r') as f:
            last_line = f.readlines()[-1]
            last_line = last_line.split('/')
        # j'ajoute +1 pour recommencer sur l'article d'après
        return int(last_line[len(last_line)-2]) + 1
    else:
        return 1


def fetch_last_index_file() -> int:
    try:
        ordre_croissant: List[int] = []
        for _, _, files in os.walk('./'):
            for file in files:
                if file.startswith('jornalet_'):
                    filename = file.split('.')
                    filename = filename[0].split('_')
                    ordre_croissant.append(int(filename[len(filename)-1]))
        ordre_croissant = sorted(ordre_croissant)
        return ordre_croissant[len(ordre_croissant) - 1] + 1
    except:
        return 0


def sentence_structure(sentence_deps: List[str]) -> bool:
    for word_dep in sentence_deps:
        if word_dep == 'nsubj':
            return True

    counter: int = 0
    for word_dep in sentence_deps:
        if word_dep == 'det' or word_dep == 'appos':
            counter += 1
            break

    for word_dep in sentence_deps:
        if word_dep == 'case':
            counter += 1
            break

    for word_dep in sentence_deps:
        if word_dep == 'nmod' or word_dep == 'amod':
            counter += 1
            break

    return True if counter == 3 else False


def sentences_cleaner(nlp, sentences: List[str]) -> List[str]:
    sentences_sanitized: List[str] = []
    for sentence in sentences:
        # vérifie si la phrase a une structure syntaxique correcte
        doc = nlp(sentence)
        sentence_deps: List[str] = [token.dep_ for token in doc]

        if not sentence_structure(sentence_deps):
            continue

        if sentence[0] == '—':
            sentence = sentence.replace('—', '')

        if sentence[0] == ')':
            sentence = sentence.replace(')', '')

        sentence = sentence.replace('[', '')
        sentence = sentence.replace(']', '')
        sentence = sentence.replace('…', '')
        sentence = sentence.replace('\xa0', '')
        sentence = sentence.replace('"', '')
        sentence = sentence.replace('“', '')
        sentence = sentence.replace('”', '')
        sentence = sentence.replace('‘', '')
        sentence = sentence.replace('’', '')

        sentence = sentence.strip()
        sentences_sanitized.append(sentence)

    return sentences_sanitized


HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}
LINE_SEPARATOR: str = '~'
A_TRADUIRE: str = '<<Ici, ajoutez la traduction en Français>>'
TOTAL_PAGE: int = 13300
START_AT: int = fetch_last_article_nb_checked()


def main():
    nlp = spacy.load('ca')
    idx_filename: int = fetch_last_index_file()
    total_words: int = 0
    total_sentences: int = 0

    for i in range(START_AT, TOTAL_PAGE):
        time.sleep(1.1)
        url: str = 'https://www.jornalet.com/nova/{0}/'.format(i)

        print(f"{url} est entrain d'être analyser...")

        req = requests.get(url, headers=HEADERS)
        if req.status_code == 404:
            continue

        soup = BeautifulSoup(req.text, features="html.parser")

        if error_page(soup):
            continue

        title = extract_title(soup)
        if not title:
            continue

        subtitle = extract_subtitle(soup)
        article = extract_whole_article(soup)
        sentences = split_article_in_sentences(article)

        try:
            filename, idx_filename = create_new_file(i, idx_filename)

            with open(filename, 'a') as f:
                f.write(title + LINE_SEPARATOR + A_TRADUIRE + '\n')
                if subtitle:
                    f.write(subtitle + LINE_SEPARATOR + A_TRADUIRE + '\n')
                for sentence in sentences:
                    f.write(sentence + LINE_SEPARATOR + A_TRADUIRE + '\n')
                    total_words += count_word_by_sentence(sentence)

            total_sentences += count_sentences(sentences)

            with open('nb_jornalet_articles.txt', 'a') as f:
                f.write(url + '\n')
        except Exception as e:
            print(e)
            continue
        finally:
            display_informations(i, total_words, total_sentences)

    print(f'Nombre total de mots: {total_words}')
    print(f'Nombre total de phrases: {total_sentences}')


if __name__ == "__main__":
    main()
