class ProcessService:
    def __init__(self):
        self.file = None
    def process_files(self, file):
        self.file = file
        return {"hi"}
    
    