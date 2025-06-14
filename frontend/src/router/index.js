import Vue from 'vue'
import VueRouter from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Moments from '../views/Moments.vue'
import CreatePost from '../views/CreatePost.vue'
import UserProfile from '../views/UserProfile.vue'
import Admin from '../views/Admin.vue'
import FirstLogin from '../views/FirstLogin.vue'

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
  },
  {
    path: '/profile',
    name: 'UserProfile',
    component: UserProfile,
    meta: { requiresAuth: true }
  },
  {
    path: '/admin',
    name: 'Admin',
    component: Admin,
    meta: { requiresAuth: true, adminOnly: true }
  },
  {
    path: '/first-login',
    name: 'FirstLogin',
    component: FirstLogin,
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
  const adminOnly = to.matched.some(record => record.meta.adminOnly)
  
  console.log('路由守卫 - 当前路由是否需要认证:', requiresAuth, '路由路径:', to.path)
  
  if (requiresAuth && !user.id) {
    console.log('路由守卫 - 需要认证但用户未登录，重定向到登录页')
    next('/login')
  } else if (teacherOnly && !user.is_teacher) {
    console.log('路由守卫 - 需要教师权限但用户不是教师，重定向到动态页')
    next('/moments')
  } else if (adminOnly && !user.is_admin) {
    console.log('路由守卫 - 需要管理员权限但用户不是管理员，重定向到动态页')
    next('/moments')
  } else if (user.id && user.is_first_login && to.path !== '/first-login' && to.path !== '/login') {
    // 首次登录用户重定向到首次登录页面，但排除登录页面避免循环
    console.log('路由守卫 - 首次登录用户重定向到首次登录页面')
    next('/first-login')
  } else {
    console.log('路由守卫 - 允许继续导航')
    next()
  }
})

export default router 