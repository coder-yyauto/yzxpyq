module.exports = {
  lintOnSave: false,
  devServer: {
    port: 8080,
    host: '0.0.0.0',
    allowedHosts: ['localhost', '127.0.0.1', '0.0.0.0'],
    disableHostCheck: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        pathRewrite: {
          '^/api': '/api'
        }
      },
      '/uploads': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        secure: false,
        pathRewrite: {
          '^/uploads': '/uploads'
        }
      }
    },
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0'
    }
  },
  // 配置构建时的选项
  configureWebpack: {
    output: {
      // 添加时间戳到文件名，避免缓存问题
      filename: `js/[name].[hash:8].[${Date.now()}].js`,
      chunkFilename: `js/[name].[hash:8].[${Date.now()}].js`
    }
  }
} 