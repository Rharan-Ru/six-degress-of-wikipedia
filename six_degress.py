import re
import requests
import collections
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, wait, as_completed

VISITED_LINKS = []
DICT_NOT_VISITED_LINKS = {}
NOT_VISITED_LINKS = []

input_start = input('Type the initial article name: \n')
input_last = input('Type the last article name: \n')

START_TERM = f"/wiki/{input_start}"
LAST_TERM = f"/WIKI/{input_last.upper()}"
EXIT_SCRIPT = False

session = requests.Session()


def remove_duplicates(list_links):
    links = [link.attrs['href']
             for link in list_links if link.attrs['href'] not in VISITED_LINKS]
    links = set(links)
    return collections.deque(links)


def remove_duplicates_not_visited(list_links, parent, actual_key):
    links = [link for link in list_links if link not in NOT_VISITED_LINKS]
    [NOT_VISITED_LINKS.append(link) for link in links]
    past_path = DICT_NOT_VISITED_LINKS[actual_key]["path"].copy()
    past_path.append(parent)
    DICT_NOT_VISITED_LINKS[parent] = {"path": past_path, "links": links}


def get_all_links(link):
    url = f"https://en.wikipedia.org{link}"
    html = session.get(url).content
    try:
        bs = BeautifulSoup(html, 'lxml')
        all_links = bs.find('div', {'id': 'bodyContent'}).find_all(
            'a', href=re.compile('^(/wiki/)((?!:).)*$'))
        all_links = remove_duplicates(all_links)
        return all_links
    except AttributeError as error:
        print(error)
        return None


def verify_links(list, parent):
    global EXIT_SCRIPT
    for link in list:
        if link.upper() == LAST_TERM:
            path = DICT_NOT_VISITED_LINKS[parent]["path"]
            url = f"https://en.wikipedia.org/{path[-1]}"
            print('\n')
            print(f'LINK ENCONTRADO NO CAMINHO: ')
            print(f'{path} - {link} / CLIQUES ATÉ O ARTIGO: {len(path)}')
            print(f'Go to article:\n{url}')
            print('\n')
            print("FINALIZANDO PROCESSO")
            EXIT_SCRIPT = True


def recursive_search(parent_wiki, actual_key, index):
    all_links = get_all_links(parent_wiki)
    remove_duplicates_not_visited(all_links, parent_wiki, actual_key)
    verify_links(all_links, parent_wiki)
    print(f'#{index} CHECKING WIKI: ', parent_wiki)
    print('ACTUAL PARENT WIKI: ', actual_key)
    print('PATH: ', DICT_NOT_VISITED_LINKS[parent_wiki]["path"])
    print("----" * 20)
    if parent_wiki not in VISITED_LINKS:
        VISITED_LINKS.append(parent_wiki)


def thread_recursive_search(list_links, actual_key):
    global EXIT_SCRIPT
    print('LINKS ENCONTRADOS: ', len(list_links))
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [
            executor.submit( recursive_search, list_links[i], actual_key, i) for i in range(len(list_links))
        ]
        for future in as_completed(futures):
            if future.cancelled():
                continue
            if EXIT_SCRIPT:
                executor.shutdown(wait=False)
                [f.cancel() for f in futures if not f.done()]
                exit()
        wait(futures)
        del DICT_NOT_VISITED_LINKS[actual_key]
        next_key = next(iter(DICT_NOT_VISITED_LINKS))
        new_list_links = DICT_NOT_VISITED_LINKS[next_key]["links"]
        print(f"WORKING ON NEW KEY: {next_key} ")
        thread_recursive_search(new_list_links, next_key)


def init_search(search_from):
    print(f"FIND CONNECTIONS BETWEEN {START_TERM.upper()} & {LAST_TERM}")
    all_links = get_all_links(search_from)
    DICT_NOT_VISITED_LINKS[search_from] = {
        "path": [search_from], "links": all_links
    }
    verify_links(all_links, search_from)
    thread_recursive_search(all_links, search_from)


init_search(START_TERM)
