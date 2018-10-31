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
        data = request.get_json()
        if isinstance(data, dict):
            data = [data]
        for item in data:  # Vérification du type des données
            if validations.validate_transaction(item):
                if not validations.validate_density(item):
                    item["date"] = dates.convert_date(item["date"])
                if validations.validate_purchase(item):
                    transactions.purchases.insert_one(item)
                elif validations.validate_transformation(item):
                    transactions.transformations.insert_one(item)
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
        )
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
    # test1 = total_cost_given_date_and_category("5 January 2018", "Base Oil")
    # test2 = avg_cost_weighted_by_unit_get_given_date_and_category("5 January 2018", "Base Oil")
    # test3 = avg_cost_weighted_by_unit_use_given_date_and_category("5 January 2018", "Base Oil")
    # test4 = image_of_leftover_quantity_in_unit_of_raw_material_given_date("5 January 2018")
    return dumps({
        "purchases": loads(create_list_purchases()),
        "transformations": loads(create_list_transformations()),
        "densities": loads(create_list_densities())
    })


# Route d'API pouvant aller extraire la transaction avec l'ID donné de votre base de données.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["GET"])
def get_one_transaction(trans_type, trans_id):
    if validations.validate_objectid(trans_id):
        if trans_type == "purchases":
            ans = transactions.purchases.find_one({"_id": ObjectId(trans_id)})
        elif trans_type == "transformations":
            ans = transactions.transformations.find_one({"_id": ObjectId(trans_id)})
        elif trans_type == "densities":
            ans = transactions.densities.find_one({"_id": ObjectId(trans_id)})
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
            status="405",
            message="The ObjectId sent is not valid"
        ), 405


# Route d'API pouvant modifier la transaction avec l'ID donnée de votre base de données.
# Les opérateurs pour modifier seront donnés avant la requête HTML.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["PUT"])
def put_one_transaction(trans_type, trans_id):
    if request.headers['Content-Type'] == "application/json":
        if validations.validate_objectid(trans_id):
            data = request.get_json()
            if trans_type == "purchases":
                ans = transactions.purchases.find_one_and_update({"_id": ObjectId(trans_id)}, {"$set": data})
            elif trans_type == "transformations":
                ans = transactions.transformations.find_one_and_update({"_id": ObjectId(trans_id)}, {"$set": data})
            elif trans_type == "densities":
                ans = transactions.densities.find_one_and_update({"_id": ObjectId(trans_id)}, {"$set": data})
            if ans:
                return jsonify(
                    result="Success",
                    status="200",
                    message="The transaction with that ID was successfully modified"
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
                status="405",
                message="The ObjectId sent is not valid"
            ), 405
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# Route d'API pouvant supprimer la transaction avec l'ID donnée de votre base de données.
@application.route("/transactions/<trans_type>/<trans_id>", methods=["DELETE"])
def delete_one_transaction(trans_type, trans_id):
    if validations.validate_objectid(trans_id):
        if trans_type == "purchases":
            ans = transactions.purchases.find_one_and_delete({"_id": ObjectId(trans_id)})
        elif trans_type == "transformations":
            ans = transactions.transformations.find_one_and_delete({"_id": ObjectId(trans_id)})
        elif trans_type == "densities":
            ans = transactions.densities.find_one_and_delete({"_id": ObjectId(trans_id)})
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
            status="405",
            message="The ObjectId sent is not valid"
        ), 405


# ---------- Fonctions ----------


# Le coût total à une date précise pour une catégorie de matériel.
def total_cost_given_date_and_category(date, category="Consumable", tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "item": {"$regex": category, "$options": "i"}}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field}},
        {"$group": {"_id": "$item", "total cost": {"$sum": "$cost"}}},
        {"$project": {"_id": 0, "item": "$_id", "total cost": 1, "unit": {"$literal": "$"}}}
    ]
    req = list(transactions.purchases.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
    else:
        return req


# Le coût moyen d'acquisition, pondéré par l'unité d'acquisition,
# à une date précise d'une catégorie de matériel.
def avg_cost_weighted_by_unit_get_given_date_and_category(date, category="Consumable", tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "item": {"$regex": category, "$options": "i"}}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field, "qte": "$qte", "unit": "$unit"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"},
                    "total cost": {"$sum": "$cost"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit",
                      "total cost": 1, "total qte": 1}}
    ]
    req = list(transactions.purchases.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
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
            item["avg cost"] = round(item["total cost"] / item["total qte"], 2)
            del item["total cost"]
            del item["total qte"]
            item["unit"] = "$/" + item["unit"]
        # Vider la list req
        del req[:]
        return ans


# Le coût moyen d'acquisition, pondéré par l'unité d'utilisation,
# à une date précise d'une catégorie de matériel.
def avg_cost_weighted_by_unit_use_given_date_and_category(date, category="Consumable", tax=True):
    req_buy = avg_cost_weighted_by_unit_get_given_date_and_category(date, category, tax)
    pipeline = [
        {"$match": {"item": {"$regex": category, "$options": ""}, "unit": {"$ne": "unit"}}},
        {"$project": {"_id": 0, "item": 1, "unit": 1}},
        {"$group": {"_id": {"item": "$item"}, "unit": {"$addToSet": "$unit"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": {"$arrayElemAt": ["$unit", 0]}}}
    ]
    req_use = list(transactions.transformations.aggregate(pipeline))
    if not req_buy or not req_use:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
    else:
        ans = req_buy
        for used in req_use:
            # Verifier ici si l'élément est déjà dans 'ans', sinon ignore
            i = commons.get_index_of(ans, used["item"])
            if i != -1:
                if ans[i]["unit"] != "$/" + used["unit"]:
                    masse_volumique = get_item_density(used["item"])
                    ans[i]["unit"] = "$/" + used["unit"]
                    if used["unit"] == "$/ml":
                        ans[i]["avg cost"] /= masse_volumique
                    elif used["unit"] == "$/g":
                        ans[i]["avg cost"] *= masse_volumique
        return ans


# L'image à une date précise de la quantité restante, en unité d'utilisation,
# des matières premières.
def image_of_leftover_quantity_in_unit_of_raw_material_given_date(date):
    # Calculer la quantité de matériaux achetées
    pipeline_buy = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit", "total qte": "$total qte"}}
    ]
    req_buy = list(transactions.purchases.aggregate(pipeline_buy))

    # Calculer la quantité de matériaux utilisées
    pipeline_use = [
        {"$match": {"date": {"$lte": dates.convert_date(date)}, "type": "usage"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit", "total qte": "$total qte"}}
    ]
    req_use = list(transactions.transformations.aggregate(pipeline_use))

    if not req_buy or not req_use:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date or before it"
        ), 400
    else:
        # Calculer la quantité de matériaux restants après utilisation
        ans = []
        for bought in req_buy:
            # Verifier ici si l'élément est déjà dans 'ans', sinon ignore
            is_added = commons.get_index_of(ans, bought["item"])
            if is_added == -1:
                ans.append(bought)
            else:
                masse_volumique = get_item_density(bought["item"])
                if ans[is_added]["unit"] == bought["unit"]:
                    ans[is_added]["total qte"] += bought["total qte"]
                elif bought["unit"] == "ml":
                    ans[is_added]["total qte"] += bought["total qte"] * masse_volumique
                elif bought["unit"] == "g":
                    ans[is_added]["total qte"] += bought["total qte"] / masse_volumique
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
                    if ans[is_added]["unit"] == used["unit"]:
                        ans[is_added]["total qte"] -= used["total qte"]
                    else:
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
        return ans


# Retourne la masse volumique d'un élément
def get_item_density(item):
    item = transactions.densities.find_one({"information": "density", "item": item})
    density = item["g"] / item["ml"]
    return density


# Retourne une liste contenant seulement les éléments Purchase
def create_list_purchases():
    return dumps(transactions.purchases.find())


# Retourne une liste contenant seulement les éléments Transformation
def create_list_transformations():
    return dumps(transactions.transformations.find())


# Retourne une liste contenant seulement les éléments Density
def create_list_densities():
    return dumps(transactions.densities.find())


# ---------- Exécution ----------

if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
