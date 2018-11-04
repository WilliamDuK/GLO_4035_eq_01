#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Extrait l'index de l'item dans l'array
def get_index_of(array, item):
    if len(array) != 0:
        i = 0
        for element in array:
            if element["item"] == item:
                return i
            i += 1
    return -1


# Extraction de la sous-string qui détermine la catégorie utilisée
def detect_category(array):
    ans = ""
    if len(array) == 1:
        ans = array[0]["item"]
    elif len(array) > 1:
        item1, item2 = array[0]["item"], array[-1]["item"]
        len1, len2 = len(item1), len(item2)
        for i in range(len1):
            match = ""
            for j in range(len2):
                if i + j < len1 and item1[i + j] == item2[j]:
                    match += item2[j]
                else:
                    if len(match) > len(ans):
                        ans = match
                    match = ""
    if ans.endswith(" - "):
        ans = ans[:-3]
    return ans
