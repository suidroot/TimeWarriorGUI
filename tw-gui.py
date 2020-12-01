#!/usr/bin/which python3
'''
    This Script provide a GUI front-end to the TimeWarror CLI application
    Author: Ben Mason
'''

import subprocess
import re
from datetime import datetime
import PySimpleGUI as sg

# Text encoding
ENCODING = 'utf-8'
# fontSize = 12
DEBUG=False
THEME="Dark Grey 4"

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

def collect_tasks_from_today():
    ''' Gather Tracked time entries from today and return table '''


    expression_1 = '^(.{19})(.+)\s(\d{1,2}:\d{1,2}:\d{1,2})\s{1,2}(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})'
    expression_2 = '(^.{19})(.+)\s(\d{1,2}:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})'

    result = []
    max_tag_len = 0

    cli = ['timew', 'summary']

    stdout = execute_cli(cli)

    output_list = str(stdout, ENCODING).split("\n")

    counter = 0
    end_data = len(output_list)-5

    if DEBUG:
        print (end_data)


    for line in output_list:

        if counter != end_data:
            match = re.search(expression_1, line)
            if DEBUG:
                print ("ex1", counter, line)
        else:
            match = re.search(expression_2, line)
            if DEBUG:
                print ("ex2", counter, line)

        entry_dict = {}

        if match:
            entry_dict['tag'] = match.group(2).strip()
            entry_dict['start_time'] = match.group(3)
            entry_dict['stop_time'] = match.group(4)
            entry_dict['duration'] = match.group(5)

            if max_tag_len < len(entry_dict['tag']):
                max_tag_len = len(entry_dict['tag'])

            if DEBUG:
                print ("matched data: ", entry_dict)

            result.append(entry_dict)

        counter += 1

    if DEBUG:
        print (result)

    table_data = []

    for i in result:
        table_data.append([i['tag'] , i['duration']])

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

    elif event == 'Continue':
        cli.append("continue")
        result_display = "Continuing last Task"

    elif event == "Modify Start":
        cli.extend(['modify', 'start', values['starttime'], '@1'])
        result_display = "Modified Start time to " + values['starttime']

    elif event == "Delete Last":
        cli.extend(['delete', '@1'])
        result_display = "Deleted last Task"
    else:
        result_display = "Default: See Results"


    result = execute_cli(cli)

    return result, result_display


def main():
    ''' Main Function '''
    fields = [ "date", "starttime", "stoptime", "taskdesc" ]

    #
    # Load inital tracked time data
    table_data, tag_len = collect_tasks_from_today()
    active_timer = get_active_timer()

    if DEBUG:
        print(tag_len)
    #
    # Define the window's contents
    sg.theme(THEME)

    timew_summary_columns = ['Tags', 'Duration']

    layout = [
            [ sg.Text("Task:"), sg.Input(key="taskdesc", size=(35,1)) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:"), sg.Input(key="starttime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Stop time:"), sg.Input(key="stoptime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Date: "), sg.Input(key="date", size=(12,1)), sg.Text("EX: 2020-10-01") ]
            ], title='Date')],
            [ sg.Text("")],
            [ sg.Button('Start'), sg.Button('Stop'), sg.Button('Modify Start'), sg.Button('Curr Running'), ],
            [ sg.Button('Start Meeting'), sg.Button('Track'), sg.Button('Continue'),  sg.Button('Delete Last'),],
            [ sg.Text(size=(40,1), key='status_result') ],
            [ sg.MLine(key="cliout", size=(40,8)) ],
            [ sg.Text("Current Tracking:" ), sg.Input(key="curr_tracking", size=(25,1), default_text=active_timer) ],
            [ sg.Text("Todays Time") ],
            [ sg.Table(values=table_data, headings=timew_summary_columns, max_col_width=25,
                    display_row_numbers=False,
                    justification='left',
                    num_rows=20,
                    key='timew_table',
                    tooltip='Todays Data')]
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
        table_data, tag_len = collect_tasks_from_today()
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
