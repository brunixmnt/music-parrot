# define notes and their frequencies, define border frequencies between notes
notes = "*A#BC#D#EF#G#A#BC#D#EF#G#A*"
noteFrequencies = [0,
    220,
    233,
    247,
    262,
    277,
    294,
    311,
    330,
    349,
    370,
    392,
    415,
    440,
    466,
    494,
    523,
    554,
    587,
    622,
    659,
    698,
    740,
    784,
    831,
    880,
    0]
borderFrequencies = [214,
    227,
    240,
    255,
    270,
    286,
    303,
    321,
    340,
    360,
    381,
    404,
    428,
    453,
    480,
    509,
    540,
    572,
    606,
    642,
    680,
    720,
    762,
    808,
    856,
    906]
audioBuffer: List[number] = []
# buffer used for storing 400 samples
sample = 0
# current sample value as read from microphone pin
average = 516
# average sample value (representing 0 amplitude)
halfCycle = False
# are we in the first half of the current cycle?
currentCycleLength = 0
# length of current cycle (measured in sample periods)
endOfLastCycle = 0
# index of sample period, where last full cycle ended
numberOfCycles = 0
# count the number of full cycles in audioBuffer
sumOfCycleLengths = 0
# sum up the length of all full cycles in audioBuffer (measured in sample periods)
calculatedFrequency = 0
# reciprocal of: average cycle length (measured in sample periods) times the length of one sample period (in seconds)
currentNote = 0
# index of Note belonging to calculated frequency (used in variables: notes, noteFrequencies[], borderFrequencies[] and recordedNotes[])
record = False
# are we currently recording a melody?
playback = False
# are we currently playing back a melody?
recordedNotes: List[number] = []
# list of all recorded notes (indices)
recordedDurations: List[number] = []
# list of the durations of all recorded notes (as multiples of 0.1 s)
recentNote = 0
# recent recorded note (index)
recentDuration = 0
# duraction of recent recorded note

def on_forever():
    global audioBuffer, endOfLastCycle, numberOfCycles, sumOfCycleLengths, halfCycle, sample, currentCycleLength, calculatedFrequency, currentNote, recentNote, recentDuration
    # analyze audio in real-time and calculate frequency of the tone measured during the last 0.1 s:
    audioBuffer = []
    # clear audio buffer
    # wait for sample period to pass (reserve 104 ms for calculations)
    for i in range(400):
        # fill buffer with 400 sample values:
        audioBuffer.append(pins.analog_read_pin(AnalogPin.P1))
        
        # read microphone pin
        control.wait_micros(250 - 105)
    # no cycle so far
    endOfLastCycle = 0
    numberOfCycles = 0
    sumOfCycleLengths = 0
    halfCycle = False
    for k in range(400):
        # iterate over buffer
        sample = audioBuffer[k]
        # store current sample in variable
        if sample < average:
            # we are in the "lower half" of a cycle
            halfCycle = True
        # add current cycle length to sum of all cycle length in buffer (measured in sample periods)
        if halfCycle and sample > average:
            # we've been in the "lower half" of a cycle and now read the first value above the average
            halfCycle = False
            # we just entered the "upper half" of the cycle
            currentCycleLength = k - endOfLastCycle
            # save length of current cycle (measured in sample periods)
            endOfLastCycle = k
            # save beginning of new cycle
            numberOfCycles += 1
            # increase number of counted cycles in buffer
            sumOfCycleLengths += currentCycleLength
    calculatedFrequency = numberOfCycles * 4000 / sumOfCycleLengths
    # calculate the frequency of the tone in buffer (measured in hertz)
    # find corresponding note in array of frequencies (by comparing to border frequencies between notes)
    currentNote = 0
    while calculatedFrequency > borderFrequencies[currentNote] and currentNote < len(borderFrequencies):
        currentNote += 1
    if record:
        # when recording:
        # reset recent duration
        # just update duration
        if currentNote != recentNote:
            # if the note has just changed compared to last buffer
            recordedNotes.append(recentNote)
            # save the recent note...
            recordedDurations.append(recentDuration)
            # ...and its duration
            recentNote = currentNote
            # reset recent note
            recentDuration = 0
        else:
            # same note as in last buffer
            recentDuration += 1
basic.forever(on_forever)

def on_forever2():
    # show name of current note:
    if not (playback):
        # turn off during playback
        if notes.char_at(currentNote) != "#":
            # no semi tone
            # just show the corresponting letter
            basic.show_string(notes.char_at(currentNote))
        else:
            # semi tone
            # switch display between letter and "#"
            basic.show_string(notes.char_at(currentNote - 1))
            basic.pause(400)
            basic.show_string("#")
            basic.pause(400)
basic.forever(on_forever2)

def on_button_pressed_a():
    global recordedNotes, recordedDurations, recentNote, recentDuration, record
    # start or stop recording a melody:
    # toggle recording-flag
    if not (playback):
        # only record while not in playback-mode
        # initialize duration of last note
        if not (record):
            # no active record: start recording
            led.enable(False)
            # switch off display
            ##basic.setLedColor(Colors.Red)
            # set rgb-led to red to indicate recording
            recordedNotes = []
            # clear any recorded notes
            recordedDurations = []
            # clear any recorded durations of notes
            recentNote = 0
            # initialize last note
            recentDuration = 0
        else:
            # active record: stop recording
            led.enable(True)
            # enable display
            # turn off rgb-led
            ##basic.setLedColor(basic.rgbw(0, 0, 0, 0))
        record = not (record)
input.on_button_pressed(Button.A, on_button_pressed_a)

def on_button_pressed_b():
    global record, playback
    # start playback of recorded melody:
    record = False
    # stop any active recording
    playback = True
    # signal that playback has started
    basic.clear_screen()
    # clear display
    ##basic.setLedColor(Colors.Green)
    # set rgb-led to green to indicate playback
    j = 0
    while j <= len(recordedNotes) - 1:
        # iterate over all recorded notes
        # very short pause to terminate note
        if recordedDurations[j] > 0:
            # only if duration of recorded note exceeds minimal threshold (eliminate short "clicks")
            music.ring_tone(noteFrequencies[recordedNotes[j]])
            # play recorded note
            basic.pause(100 * recordedDurations[j])
            # wait for 0.1 s times the duration of recorded note
            music.rest(music.beat(BeatFraction.SIXTEENTH))
        j += 1
    playback = False
    # signal that playback is finished
    # turn off rgb-led
    ##basic.setLedColor(basic.rgbw(0, 0, 0, 0))
input.on_button_pressed(Button.B, on_button_pressed_b)
