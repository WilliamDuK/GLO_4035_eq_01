#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import jsonify
from datetime import date
import validations


DATE_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]


# Convertit une date donnée dans le format original au nouveau format
def convert_date(old_date):
    new_date = old_date.split(" ")
    new_date = date(int(new_date[2]), DATE_MONTHS.index(new_date[1])+1, int(new_date[0]))
    new_date = str(new_date)
    return str(new_date)


# Retourne une date donnée dans le nouveau format au format original
def revert_date(new_date):
    old_date = new_date.split("-")
    old_date = old_date[2].lstrip("0") + " " + DATE_MONTHS[int(old_date[1])-1] + " " + old_date[0]
    return old_date
