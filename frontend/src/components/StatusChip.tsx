import Chip, { type ChipProps } from '@mui/material/Chip'
import CircularProgress from '@mui/material/CircularProgress'
import type { InstanceStatus } from '../api/types'

type StatusAppearance = {
  label: string
  color: ChipProps['color']
  inProgress: boolean
}

const STATUS_APPEARANCE: Record<InstanceStatus, StatusAppearance> = {
  provisioning: { label: 'Provisioning', color: 'warning', inProgress: true },
  running: { label: 'Running', color: 'success', inProgress: false },
  failed: { label: 'Failed', color: 'error', inProgress: false },
  deleting: { label: 'Deleting', color: 'default', inProgress: true },
}

export function StatusChip({ status }: { status: InstanceStatus }) {
  const { label, color, inProgress } = STATUS_APPEARANCE[status]
  return (
    <Chip
      size="small"
      variant="outlined"
      color={color}
      label={label}
      icon={inProgress ? <CircularProgress size={12} color="inherit" /> : undefined}
    />
  )
}
