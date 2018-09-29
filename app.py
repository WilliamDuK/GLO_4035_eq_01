from flask import Flask
application = Flask("my_glo4035_application")


# Route d'API accueillant les utilisateurs.
@application.route("/", methods=["GET", "POST"])
def index():
    return "Oh yeah"


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


# Contient une interface graphique permettant d'afficher:
# - Le coût total à unedate précise pour une catégorie de matériel.
# - Le coût moyen d'acquisition, pondéré par l'unité d'acquisiton, à une date
#   précise d'une catégorie de matériel.
# - L'image à une date précise de la quantité restante, en unité d'utilisation,
#   des matières premières.


# Contient une interface (API ou Graphique) permettant d'ajouter, modifier ou
# supprimer une transaction.


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
