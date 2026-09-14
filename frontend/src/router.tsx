import { Navigate, type RouteObject } from 'react-router-dom'
import { AppLayout } from './components/AppLayout'
import { InstanceDetailPage } from './pages/InstanceDetailPage'
import { InstanceListPage } from './pages/InstanceListPage'
import { LaunchInstancePage } from './pages/LaunchInstancePage'
import { NotFoundPage } from './pages/NotFoundPage'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/instances" replace /> },
      { path: 'instances', element: <InstanceListPage /> },
      { path: 'instances/new', element: <LaunchInstancePage /> },
      { path: 'instances/:instanceId', element: <InstanceDetailPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]
