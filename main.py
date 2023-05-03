import argparse
import os
import json
import csv
import sys

from elasticsearch import Elasticsearch
from PyQt6.QtWidgets import QApplication

from es_client import ESClient
from GUI import MyWidget
from searcher import Searcher
import yaml

yaml_path = './config.yaml'
with open(yaml_path, 'rb') as f:
    yaml_dict = list(yaml.safe_load_all(f))[0]
    META_PATH = yaml_dict["meta_path"]
    TRANS_ROOT = yaml_dict["trans_root"]

# Define mapping
configurations = {
    "settings": {  # TODO 暂时不懂setting各参数代表什么意思
        "index": {"number_of_replicas": 2},
        "analysis": {
            "filter": {
                "ngram_filter": {
                    "type": "edge_ngram",
                    "min_gram": 2,
                    "max_gram": 15,
                },
            },
            "analyzer": {
                "ngram_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "ngram_filter"],
                },
            },
        },
    },

    "ep_mappings": {
        'properties': {
            'show_filename_prefix': {'type': 'keyword'},
            'episode_filename_prefix': {'type': 'keyword'},
            'language': {'type': 'keyword'},
            'show_name': {'type': 'text'},
            'show_description': {'type': 'text'},
            'publisher': {'type': 'text'},
            'episode_name': {'type': 'text'},
            'episode_description': {'type': 'text'},
            'duration': {'type': 'double'},  # in minute
        }
    },

    "tr_mappings": {
        'properties': {
            'show_filename_prefix': {'type': 'keyword'},
            'episode_filename_prefix': {'type': 'keyword'},
            'transcript': {'type': 'text'},
            'startTime': {'type': 'double'},  # in second
            'endTime': {'type': 'double'},
            'totalTime': {'type': 'double'}
        }
    }
}

# Define search query
search_query = {
    "match": {
        "description": "second"
    }
}


def getargs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, default='index', help='index or search')
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = getargs()

    # init es client
    es = ESClient(url="http://localhost:9200")
    # index_names = es.get_index_names()

    ######################
    # Index documents
    ######################
    if args.mode == 'index':
        # check if index exists
        if es.es_client.indices.exists(index='episodes'):
            a = input(f"Index “episodes” already exists. Do you want to delete it and regenerate? (y/n): ")
            if a == 'y':
                es.es_client.indices.delete(index='episodes')
        # Create index named 'episodes' according to mappings
        es.create_index(index_name='episodes', mappings=configurations['ep_mappings'])
        # Index documents
        print("Indexing metadata...")
        es.index_meta(META_PATH)  # Index metadata

        # check if index exists
        if es.es_client.indices.exists(index='transcripts'):
            a = input(f"Index “transcripts” already exists. Do you want to delete it and regenerate? (y/n): ")
            if a == 'y':
                es.es_client.indices.delete(index='transcripts')
        # create index named 'transcripts' according to mappings
        es.create_index(index_name='transcripts', mappings=configurations['tr_mappings'])
        print("Indexing transcripts...")

        es.index_trans(TRANS_ROOT)  # Index transcripts


    ######################
    # Execute search query
    ######################
    if args.mode == 'search':
        app = QApplication(sys.argv)
        search_engine = Searcher(es.es_client)
        w = MyWidget(search_engine)
        sys.exit(app.exec())


