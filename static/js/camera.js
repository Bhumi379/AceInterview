navigator.mediaDevices.getUserMedia({ video: true })
.then(function(stream) {

    const video = document.getElementById("video")
    video.srcObject = stream

})
.catch(function(error) {

    console.log("Camera access denied")

})