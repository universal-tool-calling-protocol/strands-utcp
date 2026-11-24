import { createHash } from 'node:crypto'
import { FunctionTool, type JSONSchema, type JSONValue } from '@strands-agents/sdk'
import type { JsonSchema, UtcpClient } from '@utcp/sdk'

function modelToolName(name: string): string {
  if (!name) throw new Error('UTCP tool names must be non-empty')
  const alias = name.replace(/[^A-Za-z0-9_-]/gu, '_')
  if (alias.length <= 64) return alias

  const suffix = createHash('sha256').update(name).digest('hex').slice(0, 8)
  return `${alias.slice(0, 55)}_${suffix}`
}

function objectSchema(inputs: JsonSchema, name: string): JSONSchema {
  const { type } = inputs
  if (type !== undefined && type !== 'object' && !(Array.isArray(type) && type.includes('object'))) {
    throw new TypeError(`UTCP tool "${name}" must accept an object as input`)
  }
  // Both SDKs use JSON Schema draft 7. UTCP types extension keywords as unknown.
  return { ...inputs, type: 'object' } as JSONSchema
}

/**
 * Convert the tools currently registered on a UTCP client into Strands tools.
 * Keep the client open for as long as the returned tools are in use.
 */
export async function toStrandsTools(client: Pick<UtcpClient, 'getTools' | 'callTool'>): Promise<FunctionTool[]> {
  const tools = await client.getTools()
  const names = new Map<string, string>()

  return tools.map(({ name, description, inputs }) => {
    const alias = modelToolName(name)
    // Strands treats hyphens and underscores as equivalent during registration.
    const key = alias.replaceAll('-', '_')
    const existing = names.get(key)
    if (existing !== undefined) {
      throw new Error(`UTCP tools "${existing}" and "${name}" have conflicting Strands tool names`)
    }
    names.set(key, name)

    return new FunctionTool({
      name: alias,
      description: description || `Call UTCP tool ${name}`,
      inputSchema: objectSchema(inputs, name),
      callback: async (input = {}) => {
        if (input === null || typeof input !== 'object' || Array.isArray(input)) {
          throw new TypeError(`Expected an object of arguments for UTCP tool "${name}"`)
        }
        const result: JSONValue = await client.callTool(name, input)
        // A payload such as { text: 'hello' } is UTCP data, even when its
        // shape matches a Strands content block. Mark structured data as JSON.
        if (Array.isArray(result)) return { json: { $value: result } }
        if (result !== null && typeof result === 'object') return { json: result }
        return result
      },
    })
  })
}
