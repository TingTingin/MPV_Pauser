import schedule
from python_mpv_jsonipc import MPV
import PySimpleGUI as sg
from rakutenma import RakutenMA
import json
import os

eng_sub = 1  # default english sub sid
jp_sub = 2  # default japanese sub sid
eng_wait_per_second = 1  # default the per word wait time in secs for english
jp_wait_per_second = 1   # default the per word wait time in secs for japanese
mpv_loc = 0  # this is the location of your mpv folder
cwd = os.path.dirname(os.path.abspath(__file__))  # find script directory
copy_subs = False

with open(f"{cwd}\\settings.txt", "r") as f:
    socket = f.readline()

# mpv = MPV()
mpv = MPV(start_mpv=False, ipc_socket=socket)

rma = RakutenMA()
rma.load("model_ja.min.json")  # loads the sentence model


def unpause():
    global broke
    mpv.command("set_property", "pause", "no")
    broke = True
    return schedule.CancelJob


def return_sub_length(sub):

    rma_string = rma.tokenize(sub)
    remove_strings = ['P-', 'X', 'M-', 'Q-n', 'W']
    rma_string = [word for word in rma_string if not any(i in word[1] for i in remove_strings)]
    print(rma_string)
    print("japanese word count", len(rma_string))
    return len(rma_string)


def jpn_toggle():  # toggles plugin on and off
    global mode
    global enable
    global run_count
    run_count += 1

    if mode == "eng" and run_count < 3:

        mpv.sid = jp_sub
        mode = "jpn"
        enable = 1
        mpv.command("show-text", "Pausing on Japanese")

    elif mode == "jpn" and run_count < 3:

        mpv.sid = eng_sub
        mode = "eng"
        enable = 1
        mpv.command("show-text", "Pausing on English")

    elif run_count == 3:

        enable = 0
        run_count = 0
        mpv.command("show-text", "Disabled MPV Pauser")

# do not edit


run_count = 0
mode = "eng"
enable = 0
current_play_time = 0
broke = False
json_data = 1
default_ran = False


# do not edit


def swap_button_check():
    if mode == "jpn" and mpv.sid != jp_sub:
        mpv.sid = jp_sub

    elif mode == "eng" and mpv.sid != eng_sub:
        mpv.sid = eng_sub


def mpv_pauser():
    paused = mpv.core_idle  # check if player is paused

    if not paused:

        global event
        global values
        global swap
        print("running")
        sub_start = mpv.sub_start
        sub_text = mpv.sub_text
        sub_end = mpv.sub_end

        ran_if = False
        if isinstance(sub_start, float) and sub_text:  # check that sub has text and a time
            if sub_start <= current_play_time <= sub_start + .3 and at_end is False:  # checks if within window of first .3 seconds of a sub to pause
                ran_if = True
                mpv.command("set_property", "pause", "yes")  # pauses within .3 sec window from sub start
                mpv.command("frame-step")  # move up one frame since sometimes the pause happens one frame before text is shown on screen

            elif at_end is True and sub_end - .11 <= current_play_time:
                ran_if = True
                mpv.command("set_property", "pause", "yes")

            if ran_if:
                if mode == "eng" and mpv.sid == eng_sub:  # if in english mode
                    sub_array = sub_text.split()  # splits subs into individual words to count later
                    eng_words = len(sub_array)
                    eng_wait = eng_words * eng_wait_per_second
                    schedule.every(round(eng_wait, 2)).seconds.do(unpause)

                    print(round(eng_wait, 2))

                    while True:
                        win_read_ops(100)
                        schedule.run_pending()
                        paused = mpv.core_idle
                        if not paused:
                            unpause()
                            break

                elif mode == "jpn" and mpv.sid == jp_sub:
                    jp_word_count = return_sub_length(sub_text)

                    if jp_word_count == 0:
                        jp_word_count = 1

                    jp_wait = (jp_word_count * jp_wait_per_second)
                    schedule.every(round(jp_wait, 2)).seconds.do(unpause)
                    print(round(jp_wait, 2))

                    while True:

                        win_read_ops(100)
                        schedule.run_pending()
                        paused = mpv.core_idle
                        if not paused:
                            unpause()
                            break

                if not broke:
                    mpv.command("set_property", "pause", "no")

                if mode == "eng" and swap is True and mpv.sid == eng_sub:
                    mpv.sid = jp_sub

                elif mode == "jpn" and swap is True and mpv.sid == jp_sub:
                    mpv.sid = eng_sub

                if not at_end:
                    wait_time = sub_end - current_play_time
                    if wait_time < 0:  # checks if wait is a negative number this sometimes happens when subs are very close together
                        wait_time = .1  # if wait is a negative number sets it to instead wait for a short time
                        print("was negative")

                    win_read_ops(wait_time*1000)

                    if mode == "eng":
                        mpv.sid = eng_sub

                    if mode == "jpn":
                        mpv.sid = jp_sub

                if at_end:
                    win_read_ops(310)


@mpv.property_observer("time-pos")
def update_time(name, value):
    global current_play_time
    current_play_time = mpv.command("get_property", "time-pos")


# @mpv.property_observer("sub-text")
# def update_time(name, value):
#
#     if copy_subs:
#         try:
#             pyperclip.copy(mpv.sub_text)
#
#         except pyperclip.PyperclipException:
#             pass


@mpv.on_key_press("U")
def on_handler():
    global mode
    jpn_toggle()


@mpv.on_key_press("2")
def up_handler():

    global jp_wait_per_second
    global eng_wait_per_second

    if mode == "jpn":
        jp_wait_per_second += .05
        window["Jpn Pause"].update(value=round(jp_wait_per_second, 2))
        mpv.command("show-text", f"Pausing {round(jp_wait_per_second, 2)} (Secs) Per Japanese Word")

    if mode == "eng":
        eng_wait_per_second += .05
        window["Eng Pause"].update(value=round(eng_wait_per_second, 2))
        mpv.command("show-text", f"Pausing {round(eng_wait_per_second, 2)} (Secs) Per English Word")


@mpv.on_key_press("1")
def down_handler():

    global jp_wait_per_second
    global eng_wait_per_second

    if mode == "jpn" and jp_wait_per_second >= .05:
        jp_wait_per_second -= .05
        window["Jpn Pause"].update(value=round(jp_wait_per_second, 2))
        mpv.command("show-text", f"Pausing {round(jp_wait_per_second, 2)} (Secs) Per Japanese Word")

    if mode == "eng" and eng_wait_per_second >= .05:
        eng_wait_per_second -= .05
        window["Eng Pause"].update(value=round(eng_wait_per_second, 2))
        mpv.command("show-text", f"Pausing {round(eng_wait_per_second, 2)} (Secs) Per English Word")

    if mode == "eng" and eng_wait_per_second <= .06:
        mpv.command("show-text", f"Cant Go Any Lower than {round(eng_wait_per_second, 2)} (Secs) English")

    if mode == "jpn" and jp_wait_per_second <= .06:
        mpv.command("show-text", f"Cant Go Any Lower than {round(jp_wait_per_second, 2)} (Secs) Japanese")


sg.theme('lightgrey1')

layout = [

    [sg.FileBrowse(key="File_browse", initial_folder="", button_text="Select Video", size=(67, 1), enable_events=True)],
    [sg.Button(key="Toggle", button_text="Toggle", size=(67, 1), enable_events=True)],
    [sg.Text("Target Lang Sid (Japanese)", size=(20, 1)),
     sg.Spin(list(range(0, 20)), key="target_lang_sid", initial_value=2, size=(5, 1)), sg.Text("Jpn Pause length", size=(13, 1)), sg.Spin(list(x/20 for x in range(0, 100)), key="Jpn Pause", initial_value=2.0, size=(5, 1), enable_events=True), sg.Text("Pause At End", size=(12, 1)), sg.Check(key="At_End", text="", checkbox_color="lightgrey", enable_events=True)],
    [sg.Text("Native Lang Sid (English)", size=(20, 1)),
     sg.Spin(list(range(0, 20)), key="native_lang_sid", initial_value=1, size=(5, 1)), sg.Text("Eng Pause length", size=(13, 1)), sg.Spin(list(x/20 for x in range(0, 100)), key="Eng Pause", initial_value=2.0, size=(5, 1), enable_events=True), sg.Text("Swap Subs", size=(12, 1), enable_events=True), sg.Check(key="Swap", text="", checkbox_color="lightgrey", enable_events=True)],

]
window = sg.Window(title="MPV Pauser", layout=layout, use_default_focus=False)


def win_read_ops(func_time_out=50):

    global swap
    global at_end
    global eng_sub
    global jp_sub
    global event
    global values
    global json_data
    global default_ran
    global jp_wait_per_second
    global eng_wait_per_second

    while True:

        event, values = window.read(timeout=func_time_out)
        swap = values["Swap"]
        at_end = values["At_End"]

        if event == sg.WIN_CLOSED:
            break

        if event == "File_browse" and values['File_browse']:
            mpv.loadfile(values['File_browse'])
            eng_sub = values['native_lang_sid']
            jp_sub = values['target_lang_sid']
            window.minimize()

        if event == "native_lang_sid" or "target_lang_sid":
            eng_sub = values['native_lang_sid']
            jp_sub = values['target_lang_sid']

        if event == "Swap":

            swap = values["Swap"]
            at_end = values["At_End"]
            window["At_End"].update(value=False)
            swap_button_check()
            print(swap)

        if event == "At_End":

            at_end = values["At_End"]
            swap = values["Swap"]
            window["Swap"].update(value=False)
            print(at_end)

        if event == "Jpn Pause" and isinstance(values["Jpn Pause"], float):
            jp_wait_per_second = values["Jpn Pause"]
            mpv.command("show-text", f"Pausing {round(jp_wait_per_second, 2)} (Secs) Per Japanese Word")

        if event == "Eng Pause":
            eng_wait_per_second = values["Eng Pause"]
            mpv.command("show-text", f"Pausing {round(eng_wait_per_second, 2)} (Secs) Per English Word")

        if not os.path.exists(f"{cwd}\\settings.json"):
            file = open("settings.json", "w")
            json.dump(values, file)
            file.close()

        if event == "Toggle":
            jpn_toggle()

        try:
            if default_ran is False:
                with open(f"{cwd}\\settings.json", "r") as loaded_json:

                    json_data = json.load(loaded_json)

                    for key in json_data:
                        print("values", json_data[key])

                        if key == "File_browse":
                            continue
                        elif isinstance(json_data[key], (float, bool, int)):
                            window[key].update(json_data[key])

                    default_ran = True

        except json.decoder.JSONDecodeError as e:
            print(e)

        finally:

            with open(f"{cwd}\\settings.json", "w") as settings_json:

                json.dump(values, settings_json)
        return


while True:
    win_read_ops(50)
    if enable == 1:  # checks if plugin is enabled in mpv
        mpv_pauser()
