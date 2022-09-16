

const http = require("http");
const url = require("url");
const fs = require("fs");
const path = require('path');
//const Game = require("./scripts/Game");

let EXPIRATION_MS = 600000;
let BOOT_CHECK_PERIOD_MS = 1000;
let TEAMMATE_BOOT_CODE = 1;

// For now, there is only one game
//let game = new Game();

// Schedule the timer that checks whether players need to be booted
//setInterval(bootStalePlayers, BOOT_CHECK_PERIOD_MS);

http.createServer(function (req, res) {

    let q = url.parse(req.url, true);
    let filename = q.pathname;

    if (q.pathname === "/"){
        filename = "./pages/UI.html";
    } else {
        if (filename.startsWith("/")) {
            filename = filename.substring(1);
        }
        if (filename.indexOf('\0') !== -1) {
            res.writeHead(403, {"Content-Type": "text/html"});
            return res.end("403 Forbidden");
        }
        filename = path.normalize(filename).replace(/^(\.\.(\/|\\|$))+/, '');
    }

    if (req.method === "POST"){
        let body = [];

        req.on("data", data => {

            body.push(data);
        }).on("end", () => {
            body = Buffer.concat(body).toString();

            // Currently, all messages to the server are heartbeat messages
            console.log("Got a POST with body " + body);
            //let response = handleHeartbeatMessage(body);

            if (body.includes("END")){
                endGame(body.split(",")[0]);
                res.writeHead(200, {"Content-Type": "text/html"});
                res.write("OK");
                res.end();
                return;
            }

            if (body.includes("instructions")) {
                const spawn = require("child_process").spawn;
                const pythonProcess = spawn("python", ["python/instruction_calculator.py", body.split(",")[0]]);
                let pythonScriptOutput = "";
                pythonProcess.stdout.on("data", function(data) {
                    pythonScriptOutput = data;
                    console.log("Python script gave me " + data);
                    // Select only the observation portion to send, so that any debug stuff printed before does not get sent
                    let startIndexOfClient = pythonScriptOutput.indexOf("client:");
                    let startIndex = startIndexOfClient > -1 ? startIndexOfClient + "client:".length : 0;
                    pythonScriptOutput = pythonScriptOutput.toString().substring(startIndex);
                    res.writeHead(200, {"Content-Type": "text/html"});
                    res.write(pythonScriptOutput);
                    res.end();
                });
                console.log("Python process started");
                return;
            }

            // If the post body does not fit the expected format, do not launch a python script
            if (body.split(",").length !== 4 && !body.includes("advice")) {
               return;
            }

            // For now, just run the python script from here
            const spawn = require("child_process").spawn;
            const pythonProcess = spawn("python", ["python/game_manager.py", body]);
            let pythonScriptOutput = "";
            pythonProcess.stdout.on("data", function(data) {
                pythonScriptOutput = data;
                console.log("Python script gave me " + data);
                // Select only the observation portion to send, so that any debug stuff printed before does not get sent
                let startIndexOfClient = pythonScriptOutput.indexOf("client:");
                let startIndex = startIndexOfClient > -1 ? startIndexOfClient + "client:".length : 0;
                pythonScriptOutput = pythonScriptOutput.toString().substring(startIndex);
                res.writeHead(200, {"Content-Type": "text/html"});
                res.write(pythonScriptOutput);
                res.end();
            });
            console.log("Python process started");
        });
    }

    if (req.method === "GET"){
        getAndSendFile(req, res, filename);
    }

}).listen(8090);

function getAndSendFile(req, res, filename){

    // Need to check if this is a byteserving request
    try {
        let responseHeaders = {};
        let stat = fs.statSync(filename);
        let rangeRequest = readRangeHeader(req.headers['range'], stat.size);

        // If 'Range' header exists, we will parse it with Regular Expression.
        if (rangeRequest != null) {
            console.log(rangeRequest);
            console.log(stat.size);
            let start = rangeRequest.Start;
            let end = rangeRequest.End;

            let fileBytes = fs.readFileSync(filename);

            if (start === end) {
                end = stat.size - 1;
            }

            // If the range can't be fulfilled.
            if (start >= stat.size || end > stat.size) {
                // Indicate the acceptable range.
                responseHeaders['Content-Range'] = 'bytes */' + stat.size; // File size.

                // Return the 416 'Requested Range Not Satisfiable'.
                res.writeHead(416, responseHeaders);
                res.end();
                return null;
            }

            // Indicate the current range.
            responseHeaders['Content-Range'] = 'bytes ' + start + '-' + end + '/' + stat.size;
            responseHeaders['Content-Length'] = start === end ? 1 : (end - start + 1);
            responseHeaders['Content-Type'] = "video/mp4";
            responseHeaders['Accept-Ranges'] = 'bytes';
            responseHeaders['Cache-Control'] = 'no-cache';

            // Return the 206 'Partial Content'.
            res.writeHead(206, responseHeaders);
            console.log(responseHeaders["Content-Length"]);
            res.write(fileBytes.slice(start, end + 1));
            res.end();
            return;
        }
    } catch (error) {
        console.log("Can't support byteserving. Will give entire file.");
    }
    console.log("Starting normal serve");
    fs.readFile(filename, function(err, data) {
        if (err) {
            res.writeHead(404, {"Content-Type": "text/html"});
            return res.end("404 Not Found");
        }
        let extension = filename.substring(filename.indexOf(".", 2) + 1, filename.length);
        switch (extension){
            // Glorified text
            case "html": res.writeHead(200, {"Content-Type": "text/html"}); break;
            case "txt": res.writeHead(200, {"Content-Type": "text/html"}); break;
            case "css": res.writeHead(200, {"Content-Type": "text/css"}); break;
            // Images
            case "gif": res.writeHead(200, {"Content-Type": "image/gif"}); break;
            case "jpg": res.writeHead(200, {"Content-Type": "image/jpeg"}); break;
            case "jpeg": res.writeHead(200, {"Content-Type": "image/jpeg"}); break;
            case "png": res.writeHead(200, {"Content-Type": "image/png"}); break;
            // audio
            case "wav": res.writeHead(200, {"Content-Type": "audio/wav"}); break;
            case "mid": res.writeHead(200, {"Content-Type": "text/midi"}); break;
            // application
            case "json": res.writeHead(200, {"Content-Type": "application/json"}); break;
            case "js": res.writeHead(200, {"Content-Type": "application/javascript"}); break;

            default: res.writeHead(200, {"Content-Type": "text/html"}); break;
        }
        // Check if we need to adjust for player id
        if (data.includes("playerName = \"XXXXXX\"")) {
            if (url.parse(req.url, true).query.pid === undefined) {
                fs.readFile("./pages/NoId.html", function (err, data) {
                    res.write(data);
                    res.end();
                });
            } else {
                fs.readFile(filename, "utf8", function (err, data) {
                    data = data.replace("playerName = \"XXXXXX\"", "playerName = \"" + url.parse(req.url, true).query.pid + "\"");
                    res.write(data);
                    res.end();
                });
            }
        } else {
            res.write(data);
            res.end();
        }
    });
}

function endGame(name){
    console.log("ending game for "+name);
    const d = new Date();
    let month = d.getMonth()+1;
    let day = d.getDate();
    let year = d.getFullYear();
    let hour = d.getHours();
    let min = d.getMinutes();
    let date = month+day+year+"_"+hour+min;

    // Find which deck index was used in order to name the completed game file correctly
    var fs = require('fs');

    // Sometimes this method is called again after the files have already been moved.
    // Detect this and avoid a crash in these cases.
    if (!fs.existsSync("./games_files/" + name)) {
        console.log("Won't move game files since the target directory doesn't exists. These files were likely already moved.");
        return;
    }

    let deckType = fs.readFileSync("./games_files/" + name + "/deck_type.txt");

    var oldPath = "./games_files/"+name;
    var newPath = "./completed_games/"+name+"__"+deckType+"__"+date;
    
    //move file from game_files to completed_games
    //this assumes the directory 'completed_games' already exists
    fs.rename(oldPath, newPath, (err) => {
        if (err){
            console.log('Rename complete!');
        }
        
    });
}

// https://www.codeproject.com/Articles/813480/HTTP-Partial-Content-In-Node-js
function readRangeHeader(range, totalLength) {
    /*
     * Example of the method 'split' with regular expression.
     *
     * Input: bytes=100-200
     * Output: [null, 100, 200, null]
     *
     * Input: bytes=-200
     * Output: [null, null, 200, null]
     */

    if (range == null || range.length === 0)
        return null;

    var array = range.split(/bytes=([0-9]*)-([0-9]*)/);
    var start = parseInt(array[1]);
    var end = parseInt(array[2]);
    var result = {
        Start: isNaN(start) ? 0 : start,
        End: isNaN(end) ? (totalLength - 1) : end
    };

    if (!isNaN(start) && isNaN(end)) {
        result.Start = start;
        result.End = totalLength - 1;
    }

    if (isNaN(start) && !isNaN(end)) {
        result.Start = totalLength - end;
        result.End = totalLength - 1;
    }

    return result;
}