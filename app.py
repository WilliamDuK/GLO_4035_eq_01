from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
from bson.json_util import dumps
import hashlib


application = Flask("my_glo4035_application")
application.config["JSON_SORT_KEYS"] = False
application.config["MONGO_URI"] = "mongodb://127.0.0.1:27017/mySystem"
mongo = PyMongo(application)
transactions = mongo.db.transactions


# md5(abc12345) = d6b0ab7f1c8ab8f514db9a6d85de160a
MD5_HASHED_PASSWORD = "d6b0ab7f1c8ab8f514db9a6d85de160a"


# ----- Interface Graphique -----


# Contient une interface graphique permettant d'afficher:
# - Le coût total à unedate précise pour une catégorie de matériel.
# - Le coût moyen d'acquisition, pondéré par l'unité d'acquisiton, à une date
#   précise d'une catégorie de matériel.
# - L'image à une date précise de la quantité restante, en unité d'utilisation,
#   des matières premières.


# Contient une interface (API ou Graphique) permettant d'ajouter, modifier ou
# supprimer une transaction.


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
        if verify_json(data):
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


def verify_transaction(item):
    return True


def verify_json(data):
    if isinstance(data, list):
        for i in range(len(data)):
            if not(verify_transaction(data[i])):
                return False
    elif isinstance(data, dict):
        if not(verify_transaction(data)):
            return False
    else:
        return False
    return True


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


# ---------- Exécution ----------


if __name__ == "__main__":
    application.run(host="127.0.0.1", port=80)
