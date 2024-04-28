document.addEventListener("DOMContentLoaded", function() {
    // 获取未完成的作业
    fetchTasks('https://example.com/api/incomplete-tasks', updateIncompleteTasks);

    // 获取已完成的作业
    fetchTasks('https://example.com/api/completed-tasks', updateCompletedTasks);
});

function fetchTasks(url, updateFunction) {
    fetch(url)
        .then(response => response.json()) // 将响应转换为JSON
        .then(tasks => updateFunction(tasks))
        .catch(error => {
            console.error(`Error fetching tasks from ${url}:`, error);
        });
}

function updateIncompleteTasks(tasks) {
    const tbody = document.querySelector('#incomplete-tasks tbody');
    tbody.innerHTML = ''; // 清空当前的内容

    tasks.forEach(task => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = task.name;
        row.appendChild(nameCell);

        const deadlineCell = document.createElement('td');
        deadlineCell.textContent = task.deadline;
        row.appendChild(deadlineCell);

        const actionCell = document.createElement('td');
        actionCell.innerHTML = '<button>标为完成</button>'; // 例如，这里可以添加一个按钮用于标记作业为已完成
        row.appendChild(actionCell);

        tbody.appendChild(row);
    });
}

function updateCompletedTasks(tasks) {
    const ul = document.querySelector('#completed-tasks ul');
    ul.innerHTML = ''; // 清空当前的内容

    tasks.forEach(task => {
        const li = document.createElement('li');
        li.textContent = `${task.name} (完成日期: ${task.completionDate})`;
        ul.appendChild(li);
    });

    // 如果没有已完成的作业，显示默认消息
    if (tasks.length === 0) {
        const li = document.createElement('li');
        li.textContent = 'No completed tasks';
        ul.appendChild(li);
    }
}
