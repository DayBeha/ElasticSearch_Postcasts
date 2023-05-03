import collections
from transcript import Transcript
from typing import List


class Clip:
    def __init__(self, clip: List[Transcript], score: float, show_info: dict) -> None:
        self.clip = clip
        self.show_info = show_info
        self.score = score
        self.text = None
        self.to_text()
        # self.desc_score = desc_score
        # self.total_time: float
        # self.ovr_score: float
        # self._calc()
        # # hyperparams
        # self.desc_weight = 0.6
        # self.transcript_weight = 0.4

    # def _calc(self):
    #     for transcript in self.clip:
    #         self.total_time += transcript.get_total_time()
    #         self.ovr_score += transcript.get_score()
    #     self.ovr_score /= (self.total_time / 60)
    #     self.ovr_score = self.ovr_score * self.transcript_weight + self.desc_score * self.desc_weight

    def to_text(self):
        s = ''
        for t in self.clip:
            s += t.get_transcript() + ' '
        self.text = s.strip()
