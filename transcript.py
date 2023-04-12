class Transcript():
    def __init__(self, **kwargs) -> None:
        if 'json_obj' not in kwargs:
            self.score = kwargs['score']
            self.start_time = kwargs['start_time']
            self.end_time = kwargs['end_time']
            self.total_time = kwargs['total_time']
            self.id = kwargs['id'] 
        else:
            self.score = kwargs['json_obj']['_score']
            self.start_time = kwargs['json_obj']['_source']['startTime']
            self.end_time = kwargs['json_obj']['_source']['endTime']
            self.total_time = kwargs['json_obj']['_source']['totalTime']
            self.id = kwargs['json_obj']['_source']['id']
            
    def get_score(self) -> float:
        return self.score
    
    def get_start_time(self) -> float:
        return self.start_time
    
    def get_end_time(self) -> float:
        return self.end_time
    
    def get_total_time(self) -> float:
        return self.total_time
    
    def get_id(self) -> int:
        return self.id
    
    def set_score(self, new_score: float) -> None:
        self.score = new_score