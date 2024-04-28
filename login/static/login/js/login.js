
// JavaScript文件中的AJAX请求函数
function performLogin() {
    var username = document.getElementById("username").value;
    var password = document.getElementById("password").value;

    console.log('Sending data to backend:', {username: username, password: password});

    if (username.trim() === "") {
        // 账号为空，显示账号为空的模态框
        $('#emptyusernameModal').modal('show');
        return; // 不执行后续的AJAX请求
    }
    else if (password.trim() === "") {
        $('#emptyPasswordModal').modal('show');
        return; // 不执行后续的AJAX请求
    }
    else {
        $.ajax({
            url: '',  // 后端处理登录的API端点
            method: 'POST',
            contentType: 'application/json',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },

            data: JSON.stringify({username: username, password: password}),
            success: function (response) {
                // 处理后端响应
                if (response.status === 'success') 
                {
                    alert('登录成功');
                    // 成功登录后,重定向到下一个页面
                    if(response.message.includes('student'))
                        // window.location.href = window.location.origin + '/student/home/';
                        window.location.href = '/student/home/';
                    else if(response.message.includes('teacher'))
                        // window.location.href = window.location.origin + '/teacher/home/';
                        window.location.href='/teacher/home/';
                    else if(response.message.includes('administrator'))
                        // window.location.href = window.location.origin + '/administrator/home/';
                        window.location.href='/administrator/home/';

                }

                else {
                    alert(response.message);
                    // 检查特定的错误条件
                    if (response.message.includes('Userid is incorrect')) {
                        // 显示学号错误模态框
                        $('#usernameErrorModal').modal('show');
                    }
                    else if (response.message.includes('Password is incorrect')) {
                        // 显示密码错误模态框
                        $('#passwordErrorModal').modal('show');
                    }
                }
            },
            error: function (error) {
                console.error(error);
            }
        });
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // 判断cookie是否以指定的name开头
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

