import Alert from '@mui/material/Alert'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogTitle from '@mui/material/DialogTitle'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Tooltip from '@mui/material/Tooltip'
import Typography from '@mui/material/Typography'
import { type ReactNode, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useDeleteInstance, useInstance } from '../api/queries'
import type { Instance } from '../api/types'
import { ApiErrorAlert } from '../components/ApiErrorAlert'
import { BackToInstancesLink } from '../components/BackToInstancesLink'
import { CopyableCommand } from '../components/CopyableCommand'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { StatusChip } from '../components/StatusChip'
import { DELETABLE_STATUSES, digCommand, formatTimestamp } from '../instances/format'
import { MONOSPACE_FONT } from '../theme'

function DetailRow({ label, children, monospace = false }: { label: string; children: ReactNode; monospace?: boolean }) {
  return (
    <>
      <Typography component="dt" color="text.secondary">
        {label}
      </Typography>
      <Typography component="dd" sx={{ m: 0, fontFamily: monospace ? MONOSPACE_FONT : undefined, overflowWrap: 'anywhere' }}>
        {children}
      </Typography>
    </>
  )
}

type DeleteInstanceDialogProps = {
  instance: Instance
  open: boolean
  onClose: () => void
}

function DeleteInstanceDialog({ instance, open, onClose }: DeleteInstanceDialogProps) {
  const deleteInstance = useDeleteInstance()

  function close() {
    if (deleteInstance.isPending) {
      return
    }
    deleteInstance.reset()
    onClose()
  }

  return (
    <Dialog open={open} onClose={close} aria-labelledby="delete-instance-title" fullWidth maxWidth="xs">
      <DialogTitle id="delete-instance-title">Delete {instance.name}?</DialogTitle>
      <DialogContent>
        <Stack spacing={2}>
          <DialogContentText>
            The instance and its hostname{' '}
            <Box component="code" sx={{ fontFamily: MONOSPACE_FONT }}>
              {instance.hostname}
            </Box>{' '}
            will be removed. This can't be undone.
          </DialogContentText>
          {deleteInstance.error && <ApiErrorAlert error={deleteInstance.error} />}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={close} disabled={deleteInstance.isPending}>
          Cancel
        </Button>
        <Button
          color="error"
          variant="contained"
          loading={deleteInstance.isPending}
          onClick={() => deleteInstance.mutate(instance.id, { onSuccess: onClose })}
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  )
}

function InstanceDetails({ instance }: { instance: Instance }) {
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const canDelete = DELETABLE_STATUSES.has(instance.status)

  return (
    <Stack spacing={3}>
      <Stack direction="row" useFlexGap sx={{ alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Typography variant="h4" component="h1" sx={{ overflowWrap: 'anywhere' }}>
          {instance.name}
        </Typography>
        <StatusChip status={instance.status} />
        <Box sx={{ flexGrow: 1 }} />
        <Tooltip title={canDelete ? '' : 'Instances can be deleted once they are running or have failed'}>
          <span>
            <Button color="error" variant="outlined" disabled={!canDelete} onClick={() => setConfirmingDelete(true)}>
              Delete
            </Button>
          </span>
        </Tooltip>
      </Stack>

      <Paper variant="outlined" sx={{ p: { xs: 2, sm: 3 } }}>
        <Box
          component="dl"
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: '140px 1fr' },
            columnGap: 3,
            rowGap: { xs: 0.5, sm: 1.5 },
            m: 0,
          }}
        >
          <DetailRow label="Hostname" monospace>
            {instance.hostname}
          </DetailRow>
          <DetailRow label="IP address" monospace>
            {instance.ip ?? '—'}
          </DetailRow>
          <DetailRow label="Type">{instance.instance_type}</DetailRow>
          <DetailRow label="Image">{instance.image}</DetailRow>
          <DetailRow label="Created">{formatTimestamp(instance.created_at)}</DetailRow>
          <DetailRow label="Updated">{formatTimestamp(instance.updated_at)}</DetailRow>
          <DetailRow label="ID" monospace>
            {instance.id}
          </DetailRow>
        </Box>
      </Paper>

      <Stack spacing={1}>
        <Typography variant="h6" component="h2">
          Try it
        </Typography>
        <Typography color="text.secondary">
          {instance.status === 'running'
            ? 'Resolve the hostname with the GPU Console DNS server:'
            : 'The hostname resolves once the instance is running.'}
        </Typography>
        <CopyableCommand command={digCommand(instance.hostname)} />
      </Stack>

      <DeleteInstanceDialog instance={instance} open={confirmingDelete} onClose={() => setConfirmingDelete(false)} />
    </Stack>
  )
}

export function InstanceDetailPage() {
  const { instanceId = '' } = useParams()
  const instance = useInstance(instanceId)
  const isNotFound = instance.error?.status === 404

  return (
    <Stack spacing={3} sx={{ maxWidth: 880 }}>
      <BackToInstancesLink />
      {instance.isPending && <LoadingIndicator label="Loading instance" />}
      {isNotFound && instance.data && (
        <Alert severity="info">{instance.data.name} has been deleted.</Alert>
      )}
      {isNotFound && !instance.data && <Alert severity="warning">No instance with ID {instanceId}.</Alert>}
      {instance.error && !isNotFound && (
        <ApiErrorAlert error={instance.error} onRetry={() => void instance.refetch()} />
      )}
      {instance.data && !isNotFound && <InstanceDetails instance={instance.data} />}
    </Stack>
  )
}
