import { afterEach, describe, expect, it, vi } from 'vitest'
import { shareOrSave } from './saveImage.js'

// 이미지 공유: 파일만 넘긴다 (제목·글을 같이 넘기면 메신저에서 글 메시지가 따로 보내진다)
describe('shareOrSave', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('공유 창에는 이미지 파일만 넘긴다 (title·text·url 없음)', async () => {
    const share = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { canShare: () => true, share })
    const result = await shareOrSave(new Blob(['x'], { type: 'image/png' }), 'a.png')
    expect(result).toBe('shared')
    const arg = share.mock.calls[0][0]
    expect(Object.keys(arg)).toEqual(['files'])
    expect(arg.files[0].name).toBe('a.png')
  })

  it('공유를 닫으면 cancelled', async () => {
    vi.stubGlobal('navigator', { canShare: () => true, share: vi.fn().mockRejectedValue(new Error('AbortError')) })
    expect(await shareOrSave(new Blob(['x']), 'a.png')).toBe('cancelled')
  })
})
