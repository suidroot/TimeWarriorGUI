'''
    Configuration of the TimeWarrior GUI scripts
'''
import logging

# GUI Astetics
THEME = "Dark Grey 4"
GLOBAL_FONT = "Any 11"
BUTTON_SIZE = 8

# Enable Debug output
#LOGGING_LEVEL = logging.ERROR # DEBUG
LOGGING_LEVEL = logging.ERROR
LOGGING_FORMAT = '[%(levelname)s] %(asctime)s - %(funcName)s %(lineno)d - %(message)s'

# Global Constants
ENCODING = 'utf-8'

CLI_BASE_COMMAND = 'timew'
ICALBUDDY_LOCATION = '/usr/local/bin/icalbuddy'
ICALBUDDY_CALENDAR='Calendar'
ICALBUDDY_ENABLE = True
