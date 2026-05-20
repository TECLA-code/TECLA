
class ProgramChange:
    def __init__(self, patch, channel=None):
        self.patch = patch
        self.channel = channel
    
    def __str__(self):
        return "ProgramChange"
