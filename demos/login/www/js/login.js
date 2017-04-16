$(function () {
    server = new rpc.WSServer('ws://' + location.hostname + '/login/ws/');

    bind.bind_status($('#status')[0], server);

    login = server.getProxy('login', ['login']);

    $('#login').w2form({ 
        name   : 'login',
        fields : [
            { name: 'Username', type: 'text', required: true },
            { name: 'Password', type: 'password', required: true },
        ],
        actions: {
            login: function () {
                var uc_p = login.login(this.record.Username, this.record.Password);
                uc_p.then(function(uc) {
                    if (uc !== null) {
                        doLogin(uc);
                    } else {
                        w2popup.open({
                            title: 'Login failed',
                            body:'<center><p style="margin-top: 50;">Invalid username or password.</center>',
                            height: 100,
                            width: 300
                        });
                    }
                });
            }
        }
    });
    $("button[name='login']").addClass('btn-green');

    $('#logout').w2form({
        name: 'logout',
        fields: [],
        actions: {
            logout: function() {
                $('#logout').hide();
                $('#login').show();
                $('#status')[0].textContent = 'connected';
            }
        }
    });

    function doLogin(user_caps) {
        $('#login').hide();
        $('#logout').show();
        $('#status')[0].textContent = 'logged in';
    }

    server.connect();
});
