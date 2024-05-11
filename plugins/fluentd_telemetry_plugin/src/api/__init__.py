class InvalidConfRequest(Exception):
    """InvalidConfRequest Exception class"""

    def __init__(self, message):
        Exception.__init__(self, message)
