#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import jsonify
from jsonschema import validate, ValidationError
from bson.objectid import ObjectId, InvalidId


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
            "type": "string"  # "number"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "string"  # "number"
        },
        "stotal": {
            "type": "string"  # "number"
        },
        "tax": {
            "type": "string"  # "number"
        },
        "job_id": {
            "type": "string"  # "number"
        },
        "type": {
            "type": "string"
        },
        "Information": {
            "type": "string"
        },
        "g": {
            "type": "string"  # "number"
        },
        "ml": {
            "type": "string"  # "number"
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
            "type": "string"  # "number"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "string"  # "number"
        },
        "stotal": {
            "type": "string"  # "number"
        },
        "tax": {
            "type": "string"  # "number"
        }
    },
    "required": ["date", "item", "qte", "unit", "total", "stotal", "tax"],
    "additionalProperties": False
}
TRANSFORMATION_SCHEMA = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "string"  # "number"
        },
        "unit": {
            "type": "string"
        },
        "job_id": {
            "type": "string"  # "number"
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
        "Information": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "g": {
            "type": "string"  # "number"
        },
        "ml": {
            "type": "string"  # "number"
        }
    },
    "required": ["Information", "item", "g", "ml"],
    "additionalProperties": False
}


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
def validate_transformation(item):
    try:
        validate(item, TRANSFORMATION_SCHEMA)
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


# Vérifie si l'ObjectId est valide
def validate_objectid(oid):
    try:
        ObjectId(oid)
        return True
    except (InvalidId, TypeError):
        return False
