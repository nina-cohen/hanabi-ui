/**
 * This class is designed to never change the original point. All
 * transformations on the original point are provided as standalone
 * copies that do not alter the original point.
 */

let Point = {
    create: function(x, y) {
        return {
            x: x,
            y: y,
            getX() {
                return this.x;
            },

            getY() {
                return this.y;
            },

            setX(newX) {
                this.x = newX;
            },

            setY(newY) {
                this.y = newY;
            },

            add(translationPoint) {
                return Point.create(translationPoint.getX() + this.x, translationPoint.getY() + this.y);
            },

            sub(subPoint) {
                return Point.create(this.x - subPoint.getX(), this.y - subPoint.getY());
            },

            rotate(centerPoint, angleRad) {
                let centerToPoint = this.sub(centerPoint);
                let newCenterToPoint = Point.create(centerToPoint.getX() * Math.cos(angleRad) - centerToPoint.getY * Math.sin(angleRad),
                    centerToPoint.getY() * Math.cos(angleRad) + centerToPoint.getX() * Math.sin(angleRad));
                return centerPoint.add(newCenterToPoint);
            },

            rotate(angleRad) {
                return Point.create(this.x * Math.cos(angleRad) - this.y * Math.sin(angleRad),
                    this.y * Math.cos(angleRad) + this.x * Math.sin(angleRad));
            },

            CP(otherPoint) {
                return this.x * otherPoint.getY() - this.y * otherPoint.getX();
            },

            mag() {
                return Math.sqrt(this.x * this.x + this.y * this.y);
            },

            scale(factor) {
                return Point.create(this.x * factor, this.y * factor);
            },

            copy() {
                return Point.create(this.x, this.y);
            },

            setLength(length) {
                if (this.mag() === 0) { return Point.create(0, 0); }
                return this.scale(length / this.mag());
            },

            print() {
                return this.x + ", " + this.y;
            }
        }
    }
}
