$$('#login').on('click', function() {
    var username = $$('input[name=username]').val();
    var password = $$('input[name=password]').val();

    if (!username || !password) {
        app.dialog.alert('Enter both username and password', 'Input error');
        return;
    }

    app.request({
        url: '/api/v1.0/login',
        type: 'POST',
        data: {
            username: username,
            password: password
        },
        success: function (data) {
            var d_obj = JSON.parse(data);
            switch (d_obj.status_code) {
                case 10: 
                    // $$('#username').text(d_obj.result.current_user);
                    // current_bidder = d_obj.result.current_bidder;
                    // mainView.router.load({
                    //     url: 'static/status.html'
                    // });
                    mainView.router.navigate('/radios/');
                    activateConnection();
                    loginScreen.close();
                    break;
                case 20: 
                    loginScreen.close();
                    break;
                case 30:
                    app.dialog.alert('Login or password incorect', 'Login error');
                    break;
            }
        }
    });
});

$$('#logout').on('click', function() {
    app.request({
        url: '/api/v1.0/logout',
        type: 'POST',
        success: function (data) {
            var d_obj = JSON.parse(data);
            switch (d_obj.status_code) {
                case 40: 
                    loginScreen.open();
                    break;
                default:
                    app.dialog.alert('Refresh the page', 'Logout error');
                    break;
            }
        }
    });
});
