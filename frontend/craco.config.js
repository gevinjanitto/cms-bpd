const path = require('path');

// Standard CRA/CRACO configuration. No platform-specific runtime or plugins.
module.exports = {
  webpack: { alias: { '@': path.resolve(__dirname, 'src') } },
  eslint: {
    configure: {
      extends: ['plugin:react-hooks/recommended'],
      rules: { 'react-hooks/rules-of-hooks': 'error', 'react-hooks/exhaustive-deps': 'warn' },
    },
  },
  devServer: config => {
    const { https, onAfterSetupMiddleware, onBeforeSetupMiddleware, onListening, setupMiddlewares, ...rest } = config;
    return {
      ...rest,
      server: https ? { type: 'https', options: typeof https === 'object' ? https : {} } : 'http',
      setupMiddlewares: (middlewares, server) => {
        if (onBeforeSetupMiddleware) onBeforeSetupMiddleware(server);
        return setupMiddlewares ? setupMiddlewares(middlewares, server) : middlewares;
      },
      onListening: server => {
        server.close ??= callback => server.stopCallback(callback);
        if (onListening) onListening(server);
        if (onAfterSetupMiddleware) onAfterSetupMiddleware(server);
      },
    };
  },
};