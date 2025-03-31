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
    path: '/create-post',
    name: 'CreatePost',
    component: CreatePost,
    meta: { requiresAuth: true }
  }
]

const router = new VueRouter({
  routes
})

router.beforeEach((to, from, next) => {
  const user = localStorage.getItem('user')
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!user) {
      next('/login')
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router 