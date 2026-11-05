import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve, dirname } from 'node:path'
import { readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const rootDir = dirname(fileURLToPath(import.meta.url))

// Automatically include all HTML pages
const htmlFiles = readdirSync(rootDir).filter(file =>
  file.toLowerCase().endsWith('.html')
)

const input = Object.fromEntries(
  htmlFiles.map(file => [
    file.replace(/\.html$/i, ''),
    resolve(rootDir, file)
  ])
)

export default defineConfig({
  plugins: [react()],

  build: {
    rollupOptions: {
      input
    }
  }
})
