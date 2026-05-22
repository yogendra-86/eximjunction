export const setAuth = (token, user) => {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
}

export const clearAuth = () => {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
}

export const getToken = () => localStorage.getItem('token')

export const getUser = () => {
  try { return JSON.parse(localStorage.getItem('user')) }
  catch { return null }
}

export const isLoggedIn = () => !!getToken()
