//  define notes and their frequencies, define border frequencies between notes
let notes = "*A#BC#D#EF#G#A#BC#D#EF#G#A*"
let noteFrequencies = [0, 220, 233, 247, 262, 277, 294, 311, 330, 349, 370, 392, 415, 440, 466, 494, 523, 554, 587, 622, 659, 698, 740, 784, 831, 880, 0]
let borderFrequencies = [214, 227, 240, 255, 270, 286, 303, 321, 340, 360, 381, 404, 428, 453, 480, 509, 540, 572, 606, 642, 680, 720, 762, 808, 856, 906]
let audioBuffer : number[] = []
//  buffer used for storing 400 samples
let sample = 0
//  current sample value as read from microphone pin
let average = 516
//  average sample value (representing 0 amplitude)
let halfCycle = false
//  are we in the first half of the current cycle?
let currentCycleLength = 0
//  length of current cycle (measured in sample periods)
let endOfLastCycle = 0
//  index of sample period, where last full cycle ended
let numberOfCycles = 0
//  count the number of full cycles in audioBuffer
let sumOfCycleLengths = 0
//  sum up the length of all full cycles in audioBuffer (measured in sample periods)
let calculatedFrequency = 0
//  reciprocal of: average cycle length (measured in sample periods) times the length of one sample period (in seconds)
let currentNote = 0
//  index of Note belonging to calculated frequency (used in variables: notes, noteFrequencies[], borderFrequencies[] and recordedNotes[])
let record = false
//  are we currently recording a melody?
let playback = false
//  are we currently playing back a melody?
let recordedNotes : number[] = []
//  list of all recorded notes (indices)
let recordedDurations : number[] = []
//  list of the durations of all recorded notes (as multiples of 0.1 s)
let recentNote = 0
//  recent recorded note (index)
let recentDuration = 0
//  duraction of recent recorded note
basic.forever(function on_forever() {
    
    //  analyze audio in real-time and calculate frequency of the tone measured during the last 0.1 s:
    audioBuffer = []
    //  clear audio buffer
    //  wait for sample period to pass (reserve 104 ms for calculations)
    for (let i = 0; i < 400; i++) {
        //  fill buffer with 400 sample values:
        audioBuffer.push(pins.analogReadPin(AnalogPin.P1))
        //  read microphone pin
        control.waitMicros(250 - 105)
    }
    //  no cycle so far
    endOfLastCycle = 0
    numberOfCycles = 0
    sumOfCycleLengths = 0
    halfCycle = false
    for (let k = 0; k < 400; k++) {
        //  iterate over buffer
        sample = audioBuffer[k]
        //  store current sample in variable
        if (sample < average) {
            //  we are in the "lower half" of a cycle
            halfCycle = true
        }
        
        //  add current cycle length to sum of all cycle length in buffer (measured in sample periods)
        if (halfCycle && sample > average) {
            //  we've been in the "lower half" of a cycle and now read the first value above the average
            halfCycle = false
            //  we just entered the "upper half" of the cycle
            currentCycleLength = k - endOfLastCycle
            //  save length of current cycle (measured in sample periods)
            endOfLastCycle = k
            //  save beginning of new cycle
            numberOfCycles += 1
            //  increase number of counted cycles in buffer
            sumOfCycleLengths += currentCycleLength
        }
        
    }
    calculatedFrequency = numberOfCycles * 4000 / sumOfCycleLengths
    //  calculate the frequency of the tone in buffer (measured in hertz)
    //  find corresponding note in array of frequencies (by comparing to border frequencies between notes)
    currentNote = 0
    while (calculatedFrequency > borderFrequencies[currentNote] && currentNote < borderFrequencies.length) {
        currentNote += 1
    }
    if (record) {
        //  when recording:
        //  reset recent duration
        //  just update duration
        if (currentNote != recentNote) {
            //  if the note has just changed compared to last buffer
            recordedNotes.push(recentNote)
            //  save the recent note...
            recordedDurations.push(recentDuration)
            //  ...and its duration
            recentNote = currentNote
            //  reset recent note
            recentDuration = 0
        } else {
            //  same note as in last buffer
            recentDuration += 1
        }
        
    }
    
})
basic.forever(function on_forever2() {
    //  show name of current note:
    if (!playback) {
        //  turn off during playback
        if (notes.charAt(currentNote) != "#") {
            //  no semi tone
            //  just show the corresponting letter
            basic.showString(notes.charAt(currentNote))
        } else {
            //  semi tone
            //  switch display between letter and "#"
            basic.showString(notes.charAt(currentNote - 1))
            basic.pause(400)
            basic.showString("#")
            basic.pause(400)
        }
        
    }
    
})
input.onButtonPressed(Button.A, function on_button_pressed_a() {
    
    //  start or stop recording a melody:
    //  toggle recording-flag
    if (!playback) {
        //  only record while not in playback-mode
        //  initialize duration of last note
        if (!record) {
            //  no active record: start recording
            led.enable(false)
            //  switch off display
            // #basic.setLedColor(Colors.Red)
            //  set rgb-led to red to indicate recording
            recordedNotes = []
            //  clear any recorded notes
            recordedDurations = []
            //  clear any recorded durations of notes
            recentNote = 0
            //  initialize last note
            recentDuration = 0
        } else {
            //  active record: stop recording
            led.enable(true)
        }
        
        //  enable display
        //  turn off rgb-led
        // #basic.setLedColor(basic.rgbw(0, 0, 0, 0))
        record = !record
    }
    
})
//  signal that playback is finished
//  turn off rgb-led
// #basic.setLedColor(basic.rgbw(0, 0, 0, 0))
input.onButtonPressed(Button.B, function on_button_pressed_b() {
    
    //  start playback of recorded melody:
    record = false
    //  stop any active recording
    playback = true
    //  signal that playback has started
    basic.clearScreen()
    //  clear display
    // #basic.setLedColor(Colors.Green)
    //  set rgb-led to green to indicate playback
    let j = 0
    while (j <= recordedNotes.length - 1) {
        //  iterate over all recorded notes
        //  very short pause to terminate note
        if (recordedDurations[j] > 0) {
            //  only if duration of recorded note exceeds minimal threshold (eliminate short "clicks")
            music.ringTone(noteFrequencies[recordedNotes[j]])
            //  play recorded note
            basic.pause(100 * recordedDurations[j])
            //  wait for 0.1 s times the duration of recorded note
            music.rest(music.beat(BeatFraction.Sixteenth))
        }
        
        j += 1
    }
    playback = false
})
