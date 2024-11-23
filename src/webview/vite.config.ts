import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import type { Plugin, ViteDevServer } from 'vite'
import type { IncomingMessage, ServerResponse } from 'http'
import { useDebugStore } from './src/store/debugStore'

// Create plugin to handle API endpoints
const apiPlugin: Plugin = {
  name: 'api',
  configureServer(server: ViteDevServer) {
    server.middlewares.use('/api/events', async (
      req: IncomingMessage,
      res: ServerResponse
    ) => {
      if (req.method === 'POST') {
        try {
          // Get request body
          const chunks = []
          for await (const chunk of req) {
            chunks.push(chunk)
          }
          const data = Buffer.concat(chunks).toString()
          const event = JSON.parse(data)

          // Update store
          const store = useDebugStore.getState()
          store.addEvent(event)
          if (event.payload.current_agent) {
            store.addAgent(event.payload.current_agent)
          }

          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ status: 'success' }))
        } catch (error) {
          console.error('Failed to process event:', error)
          res.statusCode = 400
          res.setHeader('Content-Type', 'application/json')
          res.end(JSON.stringify({ error: 'Invalid event data' }))
        }
      } else {
        res.statusCode = 405
        res.setHeader('Content-Type', 'application/json')
        res.end(JSON.stringify({ error: 'Method not allowed' }))
      }
    })
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), apiPlugin]
})
