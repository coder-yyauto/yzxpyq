import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    user: null,
    posts: []
  },
  mutations: {
    setUser(state, user) {
      state.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    setPosts(state, posts) {
      state.posts = posts
    },
    addPost(state, post) {
      state.posts.unshift(post)
    },
    updatePost(state, updatedPost) {
      const index = state.posts.findIndex(post => post.id === updatedPost.id)
      if (index !== -1) {
        state.posts.splice(index, 1, updatedPost)
      }
    }
  },
  actions: {
    async login({ commit }, credentials) {
      try {
        const response = await Vue.prototype.$api.post('/login', credentials)
        commit('setUser', response.data)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async register({ commit }, userData) {
      try {
        const response = await Vue.prototype.$api.post('/register', userData)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async fetchPosts({ commit }) {
      try {
        const response = await Vue.prototype.$api.get('/posts')
        commit('setPosts', response.data)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async createPost({ commit }, postData) {
      try {
        const response = await Vue.prototype.$api.post('/posts', postData)
        commit('addPost', response.data)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async likePost({ commit }, postId) {
      try {
        const response = await Vue.prototype.$api.post(`/posts/${postId}/like`)
        commit('updatePost', response.data)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async addComment({ commit }, { postId, commentData }) {
      try {
        const response = await Vue.prototype.$api.post(`/posts/${postId}/comments`, commentData)
        commit('updatePost', response.data)
        return response.data
      } catch (error) {
        throw error
      }
    },
    async uploadImage({ commit }, file) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const response = await Vue.prototype.$api.post('/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        return response.data
      } catch (error) {
        throw error
      }
    }
  }
}) 