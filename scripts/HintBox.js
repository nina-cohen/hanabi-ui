let HintBox = {
    PIXEL_WIDTH: 100,
    PIXEL_HEIGHT: 0,
    create: function(color, rank, xPos = 100, yPos = 100) {
        return {
            point: Point.create(xPos, yPos),
            colorKnowledge: color,
            rankKnowledge: rank,
            paint(canvas, ctx) {
                ctx.fillRect(this.point.getX(), this.point.getY(), HintBox.PIXEL_WIDTH, HintBox.PIXEL_HEIGHT);
                ctx.font = "14px Arial";
                ctx.fillStyle = "white";
                //ctx.fillText = "white"
                ctx.textAlign = "center";
                ctx.fillText("Color: "+color, this.point.getX() + HintBox.PIXEL_WIDTH/2, this.point.getY() + HintBox.PIXEL_HEIGHT+75);
                ctx.fillText("Rank: "+rank, this.point.getX() + HintBox.PIXEL_WIDTH/2, this.point.getY() + HintBox.PIXEL_HEIGHT+95);
            }
        }
    }

}
