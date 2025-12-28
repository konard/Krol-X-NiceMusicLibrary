import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Input from '@/components/ui/Input.vue'

describe('Input', () => {
  it('renders input element', () => {
    const wrapper = mount(Input)
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('binds v-model correctly', async () => {
    const wrapper = mount(Input, {
      props: {
        modelValue: 'initial',
        'onUpdate:modelValue': (e: string) => wrapper.setProps({ modelValue: e }),
      },
    })

    const input = wrapper.find('input')
    await input.setValue('new value')
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')![0]).toEqual(['new value'])
  })

  it('renders label when provided', () => {
    const wrapper = mount(Input, {
      props: { label: 'Email' },
    })
    expect(wrapper.find('label').text()).toBe('Email')
  })

  it('shows error message', () => {
    const wrapper = mount(Input, {
      props: { error: 'This field is required' },
    })
    expect(wrapper.text()).toContain('This field is required')
  })

  it('applies error classes when error exists', () => {
    const wrapper = mount(Input, {
      props: { error: 'Error' },
    })
    expect(wrapper.find('input').classes()).toContain('border-accent-error')
  })

  it('disables input when disabled prop is true', () => {
    const wrapper = mount(Input, {
      props: { disabled: true },
    })
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
  })

  it('sets input type correctly', () => {
    const wrapper = mount(Input, {
      props: { type: 'password' },
    })
    expect(wrapper.find('input').attributes('type')).toBe('password')
  })

  it('sets placeholder correctly', () => {
    const wrapper = mount(Input, {
      props: { placeholder: 'Enter your email' },
    })
    expect(wrapper.find('input').attributes('placeholder')).toBe('Enter your email')
  })

  it('emits focus event', async () => {
    const wrapper = mount(Input)
    await wrapper.find('input').trigger('focus')
    expect(wrapper.emitted('focus')).toBeTruthy()
  })

  it('emits blur event', async () => {
    const wrapper = mount(Input)
    await wrapper.find('input').trigger('blur')
    expect(wrapper.emitted('blur')).toBeTruthy()
  })
})
