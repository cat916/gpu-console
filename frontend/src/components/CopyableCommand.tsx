import CheckIcon from '@mui/icons-material/Check'
import ContentCopyIcon from '@mui/icons-material/ContentCopy'
import Box from '@mui/material/Box'
import IconButton from '@mui/material/IconButton'
import Paper from '@mui/material/Paper'
import Tooltip from '@mui/material/Tooltip'
import { useEffect, useState } from 'react'
import { MONOSPACE_FONT } from '../theme'

type CopyState = 'idle' | 'copied' | 'failed'

const COPY_FEEDBACK_MS = 1500

const TOOLTIP_BY_STATE: Record<CopyState, string> = {
  idle: 'Copy command',
  copied: 'Copied',
  failed: 'Copy failed, select the text instead',
}

export function CopyableCommand({ command }: { command: string }) {
  const [copyState, setCopyState] = useState<CopyState>('idle')

  useEffect(() => {
    if (copyState === 'idle') {
      return
    }
    const timer = setTimeout(() => setCopyState('idle'), COPY_FEEDBACK_MS)
    return () => clearTimeout(timer)
  }, [copyState])

  function copy() {
    navigator.clipboard.writeText(command).then(
      () => setCopyState('copied'),
      () => setCopyState('failed'),
    )
  }

  return (
    <Paper
      variant="outlined"
      sx={{ display: 'flex', alignItems: 'center', gap: 1, pl: 2, pr: 1, py: 0.75, bgcolor: 'action.hover' }}
    >
      <Box
        component="code"
        sx={{ flex: 1, fontFamily: MONOSPACE_FONT, fontSize: 14, overflowX: 'auto', whiteSpace: 'nowrap' }}
      >
        {command}
      </Box>
      <Tooltip title={TOOLTIP_BY_STATE[copyState]}>
        <IconButton aria-label="Copy command" size="small" onClick={copy}>
          {copyState === 'copied' ? <CheckIcon fontSize="small" /> : <ContentCopyIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Paper>
  )
}
