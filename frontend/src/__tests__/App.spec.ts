import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import App from '../App.vue'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
Object.defineProperty(global, 'localStorage', { value: localStorageMock })

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

describe('App', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('renders properly', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          AppLayout: true,
        },
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('uses AppLayout component', () => {
    const wrapper = mount(App, {
      global: {
        stubs: {
          RouterView: true,
          AppLayout: {
            template: '<div class="app-layout"><slot /></div>',
          },
        },
      },
    })
    expect(wrapper.find('.app-layout').exists()).toBe(true)
  })
})
