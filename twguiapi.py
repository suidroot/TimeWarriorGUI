#!/usr/bin/which python3
'''
    This script provides the backend logic for the GUI front end to interface with TimeWarrior
    Author: Ben Mason
'''

__author__ = "Ben Mason"
__copyright__ = "Copyright 2022"
__version__ = "2.0.0"
__email__ = "locutus@the-collective.net"
__status__ = "Production"

import subprocess
import json
import logging
from datetime import datetime, timezone
import PySimpleGUI as sg
import config


def utc_to_local(utc_dt: datetime) -> datetime:
    ''' Convert datetime object to local time from UTC '''
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def list_to_str(orig_list: list) -> str:
    ''' Convert List into Comma sperated String '''
    return ', '.join(orig_list)

def error_popup(popup_message: str) -> 'tuple[str,str]':
    ''' 
    Popup error dialog with message
    Returns blank cli and 'Error' return message
    '''

    sg.popup("ERROR: " + popup_message)

    cli = ""
    results_display = "Error"

    return cli, results_display

class TwButtonLogic:
    ''' This class hold the logic and actions for selected buttons '''

    no_of_tasks_tracked = 0
    todays_tasks = None

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
        ''' Get Actively tracked task and return tag '''

        cli = [config.CLI_BASE_COMMAND]

        stdout = self.execute_cli(cli)
        output_list = str(stdout, config.ENCODING).split("\n")
        logging.debug("output_list: %s", output_list)

        if output_list[0].strip() == "There is no active time tracking.":
            result = "no active time tracking"
        else:
            result = output_list[0][9:].replace('"', '')

        return result

    #
    ## Start iCalBuddy Function
    def run_icalbuddy(self, date_range: str, exclude_fields='url,location,notes,attendees') -> str:
        '''
        Run iCalBuddy Commands
        return output as str
        '''

        cli = [config.ICALBUDDY_LOCATION,
            '-npn', '-ea', '-nc', '-b', '',
            '-ps', '" | "',
            '-eep', exclude_fields,
            '-ic', config.ICALBUDDY_CALENDAR, date_range, ]

        stdout = self.execute_cli(cli)

        return str(stdout, config.ENCODING)


    def get_current_calendar_entry(self) -> str:
        '''
        Use icalbuddy to get the meeting on your calendar right now
        '''
        stdout = self.run_icalbuddy('eventsNow', \
            exclude_fields='url,location,notes,attendees,datetime')

        return stdout

    def get_current_calendar_starttime(self) -> str:
        '''
        Use icalbuddy to get the start time of the currnet meeting on your calendar right now
        '''
        stdout = self.run_icalbuddy('eventsNow')

        start_time = stdout.split("|")[1].split(" - ")[0].strip()
        logging.debug("start_time: %s", start_time)

        return start_time

    def get_calendar_entries(self, date_range='today') -> list:
        '''
        Collect calendar entries from icalbuddy
        returns list of lists containing task name, start time,  stop time
        '''

        return_list = []

        # TODO: selectable date ranges
        if date_range == 'today':
            icalbuddy_command = 'eventsToday'

        stdout = self.run_icalbuddy(icalbuddy_command)

        output_list = stdout.split("\n")
        for i in output_list:
            logging.debug("i: %s", i)
            try:
                tag, time = i.split(" | ")
                starttime, endtime = time.split(' - ')
                return_list.append([tag, starttime, endtime])
            except ValueError:
                if i != '':
                    logging.error("Error with cenlendar entry %s", i)
                else:
                    continue

        logging.debug("return_list: %s", return_list)

        return return_list
    ## End iCalBuddy Function
    #

    def collect_tasks_list(self, duration='day') -> int:
        '''
        Collect list of tracked tasks (default to today)
        Store in object variable

        return number of tasks
        '''

        table_dict = []
        date_format = "%Y%m%dT%H%M%SZ"


        cli = [config.CLI_BASE_COMMAND, 'export', ':'+duration]
        stdout = self.execute_cli(cli)

        task_list = json.loads(stdout)

        for task_item in task_list:
            task = {}

            task['starttime'] = datetime.strptime(task_item['start'], date_format)

            # Calculate Duration (skip or active)
            if 'end' in task_item.keys():
                task['stoptime'] = datetime.strptime(task_item['end'], date_format)
                task['duration'] = task['stoptime'] - task['starttime']
            else:
                task['duration'] = 'Active'

            task['id'] = task_item['id']
            task['tag'] = task_item.get('tags', [''])

            table_dict.append(task)

        self.todays_tasks = table_dict
        self.no_of_tasks_tracked = len(table_dict)

        return len(table_dict)

    def return_task_table(self) -> 'tuple[list,int]':
        ''' Return basic list of tasks used to generate list in UI '''

        table_data = []
        max_tag_len = 0

        self.collect_tasks_list()

        for task_item in self.todays_tasks:
            table_data.append([ list_to_str(task_item['tag']) , str(task_item['duration']) ])

            if max_tag_len < len(task_item['tag']):
                max_tag_len = len(task_item['tag'])

        logging.debug("table_data: %s", table_data)

        return table_data, max_tag_len

    def return_task_details(self, values: dict):
        ''' Return details of a specific task '''

        task_no, _ = self.get_tw_taskid_from_timetable(values['timew_table'])
        task = None

        logging.debug("task_no: %s", task_no)

        for task_item in self.todays_tasks:
            logging.debug("task_item: %s", task_item)

            if task_item['id'] == task_no:
                task = task_item
                break

        logging.debug("task: found %s", task)

        return task

    def get_tw_taskid_from_timetable(self, timetable) -> 'tuple[int,int]':
        ''' Collect the TimeWarrior taskid and GUI table id '''

        if timetable != []:
            task_no = self.no_of_tasks_tracked - timetable[0]
            table_no = timetable[0]

        else:
            task_no = 1
            table_no = self.no_of_tasks_tracked-1

        logging.debug("task_no: %s %s ", task_no, table_no)

        return task_no, table_no

    #
    ##### Start methods supporting UI button elements
    @staticmethod
    def button_start(values: dict, cli: str) -> 'tuple[str, str]':
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
    def button_track(values: dict, cli: str) -> 'tuple[str, str]':
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
    def button_stop(values, cli: str) -> 'tuple[str, str]':
        ''' Run buttons starting with "Stop" '''

        cli.append("stop")

        if values['stoptime'] != '':
            cli.append(values['stoptime'])
        result_display = "Stopped Tracking"

        return cli, result_display

    def button_rename(self, values: dict, cli: str) -> 'tuple[str, str]':
        '''
        Run buttons starting with "Rename"
        Change the text of the first tag on a task
        '''

        task = self.return_task_details(values)
        old_description = task['tag'][0]
        taskid = '@' + str(task['id'])

        ### Open window
        new_description = sg.popup_get_text('Rename Task', default_text=old_description)

        if new_description is not None:
            self.execute_cli([config.CLI_BASE_COMMAND, 'tag', taskid, new_description])
            cli = [config.CLI_BASE_COMMAND, 'untag', taskid, old_description]
            result_display = "Renamed task"
        else:
            result_display= "Rename Canceled"

        return cli, result_display

    def button_start_meeting(self, cli: str) -> 'tuple[str, str]':
        ''' Run Start Meeting from calendar info routine '''

        calendarentry = self.get_current_calendar_entry()
        if calendarentry:
            cli.extend(["start", calendarentry])
            result_display = "Started meeting"
        else:
            cli, result_display = error_popup('Nothing available on Calendar')

        return cli, result_display

    def button_continue_delete(self, event: str, values: dict, cli: str) -> 'tuple[str, str]':
        ''' Run commands for Delete or Continue '''

        command = event.lower()
        task_no, _ = self.get_tw_taskid_from_timetable(values['timew_table'])
        cli.extend([command, '@'+str(task_no)])
        result_display = command + " @" + str(task_no)

        return cli, result_display

    def button_modify(self, values: dict, cli: str) -> 'tuple[str, str]':
        ''' Modify start or stop time of a task '''
        # TODO: ability to modify start and stop at time time
        task_no, _ = self.get_tw_taskid_from_timetable(values['timew_table'])
        taskid = '@'+str(task_no)

        if values['starttime'] != "":
            modify_time = values['starttime']
            modify_mode = "start"
        elif values['stoptime'] != "":
            modify_time = values['stoptime']
            modify_mode = "end"
        else: 
            return error_popup('Please enter a time')

        cli.extend(['modify', modify_mode, taskid, modify_time])
        result_display = "Modified " + modify_mode + " time to " + modify_time

        return cli, result_display

    def button_details(self, values: dict):
        ''' Collect and display details of a selected specific task '''
        task = self.return_task_details(values)

        start_time = utc_to_local(task['starttime'])

        layout = [
                    [ sg.Text('Task Tag', size=(8, 1)), sg.InputText( list_to_str(task['tag']) ) ],
                    [ sg.Text('Start Time', size=(8, 1)), \
                        sg.InputText(start_time.strftime("%H:%M:%S")) ],
                    [ sg.Text('Duration', size=(8, 1)), sg.InputText(task['duration']) ],
                    [ sg.Button('Close', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT) ]
                ]

        if 'stoptime' in task.keys():
            stop_time = utc_to_local(task['stoptime'])
            layout.insert(2, [ sg.Text('Stop Time'), \
                sg.InputText(stop_time.strftime("%H:%M:%S")) ])

        sg.Window('Task Details', layout).read(close=True)

        return 0

    def button_celendar_track(self, cli: str) -> list:
        ''' Create Task based on calendar entry from today '''

        calendar_entries = self.get_calendar_entries()

        calendar_columns = ['Tag', 'Start', 'Stop']

        layout = [
            [ sg.Text("Todays Tasks", font=config.GLOBAL_FONT) ],
            [ sg.Table(values=calendar_entries, headings=calendar_columns, max_col_width=40,
                    display_row_numbers=False,
                    justification='left',
                    num_rows=20,
                    key='calendar_entry',
                    tooltip='Todays Data',
                    font=config.GLOBAL_FONT)],
            [ sg.Button('Track', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
                sg.Button('Cancel', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT) ]
        ]

        event, values = sg.Window('Calendar', layout).read(close=True)
        logging.debug("values['calendar_entry']: %s", values['calendar_entry'])

        if event == 'Track' and values['calendar_entry'] != []:
            logging.debug("calendar_entries[values['calendar_entry'][0]]: %s ", \
                calendar_entries[values['calendar_entry'][0]])
            values['taskdesc'] = calendar_entries[values['calendar_entry'][0]][0]
            values['starttime']= calendar_entries[values['calendar_entry'][0]][1]
            values['stoptime'] = calendar_entries[values['calendar_entry'][0]][2]
            values['date'] = ''

            return_data = self.button_track(values, cli)
        elif event == 'Track' and values['calendar_entry'] == []:
            cli, result_display = error_popup("Must Select an entry in list")

            return_data = [ cli, result_display ]

        else:
            cli = None
            result_display = "Canceled"

            return_data = [ cli, result_display ]

        return return_data

    ##### Stop methods supporting UI button elements
    #

    def button_logic(self, event: str, values: dict) -> 'tuple[bytes, str]':
        '''
        Execute Button based events executing TimeWarrior CLI commands
        Command line is extended based on the button selection and outputs
        of the hander functions when used
        '''

        cli = [config.CLI_BASE_COMMAND]

        if event == 'Start Meeting':
            cli, result_display = self.button_start_meeting(cli)
        elif event in 'Start':
            cli, result_display = self.button_start(values, cli)
        elif event == 'Track':
            cli, result_display = self.button_track(values, cli)
        elif event == 'Stop':
            cli, result_display = self.button_stop(values, cli)
        elif event == "Modify":
            # Modify start of current / last task
            cli, result_display = self.button_modify(values, cli)
        elif event == "Fix Start":
            start_time = self.get_current_calendar_starttime()
            cli.extend(['modify', 'start', '@1', start_time])
            result_display = "Modified Start time to " + start_time
        elif event == "Rename":
            cli, result_display = self.button_rename(values, cli)
        elif event in ('Continue', "Delete"):
            cli, result_display = self.button_continue_delete(event, values, cli)
        elif event == "Refresh":
            result_display = "Default: See Results"
        elif event == "Details":
            self.button_details(values)
            result_display = ""
        elif event == "Calendar Track":
            cli, result_display = self.button_celendar_track(cli)
        else:
            result_display = "Button not Matched"
            logging.error("******* Button not Matched '%s' *************", event)

        if cli:
            # TODO: Run more then one command
            result = self.execute_cli(cli)
        else:
            # return null bytes for CLI output if cli is not set
            result = b''

        return result, result_display


####### Start Main Function #############
if __name__ == "__main__":
    pass
