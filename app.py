from flask import Flask, jsonify
# import pymongo
# import flask_pymongo
application = Flask("my_glo4035_application")


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
    return "Graphic interface goes here!"


# Route d'API pouvant recevoir et persister les transactions envoyés par une
# application web. On a les réponses retournées suivantes:
# - Code HTTP 200: JSON bien formaté.
# - Code HTTP 400: JSON mal formaté.
@application.route("/transactions", methods=["POST"])
def correction_add():
    return ""


# Route d'API pouvant vider les collections de votre base de données. Dois être
# protégée via un mot de passe. On a les réponses retournées suivantes:
# - Code HTTP 200: si bon mot de passe.
# - Code HTTP 401: si mauvais mot de passe.
@application.route("/transactions", methods=["DELETE"])
def correction_drop():
    return ""


# ---------- Fonctions ----------


def verify_passwd(data):
    if data.password == "abc12345":
        return jsonify({"result": "success", "status": "200",
                        "message": "Correct password."}), 200
    else:
        return jsonify({"result": "failure", "status": "401",
                        "message": "Wrong password."}), 401


# ---------- Exécution ----------


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
