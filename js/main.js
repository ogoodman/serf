require(['when/when', 'app/rpc'], function(when, rpc) {

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
    rpc.WSServer.prototype.hooks['HookCls'] = function(args) {
	return new HookCls(args[0]);
    };

    window.HookCls = HookCls;
    window.Proxy = rpc.Proxy;

    window.h = new HookCls("hi");

    // set up binding.
    var input = document.getElementById('input1');
    function doBind() {
	if (!bound) {
	    window.model = new rpc.Proxy(serv, 'shared');
	    window.model.addMethod('get');
	    window.model.addMethod('set');
	    window.model.addMethod('notify');
	    window.model.addMethod('subscribers');

	    bindInput(input, model, 'name');
	    bound = true;
	} else {
	    console.log('already bound');
	}
    }

    window.rlog = function(result) { console.log('got:', result); }
    window.elog = function(err) { console.log('error:', err); }

    window.WSServer = rpc.WSServer;
    window.serv = serv;

    doBind();
    window.doBind = doBind;
});
