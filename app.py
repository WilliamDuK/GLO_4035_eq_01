#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
import hashlib
import validations
import dates
import commons


DB_NAME = "glo4035_inventory"
DB_HOST = "ds045679.mlab.com"
DB_PORT = 45679
DB_USER = "admin"
DB_PASS = "tXKqB2bZ9v"


application = Flask("my_glo4035_application")
application.config["JSON_SORT_KEYS"] = False
application.config["MONGO_URI"] = "mongodb://" + DB_USER + ":" + DB_PASS + "@" + DB_HOST + ":" + str(DB_PORT) + "/" + DB_NAME
mongo = PyMongo(application)
transactions = mongo.db.transactions
# purchases = mongo.db.transactions.purchases
# transformations = mongo.db.transactions.transformations
# densities = mongo.db.transactions.densities


# ------------- API -------------

# Route d'API accueillant les utilisateurs.
@application.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# Route d'API pouvant recevoir et persister les transactions envoyés par une
# application web. On a les réponses retournées suivantes:
# - Code HTTP 200: JSON bien formaté.
# - Code HTTP 400: JSON mal formaté.
@application.route("/transactions", methods=["POST"])
def add_transactions():
    if request.headers['Content-Type'] == "application/json":
        try:
            data = request.get_json()
        except Exception:
            return jsonify(
                result="Failure",
                status="400",
                message="The JSON is incorrectly formatted"
            ), 400
        if isinstance(data, dict):
            data = [data]
        for item in data:  # Vérification du type des données
            if validations.validate_any_csv(item):
                if validations.validate_purchase_csv(item):
                    if dates.validate_old_date(item["date"]):
                        item["date"] = dates.convert_date(item["date"])
                        if validate_purchases_numbers(item):
                            item = convert_purchases_numbers(item)
                            if validations.validate_subtotal(item) and validations.validate_tax(item):
                                transactions.purchases.insert_one(item)
                            else:
                                return jsonify(
                                    result="Failure",
                                    status="400",
                                    message="The price is incorrectly formatted"
                                ), 400
                        else:
                            return jsonify(
                                result="Failure",
                                status="400",
                                message="The numbers are incorrectly formatted"
                            ), 400
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The date is incorrectly formatted"
                        ), 400
                elif validations.validate_transformation_csv(item):
                    if dates.validate_old_date(item["date"]):
                        item["date"] = dates.convert_date(item["date"])
                        if validate_transformations_numbers(item):
                            item = convert_transformations_numbers(item)
                            transactions.transformations.insert_one(item)
                        else:
                            return jsonify(
                                result="Failure",
                                status="400",
                                message="The numbers are incorrectly formatted"
                            ), 400
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The date is incorrectly formatted"
                        ), 400
                elif validations.validate_density_csv(item):
                    if validate_densities_numbers(item):
                        item = convert_densities_numbers(item)
                        transactions.densities.insert_one(item)
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The numbers are incorrectly formatted"
                        ), 400
                else:
                    return jsonify(
                        result="Failure",
                        status="400",
                        message="The JSON is incorrectly formatted"
                    ), 400
            elif validations.validate_any(item):
                if validations.validate_purchase(item):
                    if dates.validate_new_date(item["date"]):
                        if validations.validate_subtotal(item) and validations.validate_tax(item):
                            transactions.purchases.insert_one(item)
                        else:
                            return jsonify(
                                result="Failure",
                                status="400",
                                message="The price is incorrectly formatted"
                            ), 400
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The date is incorrectly formatted"
                        ), 400
                elif validations.validate_transformation(item):
                    if dates.validate_new_date(item["date"]):
                        transactions.transformations.insert_one(item)
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The date is incorrectly formatted"
                        ), 400
                elif validations.validate_density(item):
                    transactions.densities.insert_one(item)
                else:
                    return jsonify(
                        result="Failure",
                        status="400",
                        message="The JSON is incorrectly formatted"
                    ), 400
            else:
                return jsonify(
                    result="Failure",
                    status="400",
                    message="The JSON is incorrectly formatted"
                ), 400
        return jsonify(
            result="Success",
            status="200",
            message="The JSON is correctly formatted"
        ), 200
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# Route d'API pouvant vider les collections de votre base de données. Dois être
# protégée via un mot de passe. On a les réponses retournées suivantes:
# - Code HTTP 200: si bon mot de passe.
# - Code HTTP 401: si mauvais mot de passe.
@application.route("/transactions", methods=["DELETE"])
def drop_all_collections():
    if request.headers["Content-Type"] == "application/json":
        passwd = hashlib.md5(request.get_json()["password"].encode("utf-8")).hexdigest()
        res = validations.verify_passwd(passwd)
        if res[0].json["result"] == "Success":
            # Doit dropper toutes les collections
            transactions.purchases.drop()
            transactions.transformations.drop()
            transactions.densities.drop()
        return res
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# Route d'API pouvant aller extraire toutes les transactions de votre base de données.
@application.route("/transactions", methods=["GET"])
def get_all_transactions():
    return dumps({
        "purchases": loads(create_list_purchases()),
        "transformations": loads(create_list_transformations()),
        "densities": loads(create_list_densities())
    })


# Route d'API pouvant aller extraire la transaction avec l'ID donné de votre base de données.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["GET"])
def get_one_transaction(trans_type, trans_id):
    if validations.validate_objectid(trans_id):
        ans = {}
        if trans_type == "purchases":
            ans = transactions.purchases.find_one({"_id": ObjectId(trans_id)})
        elif trans_type == "transformations":
            ans = transactions.transformations.find_one({"_id": ObjectId(trans_id)})
        elif trans_type == "densities":
            ans = transactions.densities.find_one({"_id": ObjectId(trans_id)})
        else:
            return jsonify(
                result="Failure",
                status="400",
                message="There is no sub-collection named " + trans_type
            ), 400
        if ans:
            return dumps(ans)
        else:
            return jsonify(
                result="Failure",
                status="400",
                message="A transaction with that ID doesn't exist"
            ), 400
    else:
        return jsonify(
            result="Failure",
            status="400",
            message="The ObjectId sent is invalid"
        ), 400


# Route d'API pouvant modifier la transaction avec l'ID donnée de votre base de données.
# Les opérateurs pour modifier seront donnés avant la requête HTML.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["PUT"])
def put_one_transaction(trans_type, trans_id):
    if request.headers['Content-Type'] == "application/json":
        if validations.validate_objectid(trans_id):
            try:
                data = request.get_json()
            except Exception:
                return jsonify(
                    result="Failure",
                    status="400",
                    message="The JSON is incorrectly formatted"
                ), 400
            ans = {}
            if trans_type == "purchases":
                ans = transactions.purchases.find_one({"_id": ObjectId(trans_id)})
                if ans:
                    del ans["_id"]
                    ans.update(data)
                    if validations.validate_purchase(ans):
                        if dates.validate_new_date(ans["date"]):
                            if validations.validate_subtotal(ans) and validations.validate_tax(ans):
                                transactions.purchases.update_one({"_id": ObjectId(trans_id)}, {"$set": data})
                            else:
                                return jsonify(
                                    result="Failure",
                                    status="400",
                                    message="The price is incorrectly formatted"
                                ), 400
                        else:
                            return jsonify(
                                result="Failure",
                                status="400",
                                message="The date is incorrectly formatted"
                            ), 400
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The modifications applied on the transaction are invalid"
                        ), 400
                else:
                    return jsonify(
                        result="Failure",
                        status="400",
                        message="A transaction with that ID doesn't exist"
                    ), 400
            elif trans_type == "transformations":
                ans = transactions.transformations.find_one({"_id": ObjectId(trans_id)})
                if ans:
                    del ans["_id"]
                    ans.update(data)
                    if validations.validate_transformation(ans):
                        if dates.validate_new_date(ans["date"]):
                            transactions.transformations.update_one({"_id": ObjectId(trans_id)}, {"$set": data})
                        else:
                            return jsonify(
                                result="Failure",
                                status="400",
                                message="The date is incorrectly formatted"
                            ), 400
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The modifications applied on the transaction are invalid"
                        ), 400
                else:
                    return jsonify(
                        result="Failure",
                        status="400",
                        message="A transaction with that ID doesn't exist"
                    ), 400
            elif trans_type == "densities":
                ans = transactions.densities.find_one({"_id": ObjectId(trans_id)})
                if ans:
                    del ans["_id"]
                    ans.update(data)
                    if validations.validate_density(ans):
                        transactions.densities.update_one({"_id": ObjectId(trans_id)}, {"$set": data})
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The modifications applied on the transaction are invalid"
                        ), 400
                else:
                    return jsonify(
                        result="Failure",
                        status="400",
                        message="A transaction with that ID doesn't exist"
                    ), 400
            else:
                return jsonify(
                    result="Failure",
                    status="400",
                    message="There is no sub-collection named " + trans_type
                ), 400
        else:
            return jsonify(
                result="Failure",
                status="400",
                message="The ObjectId sent is invalid"
            ), 400
        return jsonify(
            result="Success",
            status="200",
            message="The transaction with that ID was successfully modified"
        ), 200
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# Route d'API pouvant supprimer la transaction avec l'ID donnée de votre base de données.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["DELETE"])
def delete_one_transaction(trans_type, trans_id):
    if validations.validate_objectid(trans_id):
        ans = {}
        if trans_type == "purchases":
            ans = transactions.purchases.find_one_and_delete({"_id": ObjectId(trans_id)})
        elif trans_type == "transformations":
            ans = transactions.transformations.find_one_and_delete({"_id": ObjectId(trans_id)})
        elif trans_type == "densities":
            ans = transactions.densities.find_one_and_delete({"_id": ObjectId(trans_id)})
        else:
            return jsonify(
                result="Failure",
                status="400",
                message="There is no sub-collection named " + trans_type
            ), 400
        if ans:
            return jsonify(
                result="Success",
                status="200",
                message="The transaction with that ID was successfully deleted"
            ), 200
        else:
            return jsonify(
                result="Failure",
                status="400",
                message="A transaction with that ID doesn't exist"
            ), 400
    else:
        return jsonify(
            result="Failure",
            status="400",
            message="The ObjectId sent is invalid"
        ), 400


# ---------- Fonctions ----------


# Le coût total à une date précise pour une catégorie de matériel.
@application.route("/total_cost/<date>/<category>/<tax>")
def total_cost(date, category="Consumable", tax=True):
    if tax is True or tax == "true":
        tax_field = "$total"
    elif tax is False or tax == "false":
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "item": {"$regex": category, "$options": ""}}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field}},
        {"$group": {"_id": "$item", "total cost": {"$sum": "$cost"}}},
        {"$project": {"_id": 0, "item": "$_id", "total cost": "$total cost"}},
        {"$sort": {"item": 1}}
    ]
    req = list(transactions.purchases.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Success",
            status="204",
            message="There are no transactions with the given date and category"
        ), 204
    else:
        ans = {}
        # Détection de la catégorie
        ans["category"] = commons.detect_category(req)
        # Sommation des coûts
        ans["total cost"] = 0
        for item in req:
            ans["total cost"] += item["total cost"]
        ans["total cost"] = round(ans["total cost"], 2)
        # Ajout de l'unité
        ans["unit"] = "$"
        return dumps(ans)


# Le coût moyen d'acquisition, pondéré par l'unité d'acquisition,
# à une date précise d'une catégorie de matériel.
@application.route("/avg_cost_buy/<date>/<category>/<tax>")
def avg_cost_buy(date, category="Consumable", tax=True):
    if tax is True or tax == "true":
        tax_field = "$total"
    elif tax is False or tax == "false":
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "item": {"$regex": category, "$options": ""}}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field, "qte": "$qte", "unit": "$unit"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"},
                    "total cost": {"$sum": "$cost"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit",
                      "total cost": 1, "total qte": 1}}
    ]
    req = list(transactions.purchases.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Success",
            status="204",
            message="There are no transactions with the given date and category"
        ), 204
    else:
        # Vérification qu'on a pas deux fois le même 'item', sinon sommation
        ans = []
        for bought in req:
            # Verifier ici si l'élément est déjà dans 'ans', sinon ignore
            is_added = commons.get_index_of(ans, bought["item"])
            if is_added == -1:
                ans.append(bought)
            else:
                masse_volumique = get_item_density(bought["item"])
                if ans[is_added]["unit"] == bought["unit"]:
                    ans[is_added]["total cost"] += bought["total cost"]
                    ans[is_added]["total qte"] += bought["total qte"]
                elif bought["unit"] == "ml":
                    ans[is_added]["total cost"] += bought["total cost"]
                    ans[is_added]["total qte"] += bought["total qte"] * masse_volumique
                elif bought["unit"] == "g":
                    ans[is_added]["total cost"] += bought["total cost"]
                    ans[is_added]["total qte"] += bought["total qte"] / masse_volumique
        # Calcul des coûts moyens
        for item in ans:
            item["avg cost"] = round(item["total cost"] / item["total qte"], 6)
            del item["total cost"]
            del item["total qte"]
            unit = "$/" + item["unit"]
            del item["unit"]
            item["unit"] = unit
        # Vider la list req
        del req[:]
        return dumps(ans)


# Le coût moyen d'acquisition, pondéré par l'unité d'utilisation,
# à une date précise d'une catégorie de matériel.
@application.route("/avg_cost_use/<date>/<category>/<tax>")
def avg_cost_use(date, category="Consumable", tax=True):
    req = loads(avg_cost_buy(date, category, tax))
    if not req:
        return jsonify(
            result="Success",
            status="204",
            message="There are no transactions with the given date and category"
        ), 204
    else:
        # Convertir en unité d'utilisation
        ans = convert_unit_to_use_avg(req)
        return dumps(ans)


# L'image à une date précise de la quantité restante, en unité d'utilisation,
# des matières premières.
@application.route("/image/<date>")
def image(date):
    # Calculer la quantité de matériaux achetées
    pipeline_buy = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "total qte": "$total qte", "unit": "$_id.unit"}}
    ]
    req_buy = list(transactions.purchases.aggregate(pipeline_buy))

    # Calculer la quantité de matériaux utilisées
    pipeline_use = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "type": "usage"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "total qte": "$total qte", "unit": "$_id.unit"}}
    ]
    req_use = list(transactions.transformations.aggregate(pipeline_use))

    if not req_buy and not req_use:
        return jsonify(
            result="Success",
            status="204",
            message="There are no transactions with the given date or before it"
        ), 204
    else:
        # Calculer la quantité de matériaux restants après utilisation
        ans = []
        for bought in req_buy:
            # Verifier ici si l'élément est déjà dans 'ans', sinon l'ajouter dans 'ans'
            is_added = commons.get_index_of(ans, bought["item"])
            if is_added == -1:
                ans.append(bought)
            else:
                # On ne change pas l'unité dans cas-ci
                if ans[is_added]["unit"] == bought["unit"]:
                    ans[is_added]["total qte"] += bought["total qte"]
                else:
                    masse_volumique = get_item_density(bought["item"])
                    if bought["unit"] == "ml":
                        ans[is_added]["total qte"] += bought["total qte"] * masse_volumique
                    elif bought["unit"] == "g":
                        ans[is_added]["total qte"] += bought["total qte"] / masse_volumique
                    else:
                        return jsonify(
                            result="Failure",
                            status="400",
                            message="The unit of this item is invalid (neither g nor ml)"
                        ), 400
            ans[is_added]["total qte"] = round(ans[is_added]["total qte"])
        # Vider la list req_buy
        del req_buy[:]
        for used in req_use:
            # Si l'item n'a jamais été achetée, on doit l'ajouter, puis inverser la qte
            is_added = commons.get_index_of(ans, used["item"])
            if is_added == -1:
                ans.append(used)
                ans[-1]["total qte"] = -1 * used["total qte"]
            else:
                if ans[is_added]["item"] == used["item"]:
                    # Soustraire la quantité utilisé de l'élément dans 'ans'
                    if ans[is_added]["unit"] != used["unit"]:
                        # On change l'unité dans ce cas-ci
                        masse_volumique = get_item_density(used["item"])
                        ans[is_added]["unit"] = used["unit"]
                        if ans[is_added]["unit"] == "ml":
                            ans[is_added]["total qte"] /= masse_volumique
                        elif ans[is_added]["unit"] == "g":
                            ans[is_added]["total qte"] *= masse_volumique
                    ans[is_added]["total qte"] -= used["total qte"]
            ans[is_added]["total qte"] = round(ans[is_added]["total qte"])
        # Vider la list req_use
        del req_use[:]
        # Convertir en unité d'utilisation
        ans = convert_unit_to_use_img(ans)
        return dumps(ans)


# Retourne une liste contenant seulement les éléments Purchase
def create_list_purchases():
    return dumps(transactions.purchases.find())


# Retourne une liste contenant seulement les éléments Transformation
def create_list_transformations():
    return dumps(transactions.transformations.find())


# Retourne une liste contenant seulement les éléments Density
def create_list_densities():
    return dumps(transactions.densities.find())


# Donne la liste de l'unité d'acquisition des items
def get_purchases_units():
    pipeline = [
        {"$group": {"_id": "$item", "units": {"$addToSet": "$unit"}}},
        {"$project": {"_id": 0, "item": "$_id",
                      "unit": {"$cond": [{"$gt": [{"$size": "$units"}, 1]}, "both", {"$arrayElemAt": ["$units", 0]}]}}},
        {"$sort": {"item": 1}}
    ]
    req = transactions.purchases.aggregate(pipeline)
    return list(req)


# Donne la liste de l'unité d'utilisation des items
def get_transformations_units():
    pipeline = [
        {"$match": {"type": "usage"}},
        {"$group": {"_id": "$item", "units": {"$addToSet": "$unit"}}},
        {"$project": {"_id": 0, "item": "$_id",
                      "unit": {"$cond": [{"$gt": [{"$size": "$units"}, 1]}, "both", {"$arrayElemAt": ["$units", 0]}]}}},
        {"$sort": {"item": 1}}
    ]
    req = transactions.transformations.aggregate(pipeline)
    return list(req)


# Convertie toutes les string(number) en number de transactions.purchases
def convert_purchases_numbers(item):
    item["qte"] = int(item["qte"])
    item["total"] = float(item["total"])
    item["stotal"] = float(item["stotal"])
    item["tax"] = float(item["tax"])
    return item


# Convertie toutes les string(number) en number de transactions.transformations
def convert_transformations_numbers(item):
    item["qte"] = int(item["qte"])
    item["job_id"] = int(item["job_id"])
    return item


# Convertie toutes les string(number) en number de transactions.densities
def convert_densities_numbers(item):
    item["g"] = float(item["g"])
    item["ml"] = float(item["ml"])
    return item


# Valider si tous les nombres de Purchases sont valides
def validate_purchases_numbers(item):
    try:
        w = int(item["qte"])
        x = float(item["total"])
        y = float(item["stotal"])
        z = float(item["tax"])
        return True
    except ValueError:
        return False


# Valider si tous les nombres de Transformations sont valides
def validate_transformations_numbers(item):
    try:
        x = int(item["qte"])
        y = int(item["job_id"])
        return True
    except ValueError:
        return False


# Valider si tous les nombres de Densities sont valides
def validate_densities_numbers(item):
    try:
        x = float(item["g"])
        y = float(item["ml"])
        return True
    except ValueError:
        return False


# Retourne une liste contenant tous les items
def list_all_items():
    req = transactions.purchases.distinct("item")
    req.extend(transactions.transformations.distinct("item"))
    return list(set(req))


# Retourne une liste contenant tous les items avec plusieurs unités possibles
def list_all_many_units_items():
    req = transactions.densities.distinct("item")
    return list(set(req))


# Retourne une liste contenant tous les items avec une seule unité possible
def list_all_single_unit_items():
    return list(set(list_all_items()) - set(list_all_many_units_items()))


# Retourne la masse volumique d'un élément
def get_item_density(item):
    # Devra être refait en évitant d'hardcoder les lignes de code comme "if 'Base Oil' in item"
    if item not in list_all_many_units_items():
        if "Base Oil" in item:
            ans = transactions.densities.find_one({"item": "Consumable - Base Oil"})
        else:
            return jsonify(
                result="Success",
                status="204",
                message="There are no density for this item"
            ), 204
    else:
        ans = transactions.densities.find_one({"item": item})
    density = ans["g"] / ans["ml"]
    return density


# Convertit les unités des items 'avg' en leur unité d'utilisation
def convert_unit_to_use_avg(array):
    units = get_transformations_units()
    for item in array:
        if item["item"] in list_all_many_units_items() or "Base Oil" in item["item"]:
            index_unit = commons.get_index_of(units, item["item"])
            if index_unit != -1:
                if item["unit"] != "$/" + units[index_unit]["unit"] and not units[index_unit]["unit"] == "both":
                    # On change l'unité dans ce cas-ci
                    masse_volumique = get_item_density(item["item"])
                    item["unit"] = "$/" + units[index_unit]["unit"]
                    if units[index_unit]["unit"] == "ml":
                        item["avg cost"] *= masse_volumique
                    elif units[index_unit]["unit"] == "g":
                        item["avg cost"] /= masse_volumique
            elif index_unit == -1 and "Base Oil" in item["item"] and item["unit"] != "$/ml":
                masse_volumique = get_item_density(item["item"])
                item["unit"] = "$/ml"
                item["avg cost"] *= masse_volumique
            item["avg cost"] = round(item["avg cost"], 6)
    return array


# Convertit les unités des items 'image' en leur unité d'utilisation
def convert_unit_to_use_img(array):
    units = get_transformations_units()
    for item in array:
        if item["item"] in list_all_many_units_items() or "Base Oil" in item["item"]:
            index_unit = commons.get_index_of(units, item["item"])
            if index_unit != -1:
                if item["unit"] != units[index_unit]["unit"] and not units[index_unit]["unit"] == "both":
                    # On change l'unité dans ce cas-ci
                    masse_volumique = get_item_density(item["item"])
                    item["unit"] = units[index_unit]["unit"]
                    if units[index_unit]["unit"] == "ml":
                        item["total qte"] /= masse_volumique
                    elif units[index_unit]["unit"] == "g":
                        item["total qte"] *= masse_volumique
            elif index_unit == -1 and "Base Oil" in item["item"] and item["unit"] != "ml":
                masse_volumique = get_item_density(item["item"])
                item["unit"] = "ml"
                item["total qte"] /= masse_volumique
            item["total qte"] = round(item["total qte"])
    return array


# ---------- Exécution ----------

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
