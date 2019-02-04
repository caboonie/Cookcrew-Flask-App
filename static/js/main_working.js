/* Copyright 2013 Chris Wilson

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

window.AudioContext = window.AudioContext || window.webkitAudioContext;

var audioContext = new AudioContext();
var audioInput = null,
    realAudioInput = null,
    inputPoint = null,
    audioRecorder = null;
var rafID = null;
var analyserContext = null;
var canvasWidth, canvasHeight;
var recIndex = 0;
var timeSinceLastNoise = 0;
var noiseThreshold = 175;
var timeThreshold = 200;
var startedTalking = false;

/* TODO:

- offer mono option
- "Monitor input" switch
*/

//Where is this function used? GUess it's not
function saveAudio() {
    audioRecorder.exportWAV( doneEncoding );
    // could get mono instead by saying
    // audioRecorder.exportMonoWAV( doneEncoding );
}

function gotBuffers( buffers ) {
    // the ONLY time gotBuffers is called is right after a new recording is completed - 
    // so here's where we should set up the download.
    audioRecorder.exportWAV( doneEncoding );
}

function storeAndRedirect( buffer) {
    console.log("storing and directing!")
    document.cookie = buffer;
    window.location.href = "/speech-post";
}

function BinaryToString(binary) {
    var error;

    try {
        return decodeURIComponent(escape(binary));
    } catch (_error) {
        error = _error;
        if (error instanceof URIError) {
            return binary;
        } else {
            throw error;
        }
    }
}

function doneEncoding( blob ) {
    //instead of downloading, post this file
    console.log("blob!")
    var myReader = new FileReader();
    myReader.readAsArrayBuffer(blob)
    
    myReader.addEventListener("loadend", function(e)
    {
        var buffer = e.srcElement.result;//arraybuffer object
        console.log("finished reading blob ")
        var form = new FormData();
        form.append('file', blob, "audio.wav");
        //form.append('title', "randoTitle");
        //Chrome inspector shows that the post data includes a file and a title.     
        $.ajax({
            type: 'POST',
            url: '/speech',
            data: form,
            cache: false,
            processData: false,
            contentType: false,
            //dataType: "json",
            success:function(response) {
                console.log("redirecting? "+  response.redirect)
                console.log(response.stay)
                if (response.redirect) {
                    // data.redirect contains the string URL to redirect to
                    console.log("redirecting")
                    window.location.href = response.url;
                }
                else if( response.stay ){
                    console.log("try again")
                    document.getElementById("record").style.display = "block";
                    document.getElementById("processing").style.display = "none";
                    /*
                    console.log(typeof message[0])
                    if(typeof message[0] != "text"){
                        var header = document.createElement('h3');
                        header.innerHTML = message[0]
                        document.append(header)
                        var list = document.createElement('ul');
                        for(entry in message[1]){
                            var item = document.createElement('li');
                            item.innerHTML = entry[0]+" needs "+entry[1]+" "+entry[2]+" of "+entry[3]
                            list.append(item)
                        }
                        document.append(list)
                    }
                    */
                   
                    document.getElementById("message").innerHTML = response.message;
                    

                } 
                else {
                    // data.form contains the HTML for the replacement form
                    console.log("overwriting")
                    document.write(response.template); 
                }   
            }
        })
       
    });
    console.log("read blob ")

}

function stopRecording(){
    //toggle off if recording
    if (document.getElementById("record").classList.contains("recording")){
        console.log("stopping recording")
        audioRecorder.stop();
        document.getElementById("record").classList.remove("recording");
        audioRecorder.getBuffers( gotBuffers );
        document.getElementById("analyser").style.display = "none";
        document.getElementById("processing").style.display = "block";
    }
}

function toggleRecording( e ) {
    if (e.classList.contains("recording")) {
        // stop recording
        stopRecording();
    } else {
        // start recording
        
        if (!audioRecorder)
            return;
        timeSinceLastNoise = 0;
        e.classList.add("recording");
        audioRecorder.clear();
        audioRecorder.record();
        document.getElementById("analyser").style.display = "block";
        document.getElementById("record").style.display = "none";
    }
}

function convertToMono( input ) {
    var splitter = audioContext.createChannelSplitter(2);
    var merger = audioContext.createChannelMerger(2);

    input.connect( splitter );
    splitter.connect( merger, 0, 0 );
    splitter.connect( merger, 0, 1 );
    return merger;
}

function cancelAnalyserUpdates() {
    window.cancelAnimationFrame( rafID );
    rafID = null;
}

function updateAnalysers(time) {
    if (!analyserContext) {
        var canvas = document.getElementById("analyser");
        canvasWidth = canvas.width;
        canvasHeight = canvas.height;
        analyserContext = canvas.getContext('2d');
    }

    // analyzer draw code here
    {
        var SPACING = 3;
        var BAR_WIDTH = 1;
        var numBars = Math.round(canvasWidth / SPACING);
        var freqByteData = new Uint8Array(analyserNode.frequencyBinCount);


        analyserNode.getByteFrequencyData(freqByteData); 

        analyserContext.clearRect(0, 0, canvasWidth, canvasHeight);
        analyserContext.fillStyle = '#F6D565';
        analyserContext.lineCap = 'round';
        var multiplier = analyserNode.frequencyBinCount / numBars;

        //console.log(startedTalking)
        timeSinceLastNoise++;
        if (timeSinceLastNoise >= timeThreshold && startedTalking){
            stopRecording();
        }
        // Draw rectangle for each frequency bin.
        var maxMag = 0;
        for (var i = 0; i < numBars; ++i) {
            var magnitude = 0;
            var offset = Math.floor( i * multiplier );
            // gotta sum/average the block, or we miss narrow-bandwidth spikes
            for (var j = 0; j< multiplier; j++)
                magnitude += freqByteData[offset + j];
            magnitude = magnitude / multiplier;
            var magnitude2 = freqByteData[i * multiplier];
            analyserContext.fillStyle = "hsl( " + Math.round((i*360)/numBars) + ", 100%, 25%)";
            analyserContext.fillRect(i * SPACING, Math.round(canvasHeight/2+magnitude/2), BAR_WIDTH, -magnitude);
            //console.log("magnitude"+magnitude)
            if (magnitude>maxMag){
                maxMag = magnitude
            }
            if (magnitude >= noiseThreshold){
                //console.log("magnitude"+magnitude)
                if(!startedTalking && timeSinceLastNoise>10 && document.getElementById("record").classList.contains("recording")){ //buffer to prevent click from counting the mouse click
                    console.log("Started Talking")
                    startedTalking = true;
                }
                else if(!startedTalking && document.getElementById("record").classList.contains("recording")){
                    noiseThreshold = magnitude+10; //this is the background level
                    console.log("resetting noiseThreshold")
                }
                timeSinceLastNoise = 0;
            }
        }
        //console.log("max magnitude"+maxMag)
    }
    
    rafID = window.requestAnimationFrame( updateAnalysers );
}

function toggleMono() {
    if (audioInput != realAudioInput) {
        audioInput.disconnect();
        realAudioInput.disconnect();
        audioInput = realAudioInput;
    } else {
        realAudioInput.disconnect();
        audioInput = convertToMono( realAudioInput );
    }

    audioInput.connect(inputPoint);
}

function gotStream(stream) {
    inputPoint = audioContext.createGain();

    // Create an AudioNode from the stream.
    realAudioInput = audioContext.createMediaStreamSource(stream);
    audioInput = realAudioInput;
    audioInput.connect(inputPoint);

//    audioInput = convertToMono( input );

    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 2048;
    inputPoint.connect( analyserNode );

    audioRecorder = new Recorder( inputPoint );

    zeroGain = audioContext.createGain();
    zeroGain.gain.value = 0.0;
    inputPoint.connect( zeroGain );
    zeroGain.connect( audioContext.destination );
    updateAnalysers();
}

function initAudio() {
        if (!navigator.getUserMedia)
            navigator.getUserMedia = navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
        if (!navigator.cancelAnimationFrame)
            navigator.cancelAnimationFrame = navigator.webkitCancelAnimationFrame || navigator.mozCancelAnimationFrame;
        if (!navigator.requestAnimationFrame)
            navigator.requestAnimationFrame = navigator.webkitRequestAnimationFrame || navigator.mozRequestAnimationFrame;

    navigator.getUserMedia(
        {
            "audio": {
                "mandatory": {
                    "googEchoCancellation": "false",
                    "googAutoGainControl": "false",
                    "googNoiseSuppression": "false",
                    "googHighpassFilter": "false"
                },
                "optional": []
            },
        }, gotStream, function(e) {
            alert('Error getting audio');
            console.log(e);
        });
}

window.addEventListener('load', initAudio );
