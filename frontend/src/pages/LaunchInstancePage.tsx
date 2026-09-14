import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import FormControl from '@mui/material/FormControl'
import FormControlLabel from '@mui/material/FormControlLabel'
import FormHelperText from '@mui/material/FormHelperText'
import FormLabel from '@mui/material/FormLabel'
import MenuItem from '@mui/material/MenuItem'
import Paper from '@mui/material/Paper'
import Radio from '@mui/material/Radio'
import RadioGroup from '@mui/material/RadioGroup'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { type FormEvent, useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import type { ApiError } from '../api/client'
import { useCreateInstance, useImages, useInstanceTypes } from '../api/queries'
import type { Image, InstanceType } from '../api/types'
import { ApiErrorAlert } from '../components/ApiErrorAlert'
import { BackToInstancesLink } from '../components/BackToInstancesLink'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { formatGpus, formatPricePerHour, formatSpecs } from '../instances/format'
import { hostnameFor, instanceNameProblem } from '../instances/names'

type FormField = 'name' | 'instance_type' | 'image'
type FieldErrors = Partial<Record<FormField, string>>

const FORM_FIELDS: ReadonlySet<string> = new Set<FormField>(['name', 'instance_type', 'image'])

function fieldErrorsFrom(error: ApiError): FieldErrors {
  const fieldErrors: FieldErrors = {}
  for (const { field, message } of error.fields) {
    if (FORM_FIELDS.has(field)) {
      fieldErrors[field as FormField] = message
    }
  }
  return fieldErrors
}

function InstanceTypeOption({ instanceType }: { instanceType: InstanceType }) {
  return (
    <Box sx={{ display: 'flex', flexWrap: 'wrap', columnGap: 2, alignItems: 'baseline' }}>
      <Typography sx={{ fontWeight: 500 }}>{formatGpus(instanceType)}</Typography>
      <Typography variant="body2" color="text.secondary">
        {formatSpecs(instanceType)}
      </Typography>
      <Typography variant="body2" sx={{ fontVariantNumeric: 'tabular-nums' }}>
        {formatPricePerHour(instanceType.price_per_hour)}
      </Typography>
    </Box>
  )
}

type LaunchFormProps = {
  instanceTypes: InstanceType[]
  images: Image[]
}

function LaunchForm({ instanceTypes, images }: LaunchFormProps) {
  const navigate = useNavigate()
  const createInstance = useCreateInstance()
  const [name, setName] = useState('')
  const [nameTouched, setNameTouched] = useState(false)
  const [instanceTypeId, setInstanceTypeId] = useState(instanceTypes[0]?.id ?? '')
  const [imageId, setImageId] = useState(images[0]?.id ?? '')
  const [serverFieldErrors, setServerFieldErrors] = useState<FieldErrors>({})

  const nameProblem = instanceNameProblem(name)
  const nameError = serverFieldErrors.name ?? (nameTouched || name.length > 0 ? nameProblem : null)
  const unmappedError =
    createInstance.error && Object.keys(fieldErrorsFrom(createInstance.error)).length === 0
      ? createInstance.error
      : null

  function handleNameChange(value: string) {
    setName(value)
    setServerFieldErrors((current) => ({ ...current, name: undefined }))
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setNameTouched(true)
    if (nameProblem) {
      return
    }
    setServerFieldErrors({})
    createInstance.mutate(
      { name, instance_type: instanceTypeId, image: imageId },
      {
        onSuccess: (instance) => void navigate(`/instances/${instance.id}`),
        onError: (error) => setServerFieldErrors(fieldErrorsFrom(error)),
      },
    )
  }

  return (
    <Stack spacing={3}>
      {unmappedError && <ApiErrorAlert error={unmappedError} />}
      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
        <Box component="form" noValidate onSubmit={handleSubmit}>
          <Stack spacing={3}>
            <TextField
              id="instance-name"
              label="Name"
              value={name}
              onChange={(event) => handleNameChange(event.target.value)}
              onBlur={() => setNameTouched(true)}
              error={Boolean(nameError)}
              helperText={nameError ?? `Hostname: ${hostnameFor(name || 'train-01')}`}
              required
              autoFocus
              autoComplete="off"
              slotProps={{ htmlInput: { spellCheck: false } }}
            />

            <FormControl error={Boolean(serverFieldErrors.instance_type)}>
              <FormLabel id="instance-type-label">Instance type</FormLabel>
              <RadioGroup
                aria-labelledby="instance-type-label"
                name="instance_type"
                value={instanceTypeId}
                onChange={(_event, value) => setInstanceTypeId(value)}
              >
                {instanceTypes.map((instanceType) => (
                  <FormControlLabel
                    key={instanceType.id}
                    value={instanceType.id}
                    control={<Radio />}
                    label={<InstanceTypeOption instanceType={instanceType} />}
                  />
                ))}
              </RadioGroup>
              {serverFieldErrors.instance_type && (
                <FormHelperText>{serverFieldErrors.instance_type}</FormHelperText>
              )}
            </FormControl>

            <TextField
              id="instance-image"
              select
              label="Image"
              value={imageId}
              onChange={(event) => setImageId(event.target.value)}
              error={Boolean(serverFieldErrors.image)}
              helperText={serverFieldErrors.image}
            >
              {images.map((image) => (
                <MenuItem key={image.id} value={image.id}>
                  {image.name}
                </MenuItem>
              ))}
            </TextField>

            <Stack direction="row" spacing={1} sx={{ justifyContent: 'flex-end' }}>
              <Button component={RouterLink} to="/instances">
                Cancel
              </Button>
              <Button type="submit" variant="contained" loading={createInstance.isPending}>
                Launch
              </Button>
            </Stack>
          </Stack>
        </Box>
      </Paper>
    </Stack>
  )
}

export function LaunchInstancePage() {
  const instanceTypes = useInstanceTypes()
  const images = useImages()
  const catalogError = instanceTypes.error ?? images.error

  function retryCatalog() {
    void instanceTypes.refetch()
    void images.refetch()
  }

  return (
    <Stack spacing={3} sx={{ maxWidth: 720 }}>
      <BackToInstancesLink />
      <Typography variant="h4" component="h1">
        Launch instance
      </Typography>
      {catalogError && <ApiErrorAlert error={catalogError} onRetry={retryCatalog} />}
      {instanceTypes.data && images.data ? (
        <LaunchForm instanceTypes={instanceTypes.data} images={images.data} />
      ) : (
        !catalogError && <LoadingIndicator label="Loading instance types and images" />
      )}
    </Stack>
  )
}
