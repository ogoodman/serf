//#include publisher.js
//#include rpc.js

window.onload = function() {

    var Publisher = publisher.Publisher;

    var serv = new rpc.WSServer('ws://' + location.hostname + '/ws/');

    var bound = false;
    var st = document.getElementById('status');

    serv.onopen = function() {
        st.style.color = 'green';
        st.textContent = 'connected';
    };
    serv.onclose = function() {
        bound = false;
        st.style.color = 'red';
        st.textContent = 'disconnected';
    };

    // ------------------------------------------------------------


    function bindInput(elem, model, name) {
        elem.addEventListener('change', function(e) {
            model.set(name, elem.value);
        });
        model.subscribe('change', function(e, info) {
            if (info.key == name) {
                elem.value = info["new"];
            }
        });
        model.get(name).done(function(value) {
            elem.value = value || '';
        });
    };
    window.bindInput = bindInput;
    
    function logEvent(event, info) {
        console.log('notified:', event, info);
    };
    window.logEvent = logEvent;

    // Example hook class
    function HookCls(val) {
        this.val = val;
    };
    HookCls.prototype.ext_encoding = function() {
        return {name: 'HookCls', args: [this.val]};
    };
    rpc.WSServer.prototype.hooks['HookCls'] = function(server, args) {
        return new HookCls(args[0]);
    };

    window.HookCls = HookCls;

    window.h = new HookCls("hi");

    // set up binding.
    var input = document.getElementById('input1');
    function doBind() {
        if (!bound) {
            window.model = serv.getProxy('shared');
            bindInput(input, model, 'name');
            bound = true;
        } else {
            console.log('already bound');
        }
    }

    // Test for passing proxy to server.
    function Squarer() {
    }
    Squarer.prototype.square = function(n) {
        console.log('squaring', n);
        return n * n;
    };

    var sqc = serv.getProxy('sqcaller');

    serv.obj['pub'] = new Publisher();
    var pp = serv.getProxy('pub', 'browser');

    function sendProxyToServer() {
        serv.obj['squarer'] = new Squarer();
        console.log('serv.obj.squarer', serv.obj['squarer']);
        var sq = serv.getProxy('squarer', 'browser');
        sqc.useSquarer(sq, 3).done(rlog);
    }

    function testBoundMethod() {
        window.shget = makeBoundMethod(serv, 'shared', 'get', 'server', true);
        console.log('doing shget("name")', shget('name').done(rlog));
        serv.obj['squarer'] = new Squarer();
        window.square = makeBoundMethod(serv, 'squarer', 'square', 'browser');
        console.log('square(6)', square(6));
    }

    function testSubscribeToClient() {
        sqc.subscribeToClient(pp).done(function() {
            serv.obj['pub'].notify('event', 'foobar');
        });
    }

    window.Publisher = Publisher;
    window.sendProxyToServer = sendProxyToServer;
    window.makeBoundMethod = rpc.makeBoundMethod;
    window.testBoundMethod = testBoundMethod;
    window.testSubscribeToClient = testSubscribeToClient;

    window.rlog = function(result) { console.log('got:', result); }
    window.elog = function(err) { console.log('error:', err); }

    window.WSServer = rpc.WSServer;
    window.serv = serv;
    window.sqc = sqc

    doBind();
    window.doBind = doBind;
};
