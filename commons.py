# Extrait l'index de l'item dans 'ans'
def get_item_index(ans, item):
    if len(ans) != 0:
        i = 0
        for element in ans:
            if element["item"] == item:
                return i
            i += 1
    return -1
