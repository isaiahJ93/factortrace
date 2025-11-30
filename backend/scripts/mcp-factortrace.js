#!/usr/bin/env node

// Custom MCP server for FactorTrace-specific tools
// Provides: factor lookup, tenant check, validation preview.

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { execSync } = require('child_process');
const fs = require('fs');

const server = new Server(
  { name: 'factortrace-tools', version: '1.0.0' },
  { capabilities: { tools: {} } }
);

server.setRequestHandler('tools/call', async (request) => {
  const { name, arguments: args } = request.params || {};

  // Tool 1: Quick emission factor lookup
  if (name === 'lookup_factor') {
    const { scope, category, country, year } = args || {};

    const query = `
      SELECT factor, unit, dataset
      FROM emission_factors
      WHERE scope='${scope}'
        AND category='${category}'
        AND country_code='${country}'
        AND year=${year}
      LIMIT 1;
    `;

    const result = execSync(`sqlite3 factortrace.db "${query}"`).toString();

    return {
      content: [
        {
          type: 'text',
          text: result ? `Factor result:\n${result}` : 'No factor found for that query.',
        },
      ],
    };
  }

  // Tool 2: Tenant isolation check for a given file
  if (name === 'check_tenant_isolation') {
    const { filepath } = args || {};

    const content = fs.readFileSync(filepath, 'utf-8');
    const hasQuery = content.includes('db.query(');
    const hasTenantFilter = content.includes('tenant_id ==');

    if (hasQuery && !hasTenantFilter) {
      return {
        content: [
          {
            type: 'text',
            text: `⚠️ SECURITY RISK: ${filepath} has DB queries without tenant_id filter!`,
          },
        ],
      };
    }

    return {
      content: [
        { type: 'text', text: `✅ ${filepath} passes tenant isolation check.` },
      ],
    };
  }

  return {
    content: [
      {
        type: 'text',
        text: `Unknown tool: ${name}`,
      },
    ],
  };
});

const transport = new StdioServerTransport();
server.connect(transport);
