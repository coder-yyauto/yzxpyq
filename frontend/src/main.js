import Vue from 'vue'
import App from './App.vue'
import router from './router'
import ElementUI from 'element-ui'
import 'element-ui/lib/theme-chalk/index.css'
import api from './api'
import store from './store'

Vue.config.productionTip = false

// 使用Element UI
Vue.use(ElementUI)

// 添加全局API对象
Vue.prototype.$api = api

// 从本地存储加载用户状态
store.dispatch('user/loadUserFromStorage')

new Vue({
  router,
  store,
  render: h => h(App)
}).$mount('#app') 