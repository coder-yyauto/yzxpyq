import Vue from 'vue'
import VueRouter from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Moments from '../views/Moments.vue'
import CreatePost from '../views/CreatePost.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/register',
    name: 'Register',
    component: Register
  },
  {
    path: '/moments',
    name: 'Moments',
    component: Moments,
    meta: { requiresAuth: true }
  },
  {
    path: '/create',
    name: 'CreatePost',
    component: CreatePost,
    meta: { requiresAuth: true }
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

// 全局路由守卫
router.beforeEach((to, from, next) => {
  const userStr = localStorage.getItem('user')
  console.log('路由守卫 - 本地存储中的用户字符串:', userStr)
  
  const user = JSON.parse(userStr || '{}')
  console.log('路由守卫 - 解析后的用户对象:', user)
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const teacherOnly = to.matched.some(record => record.meta.teacherOnly)
  
  console.log('路由守卫 - 当前路由是否需要认证:', requiresAuth, '路由路径:', to.path)
  
  if (requiresAuth && !user.id) {
    console.log('路由守卫 - 需要认证但用户未登录，重定向到登录页')
    next('/login')
  } else if (teacherOnly && !user.is_teacher) {
    console.log('路由守卫 - 需要教师权限但用户不是教师，重定向到动态页')
    next('/moments')
  } else {
    console.log('路由守卫 - 允许继续导航')
    next()
  }
})

export default router 