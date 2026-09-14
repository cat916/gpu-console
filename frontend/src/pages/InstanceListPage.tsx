import AddIcon from '@mui/icons-material/Add'
import Button from '@mui/material/Button'
import Link from '@mui/material/Link'
import Paper from '@mui/material/Paper'
import Stack from '@mui/material/Stack'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Typography from '@mui/material/Typography'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { useInstances } from '../api/queries'
import type { Instance } from '../api/types'
import { ApiErrorAlert } from '../components/ApiErrorAlert'
import { LoadingIndicator } from '../components/LoadingIndicator'
import { StatusChip } from '../components/StatusChip'
import { MONOSPACE_FONT } from '../theme'

function LaunchInstanceButton() {
  return (
    <Button component={RouterLink} to="/instances/new" variant="contained" startIcon={<AddIcon />}>
      Launch instance
    </Button>
  )
}

function EmptyInstances() {
  return (
    <Paper variant="outlined" sx={{ p: 6, textAlign: 'center' }}>
      <Stack spacing={2} sx={{ alignItems: 'center' }}>
        <Typography variant="h6" component="h2">
          No instances yet
        </Typography>
        <Typography color="text.secondary">
          Launch a GPU instance and it will appear here with its hostname and IP address.
        </Typography>
        <LaunchInstanceButton />
      </Stack>
    </Paper>
  )
}

function InstancesTable({ instances }: { instances: Instance[] }) {
  const navigate = useNavigate()
  return (
    <Paper variant="outlined">
      <TableContainer>
        <Table aria-label="Instances">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Hostname</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>IP address</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {instances.map((instance) => (
              <TableRow
                key={instance.id}
                hover
                onClick={() => void navigate(`/instances/${instance.id}`)}
                sx={{ cursor: 'pointer', '&:last-child td': { borderBottom: 0 } }}
              >
                <TableCell>
                  <Link
                    component={RouterLink}
                    to={`/instances/${instance.id}`}
                    underline="hover"
                    onClick={(event) => event.stopPropagation()}
                    sx={{ fontWeight: 500 }}
                  >
                    {instance.name}
                  </Link>
                </TableCell>
                <TableCell sx={{ fontFamily: MONOSPACE_FONT }}>{instance.hostname}</TableCell>
                <TableCell>{instance.instance_type}</TableCell>
                <TableCell>
                  <StatusChip status={instance.status} />
                </TableCell>
                <TableCell sx={{ fontFamily: MONOSPACE_FONT }}>{instance.ip ?? '—'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  )
}

export function InstanceListPage() {
  const instances = useInstances()

  return (
    <Stack spacing={3}>
      <Stack
        direction="row"
        useFlexGap
        sx={{ justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}
      >
        <Typography variant="h4" component="h1">
          Instances
        </Typography>
        <LaunchInstanceButton />
      </Stack>

      {instances.error && (
        <ApiErrorAlert error={instances.error} onRetry={() => void instances.refetch()} />
      )}

      {instances.isPending && !instances.error && <LoadingIndicator label="Loading instances" />}
      {instances.data?.length === 0 && <EmptyInstances />}
      {instances.data && instances.data.length > 0 && <InstancesTable instances={instances.data} />}
    </Stack>
  )
}
