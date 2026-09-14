import { createTheme } from '@mui/material/styles'

export const MONOSPACE_FONT = 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

export const theme = createTheme({
  cssVariables: true,
  colorSchemes: {
    light: { palette: { primary: { main: '#0E7456' } } },
    dark: { palette: { primary: { main: '#5CC99C' } } },
  },
  shape: { borderRadius: 8 },
  typography: {
    h4: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
})
