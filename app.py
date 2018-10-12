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
        },
        "information": {
            "type": "string"
        },
        "g": {
            "type": "number"
        },
        "ml": {
            "type": "number"
        }
    },
    "required": ["item"],
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
DENSITY_SCHEMA = {
    "properties": {
        "information": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "g": {
            "type": "number"
        },
        "ml": {
            "type": "number"
        }
    },
    "required": ["information", "item", "g", "ml"],
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
    # test1 = total_cost_given_date_and_category("5 January 2018", "Base Oil")
    # test2 = avg_cost_weighted_by_unit_get_given_date_and_category("5 January 2018", "Base Oil")
    # test3 = avg_cost_weighted_by_unit_use_given_date_and_category("5 January 2018", "Base Oil")
    # test4 = image_of_leftover_quantity_in_unit_of_raw_material_given_date("5 January 2018")
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

# Vérification du mot de passe permettant l'accès au vidage de toutes les collections
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


# Vérification de chacun des documents JSON un à la fois
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


# Vérifie si l'objet reçu en paramètre est Transaction
def validate_transaction(item):
    try:
        validate(item, TRANSACTION_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Purchase
def validate_purchase(item):
    try:
        validate(item, PURCHASE_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Transform
def validate_transform(item):
    try:
        validate(item, TRANSFORM_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Density
def validate_density(item):
    try:
        validate(item, DENSITY_SCHEMA)
    except ValidationError:
        return False
    else:
        return True


# Le coût total à une date précise pour une catégorie de matériel.
def total_cost_given_date_and_category(date, category="Consumable", tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": convert_date(date)}, "item": {"$regex": category, "$options": ""}, "job_id": None}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field}},
        {"$group": {"_id": "$item", "total cost": {"$sum": "$cost"}}},
        {"$project": {"_id": 0, "item": "$_id", "total cost": 1}}
    ]
    req = list(transactions.aggregate(pipeline))
    if not req:
        return jsonify(
            result="Failure",
            status="400",
            message="There are no transactions with the given date and category"
        ), 400
    else:
        ans = []
        for bought in req:
            ans.append(bought)
            ans[-1]["unit"] = "$"
        return ans


# Le coût moyen d'acquisition, pondéré par l'unité d'acquisition,
# à une date précise d'une catégorie de matériel.
def avg_cost_weighted_by_unit_get_given_date_and_category(date, category="Consumable", tax=True):
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    pipeline = [
        {"$match": {"date": {"$lte": convert_date(date)}, "item": {"$regex": category, "$options": ""}, "job_id": None}},
        {"$project": {"_id": 0, "item": 1, "cost": tax_field, "qte": "$qte", "unit": "$unit"}},
        {"$group": {"_id": {"item": "$item", "unit": "$unit"},
                    "total cost": {"$sum": "$cost"}, "total qte": {"$sum": "$qte"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": "$_id.unit",
                      "total cost": 1, "total qte": 1}}
    ]
    req = list(transactions.aggregate(pipeline))
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
            is_added = get_item_index(ans, bought["item"])
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
    if tax:
        tax_field = "$total"
    else:
        tax_field = "$stotal"
    req_buy = avg_cost_weighted_by_unit_get_given_date_and_category(date, category, tax)
    pipeline = [
        {"$match": {"item": {"$regex": category, "$options": ""}, "tax": None,
                    "unit": {"$ne": "unit"}}},
        {"$project": {"_id": 0, "item": 1, "unit": 1}},
        {"$group": {"_id": {"item": "$item"}, "unit": {"$addToSet": "$unit"}}},
        {"$project": {"_id": 0, "item": "$_id.item", "unit": {"$arrayElemAt": ["$unit", 0]}}}
    ]
    req_use = list(transactions.aggregate(pipeline))
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
            i = get_item_index(ans, used["item"])
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
            # Verifier ici si l'élément est déjà dans 'ans', sinon ignore
            is_added = get_item_index(ans, bought["item"])
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
            is_added = get_item_index(ans, used["item"])
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
    item = transactions.find_one({"information": "density", "item": item})
    density = item["g"] / item["ml"]
    return density


# Construction de la liste des matières premières
def list_raw_materials():
    return transactions.distinct("item")


# Extrait l'index de l'item dans 'ans'
def get_item_index(ans, item):
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
            if not validate_density(item):
                item["date"] = convert_date(item["date"])
        return data
    elif isinstance(data, dict):
        if not validate_density(data):
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
