import logging as loglib

##############################################################
######## globals #############################################
##############################################################
# Configure logger
class CustomFormatter(loglib.Formatter):
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[32;1m"
    reset = "\x1b[0m"
    timeStr = "[%(asctime)s]"
    formatStr = " %(levelname)s "
    messageStr = "- %(message)s"
    FORMATS = {
        loglib.DEBUG: timeStr + grey + formatStr + reset + messageStr,
        loglib.INFO: timeStr + grey + formatStr + reset + messageStr,
        loglib.WARNING: timeStr + yellow + formatStr + reset + messageStr,
        loglib.ERROR: timeStr + red + formatStr + reset + messageStr,
        loglib.CRITICAL: timeStr + bold_red + formatStr + reset + messageStr,
    }         
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = loglib.Formatter(log_fmt, datefmt='%H:%M:%S')
        return formatter.format(record)
# create logger with 'spam_application'
logging = loglib.getLogger("rootConverter")
logging.setLevel(loglib.INFO)
# create console handler with a higher log level
ch = loglib.StreamHandler()
ch.setLevel(loglib.DEBUG)
ch.setFormatter(CustomFormatter())
logging.addHandler(ch)