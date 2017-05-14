//#include /js/serf/rpc.js

$(function() {
    // Register some classes we can pass to and from the server.
    // 
    // NOTE: On the server these classes actually do something. Here
    // we only need to be able to create them or examine their values
    // so their construction can be completely automated.
    KeyValue = rpc.makePODClass('KeyValue', ['key', 'value']);
    KeyValueChange = rpc.makePODClass('KeyValueChange', ['key', 'value', 'old']);
    PKey = rpc.makePODClass('PKey', ['pk']);
    QTerm = rpc.makePODClass('QTerm', ['field', 'condition', 'value']);
    FieldValue = rpc.makePODClass('FieldValue', ['field', 'value']);

    // Create server connection.
    serv = new rpc.WSServer('ws://' + location.hostname + '/tables/');

    // Show connection status.
    var st = document.getElementById('status');
    serv.onopen = function() {
        st.style.color = 'green';
        st.textContent = 'connected';
    };
    serv.onclose = function() {
        st.style.color = 'red';
        st.textContent = 'disconnected';
    };

    // Create grid UI element.
    window.grid = $('#grid').w2grid({
        name: 'grid',
        header: 'List of Names',
        show: {
            toolbar: false
        },
        columns: [
            { field: 'fname', caption: 'First Name', size: '20%', editable: { type: 'text' } },
            { field: 'lname', caption: 'Last Name', size: '20%', editable: { type: 'text' } },
            { field: 'email', caption: 'Email', size: '30%', editable: { type: 'text' } },
            { field: 'sdate', caption: 'Start Date', size: '120px', editable: { type: 'text' } }
        ]
    });

    // Connect to table on the server.
    t = serv.getProxy('table', ['insert', 'select', 'update']);

    // Populate the table.
    t.select().done(function(rows) {
        var recs = rows.map(function(kv) {
            kv.value.recid = kv.key;
            return kv.value;
        });
        grid.add(recs);
    });

    // Watch for changes from the server.
    t.subscribe('change', function(ev, info) {
        let recid = info.key;
        let newrow = info.value;
        if (!newrow) {
            grid.remove(recid);
        } else if (grid.get(recid)) {
            grid.set(recid, newrow);
        } else {
            newrow.recid = recid;
            grid.add([newrow]);
        }
    });

    // Send local changes.
    grid.on('change', function(event) {
        let field = grid.columns[event.column].field;
        t.update(new PKey(event.recid), [new FieldValue(':' + field, event.value_new)]);
        event.onComplete = function() { grid.save(); };
    });
});
