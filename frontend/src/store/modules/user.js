// 用户状态管理模块

// 初始状态
const state = {
  currentUser: null
}

// Getters
const getters = {
  isLoggedIn: state => !!state.currentUser,
  isAdmin: state => state.currentUser && state.currentUser.is_admin,
  isTeacher: state => state.currentUser && state.currentUser.is_teacher,
  isFirstLogin: state => state.currentUser && state.currentUser.is_first_login,
  canPost: state => state.currentUser && state.currentUser.can_post,
  currentUser: state => state.currentUser
}

// Mutations
const mutations = {
  // 设置当前用户
  setCurrentUser(state, user) {
    state.currentUser = user
  },
  
  // 清除当前用户
  clearCurrentUser(state) {
    state.currentUser = null
  }
}

// Actions
const actions = {
  // 从本地存储加载用户
  loadUserFromStorage({ commit }) {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        const userData = JSON.parse(userStr)
        commit('setCurrentUser', userData)
        return userData
      }
    } catch (error) {
      console.error('从本地存储加载用户失败:', error)
    }
    return null
  },
  
  // 注销用户
  logout({ commit }) {
    localStorage.removeItem('user')
    commit('clearCurrentUser')
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
} 