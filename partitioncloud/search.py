#!/usr/bin/python3
"""
Module implémentant la recherche de partitions par mots-clés
"""

def search(query, partitions):
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
