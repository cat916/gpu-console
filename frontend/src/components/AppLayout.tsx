import MemoryIcon from '@mui/icons-material/Memory'
import AppBar from '@mui/material/AppBar'
import Container from '@mui/material/Container'
import Toolbar from '@mui/material/Toolbar'
import Typography from '@mui/material/Typography'
import { Outlet, Link as RouterLink } from 'react-router-dom'

export function AppLayout() {
  return (
    <>
      <AppBar
        position="static"
        color="default"
        elevation={0}
        sx={{ borderBottom: 1, borderColor: 'divider', bgcolor: 'background.paper' }}
      >
        <Toolbar sx={{ gap: 1.5 }}>
          <MemoryIcon color="primary" />
          <Typography
            variant="h6"
            component={RouterLink}
            to="/instances"
            sx={{ color: 'text.primary', textDecoration: 'none' }}
          >
            GPU Console
          </Typography>
        </Toolbar>
      </AppBar>
      <Container component="main" maxWidth="lg" sx={{ py: 4 }}>
        <Outlet />
      </Container>
    </>
  )
}
