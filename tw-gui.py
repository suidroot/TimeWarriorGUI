#!/usr/bin/which python3

import PySimpleGUI as sg
import subprocess
from datetime import datetime
# Text encoding
encoding = 'utf-8'
# fontSize = 12
debug=False
theme="Dark Grey 4"

my_tags = ["", "status", "usergroup", "teammeeting" ]


def validate_date(date_text):
    return_val = False

    try:
        datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        return_val = True
        
    return return_val

def validate_time(time_text):
    return_val = False

    try:
        datetime.strptime(time_text, '%H:%M')
    except ValueError:
        return_val = True
        
    return return_val

''' Executing TW CLI '''
def call_tw(tw_command, starttime='', stoptime='', date='', taskdesc=''):
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
    
    if (debug): 
        print(cli)

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if (debug): 
        print(stdout)

    return stdout

''' Get current calendar '''
def get_calendar_entry():

    cli = ['/usr/local/bin/icalbuddy',
        '-npn', 
        '-ea', 
        '-nc', 
        '-b', '', 
        '-ps', '" - "',
        '-eep', 'url,location,notes,attendees,datetime',
        '-ic', 'Calendar',
        'eventsNow', ]

    if (debug): 
        print (cli)

    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if (debug): 
        print(stdout)
        print(stderr)

    return str(stdout, encoding)


''' Main Function '''
def main():

    fields = [ "date", "starttime", "stoptime", "taskdesc", "tag" ]

    sg.theme(theme)
    # Define the window's contents
    layout = [  
            [ sg.Text("Task:"), sg.Input(key="taskdesc") ],
            #[ sg.Text("Tag:"), sg.Input(key="tag", size=(10,1)) ],
            [ sg.Text("Tag:"), sg.Combo(my_tags, key="tag", size=(10,1)) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:"), sg.Input(key="starttime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Stop time:"), sg.Input(key="stoptime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Date:"), sg.Input(key="date", size=(12,1)), sg.Text("EX: 2020-10-01") ]
            ], title='Date')],
            [ sg.Text("")],
            [ sg.Button('Start Meeting'), sg.Button('Track'), sg.Button('Continue') ],
            [ sg.Button('Start'), sg.Button('Stop'), sg.Button('Curr Running') ],
            [ sg.Text(size=(40,1), key='status_result') ],
            [ sg.MLine(key="cliout", size=(40,8)) ]
        ]

    window = sg.Window('Timewarrior Tracking', layout)

    # font = "Helvetica "  + str(fontSize)
    # window['text'].update(font=font)

    while True:
        event, values = window.read()

        # Clean up and Close
        if event == sg.WINDOW_CLOSED or event == 'Quit':
            break

        if values['date'] != '':
            if (validate_date(values['date'])):
                sg.popup('Invalid date please use format "YYYY-MM-DD" data entered:', values['date'])
                continue
        if values['starttime'] != '':
            if (validate_time(values['starttime'])):
                sg.popup('Invalid date please use format "HH:MM" data entered:', values['starttime'])
                continue
        if values['stoptime'] != '':
            if (validate_time(values['stoptime'])):
                sg.popup('Invalid date please use format "HH:MM" data entered:', values['stoptime'])
                continue


        if values['tag'] != '':
            task_description = [ '"' + values['taskdesc'] + '"', values['tag'] ]
        else:
            task_description = [ '"' + values['taskdesc'] + '"' ]

        #
        # Button Logic
        #
        if event == 'Start Meeting':
            result = call_tw('meeting')
            result_display = "Started meeting"
        elif event in 'Start':
            if (values['starttime'] != ''):
                result = call_tw('starttime', 
                    starttime=values['starttime'], 
                    taskdesc=task_description)
                result_display = "Started: " + values['taskdesc'] + " at " + values['starttime']
            else:
                result = call_tw('startnow', 
                    taskdesc=task_description)
                result_display = "Started: " + values['taskdesc']
        elif event == 'Track':
            result = call_tw('track',
                date=values['date'],
                starttime=values['starttime'], 
                stoptime=values['stoptime'], 
                taskdesc=task_description)
            result_display = "Tracked: " + values['taskdesc']
        elif event == 'Stop':
            if (values['stoptime'] != ''):
                result = call_tw('stop', 
                    stoptime=values['stoptime'])
            else:
                result = call_tw('stop')
            result_display = "Stopped Tracking"
        elif event == 'Continue':
            result = call_tw('continue')
            result_display = "Continuing last Task"
        else:
            result = call_tw('running')
            result_display = "See Results"

        # Return results and Status
        window['status_result'].update(result_display)
        window['cliout'].update(str(result, encoding))

        # clear input fields
        for i in fields:
            window[i].update('')

    window.close()

    return 0

####### Start Main Function #############
if __name__ == "__main__":
    main()