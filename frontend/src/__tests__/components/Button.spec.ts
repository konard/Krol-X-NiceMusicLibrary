import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from '@/components/ui/Button.vue'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, {
      slots: {
        default: 'Click me',
      },
    })
    expect(wrapper.text()).toContain('Click me')
  })

  it('applies primary variant classes by default', () => {
    const wrapper = mount(Button)
    expect(wrapper.classes()).toContain('bg-accent-primary')
  })

  it('applies secondary variant classes', () => {
    const wrapper = mount(Button, {
      props: { variant: 'secondary' },
    })
    expect(wrapper.classes()).toContain('bg-bg-secondary')
  })

  it('applies ghost variant classes', () => {
    const wrapper = mount(Button, {
      props: { variant: 'ghost' },
    })
    expect(wrapper.classes()).toContain('bg-transparent')
  })

  it('applies danger variant classes', () => {
    const wrapper = mount(Button, {
      props: { variant: 'danger' },
    })
    expect(wrapper.classes()).toContain('bg-accent-error')
  })

  it('applies size classes', () => {
    const wrapperSm = mount(Button, { props: { size: 'sm' } })
    expect(wrapperSm.classes()).toContain('px-3')

    const wrapperLg = mount(Button, { props: { size: 'lg' } })
    expect(wrapperLg.classes()).toContain('px-6')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
  })

  it('does not emit click when disabled', async () => {
    const wrapper = mount(Button, {
      props: { disabled: true },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('does not emit click when loading', async () => {
    const wrapper = mount(Button, {
      props: { loading: true },
    })
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toBeFalsy()
  })

  it('shows loading spinner when loading', () => {
    const wrapper = mount(Button, {
      props: { loading: true },
    })
    expect(wrapper.find('svg.animate-spin').exists()).toBe(true)
  })

  it('applies fullWidth class', () => {
    const wrapper = mount(Button, {
      props: { fullWidth: true },
    })
    expect(wrapper.classes()).toContain('w-full')
  })

  it('has correct button type', () => {
    const wrapper = mount(Button, {
      props: { type: 'submit' },
    })
    expect(wrapper.attributes('type')).toBe('submit')
  })
})
