import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { BackToInstancesLink } from '../components/BackToInstancesLink'

export function NotFoundPage() {
  return (
    <Stack spacing={2}>
      <Typography variant="h4" component="h1">
        Page not found
      </Typography>
      <Typography color="text.secondary">There is nothing at this address.</Typography>
      <BackToInstancesLink />
    </Stack>
  )
}
