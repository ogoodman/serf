var bind = (function() {
    /**
     * Binds a span element to the status of a websocket.
     */
    function bind_status(el, server) {
        server.onopen = function() {
            el.style.color = 'green';
            el.textContent = 'connected';
        };
        server.onclose = function() {
            el.style.color = 'red';
            el.textContent = 'disconnected';
        };
    }

    return {
        bind_status: bind_status
    };
})();
