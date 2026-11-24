# UTCP tools for Strands Agents

`@utcp/strands` exposes the tools registered on a UTCP client to a Strands TypeScript agent. It requires Node.js 22 or later.

## Install from source

From this repository, build, test, and pack the adapter.

```sh
cd typescript
npm ci
npm test
npm pack
```

In your application, install the tarball using its local path. The example below uses the UTCP HTTP transport.

```sh
npm install /path/to/strands-utcp/typescript/utcp-strands-0.1.0.tgz @strands-agents/sdk@^1.26.0 @utcp/sdk@^1.2.0 @utcp/http@^1.1.14
```

## Use a UTCP manual

Set `UTCP_MANUAL_URL` to the HTTPS URL of a weather service's UTCP manual or OpenAPI document. Configure AWS credentials for the default Strands Bedrock model, or pass your own model to `Agent`.

```typescript
import { Agent } from '@strands-agents/sdk'
import { HttpCallTemplateSerializer } from '@utcp/http'
import { UtcpClient } from '@utcp/sdk'
import { toStrandsTools } from '@utcp/strands'

const url = process.env.UTCP_MANUAL_URL
if (!url) throw new Error('Set UTCP_MANUAL_URL to your weather service manual')

const client = await UtcpClient.create()
try {
  const manual = new HttpCallTemplateSerializer().validateDict({
    name: 'weather',
    call_template_type: 'http',
    http_method: 'GET',
    url,
  })
  const registration = await client.registerManual(manual)
  if (!registration.success) throw new Error(registration.errors.join('\n'))

  const agent = new Agent({ tools: await toStrandsTools(client) })
  const result = await agent.invoke('Use the weather service to get the forecast for Seattle.')
  console.log(result.lastMessage)
} finally {
  await client.close()
}
```

`toStrandsTools(client)` takes a snapshot of the client's registered tools. Calls go through the same client, so your application controls the transports, credentials, and manual registration. Keep the client open while the agent uses its tools. If you change the registered manuals, call `toStrandsTools(client)` again to get the updated list.

The agent sees `weather.forecast` as `weather_forecast`. The adapter shortens names over 64 characters with a stable hash suffix. If two names would conflict in the Strands registry, discovery reports both original names so you can rename a tool or manual.
