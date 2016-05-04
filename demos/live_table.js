// Some boilerplate to ensure that AMD require modules and
// jquery are all ready before we run the main program.

require(['serf/rpc'],
function(rpc) {
    window.rpc = rpc;

    $(mainprog);
});

function mainprog() {
    // Register some classes we can pass to and from the server.
    // 
    // NOTE: On the server these classes actually do something. Here
    // we only need to be able to create them or examine their values
    // so their construction can be completely automated.
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
    t = serv.getProxy('table');

    // Populate the table.
    t.select().done(rows => {
        var recs = rows.map(kv => { rec = kv[1]; rec.recid = kv[0]; return rec; });
        grid.add(recs);
    });

    // Watch for changes from the server.
    t.subscribe('change', (ev, info) => {
        let recid = info[0];
        let newrow = info[2];
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
    grid.on('change', event => {
        let field = grid.columns[event.column].field;
        t.update(new PKey(event.recid), [new FieldValue(':' + field, event.value_new)]);
        event.onComplete = () => grid.save();
    });
}

