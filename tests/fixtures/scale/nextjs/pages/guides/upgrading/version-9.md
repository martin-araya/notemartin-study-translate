[Pages Router](/docs/pages)
[Guides](/docs/pages/guides)
[Upgrading](/docs/pages/guides/upgrading)

# How to upgrade to version 9

To upgrade to version 9, run the following command:
Terminal
```text
npm i next@9
```
Terminal

```text
yarn add next@9
```
Terminal

```text
pnpm up next@9
```
Terminal

```text
bun add next@9
```

Good to know
If you are using TypeScript, ensure you also upgrade `@types/react` and `@types/react-dom` to their corresponding versions.
## [Check your Custom App File (`pages/_app.js`)](#check-your-custom-app-file-pages_appjs) <a id="check-your-custom-app-file-pages_appjs"></a>

If you previously copied the [Custom `<App>`](/docs/pages/building-your-application/routing/custom-app) example, you may be able to remove your `getInitialProps`.
Removing `getInitialProps` from `pages/_app.js` (when possible) is important to leverage new Next.js features!
The following `getInitialProps` does nothing and may be removed:
```text
class MyApp extends App {
  // Remove me, I do nothing!
  static async getInitialProps({ Component, ctx }) {
    let pageProps = {}

    if (Component.getInitialProps) {
      pageProps = await Component.getInitialProps(ctx)
    }

    return { pageProps }
  }

  render() {
    // ... etc
  }
}
```

## [Breaking Changes](#breaking-changes) <a id="breaking-changes"></a>

### [`@zeit/next-typescript` is no longer necessary](#zeitnext-typescript-is-no-longer-necessary) <a id="zeitnext-typescript-is-no-longer-necessary"></a>

Next.js will now ignore usage `@zeit/next-typescript` and warn you to remove it. Please remove this plugin from your `next.config.js`.
Remove references to `@zeit/next-typescript/babel` from your custom `.babelrc` (if present).
The usage of [`fork-ts-checker-webpack-plugin`](https://github.com/Realytics/fork-ts-checker-webpack-plugin/issues) should also be removed from your `next.config.js`.
TypeScript Definitions are published with the `next` package, so you need to uninstall `@types/next` as they would conflict.
The following types are different:
>
> This list was created by the community to help you upgrade, if you find other differences please send a pull-request to this list to help other users.

From:
```text
import { NextContext } from 'next'
import { NextAppContext, DefaultAppIProps } from 'next/app'
import { NextDocumentContext, DefaultDocumentIProps } from 'next/document'
```

to
```text
import { NextPageContext } from 'next'
import { AppContext, AppInitialProps } from 'next/app'
import { DocumentContext, DocumentInitialProps } from 'next/document'
```

### [The `config` key is now an export on a page](#the-config-key-is-now-an-export-on-a-page) <a id="the-config-key-is-now-an-export-on-a-page"></a>

You may no longer export a custom variable named `config` from a page (i.e. `` export { config } `` / `` export const config ... ``).
This exported variable is now used to specify page-level Next.js configuration like Opt-in AMP and API Route features.
You must rename a non-Next.js-purposed `config` export to something different.
### [`next/dynamic` no longer renders "loading..." by default while loading](#nextdynamic-no-longer-renders-loading-by-default-while-loading) <a id="nextdynamic-no-longer-renders-loading-by-default-while-loading"></a>

Dynamic components will not render anything by default while loading. You can still customize this behavior by setting the `loading` property:
```text
import dynamic from 'next/dynamic'

const DynamicComponentWithCustomLoading = dynamic(
  () => import('../components/hello2'),
  {
    loading: () => <p>Loading</p>,
  }
)
```

### [`withAmp` has been removed in favor of an exported configuration object](#withamp-has-been-removed-in-favor-of-an-exported-configuration-object) <a id="withamp-has-been-removed-in-favor-of-an-exported-configuration-object"></a>

Next.js now has the concept of page-level configuration, so the `withAmp` higher-order component has been removed for consistency.
This change can be **automatically migrated by running the following commands in the root of your Next.js project:**
Terminal
```text
curl -L https://github.com/vercel/next-codemod/archive/master.tar.gz | tar -xz --strip=2 next-codemod-master/transforms/withamp-to-config.js npx jscodeshift -t ./withamp-to-config.js pages/**/*.js
```

To perform this migration by hand, or view what the codemod will produce, see below:
**Before**
```text
import { withAmp } from 'next/amp'

function Home() {
  return <h1>My AMP Page</h1>
}

export default withAmp(Home)
// or
export default withAmp(Home, { hybrid: true })
```

**After**
```text
export default function Home() {
  return <h1>My AMP Page</h1>
}

export const config = {
  amp: true,
  // or
  amp: 'hybrid',
}
```

### [`` next export `` no longer exports pages as `index.html`](#next-export-no-longer-exports-pages-as-indexhtml) <a id="next-export-no-longer-exports-pages-as-indexhtml"></a>

Previously, exporting `pages/about.js` would result in `out/about/index.html`. This behavior has been changed to result in `out/about.html`.
You can revert to the previous behavior by creating a `next.config.js` with the following content:
next.config.js
```text
module.exports = {
  trailingSlash: true,
}
```

### [`pages/api/` is treated differently](#pagesapi-is-treated-differently) <a id="pagesapi-is-treated-differently"></a>

Pages in `pages/api/` are now considered [API Routes](/blog/next-9#api-routes).
Pages in this directory will no longer contain a client-side bundle.
## [Deprecated Features](#deprecated-features) <a id="deprecated-features"></a>

### [`next/dynamic` has deprecated loading multiple modules at once](#nextdynamic-has-deprecated-loading-multiple-modules-at-once) <a id="nextdynamic-has-deprecated-loading-multiple-modules-at-once"></a>

The ability to load multiple modules at once has been deprecated in `next/dynamic` to be closer to React's implementation (`React.lazy` and `Suspense`).
Updating code that relies on this behavior is relatively straightforward! We've provided an example of a before/after to help you migrate your application:
**Before**
```text
import dynamic from 'next/dynamic'

const HelloBundle = dynamic({
  modules: () => {
    const components = {
      Hello1: () => import('../components/hello1').then((m) => m.default),
      Hello2: () => import('../components/hello2').then((m) => m.default),
    }

    return components
  },
  render: (props, { Hello1, Hello2 }) => (
    <div>
      <h1>{props.title}</h1>
      <Hello1 />
      <Hello2 />
    </div>
  ),
})

function DynamicBundle() {
  return <HelloBundle title="Dynamic Bundle" />
}

export default DynamicBundle
```

**After**
```text
import dynamic from 'next/dynamic'

const Hello1 = dynamic(() => import('../components/hello1'))
const Hello2 = dynamic(() => import('../components/hello2'))

function HelloBundle({ title }) {
  return (
    <div>
      <h1>{title}</h1>
      <Hello1 />
      <Hello2 />
    </div>
  )
}

function DynamicBundle() {
  return <HelloBundle title="Dynamic Bundle" />
}

export default DynamicBundle
```

Last updated April 25, 2025
[PreviousVersion 16](/docs/pages/guides/upgrading/version-16)
[NextBuilding Your Application](/docs/pages/building-your-application)