import collections
from elasticsearch import Elasticsearch
from transcript import Transcript
from transcript_dict import TranscriptDict

QUERY = {
    "bool": {
        "should": [
            {"match": {"transcript": "Higgs"}},
            {"match": {"transcript": "Boson"}},
        ],
    }
}


# QUERY2 = {
#     "bool": {
#         "should": [
#             {"match": {"episode_description": "Higgs"}},
#             {"match": {"episode_description": "Boson"}},
#         ],
#         "filter": {
#             "bool": {
#                 "should":
#                     [
#                         {"term": {"episode_filename_prefix": "6qHTRpSBv1PBVXvddDPGbF"}},
#                         {"term": {"episode_filename_prefix": "7CNb3xMLYNE0kF9tyFMFQA"}},
#                     ]
#             }
#         }
#     }
# }


class Searcher:
    def __init__(self, es: Elasticsearch, n_minute=2, size=100):
        self.es = es
        self.transcript_dict = None
        self.n_minute = n_minute
        self.raw_search_size = 100
        self.max_search_size = 10000
        self.half_cache_number = 100
        self.final_size = size

    def search(self, query: dict) -> list:
        # search raw transcripts
        raw_transcripts = self.es.search(
            index='transcripts',
            query=query,
            size=self.raw_search_size
        )
        raw_transcripts = raw_transcripts['hits']['hits']
        self.update_transcript_dict(raw_transcripts)

        # search in episodes
        new_query = QUERY.copy()
        for prefix in self.transcript_dict.get_all_prefix():
            self.update_query(prefix, new_query)
        raw_episodes = self.es.search(
            index='episodes',
            query=new_query,
            size=self.max_search_size
        )
        raw_episodes = raw_episodes['hits']['hits']
        episodes_score = [hit for hit in raw_episodes if hit["_score"] > 0]

        self.modify_score(episodes_score)  # 此时，self.transcript_dict中存的是修改分数后的结果
        modified_transcripts = self.transcript_dict.get_sorted_results()  # 对结果按score进行重新排序
        res = self.combine_clips(modified_transcripts)
        return res

    def modify_score(self, episodes_score):
        if not episodes_score:
            return

        for episodes_json in episodes_score:
            prefix = episodes_json['_source']['episode_filename_prefix']
            ep_score = episodes_json['_score']
            for transcript in self.transcript_dict.transcript_dict[prefix]:
                transcript.add_score(ep_score)  # TODO:可以修改具体的分数加权方式

    @staticmethod
    def update_query(prefix, query):
        if "episode_description" not in QUERY["bool"]["should"][0]["match"]:
            # modify match name
            for t in QUERY["bool"]["should"]:
                t["match"]["episode_description"] = t["match"].pop("transcript")
        # add filter
        entry = {"term": {"episode_filename_prefix": prefix}}

        if "filter" not in query["bool"].keys():
            query["bool"]["filter"] = {"bool": {"should": []}}

        query["bool"]["filter"]["bool"]["should"].append(entry)

    def update_transcript_dict(self, raw_transcripts):
        self.transcript_dict = TranscriptDict()

        for trans_json in raw_transcripts:
            trans_obj = Transcript(json_obj=trans_json)
            self.transcript_dict.add_new_list_simple(transcript=trans_obj)

        # for trans_json in raw_transcripts:
        #     trans_obj = Transcript(json_obj=trans_json)
        #     # get retrieved_trans
        #     all_in_this_ep = self.es.search(
        #         index='transcripts',
        #         query={
        #             "bool": {
        #                 "should": [
        #                     {"match": {"episode_filename_prefix": trans_obj.get_episode_filename_prefix()}}
        #                 ]
        #             }
        #         },
        #         size=-1
        #     )
        #     all_in_this_ep = all_in_this_ep['hits']['hits']
        #     self.transcript_dict.add_new_list(transcript=trans_obj, retrieved_trans=all_in_this_ep)

    def combine_clips(self, modified_transcripts) -> list:
        # TODO: 搜索每一个transcript前后的部分，凑够n-minutes
        res = []
        total_sec = 60 * self.n_minute

        for trans in modified_transcripts:
            combine_query = {
                "bool": {
                    "must": [
                        {"match": {"episode_filename_prefix": trans.get_episode_filename_prefix()}},
                        {
                            "range": {
                                "id": {
                                    "gte": max(0, trans.get_id() - self.half_cache_number),
                                    "lte": trans.get_id() + self.half_cache_number
                                }
                            }
                        }
                    ]
                }
            }
            combine_cache = self.es.search(
                index='transcripts',
                query=combine_query,
                size=2 * self.half_cache_number + 1
            )
            combine_cache = combine_cache['hits']['hits']
            combine_cache = [Transcript(json_obj=hit) for hit in combine_cache]
            # 向前向后搜索并添加
            # 注意：暂时没有实现缓存不够重读的功能，因此，有必要将self.half_cache_number设置的比较大
            deque = collections.deque()  # 双端队列
            res_list = self.front_back_search(deque, trans, combine_cache, total_sec)
            res.append(res_list)

        return res

    def front_back_search(self, deque, trans, combine_cache, total_sec) -> collections.deque:
        deque.append(trans)
        cur_sec = trans.get_total_time()
        base_pos = trans.get_id() - combine_cache[0].get_id()
        i = 1
        while cur_sec <= total_sec and i <= self.half_cache_number:
            if base_pos - i >= 0:
                front_trans = combine_cache[base_pos - i]
                deque.appendleft(front_trans)
                cur_sec += front_trans.get_total_time()
                if cur_sec > total_sec:
                    break

            if base_pos + i <= len(combine_cache) - 1:
                back_trans = combine_cache[base_pos + i]
                deque.append(back_trans)
                cur_sec += back_trans.get_total_time()

            i += 1
        return deque


def main():
    es_client = Elasticsearch("http://localhost:9200")
    searcher = Searcher(es_client)
    res = searcher.search(QUERY)
    print('search finish')


if __name__ == '__main__':
    main()
