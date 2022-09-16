let canvas = document.getElementById("canvas");
let ctx = canvas.getContext("2d");
addEventListeners();
let paintStackManager = PaintStackManager.create(canvas, "#000000");
// For now, we'll initially build the UI to only allow button controls of cards.
let mouseManager = MouseManager.create(canvas);

const ANIMATION_DURATION_MS = 990;
const ANIMATION_FRAME_DURATION_MS = 15;
let currentAnimationProgress = 1;

let clueAnimationBoxCardIndices = [];
let clueAnimationProgress = 0;
let clueText = "";

// Fields regarding the current game state
let numberOfInformationTokens = 0;
let numberOfStrikes = 0;
let deckSize = 0;
let fireworks = {};
let humanCardRanks = [1,2,3,4,5]; //set this to be the ranks of the cards in the user's hand
let humanCardColors = [1,2,3,4,5]; //set this to be the colors of the cards in the user's hand
let humanCardObjects = [];
let botCardRanks= [1,2,3,4,5]; //set this to be the ranks of the cards in the bot's hand
let botCardColors= [0,0,0,0,0]; //set this to be the colors of the cards in the bot's hand
let botCardObjects = [];
let discardPileObject = [];
let discardPileCards = [];
// TODO adjust this relative to canvasWidth, canvasHeight and retrieve it through a getter like the remaining cards table?
let discardPilePosition = Point.create(1150, 280);
let selectedCard = null;
let selectedCardOldPosition = null;
let fireworkCards = [];
let lifeTokens = -1;
let informationTokens = -1;
let possibleMoves = [];
let cardKnowledgeHumanObjects = [];
//let cardKnowledgeHuman_color = [];
let cardKnowledgeHuman_rank = [];
let cardKnowledgeBotObjects = []; 
//let cardKnowledgeBot_color = []; 
let cardKnowledgeBot_rank = []; 
let botsLastMove = null;
let prevDeckSize = 40;
let instructions = null;
let instructionsText = [];
let instructionDiv = document.getElementById("instructionDiv");
let instruction1 = document.getElementById("instruction1");
let instruction2 = document.getElementById("instruction2");
let gameOver = false;
let deckType = 0;
let participantGroup = 0;

// Participant groups
let CONTROL = 0;
let INSTRUCTION = 1;
let PRE_CORRECTION = 2;
let POST_CORRECTION = 3;

let feedbackDiv = document.getElementById("feedbackDiv");
let feedbackTextDiv = document.getElementById("feedbackText");
let feedbackTextAnimationProgress = 0;

//card placeholders
let placeHolders = {};
let discardPileHolder = null;
let placeHolderColors = ["W", "Y", "B", "G", "R"];

let videoIndex = -1;
let videoDiv = document.getElementById("videoDiv");
let backButton = document.getElementById("back");
let forwardButton = document.getElementById("forward");
let hanabiVideo1 = document.getElementById("hanabiVideo1");
let hanabiVideo2 = document.getElementById("hanabiVideo2");
let hanabiVideo3 = document.getElementById("hanabiVideo3");
let hanabiVideo4Instruction = document.getElementById("hanabiVideo4Instruction");
let hanabiVideo4PreCorrection = document.getElementById("hanabiVideo4PreCorrection");
let hanabiVideo4PostCorrection = document.getElementById("hanabiVideo4PostCorrection");
let videoHeader = document.getElementById("videoHeader");

let ALL_LIFE_TOKENS_GONE_MESSAGE = "The last life token was lost on the latest play.";
let DECK_GONE_MESSAGE = "There are no more cards in the deck left to draw.";
let GAME_WON_MESSAGE = "A perfect score was achieved."

let cachedInstructionObservation = null;
let hasSatisfiedMinimumEndGameWait = false;
let MINIMUM_END_GAME_WAIT_MILLISECONDS = 8000;

// TODO should these be flipped around, not assigning height to width and vice versa?
let canvasWidth = canvas.height;
let canvasHeight = canvas.width;

function initialize() {

    // Determine participant group
    let lastDigitOfPlayerName = parseInt(playerName.substring(playerName.length - 1, playerName.length));
    if (!isNaN(lastDigitOfPlayerName) && lastDigitOfPlayerName >= 0 && lastDigitOfPlayerName < 4) {
        participantGroup = lastDigitOfPlayerName;
    }

    // Don't display instructions until there are some to display
    instructionDiv.style.display = "none";
    feedbackDiv.style.display = "none";

    if (!(canvas == null)){
        canvas = document.getElementById("canvas");
        canvasWidth = canvas.width;
        canvasHeight = canvas.height;
        // add in cards to indicate where the piles will be
        for (let color of placeHolderColors) {
            let position = getFireworkPositionByColor(color);
            placeHolders[color] = Card.create(color, 0, position.getX(), position.getY());
            paintStackManager.register(placeHolders[color], placeHolders[color].paint);
        }

        //create discard pile
        discardPileHolder = Card.create(Card.WHITE, -1, discardPilePosition.getX(), discardPilePosition.getY());
        paintStackManager.register(discardPileHolder, discardPileHolder.paint); 

        paintStackManager.paint();
        
        // Since the server might take a second to initialize the game, show the please wait text until there is
        // an observation to paint.
        paintStackManager = PaintStackManager.create(canvas, "#000000");
        ctx.font = "50pt Calibri";
        ctx.textAlign = "center";
        ctx.fillText("Please wait...", canvasWidth/2, canvasHeight/2);
    }

    updateVideoFromIndex();

}

function loadSurvey() {
    if (participantGroup === CONTROL) {
        window.location = "https://jhuapl.az1.qualtrics.com/jfe/form/SV_9YnIrhRCbYyeyQ6";
    } else {
        window.location = "https://jhuapl.az1.qualtrics.com/jfe/form/SV_9GOVUkWqrwYsr8q";
    }
}

function launchVideos() {
    videoIndex = 0;
    updateVideoFromIndex();
}

function advanceVideo() {
    videoIndex++;
    if (videoIndex >= 4) {
        videoIndex = -1;
    }
    updateVideoFromIndex();
}

function backVideo() {
    if (videoIndex > 0) {
        videoIndex--;
    }
    updateVideoFromIndex();
}

function closeVideo() {
    videoIndex = -1;
    updateVideoFromIndex();
}

function updateVideoFromIndex() {

    let videoCount = participantGroup === CONTROL ? 3 : 4;

    videoHeader.innerHTML = "Introductory video (" + (videoIndex + 1) + " of " + videoCount + ")";

    hanabiVideo1.pause();
    hanabiVideo2.pause();
    hanabiVideo3.pause();
    hanabiVideo4Instruction.pause();
    hanabiVideo4PreCorrection.pause();
    hanabiVideo4PostCorrection.pause();

    if (videoIndex < 0 || (videoIndex === 3 && participantGroup === CONTROL)) {
        videoDiv.style.display = "none";
    } else {
        videoDiv.style.display = "block";
        backButton.style.display = videoIndex !== 0 ? "block" : "none";
        forwardButton.innerHTML = videoIndex === 3 || (videoIndex === 2 && participantGroup === CONTROL) ? "Close" : "Next";
        hanabiVideo1.style.display = videoIndex === 0 ? "block" : "none";
        hanabiVideo2.style.display = videoIndex === 1 ? "block" : "none";
        hanabiVideo3.style.display = videoIndex === 2 ? "block" : "none";
        hanabiVideo4Instruction.style.display = videoIndex === 3 && participantGroup === INSTRUCTION ? "block" : "none";
        hanabiVideo4PreCorrection.style.display = videoIndex === 3 && participantGroup === PRE_CORRECTION ? "block" : "none";
        hanabiVideo4PostCorrection.style.display = videoIndex === 3 && participantGroup === POST_CORRECTION ? "block" : "none";
    }
}

function resizeCanvas(){
    //redraws the canvas when the window gets resized
    redraw()
}

function redraw(){

    canvas = document.getElementById("canvas");
    canvasWidth = canvas.width;
    canvasHeight = canvas.height;
    paintStackManager = PaintStackManager.create(canvas, "#000000");

    // Draw the firework piles
    for (let color of placeHolderColors) {
        let position = getFireworkPositionByColor(color);
        placeHolders[color] = Card.create(color, fireworkCards[color], position.getX(), position.getY());
        placeHolders[color].rank = fireworkCards[color];
        placeHolders[color].isFaceUp = true;
        paintStackManager.register(placeHolders[color], placeHolders[color].paint);
    }

    //create discard pile
    discardPilePosition = Point.create(5*canvasWidth/6, canvasHeight/3);
    discardPileHolder = Card.create(Card.WHITE, -1, discardPilePosition.getX(), discardPilePosition.getY());
    paintStackManager.register(discardPileHolder, discardPileHolder.paint); 

    //draw cards on canvas
    // To simplify things, clear out all old mouse manager objects
    mouseManager.clear();
    for (let i = 0; i < humanCardObjects.length; i++) {
        let card = humanCardObjects[i];
        let updatedCard = Card.create(card.color, card.rank, (7 * canvasWidth / 10) - 120 * i, canvasHeight - 300);
        //updatedCard.isFaceUp = true;
        paintStackManager.register(updatedCard, updatedCard.paint);
        mouseManager.register(updatedCard, (deltaPoint) => {
            if (gameOver) {
                return;
            }
            updatedCard.translate(deltaPoint);
            paintStackManager.paint();
            updatedCard.paint(canvas, ctx);
        });
    }

    for (let i=0; i<botCardObjects.length; i++) {
        let card = botCardObjects[i]
        let updatedCard = Card.create(card.color,card.rank,(7*canvasWidth/10)-120*i, 30)
        updatedCard.isFaceUp = true;
        botCardObjects[i] = updatedCard;
        paintStackManager.register(updatedCard, updatedCard.paint);
    }

    //draw discard cards on canvas
    if (discardPileObject.length){
        discardPileHolder.rank = discardPileObject.at(-1).rank;
        discardPileHolder.color = discardPileObject.at(-1).color;
        discardPileHolder.isFaceUp = true;
    }

    //draw played firework cards
    for (let i=0; i<cardKnowledgeHumanObjects.length; i++){
        let hint = cardKnowledgeHumanObjects[i];
        let hintObj = HintBox.create(hint.colorKnowledge, hint.rankKnowledge, (7*canvasWidth/10)-120*i, canvasHeight-200);
        paintStackManager.register(hintObj, hintObj.paint);
    }
    for (let i=0; i<cardKnowledgeBotObjects.length; i++){
        let hint = cardKnowledgeBotObjects[i];
        let hintObj = HintBox.create(hint.colorKnowledge, hint.rankKnowledge, (7*canvasWidth/10)-120*i,130);
        paintStackManager.register(hintObj, hintObj.paint);
    }
    
    //draw number of life and information tokens left
    let lifeTokenPosition = getLifeTokenBoxPosition();
    lifeTokensObj = TokenBox.create("L", lifeTokenPosition.getX(), lifeTokenPosition.getY());
    paintStackManager.register(lifeTokensObj,lifeTokensObj.paint);
    let infoTokenPosition = getInfoTokenBoxPosition();
    infoTokensObj = TokenBox.create("I", infoTokenPosition.getX(), infoTokenPosition.getY());
    paintStackManager.register(infoTokensObj,infoTokensObj.paint);
    
    //draw remaining cards in deck
    createCardsRemainingTable();
    
    //update with bots last move
    if (botsLastMove == null){
        document.getElementById('botsMove').innerHTML = "Has not gone yet";
    }else{
        switch(botsLastMove["action_type"]){
            case "REVEAL_COLOR":
                switch(botsLastMove["color"]){
                    case "W":
                        document.getElementById('botsMove').innerHTML = "Gave hint of color - White";
                        break;
                    case "Y":
                        document.getElementById('botsMove').innerHTML = "Gave hint of color - Yellow";
                        break;
                    case "B":
                        document.getElementById('botsMove').innerHTML = "Gave hint of color - Blue";
                        break;
                    case "G":
                        document.getElementById('botsMove').innerHTML = "Gave hint of color - Green";
                        break;
                    case "R":
                        document.getElementById('botsMove').innerHTML = "Gave hint of color - Red";
                        break;
                } 
                break;
            case "REVEAL_RANK":
                document.getElementById('botsMove').innerHTML = "Gave hint of rank "+(botsLastMove["rank"]+1).toString();
                break;
            case "DISCARD":
                document.getElementById('botsMove').innerHTML = "Discarded card";
                break;
            case "PLAY":
                //check if legal move 
                let idx = isLegalMove(botsLastMove);
                if (idx > -1){
                    document.getElementById('botsMove').innerHTML = "Played card ";
                }else{
                    document.getElementById('botsMove').innerHTML = "Tried to play unplayable card";
                }
                break;
        }
    }

    paintStackManager.paint();

    // Paint the clue boxes if there are any
    paintClueBoxes();

}

function paintClueBoxes() {
    ctx.globalAlpha = 1;
    for (let index of clueAnimationBoxCardIndices) {
        ctx.fillStyle = "#FFFFFF";
        ctx.beginPath();
        let marginWidth = 6;
        let margin = Point.create(marginWidth, marginWidth);
        let location = getHumanCardPositionByIndex(index).sub(margin);
        ctx.strokeRect(location.getX(), location.getY(), (Card.PIXEL_WIDTH + 2 * marginWidth) * sigmoid(clueAnimationProgress), Card.PIXEL_HEIGHT + 2 * marginWidth);
        ctx.stroke();
    }
    // Paint clue text
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "24px Arial";
    let location = getHumanCardPositionByIndex(2).sub(Point.create(-Card.PIXEL_WIDTH / 2, 20));
    console.log(clueText);
    ctx.fillText(clueText, location.getX(), location.getY());
}

function showFeedbackWithAnimation(text) {
    let parts = text.split(" ");
    feedbackTextAnimationProgress = 0;
    let interval = setInterval(function() {
        let textToShow = "";
        for (let i = 0; i <= feedbackTextAnimationProgress * parts.length; i++) {
            textToShow += parts[i] + " ";
        }
        feedbackTextDiv.innerHTML = textToShow;
        feedbackTextAnimationProgress += ANIMATION_FRAME_DURATION_MS / ANIMATION_DURATION_MS;
    }, ANIMATION_FRAME_DURATION_MS);
    setTimeout(function() {
        clearInterval(interval);
        feedbackTextDiv.innerHTML = text;
    }, ANIMATION_DURATION_MS);
}

function getFireworkPositionByColor(color) {
    let colors = ["W", "Y", "B", "G", "R"];
    return Point.create(canvasWidth/6 + 150 * colors.indexOf(color), canvasHeight/3);
}

function addEventListeners(){
    if (!(canvas == null)){
        canvas.addEventListener("mousedown",onMouseDown);
        canvas.addEventListener("mouseup",onMouseUp);   
    }
}

function onMouseDown(evt){
    if (gameOver) {
        selectedCard = null;
        return;
    }
    selectedCard = getSelectedCard(evt);
}

function onMouseUp(evt){
    if (gameOver) {
        return;
    }
    mousePointer = Point.create(evt.x,evt.y);
    let isOverAnyPile = false;
    for (let color of placeHolderColors) {
        isOverAnyPile |= placeHolders[color].isOver(mousePointer);
    }
    if (discardPileHolder.isOver(mousePointer)){
        if (selectedCard != null){
            //get idx card was in array
            cardIdx = -1;
            for(let i=0; i<humanCardObjects.length; i++){
                if (humanCardObjects[i] == selectedCard){
                    cardIdx = i;
                }
            }

            // Catch if cardIdx is negative. Can happen if the user is interacting with the UI very quickly
            if (cardIdx < 0) {
                selectedCard.point = selectedCardOldPosition;
                redraw();
                return;
            }

            let message = playerName + ",1,D,"+cardIdx;
            postToServer(message, animateAndUpdate);
            selectedCard = null; //resetting the selectedCard to null since no card is selected
        }
    }
    else if(isOverAnyPile){
        if (selectedCard != null){
            //get idx card was in array
            cardIdx = -1;
            for(let i=0; i<humanCardObjects.length; i++){
                if (humanCardObjects[i] == selectedCard){
                    cardIdx = i;
                }
            }

            // Catch if cardIdx is negative. Can happen if the user is interacting with the UI very quickly
            if (cardIdx < 0) {
                selectedCard.point = selectedCardOldPosition;
                redraw();
                return;
            }

            let message = playerName + ",1,P,"+cardIdx;
            postToServer(message, animateAndUpdate);
            selectedCard = null; //resetting the selectedCard to null since no card is selected
        }

    } else {
        if (selectedCard != null) {
            // The player dropped the card where it should not be (and in a way that doesn't count as a discard or play).
            // return the card to the player's hand.
            selectedCard.point = selectedCardOldPosition;
            redraw();
        }
    }
}

function startNewGame() {
    instructionDiv.style.display = "none";
    clueAnimationBoxCardIndices = [];
    clueText = "";

    cachedInstructionObservation = null;
    hasSatisfiedMinimumEndGameWait = false;
    document.getElementById("hintButton").disabled = false;
    numberOfInformationTokens = 0;
    numberOfStrikes = 0;
    deckSize = 0;
    fireworks = {};
    humanCardRanks = [1,2,3,4,5]; //set this to be the ranks of the cards in the user's hand
    humanCardColors = [1,2,3,4,5]; //set this to be the colors of the cards in the user's hand
    humanCardObjects = [];
    botCardRanks= [1,2,3,4,5]; //set this to be the ranks of the cards in the bot's hand
    botCardColors= [0,0,0,0,0]; //set this to be the colors of the cards in the bot's hand
    botCardObjects = [];
    discardPileObject = [];
    discardPileCards = [];
    selectedCard = null;
    selectedCardOldPosition = null;
    fireworkCards = [];
    lifeTokens = -1;
    informationTokens = -1;
    possibleMoves = [];
    cardKnowledgeHumanObjects = [];
    cardKnowledgeHuman_rank = [];
    cardKnowledgeBotObjects = [];
    cardKnowledgeBot_rank = [];
    botsLastMove = null;
    prevDeckSize = 40;
    instructions = null;
    instructionsText = [];
    gameOver = false;
    deckType = 0;
    submitName();
}

 function submitName() {
    let message = playerName + ",0,0,0";
    postToServer(message, animateAndUpdate);
    document.getElementById("namePrompt").style.display = "none";
}

function getSelectedCard(location){
    for(let i=0; i<humanCardObjects.length; i++){
        mousePointer = Point.create(location.x,location.y)
        if (humanCardObjects[i].isOver(mousePointer)){
            selectedCard = humanCardObjects[i];
            selectedCardOldPosition = selectedCard.point;
            return humanCardObjects[i]
        }
    }
    console.log("no card selected")
    return null   
}

function isLegalMove(move){
    for (let i=0; i<possibleMoves.length;i++){
        if (possibleMoves[i]["action_type"]==move["action_type"] && possibleMoves[i]["card_index"]==move["card_index"]){
            return i 
        }
    }
    return -1
}

function giveHint() {
    
    if (informationTokens == 0) {
        alert("You have no information tokens left, you cannot give a hint");
        
    }else {
        let hint = document.getElementById("hint").value;
        hint = hint.toUpperCase();
        // Catch a few special cases of the hint that we can definitely interpret even though they weren't encouraged.
        switch (hint) {
            case "BLUE":
                hint = "B";
                break;
            case "RED":
                hint = "R";
                break;
            case "GREEN":
                hint = "G";
                break;
            case "YELLOW":
                hint = "Y";
                break;
            case "WHITE":
                hint = "W";
                break;
            case "ONE":
                hint = 1;
                break;
            case "TWO":
                hint = 2;
                break;
            case "THREE":
                hint = 3;
                break;
            case "FOUR":
                hint = 4;
                break;
            case "FIVE":
                hint=  5;
                break;
        }
        const hintColorRegex = new RegExp('[R|B|G|Y|W]');
        const hintNumberRegex = new RegExp('[1-5]');
        if (hint === "advice") {
            postToServer(playerName + ",advice", function(response) {
                console.log("Received advice: " + response);
            });
            return;
        }
        if (hintColorRegex.test(hint)){
            // Test whether the other player has any of this color
            let botHasColor = false;
            for (let card of botCardObjects) {
                if (card.color === hint) {
                    botHasColor = true;
                }
            }
            if (!botHasColor) {
                alert("You cannot give this clue, since the bot has no cards that match this color.");
                return;
            }
            let message = playerName + ",1,C,"+hint;
            postToServer(message, animateAndUpdate);
        }else if (hintNumberRegex.test(hint)) {
            // Test whether the other player has any of this color
            let botHasRank = false;
            for (let card of botCardObjects) {
                if (card.rank === parseInt(hint)) {
                    botHasRank = true;
                }
            }
            if (!botHasRank) {
                alert("You cannot give this clue, since the bot has no cards that match this color.");
                return;
            }
            hint = hint-1;
            let message = playerName + ",1,R,"+hint;
            postToServer(message, animateAndUpdate);
        }else{
            alert("You gave an incorrect hint. Please hint either a number or color (capital letter)");
        }
    }
    
    document.getElementById("hint").value = "";
}

function animateAndUpdate(observationString) {

    let observations = JSON.parse(observationString);

    deckType = observations["deck_type"];

    // Immediately update the UI with changes that were directly caused by the human's most recent move
    updateUiWithObservation(observations["after_human_move"]);

    // If we are showing Cyclone's recommendations after human moves, handle that now.
    console.log(deckType + ", " + participantGroup);

    let shouldFeedbackDivShow = !gameOver && participantGroup !== CONTROL &&
        // One of the following cases needs to be met
        (
            (participantGroup === INSTRUCTION && deckType > 3) ||
            (participantGroup === PRE_CORRECTION && deckType < 2) ||
            (participantGroup === POST_CORRECTION && deckType < 2)
        );

    // Using virtualParticipantGroup, we can handle swapping participants around after the required games
    let virtualParticipantGroup = participantGroup;
    if (deckType > 3) {
        if (participantGroup === INSTRUCTION) {
            virtualParticipantGroup = POST_CORRECTION;
        } else if (participantGroup === POST_CORRECTION) {
            virtualParticipantGroup = INSTRUCTION;
        }
    }

    if (shouldFeedbackDivShow) {
        feedbackDiv.style.display = "block";
        switch (virtualParticipantGroup) {
            case CONTROL:
            case INSTRUCTION:
            // These groups get no special feedback
            break;
            case PRE_CORRECTION:
                // TODO similar to above, but based on a separate call for advice
                postToServer(playerName + ",advice", function(response) {
                    let responseObject = JSON.parse(response);
                    showFeedbackFromAction(responseObject["move"], true);
                });
                break;
            case POST_CORRECTION:
                if (observations.hasOwnProperty("cyclone_recommendation")) {
                    let cycloneRecommendation = observations["cyclone_recommendation"];
                    if (cycloneRecommendation == null) {
                        showFeedbackWithAnimation("In this box you will receive feedback from the AI.");
                    } else {
                        let okMoves = observations["tied_top_moves"];
                        let humanMove = observations["after_human_move"]["prev_move"];
                        let cycloneApproves = doMovesMatch(humanMove, cycloneRecommendation);
                        for (let move of okMoves) {
                            if (cycloneApproves) {
                                break;
                            }
                            cycloneApproves |= doMovesMatch(move, okMoves);
                        }
                        if (cycloneApproves) {
                            showFeedbackWithAnimation("The AI would have made that same move.");
                        } else {
                            showFeedbackFromAction(cycloneRecommendation, false);
                        }
                    }
                }
                break;
        }
    } else {
        feedbackDiv.style.display = "none";
    }
    
    if (!gameOver){
        // Get the observation for the state after the cyclone move. This is the most current state of the game.
        let observation = observations["after_cyclone_move"];

        // If Cyclone gave a clue, don't animate (this could change if we come up with a clue animation)
        let actionType = observation["prev_move"]["action_type"];
        if (actionType.includes("REVEAL")) {
            updateUiWithObservation(observation);

            // Schedule clue box animations for any card that was mentioned in the clue
            clueAnimationBoxCardIndices = [];
            let previousMove = observation["prev_move"];
            let clueColor = previousMove.hasOwnProperty("color") ? previousMove["color"] : null;
            let clueRank = previousMove.hasOwnProperty("rank") ? previousMove["rank"] : null;

            console.log(clueColor);
            console.log(clueRank);

            for (let i = 0; i < humanCardObjects.length; i++) {
                let card = humanCardObjects[i];
                if ((clueColor !== null && clueColor === card.color) || (clueRank !== null && clueRank === card.rank - 1)) {
                    clueAnimationBoxCardIndices.push(i);
                }
            }

            console.log(clueAnimationBoxCardIndices);

            clueAnimationProgress = 0;
            let interval = setInterval(function() {
                clueAnimationProgress += ANIMATION_FRAME_DURATION_MS / ANIMATION_DURATION_MS;
                redraw();
            }, ANIMATION_FRAME_DURATION_MS);
            setTimeout(function() {
                clearInterval(interval);
                clueText = "These are your " + adjectiveFromClueDetails(clueColor, clueRank + 1) + " cards.";
                redraw();
            }, ANIMATION_DURATION_MS);

            return;
        } else {
            clueText = "";
            clueAnimationBoxCardIndices = [];
        }

        // From here, Cyclone made a non-hint action, so we should animate the card's motion
        currentAnimationProgress = 0;
        let movingCardIndex = observation["prev_move"]["card_index"];

        // Parse the action and animate the action taking place
        let newInfoTokenCount = observation["information_tokens"];
        let destinationPoint = undefined;
        console.log("Moving card index: " + movingCardIndex);
        console.log(botCardObjects[movingCardIndex]);
        let originPoint = botCardObjects[movingCardIndex].point.copy();
        if (newInfoTokenCount < numberOfInformationTokens || actionType === "DISCARD") {
            destinationPoint = discardPilePosition;
        }
        if (actionType === "PLAY") {
            destinationPoint = getFireworkPositionByColor(botCardColors[movingCardIndex]);
        }

        let interval = setInterval(function() {
            currentAnimationProgress += ANIMATION_FRAME_DURATION_MS / ANIMATION_DURATION_MS;
            // Set the card point to be a weight average of the origin point and the destination point
            let sigmoidProgress = sigmoid(currentAnimationProgress);
            botCardObjects[movingCardIndex].point = destinationPoint.scale(sigmoidProgress).add(originPoint.scale(1 - sigmoidProgress));
            paintStackManager.paint();
            botCardObjects[movingCardIndex].paint(canvas, canvas.getContext("2d"));
        }, ANIMATION_FRAME_DURATION_MS);

        // Schedule the end of the animation and the full update
        setTimeout(function() {
            clearInterval(interval);
            updateUiWithObservation(observation);
        }, ANIMATION_DURATION_MS);
    }
}

function doMovesMatch(move1, move2) {
    let result = true;
    for (let property of Object.keys(move2)) {
        result &= move1[property] === move2[property];
    }
    return result;
}

function showFeedbackFromAction(actionObject, isPre) {
    let isClue = actionObject["action_type"].includes("REVEAL");
    let clueColor = isClue ? actionObject["color"] : null;
    let clueRank = isClue && clueColor == null ? actionObject["rank"] + 1 : null;
    let isDiscard = actionObject["action_type"] === "DISCARD";
    let cardIndex = isClue ? -1 : actionObject["card_index"]
    let cardName = cardIndex > -1 ?
        cardIndex === 0 ? "right-most card" :
            cardIndex === 1 ? "card second from the right" :
                cardIndex === 2 ? "center card" :
                    cardIndex === 3 ? "card second from the left" :
                        cardIndex === 4 ? "left-most card" : "favorite card (please mention this AI input in the survey)"
        : null;
    showFeedbackWithAnimation((isPre ? "The AI recommends that you " : "The AI would have recommended that you ") +
        (isClue ?
            "give a clue revealing " + adjectiveFromClueDetails(clueColor, clueRank) + " cards."
            : (isDiscard ? "discard" : "play") + " your " + cardName + "."));
}

function adjectiveFromClueDetails(clueColor, clueRank) {
    if (clueColor == null) {
        return "rank " + clueRank;
    } else {
        switch (clueColor) {
            case "W":
                return "white";
            case "Y":
                return "yellow";
            case "R":
                return "red";
            case "G":
                return "green";
            case "B":
                return "blue";
        }
    }
}

function getInstructions(observation) {

    if (typeof observation === "string" && observation.includes("instructions")) {
        observation = JSON.parse(observation);
        instructions = observation["instructions"];
    }
}

function sigmoid(animationProgress) {
    let sigma = 10;
    let low = 1 / (1 + Math.exp(sigma / 2));
    let high = 1 / (1 + Math.exp(-sigma / 2));
    return 1 / (high - low) *
        (1 / (1 + Math.exp(-sigma * (animationProgress - 0.5))) - low);
}

function updateUiWithObservation(observation) {

    // In case the observation is still a JSON string, make it an object
    if (typeof observation === "string") {
        observation = JSON.parse(observation);
    }

    // This method should not be called with a {"after_human_move": observation1, "after_cyclone_move": observation2} object.
    if (observation.hasOwnProperty("after_cyclone_move")) {
        observation = observation["after_cyclone_move"];
    }

    let humanCards = observation["observed_hands"][0];
    let botCards = observation["observed_hands"][1];
    let discardPile = observation["discard_pile"]; 
    let fireworks = observation["fireworks"];
    let numLifeTokens = observation["life_tokens"];
    let numInformationTokens = observation["information_tokens"];
    let legalMoves = observation["legal_moves"];
    let cardKnowledgeH = observation["card_knowledge"][0];
    let cardKnowledgeB = observation["card_knowledge"][1];
    let botsMove = observation["prev_move"];
    
    
    fireworkCards = fireworks;
    lifeTokens = numLifeTokens;
    informationTokens = numInformationTokens;
    
    //get canvas width/height
    canvas = document.getElementById("canvas");
    canvasWidth = canvas.width;
    canvasHeight = canvas.height;
    numberOfInformationTokens = observation["information_tokens"];
    numberOfStrikes = observation["life_tokens"];
    deckSize = observation["deck_size"];
    fireworks = observation["fireworks"];
    possibleMoves = legalMoves;
    lifeTokens = numLifeTokens;
    informationTokens = numInformationTokens;
    botsLastMove = botsMove;

    humanCardRanks = [];
    humanCardColors = [];
    humanCardObjects = [];
    //create human card objects for later use
    let i = 0;
    for (let card of humanCards) {
        humanCardRanks.push(parseInt(card["rank"]) + 1);
        humanCardColors.push(card["color"]);
        let position = getHumanCardPositionByIndex(i);
        let cardObj = Card.create(card["color"], parseInt(card["rank"]) + 1, position.getX(),position.getY());
        cardObj.isFaceUp = true;
        humanCardObjects[i] = cardObj;
        i++;
    }
    //create bot card objects for later use
    botCardRanks = [];
    botCardColors = [];
    botCardObjects = [];
    i = 0;
    for (let card of botCards) {
        botCardRanks.push(parseInt(card["rank"]) + 1);
        botCardColors.push(card["color"]);
        let cardPosition = getBotCardPositionByIndex(i);
        let cardObj = Card.create(card["color"], parseInt(card["rank"]) + 1, cardPosition.getX(),cardPosition.getY());
        cardObj.isFaceUp = true;
        botCardObjects[i] = cardObj;
        i++;
    }

    discardPileObject = [];
    discardPileCards = [];
    i = 0;
    for (let card of discardPile) {
        discardPileCards.push([card["color"],card["rank"]])
        let cardObj = Card.create(card["color"], parseInt(card["rank"]) + 1,  discardPilePosition.getX(), discardPilePosition.getY());
        cardObj.isFaceUp = true;
        discardPileObject[i] = cardObj;
        i += 1
    }
    
    //cardKnowledgeHuman = cardKnowledgeH;
    //cardKnowledgeBot = cardKnowledgeB;
    i = 0;
    cardKnowledgeHumanObjects = [];
    for (let cardHint of cardKnowledgeH){
        //cardKnowledgeHuman_color[i] = cardHint["color"];
        let hintObj = [];
        let cardKnowledgePosition = getHumanCardPositionByIndex(i);
        if (cardHint["rank"] != null){ //if not null
            cardKnowledgeHuman_rank[i] = cardHint["rank"]+1;
            hintObj = HintBox.create(cardHint["color"], cardHint["rank"]+1, cardKnowledgePosition.getX(), cardKnowledgePosition.getY());
        }else{
            cardKnowledgeHuman_rank[i] = cardHint["rank"];
            hintObj = HintBox.create(cardHint["color"], cardHint["rank"], cardKnowledgePosition.getX(),cardKnowledgePosition.getY());
        }    
        cardKnowledgeHumanObjects[i] = hintObj;
        i +=1; 
    }
    
    i = 0;
    cardKnowledgeBotObjects = [];
    for (let cardHint of cardKnowledgeB){
        //cardKnowledgeBot_color[i] = cardHint["color"];
        let hintObj = [];
        let cardKnowledgePosition = getBotCardPositionByIndex(i);
        if (cardHint["rank"] != null){ //not null
            cardKnowledgeBot_rank[i] = cardHint["rank"]+1;
            hintObj = HintBox.create(cardHint["color"], cardHint["rank"]+1, cardKnowledgePosition.getX(),cardKnowledgePosition.getY());
        }else{
            cardKnowledgeBot_rank[i] = cardHint["rank"];
            hintObj = HintBox.create(cardHint["color"], cardHint["rank"], cardKnowledgePosition.getX(),cardKnowledgePosition.getY());
        }
        cardKnowledgeBotObjects[i] = hintObj;
        i +=1; 
    }

    redraw();

    //see if game is over
    if (numLifeTokens == 0){
        console.log("Out of life tokens");
        endGameBasicScreen(ALL_LIFE_TOKENS_GONE_MESSAGE);
        // return null;
    }
    if (humanCards.length < 5 || botCards.length < 5){
        //game over
        console.log("Ending game because someone was down cards. " + humanCards.length + ", " + botCards.length);
        endGameBasicScreen(DECK_GONE_MESSAGE);
        // return null;
    }

    //if for each color in fireworks is a 5, then game is won
    if (fireworkCards["W"] == 5 && fireworkCards["Y"] == 5 && fireworkCards["B"] == 5 &&
        fireworkCards["G"] == 5 && fireworkCards["R"] == 5) {
        //game over - Won
        console.log("All cards have been played");
        endGameBasicScreen(GAME_WON_MESSAGE);
        // return null;
    }

}

function getCurrentScore() {
    let score = 0;
    for (let color of placeHolderColors) {
        score += fireworkCards[color];
    }
    return score;
}

function getCardKnowledgeHumanByIndex(index) {
    return Point.create((7*canvasWidth/10)-120*index,canvasHeight-200);
}

function getCardKnowledgeBotByIndex(index) {
    return Point.create((7*canvasWidth/10)-120*index,130);
}

function getHumanCardPositionByIndex(index) {
    return Point.create((7*canvasWidth/10)-120*index,canvasHeight-300);
}

function getBotCardPositionByIndex(index) {
    return Point.create((7*canvasWidth/10)-120*index,30);
}

function postToServer(message, callback) {
    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function () {
        if (this.readyState === 4 && this.status === 200) {
            let response = xhttp.responseText;
            callback(response);
        }
    };
    xhttp.open("POST", "/", true);
    xhttp.send(message);
}

function doEndTest(){
    postToServer(playerName + ",END" /* TODO could append score */, function(response) {
       console.log("Asking for instructions");
       document.getElementById("scoreText").innerHTML = "Final score: " + getCurrentScore();
       // TODO could parse the response and interpret it as score history
       getInstructionsFromServerAndDisplay();
    });
}

function createDeckOfCards() {
    colors = ["W", "Y", "B", "G", "R"];
    ranks = [0,0,0,1,1,2,2,3,3,4]
    deck = [];
    
    for (let c = 0; c < colors.length; c++){
        for (let r = 0; r < ranks.length; r++ ) { 
            //tuple has format (color, rank, stillInDeck)
            deck.push([colors[c], ranks[r], 1]);
        }
    }
    return deck
}

function createCardsRemainingTable() {
    deck = createDeckOfCards();
    
    for (let i=0; i < discardPileCards.length; i++) {
        let card = discardPileCards[i];
        for (let j=0; j < deck.length; j++) {
            let cardInDeck = deck[j];
            if (card[0] == cardInDeck[0] && card[1] == cardInDeck[1] && cardInDeck[2] == 1) {
                deck[j] = [card[0],card[1],0]
                break;
            }
        }
    }
    
    //loop over cards in firework for cards already played
    colors = ["W", "Y", "B", "G", "R"];
    for (let i = 0; i < colors.length; i++){
        currColor = colors[i];
        fireworkNum = fireworkCards[currColor];
        for (let j = 0; j < fireworkNum; j++){
            for (let k=0; k < deck.length; k++) {
                let currDeckCard = deck[k];
                if (currColor == currDeckCard[0] && j == currDeckCard[1] && currDeckCard[2] == 1){
                    deck[k] = [currColor, j, 0];
                    break;
                }
            }
        }
    }
    
    let remainingCardsTablePosition = getRemainingCardsTablePosition();
    remainingCardsTable = CardsRemainingBox.create(deck, deckSize, remainingCardsTablePosition.getX(), remainingCardsTablePosition.getY());
    paintStackManager.register(remainingCardsTable, remainingCardsTable.paint);
}

function getInstructionsFromServerAndDisplay() {
    postToServer(playerName + ",instructions", instructionsCallback);
    setTimeout(minimumWaitCallback, MINIMUM_END_GAME_WAIT_MILLISECONDS);
}

function instructionsCallback(observation){
    if (hasSatisfiedMinimumEndGameWait) {
        displayInstructions(observation);
    }
    cachedInstructionObservation = observation;
}

function minimumWaitCallback() {
    if (cachedInstructionObservation != null) {
        displayInstructions(cachedInstructionObservation);
    }
    hasSatisfiedMinimumEndGameWait = true;
}

function displayInstructions(observation) {
    console.log(observation);
    paintStackManager = PaintStackManager.create(canvas, "#000000");
    ctx.font = "50pt Calibri";
    ctx.textAlign = "center";
    ctx.fillText("Please wait...", canvasWidth/2, canvasHeight/2);
    ctx.font = "30pt Calibri";
    if (typeof observation === "string" && !observation.includes("There is no")) {
        observation = JSON.parse(observation);
        instructions = observation["instructions"];
    } //else will be using the instructions that were previously set during the update function call

    if (instructionsText.length >= 2) {
        //No need to add duplicate more instructions already present
        return;
    }

    var tempInstructions = instructions.map(Math.abs);
    var topInstructionIdx = tempInstructions.indexOf(Math.max.apply(null,tempInstructions));
    tempInstructions.splice(topInstructionIdx, 1, -1); //replacing max with -1 so the indices so can easily find next max without removing anything
    var secondTopInstructionIdx = tempInstructions.indexOf(Math.max.apply(null,tempInstructions));

    instruction1.innerHTML = "Please read the following recommendations from your AI teammate.<br/><br/>" +
        getInstructionText(topInstructionIdx, instructions[topInstructionIdx] > 0);
    instruction2.innerHTML = getInstructionText(secondTopInstructionIdx, instructions[secondTopInstructionIdx] > 0);

    // If there are any cases in which instructions should definitely show, catch them here
    let playAgainButton = document.getElementById("playAgain");
    let instructionsShouldShow = (participantGroup === INSTRUCTION && deckType === 1) || (participantGroup === POST_CORRECTION && deckType > 3);
    if (instructionsShouldShow) {
        instructionDiv.style.display = "block";
        // Alter the play again button so that it is very different
        playAgainButton.classList.add("scaryButton");
        playAgainButton.innerHTML = "Once you have read the AI's suggestions above, click here to start the next game.";
        return;
    } else {
        // Ensure the play again button looks regular
        playAgainButton.classList.remove("scaryButton");
        playAgainButton.innerHTML = "Play Again";
    }

    // If the participant has finished the four required games, remove the play again button. This helps prevent the user
    // from clicking past the survey link in their zeal to play more Hanabi.
    if (deckType >= 3) {
        playAgainButton.style.display = "none";
    }

    // The latter portion of the boolean below activates the instructions for games after the four required games.
    if (deckType !== 1 /*&& deckType < 4*/) {
        instruction1.innerHTML = "You have completed " + (deckType + 1) +
            " of 4 games. " + (deckType >= 3 ? "Please complete the post-experiment survey if you have not already done so. To access the survey, you can use the original link you received from the experimenters," +
                " or you can follow <br><a href='https://jhuapl.az1.qualtrics.com/jfe/form/SV_8vUAknoJwrTZHo2/?pid=" + playerName.substring(0, playerName.length - 1) + "&condition=" + participantGroup +"'>this link to complete the survey</a>." : "Please start your next game.");
        instruction2.innerHTML = deckType >= 3 ? "After completing the survey, you are allowed to play more games with the AI. To do so, refresh this page." : "";
    }

    if (participantGroup !== INSTRUCTION) {
        instruction1.innerHTML = deckType >= 3 ? "Please complete the post-experiment survey if you have not already done so. To access the survey, you can use the original link you received from the experimenters," +
            " or you can follow <br><a href='https://jhuapl.az1.qualtrics.com/jfe/form/SV_8vUAknoJwrTZHo2/?pid=" + playerName.substring(0, playerName.length - 1) + "&condition=" + participantGroup +"'>this link to complete the survey</a>." : "You have completed " + (deckType + 1) + " of 4 games. Please start your next game.";
        instruction2.innerHTML = deckType >= 3 ? "After completing the survey, you are allowed to play more games with the AI. To do so, refresh this page." : "";
    }
    instructionDiv.style.display = "block";
}

function endGameBasicScreen(message) {

    // TODO deactivate the mouse motion listener and the clue button, and reactivate on game reset?

    gameOver = true;
    canvas = document.getElementById("canvas");
    var context = canvas.getContext("2d");

    context.font = "50pt Calibri";
    context.textAlign = "center";
    context.fillStyle = "#000000";
    context.strokeStyle = "#000000";

    let text = "Game over (Score: " + getCurrentScore() + "). Please wait...";

    // setup these to match your needs
    context.miterLimit = 2;
    context.lineJoin = 'circle';

    // draw an outline, then filled
    context.lineWidth = 7;
    context.strokeText(text, canvasWidth/2, canvasHeight/2);
    context.fillStyle = "#FFFFFF";
    context.strokeStyle = "#FFFFFF";
    context.lineWidth = 1;
    context.fillText(text, canvasWidth/2, canvasHeight/2);

    context.font = "30pt Calibri";
    context.strokeText(message, canvasWidth/2, canvasHeight/2 + 100);
    context.fillText(message, canvasWidth/2, canvasHeight/2 + 100);
    feedbackDiv.style.display = "none";
    //check to see if user should receive instruction or not
    // if (receiveInstructions){
        //context.fillText("Refresh page to begin a new game", canvasWidth/2, (canvasHeight/2)+50);
    //}else{
    // context.fillText("Please wait to receive instructions on how you can play better", canvasWidth/2, (canvasHeight/2)+50);
    //}
    document.getElementById("hintButton").disabled = true;
    doEndTest();
}

function getRemainingCardsTablePosition() {
    return Point.create(canvasWidth / 15, 7 * canvasHeight / 10);
}

function getInfoTokenBoxPosition() {
    return Point.create(6*canvasWidth/7, 90);
}

function getLifeTokenBoxPosition() {
    return Point.create(6*canvasWidth/7, 50);
}