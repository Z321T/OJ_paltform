const path = require('path');

module.exports = {
  entry: 'static/js/main.js', // 您的入口文件
  output: {
    path: path.resolve(__dirname, 'static/js'), // 输出目录，例如Django的static文件夹
    filename: 'bundle.js', // 输出文件
  },
  module: {
    rules: [
      {
        test: /\.js$/, // 使用正则表达式来匹配所有.js文件
        exclude: /node_modules/, // 排除node_modules目录
        use: {
          loader: 'babel-loader', // 使用babel-loader
          options: {
            presets: ['@babel/preset-env'], // 使用@babel/preset-env
          },
        },
      },
    ],
  },
};
