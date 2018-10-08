from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
from bson.json_util import dumps
from jsonschema import validate, ValidationError
from datetime import date
import hashlib


application = Flask("my_glo4035_application")
application.config["JSON_SORT_KEYS"] = False
application.config["MONGO_URI"] = "mongodb://127.0.0.1:27017/inventory"
mongo = PyMongo(application)
transactions = mongo.db.transactions


# md5(abc12345) = d6b0ab7f1c8ab8f514db9a6d85de160a
MD5_HASHED_PASSWORD = "d6b0ab7f1c8ab8f514db9a6d85de160a"
TRANSACTION_SCHEMA = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "number"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "number"
        },
        "stotal": {
            "type": "number"
        },
        "tax": {
            "type": "number"
        },
        "job_id": {
            "type": "number"
        },
        "type": {
            "type": "string"
        }
    },
    "required": ["date", "item", "qte", "unit"],
    "additionalProperties": False
}
PURCHASE_SCHEMA = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "number"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "number"
        },
        "stotal": {
            "type": "number"
        },
        "tax": {
            "type": "number"
        }
    },
    "required": ["date", "item", "qte", "unit", "total", "stotal", "tax"],
    "additionalProperties": False
}
TRANSFORM_SCHEMA = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "number"
        },
        "unit": {
            "type": "string"
        },
        "job_id": {
            "type": "number"
        },
        "type": {
            "type": "string"
        }
    },
    "required": ["date", "item", "qte", "unit", "job_id", "type"],
    "additionalProperties": False
}
DATE_MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]


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
def add_many_transactions():
    if request.headers['Content-Type'] == "application/json":
        data = request.get_json()
        data = update_dates_format_db(data)  # convert date to str(datetime)
        if validate_json(data):
            if isinstance(data, list):
                transactions.insert_many(data)
            elif isinstance(data, dict):
                transactions.insert_one(data)
            return jsonify(
                result="Success",
                status="200",
                message="The JSON is correctly formatted"
            ), 200
        return jsonify(
            result="Failure",
            status="400",
            message="The JSON is incorrectly formatted"
        ), 400
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
        res = verify_passwd(passwd)
        if res[0].json["result"] == "Success":
            transactions.drop()  # Doit dropper toutes les collections
        return res
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# Route d'API pouvant aller extraire toutes les transactions de votre base de données.
@application.route("/transactions", methods=["GET"])
def get_all_transactions():
    test1 = total_cost_given_date_and_category("15 July 2018", "HE")
    test2 = avg_cost_weighted_by_unit_given_date_and_category("10 September 2018", "Base Oil")
    test3 = image_of_leftover_quantity_in_unit_of_raw_material_given_date("5 January 2018")
    return dumps(transactions.find())


# Route d'API pouvant aller extraire la transaction avec l'ID donné de votre base de données.
@application.route("/transactions/<trans_id>", methods=["GET"])
def get_one_transaction(trans_id):
    ans = transactions.find_one({"_id": trans_id})
    if ans:
        return dumps(ans)
    else:
        return jsonify(
            result="Failure",
            status="400",
            message="A transaction with that ID doesn't exist"
        ), 400


# Route d'API pouvant modifier la transaction avec l'ID donnée de votre base de données.
# Les opérateurs pour modifier seront donnés avant la requête HTML.
@application.route("/entries/<trans_id>", methods=["PUT"])
def put_one_transaction(trans_id, trans_mod):
    ans = transactions.find_one({"_id": trans_id})
    if ans:
        transactions.update_one(ans, trans_mod)
        return jsonify(
            result="Success",
            status="200",
            message="The transaction with that ID was successfuly modified"
        ), 200
    else:
        return jsonify(
            result="Failure",
            status="400",
            message="A transaction with that ID doesn't exist"
        ), 400


# Route d'API pouvant supprimer la transaction avec l'ID donnée de votre base de données.
@application.route("/entries/<trans_id>", methods=["DELETE"])
def delete_one_transaction(trans_id):
    ans = transactions.find_one({"_id": trans_id})
    if ans:
        transactions.delete_one(ans)
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


# ---------- Fonctions ----------

#
def verify_passwd(password):
    if password == MD5_HASHED_PASSWORD:
        return jsonify(
            result="Success",
            status="200",
            message="Correct password"
        ), 200
    else:
        return jsonify(
            result="Failure",
            status="401",
            message="Wrong password"
        ), 401


#
def validate_json(data):
    if isinstance(data, list):
        for i in range(len(data)):
            if not(validate_transaction(data[i])):
                return False
    elif isinstance(data, dict):
        if not(validate_transaction(data)):
            return False
    else:
        return False
    return True


#
def validate_transaction(item):
    try:
        validate(item, TRANSACTION_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


#
def validate_purchase(item):
    try:
        validate(item, PURCHASE_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


#
def validate_transform(item):
    try:
        validate(item, TRANSFORM_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


# Le coût total à une date précise pour une catégorie de matériel.
def total_cost_given_date_and_category(date, category, tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": convert_date(date)}, "item": {"$regex": category, "$options": "i"}, "job_id": None}},
        {"$project": {"_id": 0, "cost": tax_field}},
        {"$group": {"_id": None, "total cost": {"$sum": "$cost"}}}
    ]
    req = list(transactions.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
    else:
        ans = str(req[0]["total cost"]) + " $"
        return ans


# Le coût moyen d'acquisition, pondéré par l'unité d'acquisition, à une date précise d'une
# catégorie de matériel.
def avg_cost_weighted_by_unit_given_date_and_category(date, category, tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": convert_date(date)}, "item": {"$regex": category, "$options": "i"}, "job_id": None}},
        {"$project": {"_id": 0, "category": "$item", "cost": tax_field, "qte": "$qte", "unit": "$unit"}},
        {"$group": {"_id": {"category": "$category", "unit": "$unit"},
                    "total cost": {"$sum": "$cost"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "category": "$_id.category", "unit": "$_id.unit",
                      "avg cost": {"$divide": ["$total cost", "$total qte"]}}},
        # On requis la masse volumique des matières premières ici
    ]
    req = list(transactions.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
    else:
        ans = str(req[0]["avg cost"]) + " $/" + req[0]["unit"]
        return ans


# L'image à une date précise de la quantité restante, en unité d'utilisation,
# des matières premières.
def image_of_leftover_quantity_in_unit_of_raw_material_given_date(date):
    # Calculer la quantité de matériaux achetées
    pipeline_buy = [
        {"$match": {"date": {"$lte": convert_date(date)}, "job_id": None}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit", "total qte": "$total qte"}}
    ]
    req_buy = list(transactions.aggregate(pipeline_buy))

    # Calculer la quantité de matériaux utilisées
    pipeline_use = [
        {"$match": {"date": {"$lte": convert_date(date)}, "tax": None, "type": "usage"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit", "total qte": "$total qte"}}
    ]
    req_use = list(transactions.aggregate(pipeline_use))

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
            for used in req_use:
                if bought["item"] == used["item"]:
                    # Verifier ici si l'élément est déjà dans 'ans', sinon ignore
                    is_added = index_of_item(ans, bought["item"])
                    if is_added == -1:
                        ans.append(bought)
                    # On doit être certain que 'ans' est accéder depuis le field 'item'
                    i = index_of_item(ans, bought["item"])
                    if bought["unit"] == used["unit"]:
                        # Soustraire la quantité utilisé de l'élément dans 'ans'
                        ans[i]["total qte"] -= used["total qte"]
                    else:
                        masse_volumique = 0.9  # À corriger à l'aide de masse volumique
                        ans[i]["unit"] = used["unit"]
                        if used["unit"] == "ml":
                            ans[i]["total qte"] -= used["total qte"] * masse_volumique
                        elif used["unit"] == "g":
                            ans[i]["total qte"] -= used["total qte"] / masse_volumique
        return ans


# Construction de la liste des matières premières
def list_raw_materials():
    return transactions.distinct("item")


# Extrait l'index de l'item dans 'ans'
def index_of_item(ans, item):
    if len(ans) != 0:
        i = 0
        for element in ans:
            if element["item"] == item:
                return i
            i += 1
    return -1


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


# Met à jour le format des dates dans la base de données
def update_dates_format_db(data):
    if isinstance(data, list):
        for item in data:
            item["date"] = convert_date(item["date"])
        return data
    elif isinstance(data, dict):
        data["date"] = convert_date(data["date"])
        return data
    else:
        return jsonify(
            result="Failure",
            status="405",
            message="The wrong type of content was sent"
        ), 405


# ---------- Exécution ----------

if __name__ == "__main__":
    application.run(host="127.0.0.1", port=80)
