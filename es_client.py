import csv
import json
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from tqdm import tqdm


class ESClient:
    def __init__(self, url="http://localhost:9200", index_name=None, configurations=None):
        self.es_client = Elasticsearch(url)
        # self.index_name = index_name
        # self.ep_mappings = configurations["ep_mappings"]
        # self.tr_mappings = configurations["tr_mappings"]
        # self.settings = configurations["settings"]

    def create_index(self, index_name, mappings):
        self.es_client.indices.create(index=index_name,
                                      # settings=self.settings,
                                      mappings=mappings)

    def delete_index(self, index_name):
        self.es_client.indices.delete(index=index_name)

    def get_index_names(self):
        # return self.es_client.indices.get_alias().keys()    # contains all index names
        indices = self.es_client.cat.indices(format='json')  # only contains artifical created index names
        return [index['index'] for index in indices]

    def generate_meta(self, META_PATH):
        with open(META_PATH, "r", encoding='UTF-8') as file:
            reader = csv.DictReader(file, delimiter='\t')
            for row in reader:
                doc = {
                    '_index': "episodes",
                    '_source': {
                        'show_filename_prefix': row["show_filename_prefix"],
                        'episode_filename_prefix': row["episode_filename_prefix"],
                        'language': row["language"],
                        'show_name': row["show_name"],
                        'show_description': row["show_description"],
                        'publisher': row["publisher"],
                        'episode_name': row["episode_name"],
                        'episode_description': row["episode_description"],
                        'duration': float(row["duration"])
                    }
                }
                yield doc

    def generate_trans(self, TRANS_ROOT):
        trans_root = Path(TRANS_ROOT)
        trans_files = trans_root.glob('**/*.json')
        for child in tqdm(trans_files):
            transcript_obj = json.load(open(child))
            for chunk in transcript_obj["results"]:
                data = chunk["alternatives"][0]
                if "transcript" in data and "words" in data:
                    startTime = float(data["words"][0]["startTime"][:-1])
                    endTime = float(data["words"][-1]["endTime"][:-1])
                    totalTime = endTime - startTime
                    doc = {
                        '_index': 'transcripts',
                        '_source': {
                            'show_filename_prefix': child.parent.name,
                            'episode_filename_prefix': child.name.split(".")[0],
                            'transcript': data["transcript"],
                            'startTime': startTime,
                            'endTime': endTime,
                            'totalTime': totalTime
                        }
                    }
                    yield doc

    def index_meta(self, META_PATH):
        bulk(client=self.es_client, actions=self.generate_meta(META_PATH))

    def index_trans(self, TRANS_ROOT):
        bulk(client=self.es_client, actions=self.generate_trans(TRANS_ROOT))



    ##############################  not used for now  ##############################
    def get_index_mappings(self, index_name):
        return self.es_client.indices.get_mapping(index=index_name)

    def get_index_settings(self, index_name):
        return self.es_client.indices.get_settings(index=index_name)

    def get_index_stats(self, index_name):
        return self.es_client.indices.stats(index=index_name)

    def get_index_status(self, index_name):
        return self.es_client.indices.status(index=index_name)

    def get_index_health(self, index_name):
        return self.es_client.cluster.health(index=index_name)

    def get_index_count(self, index_name):
        return self.es_client.count(index=index_name)

    def get_index_size(self, index_name):
        return self.es_client.indices.get(index=index_name)

    def get_index_doc(self, index_name, doc_id):
        return self.es_client.get(index=index_name, id=doc_id)

    def get_index_docs(self, index_name, doc_ids):
        return self.es_client.mget(index=index_name, body={"ids": doc_ids})

    def get_index_doc_count(self, index_name):
        return self.es_client.count(index=index_name)

    def get_index_doc_size(self, index_name):
        return self.es_client.indices.get(index=index_name)

    def get_index_doc_field(self, index_name, doc_id, field):
        return self.es_client.get_source(index=index_name, id=doc_id, _source=field)

    def insert_data(self, index_name, data):
        self.es_client.index(index=index_name, body=data)

