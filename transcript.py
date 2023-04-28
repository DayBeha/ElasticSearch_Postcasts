class Transcript():
    def __init__(self, **kwargs) -> None:
        if 'json_obj' not in kwargs:
            self.score = kwargs['score']
            self.id = kwargs['id']
            self.transcript = kwargs['transcript']
            self.episode_filename_prefix = kwargs['episode_filename_prefix']
            self.start_time = kwargs['start_time']
            self.end_time = kwargs['end_time']
            self.total_time = kwargs['total_time']
            self.episode_score = 0
        else:
            self.score = kwargs['json_obj']['_score']
            self.id = kwargs['json_obj']['_source']['id']
            self.transcript = kwargs['json_obj']['_source']['transcript']
            self.episode_filename_prefix = kwargs['json_obj']['_source']['episode_filename_prefix']
            self.start_time = kwargs['json_obj']['_source']['startTime']
            self.end_time = kwargs['json_obj']['_source']['endTime']
            self.total_time = kwargs['json_obj']['_source']['totalTime']
            self.episode_score = 0

    def get_score(self) -> float:
        return self.score

    def get_id(self) -> int:
        return self.id

    def get_transcript(self) -> int:
        return self.transcript

    def get_episode_filename_prefix(self) -> int:
        return self.episode_filename_prefix

    def get_start_time(self) -> float:
        return self.start_time

    def get_end_time(self) -> float:
        return self.end_time

    def get_total_time(self) -> float:
        return self.total_time

    def set_score(self, new_score: float) -> None:
        self.score = new_score

    def add_score(self, new_score: float, weight: float=1) -> None:
        self.score += new_score * weight
        
    def __str__(self) -> str:
        return self.transcript + " | " + str(self.total_time) + " | " + str(self.score)
    
    def to_str(self) -> str:
        return self.__str__()