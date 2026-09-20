import { describe, expect, it } from 'vitest'
import { hostnameFor, instanceNameProblem } from './names'

describe('instanceNameProblem', () => {
  it('accepts a dns label', () => {
    expect(instanceNameProblem('train-01')).toBeNull()
  })

  it.each(['', 'Train-01', 'train_01', 'train.01', '-train', 'train-', 'a'.repeat(64)])(
    'rejects %j',
    (name) => {
      expect(instanceNameProblem(name)).not.toBeNull()
    },
  )

  it('counts the characters when the name is too long', () => {
    expect(instanceNameProblem('a'.repeat(64))).toContain('currently 64')
  })
})

describe('hostnameFor', () => {
  it('joins the name to the dns zone', () => {
    expect(hostnameFor('train-01')).toBe('train-01.gpu.internal')
  })
})
