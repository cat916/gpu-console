import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import Link from '@mui/material/Link'
import { Link as RouterLink } from 'react-router-dom'

export function BackToInstancesLink() {
  return (
    <Link
      component={RouterLink}
      to="/instances"
      underline="hover"
      sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5, alignSelf: 'flex-start' }}
    >
      <ArrowBackIcon fontSize="small" />
      Instances
    </Link>
  )
}
