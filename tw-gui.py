#!/usr/bin/which python3

import PySimpleGUI as sg
import subprocess
from datetime import datetime
# Text encoding
encoding = 'utf-8'
# fontSize = 12
debug=False
theme="Dark Grey 4"

'''
    Executing TW CLI

'''
def call_tw(tw_command, starttime='', stoptime='', date='', taskdesc=''):
    cli = ['timew']

    if tw_command == 'startnow':
        cli.extend(["start", taskdesc])
    elif tw_command == 'meeting':
        taskdesc = get_calendar_entry()
        cli.extend(["start", taskdesc])
    elif tw_command == 'starttime':
        cli.extend(["start", starttime, taskdesc])
    elif tw_command == 'track':
        if date != '':
            starttime = date + "T" + startime
            stoptime = date + "T" + stoptime
        cli.extend(['track' , starttime, ' - ', stoptime, taskdesc])
    elif tw_command == 'stop':
        cli.append("stop")
        
    process = subprocess.Popen(cli, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    if (debug): 
        print(stdout)

    return stdout

'''
    Get current calendar
'''
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

    return str(stdout, encoding)


'''
Main Function
'''
def main():

    fields = [ "date", "starttime", "stoptime", "taskdesc" ]

    sg.theme(theme)
    # Define the window's contents
    layout = [  
            [ sg.Text("Task:"), sg.Input(key="taskdesc") ],
            #[ sg.Text("Tag:"), sg.Input(key="tag", size=(10,1)) ],
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:"), sg.Input(key="starttime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Stop time:"), sg.Input(key="stoptime", size=(12,1)), sg.Text("EX: 15:00") ],
                [ sg.Text("Date:"), sg.Input(key="date", size=(12,1)), sg.Text("EX: 2020-10-01") ]
            ], title='Date')],
            [ sg.Text("")],
            [ sg.Button('Start Meeting'), sg.Button('Track') ],
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

        # if values['tag'] != '':
        #     task_description = '"' + values['taskdesc'] + '"' + ', "' + values['tag'] + '"'
        # else:
        task_description = '"' + values['taskdesc'] + '"'

        #
        # Button Logic
        #
        if event == 'Start Meeting':
            result = call_tw('meeting')
            result_display = "Started meeting"
        elif event == 'Start':
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
                starttime=values['starttime'], 
                stoptime=values['stoptime'], 
                taskdesc=task_description)
        elif event == 'Stop':
            if (values['starttime'] != ''):
                result = call_tw('stop', 
                    stoptime=values['stoptime'])
            else:
                result = call_tw('stop')
            result_display = "Stopped Tracking"
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