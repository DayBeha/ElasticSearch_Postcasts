import collections
import copy
from elasticsearch import Elasticsearch
from clip import Clip
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

QUERY_TEXT = 'Higgs Boson'

QUERY_COMPLEX = {
    "bool": {
        "must": {
            "match": {
                "transcript": {
                    "query": "Higgs Boson",
                    "minimum_should_match": "50%"
                }
            }
        },
        "should": {
            "match_phrase": {
                "transcript": {
                    "query": "Higgs Boson",
                    "slop": 20
                }
            }
        }
    }
}


# EPISODE_QUERY = {
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
    def __init__(self, es: Elasticsearch, time_limit=2, size=100):
        # Elasticsearch
        self.es = es
        self.transcript_dict = None
        # 由用户输入的，需要返回的n-minutes片段
        self.time_limit = time_limit
        # 第1次对transcripts进行搜索的结果数目
        self.raw_search_size = 100
        # 第2次对episodes进行搜索的结果数目
        self.max_search_size = 10000
        # 进行clip拼接时缓存的（一半）长度
        self.half_cache_number = 100
        # 最终返回的结果数目
        self.final_size = size
        # TODO: 找到最好的权重
        self.EPISODE_WEIGHT = 1.5

    def set_time_limit(self, time_limit):
        self.time_limit = time_limit

    def search(self, query: dict, query_text: str) -> list:
        # search raw transcripts
        raw_transcripts = self.es.search(
            index='transcripts',
            query=query,
            size=self.raw_search_size
        )
        raw_transcripts = raw_transcripts['hits']['hits']
        self.update_transcript_dict(raw_transcripts)

        # search in episodes
        episodes_query = {
            "bool": {
                "should": [
                    {"match": {"episode_description": query_text}},
                ],
                "filter": {
                    "bool": {
                        "should":
                            []
                    }
                }
            }
        }
        for prefix in self.transcript_dict.get_all_prefix():
            self.update_query(prefix, episodes_query, query_text)
        raw_episodes = self.es.search(
            index='episodes',
            query=episodes_query,
            size=self.max_search_size
        )
        raw_episodes = raw_episodes['hits']['hits']
        episodes_score = [hit for hit in raw_episodes if hit["_score"] > 0]

        # 根据raw_episodes构造prefix_id与show_name, episode_name的对应关系
        show_info = self.build_show_info(raw_episodes)

        self.modify_score(episodes_score)  # 此时，self.transcript_dict中存的是修改分数后的结果
        modified_transcripts = self.transcript_dict.get_sorted_results()  # 对结果按score进行重新排序
        res = self.combine_clips(modified_transcripts, show_info)
        return res

    @staticmethod
    def build_show_info(raw_episodes):
        show_info = {}
        for raw in raw_episodes:
            raw = raw['_source']
            show_info[raw['episode_filename_prefix']] = {
                'show_filename_prefix': raw['show_filename_prefix'],
                'episode_filename_prefix': raw['episode_filename_prefix'],
                'show_name': raw['show_name'],
                'show_description': raw['show_description'],
                'publisher': raw['publisher'],
                'episode_name': raw['episode_name'],
                'episode_description': raw['episode_description'],
            }
        return show_info

    def modify_score(self, episodes_score):
        """将每段transcript的原始得分与其对应的episodes的得分进行加权"""
        if not episodes_score:
            return

        for episodes_json in episodes_score:
            prefix = episodes_json['_source']['episode_filename_prefix']
            ep_score = episodes_json['_score']
            for transcript in self.transcript_dict.transcript_dict[prefix]:
                transcript.add_score(ep_score, self.EPISODE_WEIGHT)

    @staticmethod
    def update_query(prefix, query, query_text):
        """根据用户提供的原始query，构造在episodes上进行查询时的query"""
        # if "episode_description" not in query["bool"]["should"][0]["match"]:
        #     # modify match name
        #     for t in query["bool"]["should"]:
        #         t["match"]["episode_description"] = t["match"].pop("transcript")

        # add filter
        entry = {"term": {"episode_filename_prefix": prefix}}

        # if "filter" not in query["bool"].keys():
        #     query["bool"]["filter"] = {"bool": {"should": []}}

        query["bool"]["filter"]["bool"]["should"].append(entry)

    def update_transcript_dict(self, raw_transcripts):
        """更新transcript_dict"""
        self.transcript_dict = TranscriptDict()

        for trans_json in raw_transcripts:
            trans_obj = Transcript(json_obj=trans_json)
            self.transcript_dict.add_new_list_simple(transcript=trans_obj)

    def combine_clips(self, modified_transcripts, show_info) -> list:
        """对最终结果的每一个transcript，构造出n-minutes的片段"""
        # 搜索每一个transcript前后的部分，凑够n-minutes
        res = []
        total_sec = 60 * (self.time_limit - 0.5)

        for trans in modified_transcripts:
            flag = False
            n = 1  # 控制搜索范围
            old_cache = []
            while not flag:
                gte = max(0, trans.get_id() - n * self.half_cache_number)
                lte = trans.get_id() + n * self.half_cache_number
                combine_query = {
                    "bool": {
                        "must": [
                            {"match": {"episode_filename_prefix": trans.get_episode_filename_prefix()}},
                            {
                                "range": {
                                    "id": {
                                        "gte": gte,
                                        "lte": lte
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
                # 实现了缓存不够重读的功能
                deque = collections.deque()  # 双端队列
                res_list, flag = self.front_back_search(deque, trans, combine_cache, total_sec)

                if not flag:  # 搜索完成后，最终clip的时长小于目标要求的时长
                    n += 1
                    if len(old_cache) == len(combine_cache):  # 说明不够的原因是没有更多文本，直接退出
                        break
                    old_cache = combine_cache
                    continue

                clip = Clip(list(res_list), trans.get_score(), show_info[trans.get_episode_filename_prefix()])
                res.append(clip)

        return res

    def front_back_search(self, deque, trans, combine_cache, total_sec):
        """为某一个transcript构造n-minutes片段"""
        trans_cp = copy.deepcopy(trans)
        trans_cp.set_transcript('<i>' + trans_cp.get_transcript() + '</i>')
        deque.append(trans_cp)
        cur_sec = trans_cp.get_total_time()
        base_pos = trans_cp.get_id() - combine_cache[0].get_id()
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

        if i == self.half_cache_number and cur_sec < total_sec:
            return deque, False
        else:
            return deque, True


def main():
    es_client = Elasticsearch("http://localhost:9200")
    searcher = Searcher(es_client)
    res = searcher.search(QUERY, QUERY_TEXT)
    for clip in res:
        a = clip.text

    for i, item in enumerate(res):
        print(i)
        print(item[0].get_episode_filename_prefix())
        for trans in item:
            print(trans)
    print('search finish')


if __name__ == '__main__':
    main()
