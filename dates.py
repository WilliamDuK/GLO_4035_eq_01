#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import date


DATE_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]


# Convertit une date donnée dans le format original au nouveau format
def convert_date(old_date):
    new_date = old_date.split(" ")
    new_date = date(int(new_date[2]), DATE_MONTHS.index(new_date[1].capitalize())+1, int(new_date[0]))
    new_date = str(new_date)
    return str(new_date)


# Retourne une date donnée dans le nouveau format au format original
def revert_date(new_date):
    old_date = new_date.split("-")
    old_date = old_date[2].lstrip("0") + " " + DATE_MONTHS[int(old_date[1])-1] + " " + old_date[0]
    return old_date


# Vérifie que le format de la date est valide
def validate_new_date(new_date):
    try:
        year, month, day = new_date.split("-")
        date(int(year), int(month), int(day))
        return True
    except ValueError:
        return False


# Vérifie que le format de la date est valide
def validate_old_date(old_date):
    try:
        day, month, year = old_date.split(" ")
        if validate_month(month):
            new_date = convert_date(old_date)
            if validate_new_date(new_date):
                return True
            else:
                return False
        else:
            return False
    except ValueError:
        return False


# Vérifie que le mois est valide
def validate_month(month):
    if month.capitalize() in DATE_MONTHS:
        return True
    else:
        return False
