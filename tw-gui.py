#!/usr/bin/which python3
'''
    This Script provide a GUI front-end to the TimeWarror CLI application
    Author: Ben Mason
'''

import subprocess
import json
from datetime import datetime
import PySimpleGUI as sg

# Astetics
THEME="Dark Grey 4"
GLOBAL_FONT='Any 11'

# Enable Debug output
DEBUG=False

# Global Constants
ENCODING = 'utf-8'
NO_OF_TASKS_TRACKED=0

def execute_cli(cli):
    ''' Execute commands on CLI returns STDOUT '''

    if DEBUG:
        print(cli)

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if DEBUG:
        print(stdout)
        print(stderr)

    return stdout

def get_active_timer():
    ''' Get Actively tracked task '''

    cli = ['timew']
    stdout = execute_cli(cli)

    output_list = str(stdout, ENCODING).split("\n")
    if DEBUG:
        print("out time output_list: ", output_list)

    if output_list[0].strip() == "There is no active time tracking.":
        result = "no active time tracking"
    else:
        result = output_list[0][9:].replace('"', '')

    return result

def get_calendar_entry():
    ''' Use icalbuddy to get the meeting on your calendar right now '''

    cli = ['/usr/local/bin/icalbuddy',
        '-npn', '-ea', '-nc', '-b', '',
        '-ps', '" - "',
        '-eep', 'url,location,notes,attendees,datetime',
        '-ic', 'Calendar', 'eventsNow', ]
    if DEBUG:
        print (cli)

    stdout = execute_cli(cli)

    return str(stdout, ENCODING)

def collect_tasks_list(duration='day'):
    ''' Collect list of tracked tasks (default to today) '''

    global NO_OF_TASKS_TRACKED

    max_tag_len = 0
    table_data = []

    cli = ['timew', 'export', ':'+duration]
    stdout = execute_cli(cli)

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

    NO_OF_TASKS_TRACKED = len(table_data)

    return table_data, max_tag_len


def validate_date(date_text):
    ''' Validate Date is correct format '''

    return_val = False

    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return_val = True

    return return_val

def validate_time(time_text):
    ''' Validate Time is correct format '''

    return_val = False

    try:
        datetime.strptime(time_text, '%H:%M')
    except ValueError:
        return_val = True

    return return_val

def button_logic(event, values):
    ''' Execute Button based events executing TimeWarrior CLI commands '''

    cli = ['timew']

    if event == 'Start Meeting':
        cli.extend(["start", get_calendar_entry()])
        result_display = "Started meeting"

    elif event in 'Start':
        cli.append("start")

        if values['starttime'] != '':
            cli.append(values['starttime'])
            result_display = "Started: " + values['taskdesc'] + " at " + values['starttime']
        else:
            result_display = "Started: " + values['taskdesc']

        cli.append(values['taskdesc'])

    elif event == 'Track':

        if values['date'] != '':
            starttime = values['date'] + "T" + values['starttime']
            stoptime = values['date'] + "T" + values['stoptime']
        else:
            starttime = values['starttime']
            stoptime = values['stoptime']

        cli.extend(['track' , starttime, '-', stoptime, values['taskdesc']])

        result_display = "Tracked: " + values['taskdesc']

    elif event == 'Stop':
        cli.append("stop")

        if values['stoptime'] != '':
            cli.append(values['stoptime'])
        result_display = "Stopped Tracking"

    # Modify start of current / last task
    elif event == "Modify Start":
        cli.extend(['modify', 'start', values['starttime'], '@1'])
        result_display = "Modified Start time to " + values['starttime']

    elif event == "Rename":
        if values['timew_table'] != []:
            table_no = values['timew_table'][0]
            task_no = NO_OF_TASKS_TRACKED - table_no
            taskid = '@'+str(task_no)
        else:
            taskid = '@1'
            table_no = NO_OF_TASKS_TRACKED-1

        table_data, tag_len = collect_tasks_list()
        old_description = table_data[table_no][0]

        ### Open window
        new_description = sg.popup_get_text('Rename Task', default_text=old_description)

        if (new_description != None):
            result = execute_cli(['timew', 'tag', taskid, new_description])
            cli = ['timew', 'untag', taskid, old_description]
            result_display = "Renamed task"
        else:
            result_display= "Rename Canceled"

    elif event == 'Continue' or event == "Delete":
        command = event.lower()
        cli.append(command)

        if values['timew_table'] != []:
            task_no = NO_OF_TASKS_TRACKED - values['timew_table'][0]
            cli.append('@'+str(task_no))

            result_display = command + " @" + str(task_no)
        else:
            cli.append('@1')

            result_display = command + " last task"

    else:
        result_display = "Default: See Results"

    result = execute_cli(cli)

    return result, result_display


def main():
    ''' Main Function '''
    fields = [ "date", "starttime", "stoptime", "taskdesc" ]

    #
    # Load inital tracked time data
    table_data, tag_len = collect_tasks_list()
    # if empty table set correct column and rows
    if table_data == []:
        table_data = [[" "*25,""]]

    active_timer = get_active_timer()

    if DEBUG:
        print(tag_len)
    #
    # Define the window's contents
    sg.theme(THEME)

    timew_summary_columns = ['Tags', 'Duration']

    layout = [
            [ sg.Text("Task:", font=GLOBAL_FONT), sg.Input(key="taskdesc", size=(35,1), font=GLOBAL_FONT) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:", font=GLOBAL_FONT), sg.Input(key="starttime", size=(12,1), font=GLOBAL_FONT), sg.Text("EX: 15:00", font=GLOBAL_FONT) ],
                [ sg.Text("Stop time:", font=GLOBAL_FONT), sg.Input(key="stoptime", size=(12,1), font=GLOBAL_FONT), sg.Text("EX: 15:00", font=GLOBAL_FONT) ],
                [ sg.Text("Date: ", font=GLOBAL_FONT), sg.Input(key="date", size=(12,1), font=GLOBAL_FONT), sg.Text("EX: 2020-10-01", font=GLOBAL_FONT) ]
            ], title='Date')],
            [ sg.Button('Start', font=GLOBAL_FONT), sg.Button('Stop', font=GLOBAL_FONT), sg.Button('Modify Start', font=GLOBAL_FONT), sg.Button('Curr Running', font=GLOBAL_FONT), ],
            [ sg.Button('Start Meeting', font=GLOBAL_FONT), sg.Button('Track', font=GLOBAL_FONT), sg.Button('Continue', font=GLOBAL_FONT),  sg.Button('Delete', font=GLOBAL_FONT),],
            [ sg.Button('Rename', font=GLOBAL_FONT) ], 
            [ sg.Text(size=(40,1), key='status_result', font=GLOBAL_FONT) ],
            [ sg.MLine(key="cliout", size=(40,8), font=GLOBAL_FONT) ],
            [ sg.Text("Current Tracking:", font=GLOBAL_FONT), sg.Input(key="curr_tracking", size=(25,1), default_text=active_timer, font=GLOBAL_FONT) ],
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

    # font = "Helvetica "  + str(fontSize)
    # window['text'].update(font=font)

    #
    ####### Event Loop
    while True:

        if DEBUG:
            print(table_data)
        #
        # Read Button triggers
        event, values = window.read()

        # Clean up and Close
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        #
        # Input Validation
        if values['date'] != '':
            if validate_date(values['date']):
                sg.popup('Invalid date please use format "YYYY-MM-DD" data entered:', values['date'])
                continue
        if values['starttime'] != '':
            if validate_time(values['starttime']):
                sg.popup('Invalid date please use format "HH:MM" data entered:', values['starttime'])
                continue
        if values['stoptime'] != '':
            if validate_time(values['stoptime']):
                sg.popup('Invalid date please use format "HH:MM" data entered:', values['stoptime'])
                continue
        if (event == 'Track' or event == 'Start') and values['taskdesc'] == '':
            sg.popup('Task Name Can not be Empty')
            continue

        #
        # Button Logic
        result, result_display = button_logic(event, values)

        if DEBUG:
            print(result)

        #
        # Update list of tracked time for today
        table_data, tag_len = collect_tasks_list()
        window['timew_table'].update(values=table_data)

        active_timer = get_active_timer()
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
