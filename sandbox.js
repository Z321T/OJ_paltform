const { VM } = require('vm2');

// 创建一个新的VM实例
const vm = new VM();

// 定义要在沙盒中执行的JavaScript代码
const userCode = '2 + 2';

try {
    // 在沙盒中执行代码并获取结果
    const result = vm.run(userCode);
    console.log('执行结果:', result);
} catch (error) {
    console.error('执行代码时发生错误:', error);
}
