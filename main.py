import argparse
import os
import json
import csv
from timeit import default_timer as timer

from elasticsearch import Elasticsearch
from es_client import ESClient


# Change them to your own working paths if needed
META_PATH = '../Project/podcasts-no-audio-13GB/metadata.tsv'
TRANS_ROOT = '../Project/podcasts-no-audio-13GB/spotify-podcasts-2020/podcasts-transcripts'

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
            'totalTime': {'type': 'double'},
            'id': {'type': 'int'} # id of the transcript in this episode, ranged from 0 to total - 1, sort according to time order
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
    parser.add_argument('-q', '--query', type=str, default='second', help='query')
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
        es.index_meta(META_PATH)    # Index metadata

        # check if index exists
        if es.es_client.indices.exists(index='transcripts'):
            a = input(f"Index “transcripts” already exists. Do you want to delete it and regenerate? (y/n): ")
            if a == 'y':
                es.es_client.indices.delete(index='transcripts')
        # create index named 'transcripts' according to mappings
        es.create_index(index_name='transcripts', mappings=configurations['tr_mappings'])
        print("Indexing transcripts...")
        es.index_trans(TRANS_ROOT)   # Index transcripts




    ######################
    # Execute search query
    ######################
    if args.mode == 'search':
        # TODO 这里应该是写一个searcher的类，封装UI和search功能
        search_query['match']['description'] = args.query
        search_results = es.es_client.search(index="episodes", query=search_query)

        print(search_results['hits']['total']['value'])  # total number of hits returned
        print(search_results['took'])  # time taken to execute the search query
        print(search_results['hits']['hits'])  # the actual search results
