import api from './api'

export function getAISystemKnowledge() {
  return api.get('/ai/system-knowledge')
}

export function postAIChat(payload) {
  return api.post('/ai/chat', payload)
}