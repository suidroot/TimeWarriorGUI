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

my_tags = ["", "status", "usergroup", "teammeeting" ]
timew_sum_columns = ['Tags', 'Duration']

''' Get current calendar '''
def get_calendar_entry():
    cli = ['/usr/local/bin/icalbuddy',
        '-npn', '-ea', '-nc', '-b', '',
        '-ps', '" - "',
        '-eep', 'url,location,notes,attendees,datetime',
        '-ic', 'Calendar', 'eventsNow', ]
    if DEBUG:
        print (cli)

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if DEBUG:
        print(stdout)
        print(stderr)

    return str(stdout, ENCODING)

''' Gather Tracked tiume entries and return table '''
def run_timew_sum():
    expression_1 = '^(.{19})(.+)\s(\d{1,2}:\d{1,2}:\d{1,2})\s{1,2}(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})'
    #expression_1 = '(^.{19})(.+)\s(\d{1,2}:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})'
    expression_2 = '(^.{19})(.+)\s(\d{1,2}:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})\s(\d{1,2}\:\d{1,2}:\d{1,2})'

    result = []
    max_tag_len = 0

    cli = ['timew', 'summary']

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

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

''' Validate Date is correct format '''
def validate_date(date_text):
    return_val = False

    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return_val = True

    return return_val

''' Validate Time is correct format '''
def validate_time(time_text):
    return_val = False

    try:
        datetime.strptime(time_text, '%H:%M')
    except ValueError:
        return_val = True

    return return_val

''' Executing TW CLI '''
def call_tw(tw_command, starttime='', stoptime='', date='', taskdesc='', taskid='@1'):
    cli = ['timew']

    if tw_command == 'startnow':
        cli.extend(["start"])
        cli.extend(taskdesc)
    elif tw_command == 'meeting':
        cli.extend(["start", get_calendar_entry()])
    elif tw_command == 'starttime':
        cli.extend(["start", starttime])
        cli.extend(taskdesc)
    elif tw_command == 'track':
        if date != '':
            starttime = date + "T" + starttime
            stoptime = date + "T" + stoptime
        cli.extend(['track' , starttime, '-', stoptime])
        cli.extend(taskdesc)
    elif tw_command == 'stop':
        cli.append("stop")
    elif tw_command == 'continue':
        cli.append("continue")
    elif tw_command == 'modify':
        cli_temp = ['modify']
        if starttime != '':
            cli_temp.extend(['start', starttime])
        if stoptime != '':
            cli_temp.extend(['stop', stoptime])
        cli_temp.append(taskid)

        cli.extend(cli_temp)

    if DEBUG:
        print(cli)

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if DEBUG:
        print(stdout)
        print(stderr)

    return stdout

''' Main Function '''
def main():

    fields = [ "date", "starttime", "stoptime", "taskdesc" ]

    #
    # Load inital tracked time data
    table_data, tag_len = run_timew_sum()

    if DEBUG:
        print(tag_len)

    sg.theme(THEME)

    #
    # Define the window's contents
    layout = [
            [ sg.Text("Task:"), sg.Input(key="taskdesc") ],
            #[ sg.Text("Tag:"), sg.Input(key="tag", size=(10,1)) ],
            #[ sg.Text("Tag:"), sg.Combo(my_tags, key="tag", size=(10,1)) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:"), sg.Input(key="starttime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Stop time:"), sg.Input(key="stoptime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Date:"), sg.Input(key="date", size=(12,1)), sg.Text("EX: 2020-10-01") ]
            ], title='Date')],
            [ sg.Text("")],
            [ sg.Button('Start Meeting'), sg.Button('Track'), sg.Button('Continue') ],
            [ sg.Button('Start'), sg.Button('Stop'), sg.Button('Modify'), sg.Button('Curr Running'), ],
            [ sg.Text(size=(40,1), key='status_result') ],
            [ sg.MLine(key="cliout", size=(40,8)) ],
            [ sg.Table(values=table_data, headings=timew_sum_columns, max_col_width=25,
                    #auto_size_columns=True,
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
        #
        # Update list of tracked time for today
        table_data, tag_len = run_timew_sum()

        if DEBUG:
            print(table_data)
        #
        # Read Button triggers
        event, values = window.read()

        # Clean up and Close
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

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

        task_description = [ '"' + values['taskdesc'] + '"' ]

        #
        # Button Logic
        if event == 'Start Meeting':
            result = call_tw('meeting')
            result_display = "Started meeting"
        elif event in 'Start':
            if values['starttime'] != '':
                result = call_tw('starttime', starttime=values['starttime'], taskdesc=task_description)
                result_display = "Started: " + values['taskdesc'] + " at " + values['starttime']
            else:
                result = call_tw('startnow', taskdesc=task_description)
                result_display = "Started: " + values['taskdesc']
        elif event == 'Track':
            result = call_tw('track', date=values['date'], starttime=values['starttime'], stoptime=values['stoptime'], taskdesc=task_description)
            result_display = "Tracked: " + values['taskdesc']
        elif event == 'Stop':
            if values['stoptime'] != '':
                result = call_tw('stop', stoptime=values['stoptime'])
            else:
                result = call_tw('stop')
            result_display = "Stopped Tracking"
        elif event == 'Continue':
            result = call_tw('continue')
            result_display = "Continuing last Task"
        elif event == 'Modify':
            result = call_tw('modify', starttime=values['starttime'], stoptime=values['stoptime'])

            result_display = "Modifed: Last task. New"
            if values['starttime'] != '':
                result_display += " start:" + values['starttime']
            if values['stoptime'] != '':
                result_display += " stop: " + values['stoptime']

        else:
            result = call_tw('running')
            result_display = "See Results"

        window['timew_table'].update(values=table_data)

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
