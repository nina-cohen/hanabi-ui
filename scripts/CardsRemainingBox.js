
let CardsRemainingBox = {
    PIXEL_WIDTH: 300,
    PIXEL_HEIGHT: 200,
    create: function(deck, deckSize, xPos = 100, yPos = 100) {
        return {
            point: Point.create(xPos, yPos),
            paint(canvas, ctx) {
                //ctx.fillRect(this.point.getX(), this.point.getY(), CardsRemainingBox.PIXEL_WIDTH, CardsRemainingBox.PIXEL_HEIGHT);
                ctx.lineWidth = 3;
                ctx.strokeStyle = "white";
                ctx.beginPath();
                ctx.strokeRect(this.point.getX()-30, this.point.getY()-40,CardsRemainingBox.PIXEL_WIDTH, CardsRemainingBox.PIXEL_HEIGHT);
                ctx.stroke();
                ctx.font = "22px Arial"
                ctx.fillStyle = "white";
                //ctx.textAlign = "center"
                ctx.fillText("Number of Cards Left in Deck: "+deckSize, this.point.getX()-30+CardsRemainingBox.PIXEL_WIDTH/2, this.point.getY()-75)
                ctx.font = "16px Arial"
                if (deckSize < 4) {
                    ctx.fillStyle = "red";
                }
                ctx.fillText("The game will end after the next "+(deckSize + 1) + " plays or discards", this.point.getX()-30+CardsRemainingBox.PIXEL_WIDTH/2, this.point.getY()-50)
                ctx.fillStyle = "white";
                ctx.fillText("Cards Still in Play", this.point.getX()-30+CardsRemainingBox.PIXEL_WIDTH/2, this.point.getY()-20)
                ctx.font = "13px Arial";
                //ctx.textAlign = "center";
                //create strings - there will be 10 rows with 5 columns, one column for each color
                let startIdx = 0;
                for (let row = 0; row < 10; row++){
                    startIdx = 0
                    for (let col = row; col < deck.length; col+=10){
                        let currCard = deck[col];
                        let color = "";
                        let rank = currCard[1];
                        if (currCard[0] == "W"){
                            color = "White - "
                        }else if (currCard[0] == "Y"){
                            color = "Yellow - "
                        }else if (currCard[0] == "B"){
                            color = "Blue - "
                        }else if (currCard[0] == "G"){
                            color = "Green - "
                        }else {
                            color = "Red - "
                        }
                        // if card is still in deck, it will appear white, if it is not it'll be greyed out
                        if ( currCard[2] == 1){
                            ctx.fillStyle = "white";
                        } else {
                            ctx.fillStyle = "grey";
                        }
                        ctx.fillText(color+(rank+1), this.point.getX() + 60*startIdx, this.point.getY() + 15*row);
                        startIdx++;
                    }
                }

                //ctx.fillText = "white"

                //ctx.fillText("Color: "+color, this.point.getX() + HintBox.PIXEL_WIDTH/2, this.point.getY() + HintBox.PIXEL_HEIGHT+75);
                //ctx.fillText("Rank: "+rank, this.point.getX() + HintBox.PIXEL_WIDTH/2, this.point.getY() + HintBox.PIXEL_HEIGHT+95);
            }
        }
    }
}