#!/usr/bin/which python3
'''
    This Script provide a GUI front-end to the TimeWarror CLI application
    Author: Ben Mason
'''

__author__ = "Ben Mason"
__copyright__ = "Copyright 2021"
__version__ = "1.5.0"
__email__ = "locutus@the-collective.net"
__status__ = "Production"


import subprocess
import json
import logging
from datetime import datetime
import PySimpleGUI as sg

# GUI Astetics
THEME = "Dark Grey 4"
GLOBAL_FONT = "Any 11"

# Enable Debug output
#LOGGING_LEVEL = logging.ERROR # DEBUG
LOGGING_LEVEL = logging.DEBUG
LOGGING_FORMAT = '[%(levelname)s] %(asctime)s - %(funcName)s %(lineno)d - %(message)s'

# Global Constants
ENCODING = 'utf-8'

class TwButtonLogic:
    ''' This class hold the logic and actions for selected buttons '''

    no_of_tasks_tracked = 0

    def __init__(self):
        ''' initialize the class '''

    @staticmethod
    def execute_cli(cli: str) -> str:
        ''' Execute commands on CLI returns STDOUT '''

        logging.debug("cli: %s", cli)

        process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        logging.debug("stdout: %s", stdout)
        logging.debug("stderr: %s", stderr)

        return stdout

    def get_active_timer(self) -> str:
        ''' Get Actively tracked task '''

        cli = ['timew']
        stdout = self.execute_cli(cli)

        output_list = str(stdout, ENCODING).split("\n")

        logging.debug("output_list: %s", output_list)

        if output_list[0].strip() == "There is no active time tracking.":
            result = "no active time tracking"
        else:
            result = output_list[0][9:].replace('"', '')

        return result

    def get_calendar_entry(self) -> str:
        ''' Use icalbuddy to get the meeting on your calendar right now '''

        cli = ['/usr/local/bin/icalbuddy',
            '-npn', '-ea', '-nc', '-b', '',
            '-ps', '" - "',
            '-eep', 'url,location,notes,attendees,datetime',
            '-ic', 'Calendar', 'eventsNow', ]

        stdout = self.execute_cli(cli)

        return str(stdout, ENCODING)

    def fixstart(self) -> str:
        '''
        Use icalbuddy to get the start time of the currnet meeting on your calendar right now
        '''

        # /usr/local/bin/icalbuddy -npn -ea -nc -ps "/ » /" -eep \
        # "url",location,notes,attendees -ic "Calendar" eventsNow
        cli = ['/usr/local/bin/icalbuddy',
            '-npn', '-ea', '-nc', '-b', '',
            '-ps', '" | "',
            '-eep', 'url,location,notes,attendees',
            '-ic', 'Calendar', 'eventsNow', ]

        stdout = self.execute_cli(cli)
        logging.debug("stdout: %s", stdout)

        start_time = str(stdout).split("|")[1].split(" - ")[0].strip()
        #stop_time  = str(stdout).split("|")[1].split(" - ")[1][:-3] - Not used
        logging.debug("stdout: %s", start_time)

        return start_time

    def collect_tasks_list(self, duration='day'):
        ''' Collect list of tracked tasks (default to today) '''

        max_tag_len = 0
        table_data = []

        cli = ['timew', 'export', ':'+duration]
        stdout = self.execute_cli(cli)

        task_list = json.loads(stdout)

        for task_item in task_list:
            date_format = "%Y%m%dT%H%M%SZ"

            # Calculate Duration (skip or active)
            if 'end' in task_item.keys():
                start_date = datetime.strptime(task_item['start'], date_format)
                end_date = datetime.strptime(task_item['end'], date_format)
                duration = end_date - start_date
            else:
                duration = "active"

            table_data.append([task_item['tags'][0] , str(duration)])

            if max_tag_len < len(task_item['tags']):
                max_tag_len = len(task_item['tags'])

        self.no_of_tasks_tracked = len(table_data)

        return table_data, max_tag_len

    def get_tw_taskid_from_timetable(self, timetable):
        ''' Collect the TimeWarrior taskid and GUI table id '''

        if timetable != []:
            task_no = self.no_of_tasks_tracked - timetable[0]
            table_no = timetable[0]

        else:
            task_no = 1
            table_no = self.no_of_tasks_tracked-1

        return task_no, table_no

    @staticmethod
    def button_start(values, cli):
        ''' Run buttons starting with "Start" '''

        cli.append("start")

        if values['starttime'] != '':
            cli.append(values['starttime'])
            result_display = "Started: " + values['taskdesc'] + " at " + values['starttime']
        else:
            result_display = "Started: " + values['taskdesc']

        cli.append(values['taskdesc'])

        return cli, result_display

    @staticmethod
    def button_track(values, cli):
        ''' Run buttons starting with "Track" '''

        if values['date'] != '':
            starttime = values['date'] + "T" + values['starttime']
            stoptime = values['date'] + "T" + values['stoptime']
        else:
            starttime = values['starttime']
            stoptime = values['stoptime']

        cli.extend(['track' , starttime, '-', stoptime, values['taskdesc']])

        result_display = "Tracked: " + values['taskdesc']

        return cli, result_display

    @staticmethod
    def button_stop(values, cli):
        ''' Run buttons starting with "Stop" '''

        cli.append("stop")

        if values['stoptime'] != '':
            cli.append(values['stoptime'])
        result_display = "Stopped Tracking"

        return cli, result_display

    def button_rename(self, values, cli):
        ''' Run buttons starting with "Rename" '''

        task_no, table_no = self.get_tw_taskid_from_timetable(values['timew_table'])
        taskid = '@'+str(task_no)

        table_data, _ = self.collect_tasks_list()
        old_description = table_data[table_no][0]

        ### Open window
        new_description = sg.popup_get_text('Rename Task', default_text=old_description)

        if new_description is not None:
            self.execute_cli(['timew', 'tag', taskid, new_description])
            cli = ['timew', 'untag', taskid, old_description]
            result_display = "Renamed task"
        else:
            result_display= "Rename Canceled"

        return cli, result_display

    def button_start_meeting(self, cli):
        ''' Run Start Meeting from calendar info routine '''

        calendarentry = self.get_calendar_entry()
        if calendarentry:
            cli.extend(["start", ])
            result_display = "Started meeting"
        else:
            sg.popup('Nothing available on Calendar')
            result_display = 'Nothing available on Calendar'
            cli = None

        return cli, result_display

    def button_logic(self, event: str, values):
        ''' Execute Button based events executing TimeWarrior CLI commands '''

        cli = ['timew']

        if event == 'Start Meeting':
            cli, result_display = self.button_start_meeting(cli)
        elif event in 'Start':
            cli, result_display = self.button_start(values, cli)
        elif event == 'Track':
            cli, result_display = self.button_track(values, cli)
        elif event == 'Stop':
            cli, result_display = self.button_stop(values, cli)

        # Modify start of current / last task
        elif event == "Modify Start":
            cli.extend(['modify', 'start', values['starttime'], '@1'])
            result_display = "Modified Start time to " + values['starttime']

        elif event == "Fix Start":
            start_time = self.fixstart()
            cli.extend(['modify', 'start', '@1', start_time])
            result_display = "Modified Start time to " + start_time

        elif event == "Rename":
            cli, result_display = self.button_rename(values, cli)

        elif event in ('Continue', "Delete"):
            command = event.lower()
            task_no, _ = self.get_tw_taskid_from_timetable(values['timew_table'])
            cli.extend([command, '@'+str(task_no)])
            result_display = command + " @" + str(task_no)

        else:
            result_display = "Default: See Results"
            logging.debug("******* Button not Matched *************")

        if cli:
            result = self.execute_cli(cli)
        else:
            # return null bytes for CLI output if cli is not set
            result = b''

        return result, result_display

def validate_date(date_text):
    ''' Validate Date is correct format '''

    return_val = False

    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return_val = True

    return return_val

def validate_time(time_text: str) -> bool:
    ''' Validate Time is correct format '''

    return_val = False

    try:
        datetime.strptime(time_text, '%H:%M')
    except ValueError:
        return_val = True

    return return_val

def main():
    ''' Main Function '''

    logging.basicConfig(level=LOGGING_LEVEL, format=LOGGING_FORMAT)
    twbuttonlogic = TwButtonLogic()

    fields = [ "date", "starttime", "stoptime", "taskdesc" ]
    timew_summary_columns = ['Tags', 'Duration']

    #
    # Load inital tracked time data
    table_data, tag_len = twbuttonlogic.collect_tasks_list()
    logging.debug("tag_len: %s", tag_len)

    # if empty table set correct column and rows
    if table_data == []:
        table_data = [[" "*25,""]]

    active_timer = twbuttonlogic.get_active_timer()

    #
    # Define the window's contents
    sg.theme(THEME)

    layout = [
            [ sg.Text("Task:", font=GLOBAL_FONT), sg.Input(key="taskdesc", size=(35,1), \
                font=GLOBAL_FONT) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:", font=GLOBAL_FONT), sg.Input(key="starttime", \
                    size=(12,1), font=GLOBAL_FONT), sg.Text("EX: 15:00", \
                        font=GLOBAL_FONT) ],
                [ sg.Text("Stop time:", font=GLOBAL_FONT), sg.Input(key="stoptime", \
                    size=(12,1), font=GLOBAL_FONT), sg.Text("EX: 15:00", font=GLOBAL_FONT) ],
                [ sg.Text("Date: ", font=GLOBAL_FONT), sg.Input(key="date", size=(12,1), \
                    font=GLOBAL_FONT), sg.Text("EX: 2020-10-01", font=GLOBAL_FONT) ]
            ], title='Date')],
            [ sg.Button('Start', font=GLOBAL_FONT), sg.Button('Stop', font=GLOBAL_FONT), \
                sg.Button('Modify Start', font=GLOBAL_FONT), sg.Button('Curr Running', \
                    font=GLOBAL_FONT), ],
            [ sg.Button('Start Meeting', font=GLOBAL_FONT), sg.Button('Track', \
                font=GLOBAL_FONT), sg.Button('Continue', font=GLOBAL_FONT),  \
                    sg.Button('Delete', font=GLOBAL_FONT),],
            [ sg.Button('Rename', font=GLOBAL_FONT), sg.Button('Fix Start', font=GLOBAL_FONT) ],
            [ sg.Text(size=(40,1), key='status_result', font=GLOBAL_FONT) ],
            [ sg.MLine(key="cliout", size=(40,8), font=GLOBAL_FONT) ],
            [ sg.Text("Current Tracking:", font=GLOBAL_FONT), sg.Input(key="curr_tracking", \
                size=(25,1), default_text=active_timer, font=GLOBAL_FONT) ],
            [ sg.Text("Todays Time", font=GLOBAL_FONT) ],
            [ sg.Table(values=table_data, headings=timew_summary_columns, max_col_width=25,
                    display_row_numbers=False,
                    justification='left',
                    num_rows=20,
                    key='timew_table',
                    tooltip='Todays Data',
                    font=GLOBAL_FONT)]
        ]

    window = sg.Window('Timewarrior Tracking', layout)

    #
    ####### Event Loop
    while True:
        logging.debug("****** Start Main Loop ******")
        logging.debug("table_data: %s", table_data)
        #
        # Read Button triggers
        event, values = window.read()

        # Clean up and Close
        if event in (sg.WINDOW_CLOSED, 'Quit'):
            break

        #
        # Input Validation
        if values['date'] != '':
            if validate_date(values['date']):
                sg.popup('Invalid date please use format "YYYY-MM-DD" data entered:', \
                    values['date'])
                continue
        if values['starttime'] != '':
            if validate_time(values['starttime']):
                sg.popup('Invalid date please use format "HH:MM" data entered:', \
                    values['starttime'])
                continue
        if values['stoptime'] != '':
            if validate_time(values['stoptime']):
                sg.popup('Invalid date please use format "HH:MM" data entered:', \
                    values['stoptime'])
                continue
        if (event in ('Track', 'Start')) and values['taskdesc'] == '':
            sg.popup('Task Name Can not be Empty')
            continue

        #
        # Button Logic
        result, result_display = twbuttonlogic.button_logic(event, values)
        logging.debug("button_logic result: %s", result)

        #
        # Update list of tracked time for today
        table_data, tag_len = twbuttonlogic.collect_tasks_list()
        window['timew_table'].update(values=table_data)

        active_timer = twbuttonlogic.get_active_timer()
        window['curr_tracking'].update(active_timer)

        #
        # Return results and Status
        window['status_result'].update(result_display)
        window['cliout'].update(str(result, ENCODING))

        #
        # clear input fields
        for i in fields:
            window[i].update('')

    window.close()

    return 0

####### Start Main Function #############
if __name__ == "__main__":
    main()
