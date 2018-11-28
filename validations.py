#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import jsonify
from jsonschema import validate, ValidationError
from bson.objectid import ObjectId, InvalidId


MD5_HASHED_PASSWORD = "d6b0ab7f1c8ab8f514db9a6d85de160a"
ANY_SCHEMA = {
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
        "Information": {
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
TRANSFORMATION_SCHEMA = {
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
        "Information": {
            "type": "string"
        },
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
    "required": ["item", "g", "ml"],
    "additionalProperties": False
}
ANY_SCHEMA_CSV = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "string"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "string"
        },
        "stotal": {
            "type": "string"
        },
        "tax": {
            "type": "string"
        },
        "job_id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        },
        "Information": {
            "type": "string"
        },
        "information": {
            "type": "string"
        },
        "g": {
            "type": "string"
        },
        "ml": {
            "type": "string"
        }
    },
    "required": ["item"],
    "additionalProperties": False
}
PURCHASE_SCHEMA_CSV = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "string"
        },
        "unit": {
            "type": "string"
        },
        "total": {
            "type": "string"
        },
        "stotal": {
            "type": "string"
        },
        "tax": {
            "type": "string"
        }
    },
    "required": ["date", "item", "qte", "unit", "total", "stotal", "tax"],
    "additionalProperties": False
}
TRANSFORMATION_SCHEMA_CSV = {
    "properties": {
        "date": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "qte": {
            "type": "string"
        },
        "unit": {
            "type": "string"
        },
        "job_id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        }
    },
    "required": ["date", "item", "qte", "unit", "job_id", "type"],
    "additionalProperties": False
}
DENSITY_SCHEMA_CSV = {
    "properties": {
        "Information": {
            "type": "string"
        },
        "information": {
            "type": "string"
        },
        "item": {
            "type": "string"
        },
        "g": {
            "type": "string"
        },
        "ml": {
            "type": "string"
        }
    },
    "required": ["item", "g", "ml"],
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
def validate_any(item):
    try:
        validate(item, ANY_SCHEMA)
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


# Vérifie si l'objet reçu en paramètre est Transaction
def validate_any_csv(item):
    try:
        validate(item, ANY_SCHEMA_CSV)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Purchase
def validate_purchase_csv(item):
    try:
        validate(item, PURCHASE_SCHEMA_CSV)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Transform
def validate_transformation_csv(item):
    try:
        validate(item, TRANSFORMATION_SCHEMA_CSV)
    except ValidationError:
        return False
    else:
        return True


# Vérifie si l'objet reçu en paramètre est Density
def validate_density_csv(item):
    try:
        validate(item, DENSITY_SCHEMA_CSV)
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


# Vérifie si 'total' => 'stotal'
def validate_subtotal(data):
    if data["total"] >= data["stotal"]:
        return True
    else:
        return False


# Vérifie si 'tax' = 'total' - 'stotal'
def validate_tax(data):
    tax_temp = data["total"] - data["stotal"]
    if data["tax"] - 0.01 <= round(tax_temp, 2) <= data["tax"] + 0.01 \
            or data["tax"] - 0.01 <= tax_temp <= data["tax"] + 0.01:
        return True
    else:
        return False
