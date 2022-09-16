/**
 * The MouseManager watches over an html element. It curates a number of objects
 * that are registered with it and allows the user to click and drag any object
 * that is registered.
 *
 * Typical use involves instantiating the manager with an element, typically a canvas.
 *
 *   let mouseManager = MouseManager.create(document.getElementById("canvas"));
 *
 * Next, one creates an object to register with the manager. Note that the manager
 * does not manage any graphics; it only makes registered changes to in-memory objects
 * in response to user clicking and dragging. So, typically you would pass an
 * object along with a function that modifies fields in the object related to painting
 * (like x y position) and likely a call to a graphics update function that is
 * defined outside of the mouse manager.
 *
 *   mouseManager.register(rectFilter, function(point) { rectFilter.translate(point); repaint(); });
 *
 * In this way, mouse management is highly decoupled from the main script, yet
 * the mouse manager is not burdened with anything extraneous to monitoring the
 * user's mouse.
 *
 * @type {any}
 */


let MouseManager = {
    create: function(parentElement) {
        let result = {
            mouseDown: false,
            oldMousePosition: Point.create(0, 0),
            objectBeingMoved: null,
            mouseMovableObjects: [],
            parentElement: parentElement,
            clickAction: null,

            /**
             * Registration is how an object in memory gets click-draggability
             * @param object - The in-memory object that is click-draggable
             * @param translateFunction - A function to call. We pass the dx, dy of the mousemove
             *    as a {@link Point}
             */
            register: function(object, translateFunction) {
                // The mouse manager assigns a z attribute in case there isn't one.
                // The z attribute helps the mouse manager click on the top object.
                if (!object.hasOwnProperty("z")) {
                    object.z = this.mouseMovableObjects.length;

                    object.getZ = function() {
                        return object.z;
                    };
                    object.setZ = function(newZ) {
                        object.z = newZ;
                    }
                }

                this.mouseMovableObjects.push(object);
                object.translateFunction = translateFunction;
            },
            unregister: function(object) {
                let index = this.mouseMovableObjects.indexOf(object);
                if (index > -1) {
                    this.mouseMovableObjects.splice(index, 1);
                } else {
                    console.log("Couldn't unregister");
                }
            },
            registerClickAction: function(clickFunction) {
                this.clickAction = clickFunction;
            },
            clear: function() {
                this.mouseMovableObjects = [];
            }
        }
        // Also activate
        result.parentElement.addEventListener('mousedown', function(e){
            result.mouseDown = true;
            let x = e.pageX - result.parentElement.offsetLeft;
            let y = e.pageY - result.parentElement.offsetTop;
            result.oldMousePosition = Point.create(x, y);
            let objectsOver = [];
            for (let i = result.mouseMovableObjects.length - 1; i >= 0; i--) {
                if (result.mouseMovableObjects[i].isOver(result.oldMousePosition)) {
                    objectsOver.push(result.mouseMovableObjects[i]);
                }
            }
            if (objectsOver.length > 0) {
                result.objectBeingMoved = objectsOver[0];
                for (let i = objectsOver.length - 1; i >= 1; i--) {
                    if (objectsOver[i].z > result.objectBeingMoved.getZ()) {
                        result.objectBeingMoved = objectsOver[i];
                    }
                }
            }

            // If there is a callback for selection, call it now
            if (result.clickAction != null) {
                result.clickAction(result.objectBeingMoved);
            }

        });
        //-----------------------------------------------------------------------------
        result.parentElement.addEventListener('mouseup', function(){
            result.mouseDown = false;
            result.objectBeingMoved = null;
        });
        //-----------------------------------------------------------------------------
        result.parentElement.addEventListener('mousemove', function(e){
            if (result.mouseDown && result.objectBeingMoved != null){
                // If there is a card held, move the card
                let x = e.pageX - result.parentElement.offsetLeft;
                let y = e.pageY - result.parentElement.offsetTop;
                let dx = x - result.oldMousePosition.getX();
                let dy = y - result.oldMousePosition.getY();
                result.objectBeingMoved.translateFunction(Point.create(dx, dy));

                // Update the old mouse position
                result.oldMousePosition = Point.create(x, y);
            }
        });

        return result;

    }
}
