import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import api from './api'

Vue.config.productionTip = false

// 使用Element UI
Vue.use(ElementUI)

// 添加全局API对象
Vue.prototype.$api = api

new Vue({
  router,
  render: h => h(App)
}).$mount('#app') 