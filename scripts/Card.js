
let Card = {
    WHITE: "W",
    YELLOW: "Y",
    BLUE: "B",
    GREEN: "G",
    RED: "R",
    // Rank of -1 means the card is discarded, and a rank of 0 means this is not a card, but instead the bottom
    // of the play stack for this color.
    RANKS: [-1, 0, 1, 2, 3, 4, 5],
    COLORS: [this.WHITE, this.YELLOW, this.BLUE, this.GREEN, this.RED],
    BODY: "BODY",
    BORDER: "BORDER",
    TEXT: "TEXT",
    PAINT_COLORS_BY_COLOR: {
        "B": {BODY: "#3355FF", BORDER: "#2233DD", TEXT: "#FFFFFF"},
        "Y": {BODY: "#E2EC18", BORDER: "#E2EC18", TEXT: "#777700"},
        "W": {BODY: "#FFFFFF", BORDER: "#FFFFFF", TEXT: "#999999"},
        "G": {BODY: "#1AA221", BORDER: "#1AA221", TEXT: "#FFFFFF"},
        "R": {BODY: "#FF0000", BORDER: "#FF0000", TEXT: "#FFFFFF"},
    },
    PIXEL_WIDTH: 100,
    PIXEL_HEIGHT: 150,
    create: function(color, rank, xPos = 100, yPos = 100) {
        return {
            /**
             * This point is the pixels coordinates relative to the canvas of the card's top left corner
             */
            point: Point.create(xPos, yPos),
            color: color,
            rank: rank,
            isFaceUp: false,
            paint(canvas, ctx) {
                if (this.rank == -1){ //discard pile
                    ctx.fillStyle = Card.PAINT_COLORS_BY_COLOR[this.color][Card.BODY];
                    ctx.globalAlpha = 1;
                    ctx.fillRect(this.point.getX(), this.point.getY(), Card.PIXEL_WIDTH, Card.PIXEL_HEIGHT);
                    ctx.font = "29px Arial";
                    ctx.textAlign = "center";
                    ctx.fillStyle = Card.PAINT_COLORS_BY_COLOR[this.color][Card.TEXT];
                    ctx.fillText("Discard", this.point.getX() + Card.PIXEL_WIDTH/2, this.point.getY() + 4*Card.PIXEL_HEIGHT/7);

                }else if (this.rank == 0){
                    ctx.fillStyle = Card.PAINT_COLORS_BY_COLOR[this.color][Card.BODY];
                    ctx.globalAlpha = 0.5;
                    ctx.fillRect(this.point.getX(), this.point.getY(), Card.PIXEL_WIDTH, Card.PIXEL_HEIGHT);
                    ctx.font = "90px Arial";
                    ctx.textAlign = "center";
                    ctx.fillStyle = "#FFFFFF";
                    ctx.fillText(this.color, this.point.getX() + Card.PIXEL_WIDTH/2, this.point.getY() + 5*Card.PIXEL_HEIGHT/7);

                }else{
                    ctx.globalAlpha = 1;
                    if (this.isFaceUp) {
                        ctx.fillStyle = Card.PAINT_COLORS_BY_COLOR[this.color][Card.BODY];
                        ctx.fillRect(this.point.getX(), this.point.getY(), Card.PIXEL_WIDTH, Card.PIXEL_HEIGHT);
                        ctx.fillStyle = Card.PAINT_COLORS_BY_COLOR[this.color][Card.TEXT];
                        // Little number
                        ctx.font = "24px Arial";
                        ctx.fillText(this.rank, this.point.getX() + 10, this.point.getY() + 30);
                        // Big number
                        ctx.font = "98px Arial";
                        ctx.fillText(this.rank, this.point.x+ 2*Card.PIXEL_WIDTH / 3, this.point.y + Card.PIXEL_HEIGHT - 20);
                    } else {
                        // Show the standard face down card appearance
                        let faceDownColor = "#663322";
                        let detailColor = "#885533";
                        let drawDiamond = function(topLeftCorner, dimX, dimY) {
                            let relX = [0, dimX / 2, dimX, dimX / 2];
                            let relY = [dimY / 2, 0, dimY / 2, dimY];
                            let x = [];
                            let y = [];
                            for (let i in relX) {
                                x.push(topLeftCorner.getX() + relX[i]);
                                y.push(topLeftCorner.getY() + relY[i]);
                            }
                            ctx.fillStyle = detailColor;
                            ctx.beginPath();
                            ctx.moveTo(x[0], y[0]);
                            for (let i = 1; i < x.length; i++) {
                                ctx.lineTo(x[i], y[i]);
                            }
                            ctx.closePath();
                            ctx.fill();
                        }

                        // background
                        ctx.fillStyle = faceDownColor;
                        ctx.fillRect(this.point.getX(), this.point.getY(), Card.PIXEL_WIDTH, Card.PIXEL_HEIGHT);
                        ctx.moveTo(100,100)

                        // diamonds
                        let xCount = 3;
                        let yCount = 3;
                        let xDim = Card.PIXEL_WIDTH / xCount;
                        let yDim = Card.PIXEL_HEIGHT / yCount;
                        for (let i = 0; i < Card.PIXEL_WIDTH; i += xDim) {
                            for (let j = 0; j < Card.PIXEL_HEIGHT; j += yDim) {
                                let anchorPoint = Point.create(i, j).add(this.point);
                                drawDiamond(anchorPoint, xDim, yDim);
                            }
                        }
                    }

                }
            },
            translate: function(deltaPoint) {
                this.point = this.point.add(deltaPoint);
            },
            isOver: function(mousePoint) {
                return Math.abs(mousePoint.getX() - this.point.getX() - Card.PIXEL_WIDTH / 2) < (Card.PIXEL_WIDTH / 2) + 10 &&
                    Math.abs(mousePoint.getY() - this.point.getY() - Card.PIXEL_HEIGHT / 2) < (Card.PIXEL_HEIGHT / 2) + 60;
            }
        }
    }
}