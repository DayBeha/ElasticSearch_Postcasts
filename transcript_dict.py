import argparse

from transcript import Transcript
from functools import cmp_to_key
from typing import Dict, List
from copy import deepcopy


class TranscriptDict():
    def __init__(self) -> None:
        self.transcript_dict: Dict[str, List] = dict()

    def add_new_list(self, transcript: Transcript, retrieved_trans: List[Dict]) -> None:
        """
        Insert a new transcript. If the corresponding episode already exists, update the old one. If not, for this episode, generate a transcript list for this key, and set their scores to base_score, which is the weighted score of episode and show, then update the score for the new transcript.

        Args:
            transcript (Transcript): The relevant transcript to be inserted.
            episode_filename_prefix (str): Identifier for the episode.
            retrieved_trans (List[Dict]): All transcripts for the episode, sorted chronologically. How to: when use episode_filename_prefix to search, first get total number of transcripts in that episode by res['hits']['total']['value'], then search again and set size = res['hits']['total']['value'] and you can get all the transcripts in this episode.
        """
        episode_filename_prefix = transcript.get_episode_filename_prefix()
        if episode_filename_prefix not in self.transcript_dict:
            self.transcript_dict[episode_filename_prefix] = list()
            for trans_json in retrieved_trans:
                trans_obj = Transcript(json_obj=trans_json)
                if trans_obj.get_id() == transcript.get_id():
                    self.transcript_dict[episode_filename_prefix].append(transcript)
                    continue
                trans_obj.set_score(0)
                self.transcript_dict[episode_filename_prefix].append(trans_obj)
        else:
            self.transcript_dict[episode_filename_prefix][transcript.get_id()] = transcript
        print('ss')

    def add_new_list_simple(self, transcript: Transcript):
        episode_filename_prefix = transcript.get_episode_filename_prefix()
        if episode_filename_prefix not in self.transcript_dict:
            self.transcript_dict[episode_filename_prefix] = list()
        self.transcript_dict[episode_filename_prefix].append(transcript)

    def get_all_prefix(self):
        return self.transcript_dict.keys()

    def sort(self) -> None:
        for f_prefix in self.transcript_dict:
            self.transcript_dict[f_prefix].sort(key=cmp_to_key(TranscriptDict.compare))

    def get_transcript_list(self, episode_filename_prefix: str) -> List[Transcript]:
        if episode_filename_prefix in self.transcript_dict:
            return self.transcript_dict[episode_filename_prefix]
        else:
            return None

    def get_raw_clip(self, episode_filename_prefix: str, ids: List[int]) -> List[Transcript]:
        t_list = self.get_transcript_list(episode_filename_prefix)
        if t_list is not None:
            raw_clip = []
            for id in ids:
                if id < len(t_list):
                    raw_clip.append(t_list[id])
            return raw_clip
        else:
            return None

    def get_sorted_results(self):
        merged_list = [transcript for t_list in self.transcript_dict.values() for transcript in t_list]
        sorted_list = sorted(merged_list, key=lambda transcript: transcript.score, reverse=True)

        return sorted_list

    @staticmethod
    def compare(x: Transcript, y: Transcript):
        return x.get_id() - y.get_id()
