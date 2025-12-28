import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Loader from '@/components/ui/Loader.vue'

describe('Loader', () => {
  it('renders svg element', () => {
    const wrapper = mount(Loader)
    expect(wrapper.find('svg').exists()).toBe(true)
  })

  it('has spin animation', () => {
    const wrapper = mount(Loader)
    expect(wrapper.find('svg').classes()).toContain('animate-spin')
  })

  it('applies size classes correctly', () => {
    const wrapperSm = mount(Loader, { props: { size: 'sm' } })
    expect(wrapperSm.find('svg').classes()).toContain('h-4')
    expect(wrapperSm.find('svg').classes()).toContain('w-4')

    const wrapperMd = mount(Loader, { props: { size: 'md' } })
    expect(wrapperMd.find('svg').classes()).toContain('h-6')
    expect(wrapperMd.find('svg').classes()).toContain('w-6')

    const wrapperLg = mount(Loader, { props: { size: 'lg' } })
    expect(wrapperLg.find('svg').classes()).toContain('h-8')
    expect(wrapperLg.find('svg').classes()).toContain('w-8')
  })

  it('applies color classes correctly', () => {
    const wrapperPrimary = mount(Loader, { props: { color: 'primary' } })
    expect(wrapperPrimary.find('svg').classes()).toContain('text-accent-primary')

    const wrapperWhite = mount(Loader, { props: { color: 'white' } })
    expect(wrapperWhite.find('svg').classes()).toContain('text-white')

    const wrapperCurrent = mount(Loader, { props: { color: 'current' } })
    expect(wrapperCurrent.find('svg').classes()).toContain('text-current')
  })

  it('has accessible role and label', () => {
    const wrapper = mount(Loader)
    expect(wrapper.find('svg').attributes('role')).toBe('status')
    expect(wrapper.find('svg').attributes('aria-label')).toBe('Loading')
  })
})
