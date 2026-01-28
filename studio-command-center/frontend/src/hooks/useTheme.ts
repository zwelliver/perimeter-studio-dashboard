import { useState, useEffect } from 'react'
import type { Theme } from '../types/dashboard'

export const useTheme = () => {
  // Get initial theme from localStorage or default to 'dark'
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('studio-theme')
      if (saved === 'light' || saved === 'dark') {
        return saved as Theme
      }

      // Check user's system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      return prefersDark ? 'dark' : 'light'
    }
    return 'dark'
  })

  useEffect(() => {
    // Apply theme to document root
    document.documentElement.setAttribute('data-theme', theme)

    // Save to localStorage
    localStorage.setItem('studio-theme', theme)

    // Update meta theme-color for mobile browsers
    const metaThemeColor = document.querySelector('meta[name="theme-color"]')
    if (metaThemeColor) {
      metaThemeColor.setAttribute('content', theme === 'dark' ? '#0a1628' : '#f5f7fa')
    }
  }, [theme])

  const toggleTheme = (): void => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  const setThemeDirectly = (newTheme: Theme): void => {
    setTheme(newTheme)
  }

  return {
    theme,
    toggleTheme,
    setTheme: setThemeDirectly,
    isDark: theme === 'dark'
  }
}