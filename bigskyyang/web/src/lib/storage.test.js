import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { KEEP_DAYS, clearSurvey, loadPicks, loadSurvey, savePicks, saveSurvey } from './storage.js'

// 응답 저장: 이 휴대폰(localStorage)에 7일, 서버로는 보내지 않음
function memoryStorage() {
  const m = new Map()
  return {
    getItem: (k) => (m.has(k) ? m.get(k) : null),
    setItem: (k, v) => m.set(k, String(v)),
    removeItem: (k) => m.delete(k),
    has: (k) => m.has(k),
  }
}

describe('응답 저장 (lib/storage.js)', () => {
  let local
  let session
  beforeEach(() => {
    local = memoryStorage()
    session = memoryStorage()
    vi.stubGlobal('localStorage', local)
    vi.stubGlobal('sessionStorage', session)
  })
  afterEach(() => vi.unstubAllGlobals())

  const state = { answers: { sex: 2 }, step: { 1: 1, 2: 0 }, done: { 1: false, 2: false } }

  it('탭을 닫았다 다시 열어도(같은 휴대폰) 이어서 불러온다', () => {
    saveSurvey(state)
    expect(loadSurvey().answers).toEqual({ sex: 2 })
  })

  it(`${KEEP_DAYS}일이 지나면 지운다`, () => {
    saveSurvey(state)
    const later = Date.now() + (KEEP_DAYS + 1) * 86400000
    expect(loadSurvey(later).answers).toEqual({})
    expect(local.has('nbti-survey-v4')).toBe(false)
  })

  it('처음부터 다시 검사하면 응답과 고른 제품을 바로 지운다', () => {
    saveSurvey(state)
    savePicks({ ids: ['a'], gate: 'ok', mine: [] })
    clearSurvey()
    expect(loadSurvey().answers).toEqual({})
    expect(loadPicks().ids).toEqual([])
  })

  it('예전 방식(탭에만 저장)의 응답은 한 번 옮겨 온다', () => {
    session.setItem('nbti-survey-v4', JSON.stringify(state))
    expect(loadSurvey().answers).toEqual({ sex: 2 })
    expect(session.has('nbti-survey-v4')).toBe(false)
    expect(local.has('nbti-survey-v4')).toBe(true)
  })

  it('저장소를 못 쓰면 빈 응답으로 계속한다', () => {
    vi.stubGlobal('localStorage', { getItem: () => { throw new Error('blocked') }, setItem: () => { throw new Error('blocked') }, removeItem: () => {} })
    expect(() => saveSurvey(state)).not.toThrow()
    expect(loadSurvey().answers).toEqual({})
  })
})
