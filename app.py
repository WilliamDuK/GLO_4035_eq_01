from flask import Flask, jsonify, request, render_template
from flask_pymongo import PyMongo
import hashlib


application = Flask("my_glo4035_application")
application.config["JSON_SORT_KEYS"] = False
application.config["MONGO_URI"] = "mongodb://127.0.0.1:27017/mySystem"
mongo = PyMongo(application)
inv = mongo.db.inventory


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
def correction_add():
    if request.headers['Content-Type'] == "application/json":
        data = request.get_json()
        if verify_json(data):  # Trouver un moyen de détecter la structure du JSON
            inv.insert(data)
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
def correction_drop():
    if request.headers['Content-Type'] == "application/json":
        passwd = hashlib.md5(request.get_json()["password"].encode("utf-8")).hexdigest()
        res = verify_passwd(passwd)
        if res[0].json["result"] == "Success":
            inv.drop()
        return res
    return jsonify(
        result="Failure",
        status="405",
        message="The wrong type of content was sent"
    ), 405


# ---------- Fonctions ----------


def verify_json(data):
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
