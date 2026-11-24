import assert from 'node:assert/strict'
import { once } from 'node:events'
import { createServer } from 'node:http'
import test from 'node:test'
import { Agent } from '@strands-agents/sdk'
import { HttpCallTemplateSerializer } from '@utcp/http'
import { UtcpClient } from '@utcp/sdk'
import { toStrandsTools } from '@utcp/strands'

test('discovers an HTTP manual and calls its tool through Strands', async (t) => {
  const requests = []
  const server = createServer((request, response) => {
    requests.push([request.method, request.url])
    response.setHeader('Content-Type', 'application/json')
    if (request.url === '/manual') {
      response.end(JSON.stringify({
        utcp_version: '1.0.0',
        manual_version: '1.0.0',
        tools: [{
          name: 'lookup',
          description: 'Look up a station by ID',
          inputs: { type: 'object', properties: { id: { type: 'string' } }, required: ['id'] },
          tool_call_template: {
            name: 'lookup', call_template_type: 'http', http_method: 'GET', url: `${baseUrl}/stations/{id}`,
          },
        }],
      }))
    } else if (request.url === '/stations/SEA') {
      response.end(JSON.stringify({ station: 'Seattle' }))
    } else {
      response.writeHead(404).end()
    }
  })
  server.listen(0, '127.0.0.1')
  await once(server, 'listening')
  t.after(() => server[Symbol.asyncDispose]())
  const baseUrl = `http://127.0.0.1:${server.address().port}`

  const client = await UtcpClient.create()
  t.after(() => client.close())
  const manual = new HttpCallTemplateSerializer().validateDict({
    name: 'stations', call_template_type: 'http', url: `${baseUrl}/manual`,
  })
  const registration = await client.registerManual(manual)
  assert.ok(registration.success, registration.errors.join(', '))

  const agent = new Agent({ tools: await toStrandsTools(client) })
  const result = await agent.tool.stations_lookup.invoke({ id: 'SEA' })

  assert.equal(result.status, 'success')
  assert.deepEqual(result.content[0].json, { station: 'Seattle' })
  assert.deepEqual(requests, [['GET', '/manual'], ['GET', '/stations/SEA']])
})
