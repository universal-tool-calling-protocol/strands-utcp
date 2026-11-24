import assert from 'node:assert/strict'
import test from 'node:test'
import { Agent } from '@strands-agents/sdk'
import { toStrandsTools } from '@utcp/strands'

const inputs = {
  type: 'object',
  properties: { city: { type: 'string', description: 'City to look up' } },
  required: ['city'],
  additionalProperties: false,
}

function definition(name) {
  return {
    name,
    description: 'Look up the local temperature',
    inputs,
    outputs: { type: 'object' },
    tags: [],
    tool_call_template: { call_template_type: 'http', url: 'https://weather.example/temperature' },
  }
}

function clientFor(names, callTool = assert.fail) {
  return {
    getTools: async () => names.map(definition),
    callTool,
  }
}

test('registers discovered schemas and calls the qualified UTCP tool through a Strands agent', async () => {
  const qualifiedName = 'weather.station.current-temperature'
  const expected = { temperature: 17, unit: 'C' }
  const calls = []
  const client = clientFor([qualifiedName], async (name, args) => {
    calls.push({ name, args })
    return expected
  })
  const tools = await toStrandsTools(client)
  const agent = new Agent({ tools })
  const [registered] = agent.tools
  assert.equal(registered.name, 'weather_station_current-temperature')
  assert.equal(registered.toolSpec.name, registered.name)
  assert.equal(registered.toolSpec.description, 'Look up the local temperature')
  assert.deepEqual(registered.toolSpec.inputSchema, inputs)

  const result = await agent.tool[registered.name].invoke({ city: 'Paris' })

  assert.equal(result.status, 'success')
  assert.deepEqual(result.content[0].json, expected)
  assert.deepEqual(calls, [{ name: qualifiedName, args: { city: 'Paris' } }])
})

test('returns UTCP call failures as Strands tool errors', async () => {
  const client = clientFor(['weather.current'], async () => {
    throw new Error('weather service unavailable')
  })
  const agent = new Agent({ tools: await toStrandsTools(client) })

  const result = await agent.tool.weather_current.invoke({ city: 'Paris' })

  assert.equal(result.status, 'error')
  assert.match(result.content[0].text, /weather service unavailable/)
})

test('preserves UTCP response data that resembles Strands content blocks', async () => {
  const message = { text: 'hello' }
  const cases = [
    { response: message, expected: message },
    { response: [message], expected: { $value: [message] } },
  ]
  for (const { response, expected } of cases) {
    const tools = await toStrandsTools(clientFor(['weather.report'], async () => response))
    const agent = new Agent({ tools })
    const result = await agent.tool.weather_report.invoke({})
    assert.equal(result.status, 'success')
    assert.deepEqual(result.content.map(block => block.json), [expected])
  }
})

test('handles sparse manual metadata and enforces object arguments', async () => {
  const tool = { ...definition('weather.now'), description: '', inputs: {} }
  const calls = []
  const client = {
    getTools: async () => [tool],
    callTool: async (name, args) => {
      calls.push({ name, args })
      return 'clear'
    },
  }
  const [adapted] = await toStrandsTools(client)
  assert.ok(adapted.description.includes(tool.name))
  assert.deepEqual(adapted.toolSpec.inputSchema, { type: 'object' })
  assert.equal(await adapted.invoke(), 'clear')
  for (const invalid of [null, 'city', []]) {
    await assert.rejects(adapted.invoke(invalid), /object/i)
  }
  assert.deepEqual(calls, [{ name: tool.name, args: {} }])
})

test('reports a non-object manual input schema during discovery', async () => {
  const tool = { ...definition('weather.list'), inputs: { type: 'string' } }
  const client = { getTools: async () => [tool], callTool: assert.fail }
  await assert.rejects(toStrandsTools(client), /weather\.list/)
})

test('keeps long names distinct and stable across discovery order', async () => {
  const prefix = 'weather.' + 'a'.repeat(64)
  const names = [prefix + '_today', prefix + '_tomorrow']
  const tools = await toStrandsTools(clientFor(names, async (name) => name))
  const reversed = await toStrandsTools(clientFor([...names].reverse(), async (name) => name))
  const agent = new Agent({ tools })
  const reversedAgent = new Agent({ tools: reversed })

  assert.notEqual(tools[0].name, tools[1].name)
  for (let i = 0; i < names.length; i++) {
    const alias = tools[i].name
    assert.match(alias, /^[a-zA-Z0-9_-]{1,64}$/)
    const result = await agent.tool[alias].invoke({})
    const reversedResult = await reversedAgent.tool[alias].invoke({})
    assert.equal(result.content[0].text, names[i])
    assert.equal(reversedResult.content[0].text, names[i])
  }
})

test('rejects ambiguous model-visible names before registering tools', async () => {
  for (const names of [
    ['weather.city.current', 'weather.city_current'],
    ['weather.city-current', 'weather.city_current'],
  ]) {
    await assert.rejects(toStrandsTools(clientFor(names)), error => {
      assert.ok(error.message.includes(names[0]))
      assert.ok(error.message.includes(names[1]))
      return true
    })
  }
})

test('distinguishes an empty catalog from a failed discovery', async () => {
  assert.deepEqual(await toStrandsTools(clientFor([])), [])
  const error = new Error('catalog unavailable')
  const client = {
    async getTools() {
      throw error
    },
    callTool: assert.fail,
  }
  await assert.rejects(toStrandsTools(client), error)
})
