from flask import Flask
application = Flask("my_glo4035_application")


@application.route("/", methods=["GET", "POST"])
def index():

    return "Oh yeah"


if __name__ == "__main__":
    application.run(host="0.0.0.0", port=80)
