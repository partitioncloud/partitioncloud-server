#!/usr/bin/python3
"""
Module implémentant la recherche de partitions par mots-clés
"""
from uuid import uuid4
import urllib.request
import threading
import socket
import os

import pypdf
import googlesearch
from unidecode import unidecode

from .db import get_db

socket.setdefaulttimeout(5) # Maximum time before we give up on downloading a file (dead url)


def local_search(query, partitions):
    """
    Renvoie les 5 résultats les plus pertinents parmi une liste donnée
    """
    query_words = [word.lower() for word in unidecode(query).split()]
    def score_attribution(partition):
        score = 0
        for word in query_words:
            if word != "":
                if word in unidecode(partition["name"]).lower():
                    score += 6
                elif word in unidecode(partition["author"]).lower():
                    score += 4
                elif word in unidecode(partition["body"]).lower():
                    score += 2
                else:
                    score -= 6
        for word in unidecode(partition["name"]).split():
            if word != "" and word.lower() not in query_words:
                score -= 1
        return score

    score_partitions = [(score_attribution(partition), partition) for partition in partitions]
    score_partitions.sort(key=lambda x: x[0], reverse=True)

    selection = []
    for score, partition in score_partitions[:5]:
        if score > 0:
            selection.append(partition)
        else:
            break
    return selection


def download_search_result(element, instance_path):
    uuid = element["uuid"]
    url = element["url"]
    filename = f"{instance_path}/search-partitions/{uuid}.pdf"

    try:
        urllib.request.urlretrieve(url, filename)
        pypdf.PdfReader(filename)

    except (urllib.error.HTTPError, urllib.error.URLError,
            pypdf.errors.PdfReadError, pypdf.errors.PdfStreamError):
        if os.path.exists(filename):
            os.remove(filename)
        with open(filename, 'a', encoding="utf8") as _:
            pass # Create empty file


def online_search(query, num_queries, instance_path):
    """
    Renvoie les 3 résultats les plus pertinents depuis google
    """
    db = get_db()
    query = f"partition filetype:pdf {query}"
    partitions = []

    try:
        results = googlesearch.search(
            query,
            num=num_queries,
            stop=num_queries,
            pause=0.2
        )
        for element in results:
            while True:
                try:
                    uuid = str(uuid4())
                    db.execute(
                        """
                        INSERT INTO search_results (uuid, url)
                        VALUES (?, ?)
                        """,
                        (uuid, element,)
                    )
                    db.commit()

                    partitions.append(
                        {
                            "name": element.split("://")[1].split("/")[0],
                            "uuid": uuid,
                            "url": element
                        }
                    )
                    break
                except db.IntegrityError:
                    pass

    except urllib.error.URLError: # Unable to access network
        return []

    threads = [
        threading.Thread(
            target=download_search_result,
            args=(elem, instance_path)
        ) for elem in partitions
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    for element in partitions.copy():
        uuid = element["uuid"]
        url = element["url"]
        if os.stat(f"{instance_path}/search-partitions/{uuid}.pdf").st_size == 0:
            print("An error occured", url)
            db.execute(
                """
                DELETE FROM search_results
                WHERE uuid = ?
                """,
                (uuid,)
            )
            db.commit()

            os.remove(f"{instance_path}/search-partitions/{uuid}.pdf")

            partitions.remove(element)

    return partitions


def flush_cache(instance_path):
    """
    Supprimer les résultats de recherche datant de plus de 15 minutes
    """
    db = get_db()
    expired_cache = db.execute(
        """
        SELECT uuid FROM search_results
        WHERE creation_time <= datetime('now', '-15 minutes', 'localtime')
        """
    ).fetchall()
    for element in expired_cache:
        uuid = element["uuid"]
        if os.path.exists(f"{instance_path}/search-partitions/{uuid}.pdf"):
            os.remove(f"{instance_path}/search-partitions/{uuid}.pdf")

        if os.path.exists(f"{instance_path}/cache/search-thumbnails/{uuid}.jpg"):
            os.remove(f"{instance_path}/cache/search-thumbnails/{uuid}.jpg")

    db.execute(
        """
        DELETE FROM search_results
        WHERE creation_time <= datetime('now', '-15 minutes', 'localtime')
        """
    )
    db.commit()
