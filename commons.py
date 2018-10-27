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
