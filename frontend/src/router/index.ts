import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Define route meta interface inline to avoid type conflicts
interface AppRouteMeta {
  requiresAuth?: boolean
  title?: string
  layout?: 'default' | 'auth'
}

// Lazy-loaded page components
const HomeView = () => import('@/pages/HomeView.vue')
const LoginView = () => import('@/pages/LoginView.vue')
const RegisterView = () => import('@/pages/RegisterView.vue')
const LibraryView = () => import('@/pages/LibraryView.vue')
const PlaylistsView = () => import('@/pages/PlaylistsView.vue')
const PlaylistView = () => import('@/pages/PlaylistView.vue')
const StatsView = () => import('@/pages/StatsView.vue')
const SettingsView = () => import('@/pages/SettingsView.vue')
const NotFoundView = () => import('@/pages/NotFoundView.vue')
const MoodChainsView = () => import('@/pages/MoodChainsView.vue')
const MoodChainView = () => import('@/pages/MoodChainView.vue')

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: 'Home',
    },
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: {
      title: 'Sign In',
      layout: 'auth',
    },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: {
      title: 'Sign Up',
      layout: 'auth',
    },
  },
  {
    path: '/library',
    name: 'library',
    component: LibraryView,
    meta: {
      title: 'Library',
      requiresAuth: true,
    },
  },
  {
    path: '/stats',
    name: 'stats',
    component: StatsView,
    meta: {
      title: 'Statistics',
      requiresAuth: true,
    },
  },
  {
    path: '/playlists',
    name: 'playlists',
    component: PlaylistsView,
    meta: {
      title: 'Playlists',
      requiresAuth: true,
    },
  },
  {
    path: '/playlists/:id',
    name: 'playlist',
    component: PlaylistView,
    meta: {
      title: 'Playlist',
      requiresAuth: true,
    },
  },
  {
    path: '/settings',
    name: 'settings',
    component: SettingsView,
    meta: {
      title: 'Settings',
    },
  },
  // Mood chain routes
  {
    path: '/mood-chains',
    name: 'mood-chains',
    component: MoodChainsView,
    meta: {
      title: 'Mood Chains',
      requiresAuth: true,
    },
  },
  {
    path: '/mood-chains/:id',
    name: 'mood-chain',
    component: MoodChainView,
    meta: {
      title: 'Mood Chain',
      requiresAuth: true,
    },
  },
  // Placeholder routes - to be implemented in future issues
  {
    path: '/search',
    name: 'search',
    component: HomeView,
    meta: {
      title: 'Search',
    },
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: HomeView,
    meta: {
      title: 'Favorites',
      requiresAuth: true,
    },
  },
  {
    path: '/recent',
    name: 'recent',
    component: HomeView,
    meta: {
      title: 'Recent',
      requiresAuth: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: NotFoundView,
    meta: {
      title: 'Page Not Found',
    },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
})

// Navigation guard for protected routes
router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore()

  // Update document title
  const meta = to.meta as AppRouteMeta
  const title = meta?.title
  document.title = title ? `${title} | NiceMusicLibrary` : 'NiceMusicLibrary'

  // Check if route requires authentication
  const requiresAuth = meta?.requiresAuth

  if (requiresAuth && !authStore.isAuthenticated) {
    // Try to initialize auth state (check for existing tokens)
    await authStore.initialize()

    if (!authStore.isAuthenticated) {
      // Redirect to login with return URL
      next({
        name: 'login',
        query: { redirect: to.fullPath },
      })
      return
    }
  }

  // Redirect authenticated users away from login/register
  if (
    authStore.isAuthenticated &&
    (to.name === 'login' || to.name === 'register')
  ) {
    next({ name: 'home' })
    return
  }

  next()
})

export default router
