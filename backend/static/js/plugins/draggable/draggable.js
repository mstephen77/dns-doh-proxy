$(() => {
    $.fn.draggable = function (handle = null) {
        let pos1x = 0, pos1y = 0, pos0x = 0, pos0y = 0;
        let position = {}, _position = {
            'top': this.css('top'),
            'left': this.css('left')
        };

        dragMouseDown = (e) => {
            e = e || window.event;
            e.preventDefault();
            position = this.position();
            pos0x = e.clientX - position.left;
            pos0y = e.clientY - position.top;

            document.onmouseup = closeDragElement;
            document.onmousemove = elementDrag;
        }
        elementDrag = (e) => {
            e = e || window.event;
            e.preventDefault();
            pos1x = e.clientX - pos0x - position.left;
            pos1y = e.clientY - pos0y - position.top;
            this.css({
                'top': position.top + pos1y,
                'left': position.left + pos1x
            })
        }
        closeDragElement = () => {
            // stop moving when mouse button is released:
            document.onmouseup = null;
            document.onmousemove = null;
        }

        if (handle) {
            $(handle).on('mousedown', dragMouseDown).css({
                'cursor': 'move',
            });
        } else {
            this.on('mousedown', dragMouseDown);
        }

        return {
            'reset': () => {
                this.css({
                    'top': _position.top,
                    'left': _position.left
                })
            }
        }
    }
});