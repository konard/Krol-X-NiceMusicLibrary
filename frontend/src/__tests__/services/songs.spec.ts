import { describe, it, expect } from 'vitest'
import {
  formatDuration,
  formatFileSize,
  isValidAudioFile,
  getStreamUrl,
  getCoverUrl,
} from '../../services/songs'

describe('songService utilities', () => {
  describe('formatDuration', () => {
    it('formats seconds under a minute', () => {
      expect(formatDuration(45)).toBe('0:45')
    })

    it('formats minutes and seconds', () => {
      expect(formatDuration(125)).toBe('2:05')
    })

    it('formats hours, minutes, and seconds', () => {
      expect(formatDuration(3661)).toBe('1:01:01')
    })

    it('pads seconds with leading zero', () => {
      expect(formatDuration(65)).toBe('1:05')
    })

    it('handles zero', () => {
      expect(formatDuration(0)).toBe('0:00')
    })

    it('handles large durations', () => {
      expect(formatDuration(7200)).toBe('2:00:00')
    })
  })

  describe('formatFileSize', () => {
    it('formats bytes', () => {
      expect(formatFileSize(500)).toBe('500 B')
    })

    it('formats kilobytes', () => {
      expect(formatFileSize(1024)).toBe('1.0 KB')
    })

    it('formats megabytes', () => {
      expect(formatFileSize(1048576)).toBe('1.0 MB')
    })

    it('formats gigabytes', () => {
      expect(formatFileSize(1073741824)).toBe('1.0 GB')
    })

    it('formats with decimal precision', () => {
      expect(formatFileSize(1536)).toBe('1.5 KB')
    })

    it('handles zero', () => {
      expect(formatFileSize(0)).toBe('0 B')
    })
  })

  describe('isValidAudioFile', () => {
    it('accepts mp3 files by type', () => {
      const file = new File([''], 'song.mp3', { type: 'audio/mpeg' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts flac files by type', () => {
      const file = new File([''], 'song.flac', { type: 'audio/flac' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts ogg files by type', () => {
      const file = new File([''], 'song.ogg', { type: 'audio/ogg' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts wav files by type', () => {
      const file = new File([''], 'song.wav', { type: 'audio/wav' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts m4a files by type', () => {
      const file = new File([''], 'song.m4a', { type: 'audio/mp4' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts files by extension when type is empty', () => {
      const file = new File([''], 'song.mp3', { type: '' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('accepts flac by extension', () => {
      const file = new File([''], 'song.flac', { type: '' })
      expect(isValidAudioFile(file)).toBe(true)
    })

    it('rejects non-audio files', () => {
      const file = new File([''], 'document.pdf', { type: 'application/pdf' })
      expect(isValidAudioFile(file)).toBe(false)
    })

    it('rejects image files', () => {
      const file = new File([''], 'image.jpg', { type: 'image/jpeg' })
      expect(isValidAudioFile(file)).toBe(false)
    })

    it('rejects unknown extensions', () => {
      const file = new File([''], 'file.xyz', { type: '' })
      expect(isValidAudioFile(file)).toBe(false)
    })
  })

  describe('getStreamUrl', () => {
    it('returns correct stream URL', () => {
      const url = getStreamUrl('song-123')
      expect(url).toContain('/songs/song-123/stream')
    })
  })

  describe('getCoverUrl', () => {
    it('returns correct cover URL', () => {
      const url = getCoverUrl('song-123')
      expect(url).toContain('/songs/song-123/cover')
    })
  })
})
