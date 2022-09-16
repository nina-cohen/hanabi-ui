
let TokenBox = {
    PIXEL_WIDTH: 100,
    PIXEL_HEIGHT: 100,
    create: function(tokenType, xPos = 100, yPos = 100) {
        return {
            point: Point.create(xPos, yPos),
            paint(canvas, ctx) {
                if (tokenType == "L"){
                    ctx.globalAlpha = 1.0;
                    ctx.font = "bold 25px Arial";
                    ctx.fillStyle = "white";
                    ctx.textAlign = "center";
                    ctx.fillText("Life Tokens: "+lifeTokens, this.point.getX() + TokenBox.PIXEL_WIDTH/2, this.point.getY() + TokenBox.PIXEL_HEIGHT/2)
                }else if (tokenType == "I"){
                    ctx.globalAlpha = 1.0;
                    ctx.font = "bold 25px Arial";
                    ctx.fillStyle = "white";
                    ctx.textAlign = "center";
                    ctx.fillText("Information Tokens: "+informationTokens, this.point.getX() + TokenBox.PIXEL_WIDTH/2, this.point.getY() + TokenBox.PIXEL_HEIGHT/2)
                }

            }
        }
    }
}