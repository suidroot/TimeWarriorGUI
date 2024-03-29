#!/usr/bin/which python3
'''
    This Script provide a GUI front-end to the TimeWarror CLI application
    Author: Ben Mason
'''

__author__ = "Ben Mason"
__copyright__ = "Copyright 2022"
__version__ = "2.0.0"
__email__ = "locutus@the-collective.net"
__status__ = "Production"

import logging
from datetime import datetime
import PySimpleGUI as sg
from twguiapi import TwButtonLogic, TwCalendarClass
import config

def validate_date(date_text: str) -> bool:
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

def input_error_check(event, values) -> int:
    ''' Validate inoput values and return an error number of error detected '''

    error_val = 0

    if values['date'] != '':
        if validate_date(values['date']):
            sg.popup('Invalid date please use format "YYYY-MM-DD" data entered:', \
                values['date'])
            error_val = 1
    if values['starttime'] != '':
        if validate_time(values['starttime']):
            sg.popup('Invalid date please use format "HH:MM" data entered:', \
                values['starttime'])
            error_val = 2
    if values['stoptime'] != '':
        if validate_time(values['stoptime']):
            sg.popup('Invalid date please use format "HH:MM" data entered:', \
                values['stoptime'])
            error_val = 3
    if values['duration'] != '':
        if validate_time(values['duration']):
            sg.popup('Invalid date please use format "HH:MM" data entered:', \
                values['duration'])
            error_val = 4
    if values['stoptime'] != '' and values['starttime'] != '' and event == 'Modify':
        sg.popup('Can only change start or end time, clear one of the fields')
        error_val = 5
    if (event in ('Track', 'Start')) and values['taskdesc'] == '':
        sg.popup('Task Name Can not be Empty')
        error_val = 6

    return error_val

def main():
    ''' Main Function '''

    table_data = []

    logging.basicConfig(level=config.LOGGING_LEVEL, format=config.LOGGING_FORMAT)

    if config.ICALBUDDY_ENABLE is True:
        twbuttonlogic = TwCalendarClass()
    else:
        twbuttonlogic = TwButtonLogic()

    input_tfields = [ "date", "starttime", "stoptime", "taskdesc", "duration" ]
    timew_summary_columns = ['Tag', 'Duration']

    #
    # Load inital tracked time data
    twbuttonlogic.collect_tasks_list()

    table_data, tag_len = twbuttonlogic.return_task_table()
    logging.debug("tag_len: %s", tag_len)

    # if empty table set correct column and rows

    table_data.append([" "*27,""])


    active_timer = twbuttonlogic.get_active_timer()

    #
    # Define the window's contents
    sg.theme(config.THEME)

    layout = [
            [ sg.Text("Task:", size=(5, 1), font=config.GLOBAL_FONT), \
                sg.Input(key="taskdesc", size=(35,1), font=config.GLOBAL_FONT) ], \
            [ sg.Frame(layout=[
                [ sg.Text("Start Time:", size=(8, 1), font=config.GLOBAL_FONT), \
                    sg.Input(key="starttime", size=(12,1), font=config.GLOBAL_FONT), \
                    sg.Text("EX: 15:00", font=config.GLOBAL_FONT) ],
                [ sg.Text("Stop time:", size=(8, 1), font=config.GLOBAL_FONT), \
                    sg.Input(key="stoptime", size=(12,1), font=config.GLOBAL_FONT), \
                    sg.Text("EX: 15:00", font=config.GLOBAL_FONT) ],
                [ sg.Text("Duration:", size=(8, 1), font=config.GLOBAL_FONT), \
                    sg.Input(key="duration", size=(12,1), font=config.GLOBAL_FONT), \
                    sg.Text("EX: 0:20", font=config.GLOBAL_FONT) ],
                [ sg.Text("Date:", size=(8, 1), font=config.GLOBAL_FONT), \
                    sg.Input(key="date", size=(12,1), font=config.GLOBAL_FONT), \
                    sg.Text("EX: 2020-10-01", size=(16,1), font=config.GLOBAL_FONT) ]
            ], title='Date') ],
            # Buttons
            [ sg.Button('Start', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
                sg.Button('Stop', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
                sg.Button('Modify', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
                sg.Button('Track', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), ],
            [ sg.Button('Continue', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT),  \
                sg.Button('Delete', size=(config.BUTTON_SIZE, 1),font=config.GLOBAL_FONT), \
                sg.Button('Details', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
                sg.Button('Rename', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT) ], \
            [ sg.Button('Refresh', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), ],
            # Calendar Buttons inserted here if enabled
            # Text Boxes
            [ sg.Text("Current Tracking:", size=(13,1), font=config.GLOBAL_FONT),
              sg.Input(key="curr_tracking", size=(27,1), default_text=active_timer, \
                  font=config.GLOBAL_FONT) ],
            [ sg.MLine(key="cliout", size=(40,8), font=config.GLOBAL_FONT) ],
            [ sg.Text(size=(40,1), key='status_result', font=config.GLOBAL_FONT) ],
            [ sg.Text("Todays Tasks", font=config.GLOBAL_FONT) ],
            [ sg.Table(values=table_data, headings=timew_summary_columns, max_col_width=30,
                    display_row_numbers=False,
                    justification='left',
                    num_rows=20,
                    key='timew_table',
                    tooltip='Todays Data',
                    font=config.GLOBAL_FONT)]
        ]

    if config.ICALBUDDY_ENABLE:
        calendar_buttons = [ sg.Button('Start Meeting', font=config.GLOBAL_FONT), \
            sg.Button('Fix Start', size=(config.BUTTON_SIZE, 1), font=config.GLOBAL_FONT), \
            sg.Button('Calendar Track', font=config.GLOBAL_FONT)]
        layout.insert(4, calendar_buttons)

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
        if input_error_check(event, values) > 0:
            continue

        #
        # Button Logic
        result, result_display = twbuttonlogic.button_logic(event, values)
        logging.debug("button_logic result: %s", result)

        #
        # Update list of tracked time for today
        table_data, tag_len = twbuttonlogic.return_task_table()
        window['timew_table'].update(values=table_data)

        active_timer = twbuttonlogic.get_active_timer()
        window['curr_tracking'].update(active_timer)

        #
        # Return results and Status
        window['status_result'].update(result_display)
        window['cliout'].update(str(result, config.ENCODING))

        #
        # clear input fields
        for i in input_tfields:
            window[i].update('')

    window.close()

    return 0

####### Start Main Function #############
if __name__ == "__main__":
    main()
