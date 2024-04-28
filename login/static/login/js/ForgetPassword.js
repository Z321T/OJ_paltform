function showConfirmationModal() {
    console.log('showConfirmationModal');
    $('#confirmationModal').modal('show');  // 使用 Bootstrap 方法显示 Modal
}

function hideConfirmationModal() {
    $('#confirmationModal').modal('hide');  // 使用 Bootstrap 方法隐藏 Modal
}

function submitRequest() {
    var studentID = document.getElementById("studentID").value;
//前端将学号传给后端
    $.ajax({
        url: '/api/forgot-password',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ studentId: studentID }),
        //后端返回密码重置成功success
        success: function (response) {
            if (response.status === 'success') {
                alert(response.message);
                hideConfirmationModal();
            } else {
                alert(response.message);
            }
        },
        error: function (error) {
            console.error(error);
        }
    });

    alert('您的请求已提交管理员确认');
    hideConfirmationModal();  // 隐藏 Modal
}

