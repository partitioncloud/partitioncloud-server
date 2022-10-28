#!/usr/bin/python3
"""
Module implémentant la recherche de partitions par mots-clés
"""
from uuid import uuid4
import urllib.request
import os

import googlesearch

from .db import get_db


def local_search(query, partitions):
    """
    Renvoie les 5 résultats les plus pertinents parmi une liste donnée
    """
    def score_attribution(partition):
        score = 0
        for word in query.split(" "):
            if word != "":
                low_word = word.lower()
                if low_word in partition["name"].lower():
                    score += 3
                elif low_word in partition["body"].lower():
                    score += 1
                elif low_word in partition["author"].lower():
                    score += 2
                else:
                    score -= .5
        return score

    partitions = sorted(partitions, key=score_attribution, reverse=True)
    sorted_partitions = []
    for partition in partitions:
        if score_attribution(partition) > 0:
            sorted_partitions.append(partition)
        else:
            break
    return sorted_partitions[:min(5,len(sorted_partitions))]


def online_search(query, num_queries):
    """
    Renvoie les 3 résultats les plus pertinents depuis google
    """
    db = get_db()
    query = f"partition filetype:pdf {query}"
    partitions = []
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
                urllib.request.urlretrieve(element, f"partitioncloud/search-partitions/{uuid}.pdf")

                os.system(
                    f'/usr/bin/convert -thumbnail\
                    "178^>" -background white -alpha \
                    remove -crop 178x178+0+0 \
                    partitioncloud/search-partitions/{uuid}.pdf[0] \
                    partitioncloud/static/search-thumbnails/{uuid}.jpg'
                )
                partitions.append(
                    {
                        "name": element.split("://")[1].split("/")[0],
                        "uuid": uuid
                    }
                )
                break
            except db.IntegrityError:
                pass
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                print(e, element)
                db.execute(
                    """
                    DELETE FROM search_results
                    WHERE uuid = ?
                    """,
                    (uuid,)
                )
                db.commit()
                break
    return partitions


def flush_cache():
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
        try:
            os.remove(f"partitioncloud/search-partitions/{uuid}.pdf")
        except FileNotFoundError:
            pass
        try:
            os.remove(f"partitioncloud/static/search-thumbnails/{uuid}.jpg")
        except FileNotFoundError:
            pass

    db.execute(
        """
        DELETE FROM search_results
        WHERE creation_time <= datetime('now', '-15 minutes', 'localtime')
        """
    )