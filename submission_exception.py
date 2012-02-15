from rest_log import mobedac_logger


class SubmissionException(Exception):
    def __init__(self, value):
        super(SubmissionException, self).__init__(value)
        self.value = value
        mobedac_logger.exception(value)
    def __str__(self):
        return repr(self.value)    
