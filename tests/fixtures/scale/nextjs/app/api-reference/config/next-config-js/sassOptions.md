[App Router](/docs/app)
[API Reference](/docs/app/api-reference)
[Configuration](/docs/app/api-reference/config)
[next.config.js](/docs/app/api-reference/config/next-config-js)

# sassOptions

`sassOptions` allow you to configure the Sass compiler.
TypeScript
next.config.ts
```text
import type { NextConfig } from 'next'

const sassOptions = {
  additionalData: `
    $var: red;
  `,
}

const nextConfig: NextConfig = {
  sassOptions: {
    ...sassOptions,
    implementation: 'sass-embedded',
  },
}

export default nextConfig
```

Good to know
- `sassOptions` are not typed outside of `implementation` because Next.js does not maintain the other possible properties.
- The `functions` property for defining custom Sass functions is only supported with webpack. When using Turbopack, custom Sass functions are not available because Turbopack's Rust-based architecture cannot directly execute JavaScript functions passed through this option.

Last updated October 19, 2025
[Previousrewrites](/docs/app/api-reference/config/next-config-js/rewrites)
[NextserverActions](/docs/app/api-reference/config/next-config-js/serverActions)