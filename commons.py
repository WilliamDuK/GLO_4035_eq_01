#!/usr/bin/env python
# -*- coding: utf-8 -*-


# Extrait l'index de l'item dans 'array'
def get_item_index(array, item):
    if len(array) != 0:
        i = 0
        for element in array:
            if element["item"] == item:
                return i
            i += 1
    return -1
