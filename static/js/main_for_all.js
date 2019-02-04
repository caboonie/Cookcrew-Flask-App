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
var noiseThreshold = 13000;
var pauseThreshold = 100;
//var startedTalking = false;
var timeSinceLastStream = 0;
var streamThreshold = 300;
var should_stream = true;
var scroll_amount = 500;
var recording = false;




function streamBuffers( buffers ) {
    // the ONLY time gotBuffers is called is right after a new recording is completed - 
    // so here's where we should set up the download.
    audioRecorder.exportWAV( sendStream );
}



function sendStream( blob ) {
    //instead of downloading, post this file
    console.log("got blob! posting stream!")
    
    var form = new FormData();
    form.append('file', blob, "stream.WAV");
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
            cur_scroll = document.body.scrollTop
            //console.log("stream posted")
            console.log(response.task)
            if (response.task=="record") {
                // data.redirect contains the string URL to redirect to
                console.log("redirecting to record")
                window.location.href = response.url;
            }
            if (response.task == "scroll down"){
                cur_scroll = document.body.scrollTop
                $("html, body").animate({ scrollTop: String(cur_scroll+scroll_amount)+"px" });
            }
            if (response.task == "scroll up"){
                cur_scroll = document.body.scrollTop
                $("html, body").animate({ scrollTop: String(Math.max(cur_scroll-scroll_amount,0))+"px" });
            }
            audioRecorder.clear();
            audioRecorder.record();
            recording = false;
        }
    })
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
    var freqByteData = new Uint8Array(analyserNode.frequencyBinCount);
    analyserNode.getByteFrequencyData(freqByteData); 
    //console.log(freqByteData[2])
    
    var magnitude = 0;
    for(var i=0;i<analyserNode.frequencyBinCount;i++){
        //console.log(freqByteData[i])
        magnitude += freqByteData[i];
    }
    //console.log(magnitude)
    
    if(!recording && magnitude>noiseThreshold){
        recording = true;
        console.log("starting recording")
        audioRecorder.clear();
        audioRecorder.record();
    }
    if(recording){
        timeSinceLastNoise++
        if(magnitude>noiseThreshold){
            timeSinceLastNoise = 0;
        }
        if(timeSinceLastNoise >= pauseThreshold && should_stream){ //don't stream if trying to record speech
            console.log("Streaming audio")
            timeSinceLastNoise = 0
            audioRecorder.stop();
            audioRecorder.getBuffers( streamBuffers );
            
    }
    }

    
    
    rafID = window.requestAnimationFrame( updateAnalysers );
}



function gotStream(stream) {
    inputPoint = audioContext.createGain();

    // Create an AudioNode from the stream.
    realAudioInput = audioContext.createMediaStreamSource(stream);
    audioInput = realAudioInput;
    audioInput.connect(inputPoint);

    analyserNode = audioContext.createAnalyser();
    analyserNode.fftSize = 2048;
    inputPoint.connect( analyserNode );

    audioRecorder = new Recorder( inputPoint );

    zeroGain = audioContext.createGain();
    zeroGain.gain.value = 0.0;
    inputPoint.connect( zeroGain );
    zeroGain.connect( audioContext.destination );

    console.log("starting recording")
    audioRecorder.clear();
    audioRecorder.record();
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
