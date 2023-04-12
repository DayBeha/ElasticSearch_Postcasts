from transcript import Transcript
from functools import cmp_to_key
from typing import Dict, List

class TranscriptDicts():
    def __init__(self) -> None:
        self.transcript_dicts: Dict[str, List] = dict()
    
    def add_new_list(self, transcript: Transcript, episode_filename_prefix: str, base_score: float, retrieved_trans: List[Dict]) -> None:
        """
        Insert a new transcript. If the corresponding episode already exists, update the old one. If not, for this episode, generate a transcript list for this key, and set their scores to base_score, which is the weighted score of episode and show, then update the score for the new transcript.

        Args:
            transcript (Transcript): The relevant transcript to be inserted.
            episode_filename_prefix (str): Identifier for the episode.
            base_score (float): Weighted score of episode and show.
            retrieved_trans (List[Dict]): All transcripts for the episode, sorted chronologically. How to: when use episode_filename_prefix to search, first get total number of transcripts in that episode by res['hits']['total']['value'], then search again and set size=total and you can get all the transcripts in this episode.
        """
    
        if episode_filename_prefix not in self.transcript_dicts:
            self.transcript_dicts[episode_filename_prefix] = list()
            for trans in retrieved_trans:
                trans_obj = Transcript(json_obj=trans)
                if trans_obj.get_id() == transcript.get_id():
                    self.transcript_dicts[episode_filename_prefix].append(transcript)
                    continue
                trans_obj.set_score(base_score)
                self.transcript_dicts[episode_filename_prefix].append(trans_obj)
        else:
            self.transcript_dicts[episode_filename_prefix][transcript.get_id()] = transcript
    
    def sort(self) -> None:
        for f_prefix in self.transcript_dicts:
            self.transcript_dicts[f_prefix].sort(key=cmp_to_key(TranscriptDicts.compare))
    
    @staticmethod
    def compare(x: Transcript, y: Transcript):
        return x.get_id() - y.get_id()