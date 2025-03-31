module.exports = {
  lintOnSave: false,
  devServer: {
    port: 8080,
    host: '0.0.0.0',
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
    }
  }
} 