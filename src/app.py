from pymongo import MongoClient
from neo4j import GraphDatabase

mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["mydatabase"]

neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test"))

from flask import Flask
app = Flask(__name__)
