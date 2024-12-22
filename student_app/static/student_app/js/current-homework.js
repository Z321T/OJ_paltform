document.addEventListener("DOMContentLoaded", function() {
    // 获取当前任务信息
    fetchCurrentTask();

    // 其他获取作业的函数...
});

function fetchCurrentTask() {
    fetch('https://example.com/api/current-task')
        .then(response => response.json())
        .then(task => {
            updateCurrentTaskMessage(task);
        })
        .catch(error => {
            console.error('Error fetching current task:', error);
            updateCurrentTaskMessage(null); // 在错误情况下更新消息
        });
}

function updateCurrentTaskMessage(task) {
    const messageDiv = document.getElementById('current-task-message');
    if (task && task.name && task.progress) {
        // 假设 `task.progress` 包含题目的进行状态
        messageDiv.innerHTML = `<p>上次退出时，您正在做 <strong>${task.name}</strong>，做到了 <strong>${task.progress}</strong>。</p>`;
    } else {
        messageDiv.innerHTML = '<p>没有找到上次的任务信息。</p>';
    }
}
