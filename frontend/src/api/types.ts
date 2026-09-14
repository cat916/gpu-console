import type { components } from './schema'

type Schemas = components['schemas']

export type Instance = Schemas['Instance']
export type InstanceStatus = Schemas['InstanceStatus']
export type InstanceType = Schemas['InstanceType']
export type Image = Schemas['Image']
export type CreateInstanceRequest = Schemas['CreateInstanceRequest']
export type ErrorResponse = Schemas['ErrorResponse']
export type FieldError = Schemas['FieldError']
