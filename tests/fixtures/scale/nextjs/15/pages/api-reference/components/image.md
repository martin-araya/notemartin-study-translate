[Pages Router](/docs/15/pages)
[API Reference](/docs/15/pages/api-reference)
[Components](/docs/15/pages/api-reference/components)

# Image

The Next.js Image component extends the HTML `<img>` element for automatic image optimization.
app/page.js
```text
import Image from 'next/image'

export default function Page() {
  return (
    <Image
      src="/profile.png"
      width={500}
      height={500}
      alt="Picture of the author"
    />
  )
}
```

Good to know
If you are using a version of Next.js prior to 13, you'll want to use the [next/legacy/image](/docs/pages/api-reference/components/image-legacy) documentation since the component was renamed.
## [Reference](#reference) <a id="reference"></a>

### [Props](#props) <a id="props"></a>

The following props are available:
```mermaid
block-beta
columns 4
  h_0["<b>Prop</b>"]
  h_1["<b>Example</b>"]
  h_2["<b>Type</b>"]
  h_3["<b>Status</b>"]
  c_0_0["`src`"]
  c_0_1["`src='/profile.png'`"]
  c_0_2["String"]
  c_0_3["Required"]
  c_1_0["`alt`"]
  c_1_1["`` alt='Picture of the author' ``"]
  c_1_2["String"]
  c_1_3["Required"]
  c_2_0["`width`"]
  c_2_1["`width=(500)`"]
  c_2_2["Integer (px)"]
  c_2_3["-"]
  c_3_0["`height`"]
  c_3_1["`height=(500)`"]
  c_3_2["Integer (px)"]
  c_3_3["-"]
  c_4_0["`fill`"]
  c_4_1["`fill=(true)`"]
  c_4_2["Boolean"]
  c_4_3["-"]
  c_5_0["`loader`"]
  c_5_1["`loader=(imageLoader)`"]
  c_5_2["Function"]
  c_5_3["-"]
  c_6_0["`sizes`"]
  c_6_1["`` sizes='(max-width: 768px) 100vw, 33vw' ``"]
  c_6_2["String"]
  c_6_3["-"]
  c_7_0["`quality`"]
  c_7_1["`quality=(80)`"]
  c_7_2["Integer (1-100)"]
  c_7_3["-"]
  c_8_0["`priority`"]
  c_8_1["`priority=(true)`"]
  c_8_2["Boolean"]
  c_8_3["-"]
  c_9_0["`placeholder`"]
  c_9_1["`placeholder='blur'`"]
  c_9_2["String"]
  c_9_3["-"]
  c_10_0["`style`"]
  c_10_1["`` style=((objectFit: 'contain')) ``"]
  c_10_2["Object"]
  c_10_3["-"]
  c_11_0["`onLoadingComplete`"]
  c_11_1["`` onLoadingComplete=(img => done())) ``"]
  c_11_2["Function"]
  c_11_3["Deprecated"]
  c_12_0["`onLoad`"]
  c_12_1["`` onLoad=(event => done())) ``"]
  c_12_2["Function"]
  c_12_3["-"]
  c_13_0["`onError`"]
  c_13_1["`` onError(event => fail()) ``"]
  c_13_2["Function"]
  c_13_3["-"]
  c_14_0["`loading`"]
  c_14_1["`loading='lazy'`"]
  c_14_2["String"]
  c_14_3["-"]
  c_15_0["`blurDataURL`"]
  c_15_1["`blurDataURL='data:image/jpeg...'`"]
  c_15_2["String"]
  c_15_3["-"]
  c_16_0["`overrideSrc`"]
  c_16_1["`overrideSrc='/seo.png'`"]
  c_16_2["String"]
  c_16_3["-"]
```

| Prop | Example | Type | Status |
|---|---|---|---|
| [`src`](#src) | `src="/profile.png"` | String | Required |
| [`alt`](#alt) | `` alt="Picture of the author" `` | String | Required |
| [`width`](#width-and-height) | `width={500}` | Integer (px) | - |
| [`height`](#width-and-height) | `height={500}` | Integer (px) | - |
| [`fill`](#fill) | `fill={true}` | Boolean | - |
| [`loader`](#loader) | `loader={imageLoader}` | Function | - |
| [`sizes`](#sizes) | `` sizes="(max-width: 768px) 100vw, 33vw" `` | String | - |
| [`quality`](#quality) | `quality={80}` | Integer (1-100) | - |
| [`priority`](#priority) | `priority={true}` | Boolean | - |
| [`placeholder`](#placeholder) | `placeholder="blur"` | String | - |
| [`style`](#style) | `` style={{objectFit: "contain"}} `` | Object | - |
| [`onLoadingComplete`](#onloadingcomplete) | `` onLoadingComplete={img => done())} `` | Function | Deprecated |
| [`onLoad`](#onload) | `` onLoad={event => done())} `` | Function | - |
| [`onError`](#onerror) | `` onError(event => fail()} `` | Function | - |
| [`loading`](#loading) | `loading="lazy"` | String | - |
| [`blurDataURL`](#blurdataurl) | `blurDataURL="data:image/jpeg..."` | String | - |
| [`overrideSrc`](#overridesrc) | `overrideSrc="/seo.png"` | String | - |


#### [`src`](#src) <a id="src"></a>

The source of the image. Can be one of the following:
An internal path string.
```text
<Image src="/profile.png" />
```

An absolute external URL (must be configured with [remotePatterns](#remotepatterns)).
```text
<Image src="https://example.com/profile.png" />
```

A static import.
```text
import profile from './profile.png'

export default function Page() {
  return <Image src={profile} />
}
```

Good to know
For security reasons, the Image Optimization API using the default [loader](#loader) will *not* forward headers when fetching the `src` image.
If the `src` image requires authentication, consider using the [unoptimized](#unoptimized) property to disable Image Optimization.
#### [`alt`](#alt) <a id="alt"></a>

The `alt` property is used to describe the image for screen readers and search engines. It is also the fallback text if images have been disabled or an error occurs while loading the image.
It should contain text that could replace the image [without changing the meaning of the page](https://html.spec.whatwg.org/multipage/images.html#general-guidelines). It is not meant to supplement the image and should not repeat information that is already provided in the captions above or below the image.
If the image is [purely decorative](https://html.spec.whatwg.org/multipage/images.html#a-purely-decorative-image-that-doesn't-add-any-information) or [not intended for the user](https://html.spec.whatwg.org/multipage/images.html#an-image-not-intended-for-the-user), the `alt` property should be an empty string (`alt=""`).
>
> Learn more about [image accessibility guidelines](https://html.spec.whatwg.org/multipage/images.html#alt).

#### [`width` and `height`](#width-and-height) <a id="width-and-height"></a>

The `width` and `height` properties represent the [intrinsic](https://developer.mozilla.org/en-US/docs/Glossary/Intrinsic_Size) image size in pixels. This property is used to infer the correct **aspect ratio** used by browsers to reserve space for the image and avoid layout shift during loading. It does not determine the *rendered size* of the image, which is controlled by CSS.
```text
<Image src="/profile.png" width={500} height={500} />
```

You **must** set both `width` and `height` properties unless:
- The image is statically imported.
- The image has the [`fill` property](#fill)

If the height and width are unknown, we recommend using the [`fill` property](#fill).
#### [`fill`](#fill) <a id="fill"></a>

A boolean that causes the image to expand to the size of the parent element.
```text
<Image src="/profile.png" fill={true} />
```

**Positioning**:
- The parent element **must** assign `` position: "relative" ``, `"fixed"`, `"absolute"`.
- By default, the `<img>` element uses `` position: "absolute" ``.

**Object Fit**:
If no styles are applied to the image, the image will stretch to fit the container. You can use `objectFit` to control cropping and scaling.
- `"contain"`: The image will be scaled down to fit the container and preserve aspect ratio.
- `"cover"`: The image will fill the container and be cropped.

>
> Learn more about [`position`](https://developer.mozilla.org/en-US/docs/Web/CSS/position) and [`object-fit`](https://developer.mozilla.org/docs/Web/CSS/object-fit).

#### [`loader`](#loader) <a id="loader"></a>

A custom function used to generate the image URL. The function receives the following parameters, and returns a URL string for the image:
- [`src`](#src)
- [`width`](#width-and-height)
- [`quality`](#quality)

```text
import Image from 'next/image'

const imageLoader = ({ src, width, quality }) => {
  return `https://example.com/${src}?w=${width}&q=${quality || 75}`
}

export default function Page() {
  return (
    <Image
      loader={imageLoader}
      src="me.png"
      alt="Picture of the author"
      width={500}
      height={500}
    />
  )
}
```

Alternatively, you can use the [loaderFile](#loaderfile) configuration in `next.config.js` to configure every instance of `next/image` in your application, without passing a prop.
#### [`sizes`](#sizes) <a id="sizes"></a>

Define the sizes of the image at different breakpoints. Used by the browser to choose the most appropriate size from the generated `srcset`.
```text
import Image from 'next/image'

export default function Page() {
  return (
    <div className="grid-element">
      <Image
        fill
        src="/example.png"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      />
    </div>
  )
}
```

`sizes` should be used when:
- The image is using the [`fill`](#fill) prop
- CSS is used to make the image responsive

If `sizes` is missing, the browser assumes the image will be as wide as the viewport (`100vw`). This can cause unnecessarily large images to be downloaded.
In addition, `sizes` affects how `srcset` is generated:
- Without `sizes`: Next.js generates a limited `srcset` (e.g. 1x, 2x), suitable for fixed-size images.
- With `sizes`: Next.js generates a full `srcset` (e.g. 640w, 750w, etc.), optimized for responsive layouts.

>
> Learn more about `srcset` and `sizes` on [web.dev](https://web.dev/learn/design/responsive-images/#sizes) and [mdn](https://developer.mozilla.org/docs/Web/HTML/Element/img#sizes).

#### [`quality`](#quality) <a id="quality"></a>

An integer between `1` and `100` that sets the quality of the optimized image. Higher values increase file size and visual fidelity. Lower values reduce file size but may affect sharpness.
```text
// Default quality is 75
<Image quality={75} />
```

If you’ve configured [qualities](#qualities) in `next.config.js`, the value must match one of the allowed entries.
Good to know
If the original image is already low quality, setting a high quality value will increase the file size without improving appearance.
#### [`style`](#style) <a id="style"></a>

Allows passing CSS styles to the underlying image element.
```text
const imageStyle = {
  borderRadius: '50%',
  border: '1px solid #fff',
  width: '100px',
  height: 'auto',
}

export default function ProfileImage() {
  return <Image src="..." style={imageStyle} />
}
```

Good to know
If you’re using the `style` prop to set a custom width, be sure to also set `` height: 'auto' `` to preserve the image’s aspect ratio.
#### [`priority`](#priority) <a id="priority"></a>

A boolean that indicates if the image should be preloaded.
```text
// Default priority is false
<Image priority={false} />
```

- `true`: [Preloads](https://web.dev/preload-responsive-images/) the image. Disables lazy loading.
- `false`: Lazy loads the image.

**When to use it:**
- The image is above the fold.
- The image is the [Largest Contentful Paint (LCP)](/learn/seo/web-performance/lcp) element.
- You want to improve the initial loading performance of your page.

**When not to use it:**
- When the `loading` prop isused (will trigger warnings).

#### [`loading`](#loading) <a id="loading"></a>

Controls when the image should start loading.
```text
// Defaults to lazy
<Image loading="lazy" />
```

- `lazy`: Defer loading the image until it reaches a calculated distance from the viewport.
- `eager`: Load the image immediately, regardless of its position in the page.

Use `eager` only when you want to ensure the image is loaded immediately.
>
> Learn more about the [`loading` attribute](https://developer.mozilla.org/docs/Web/HTML/Element/img#loading).

#### [`placeholder`](#placeholder) <a id="placeholder"></a>

Specifies a placeholder to use while the image is loading, improving the perceived loading performance.
```text
// defaults to empty
<Image placeholder="empty" />
```

- `empty`: No placeholder while the image is loading.
- `blur`: Use a blurred version of the image as a placeholder. Must be used with the [`blurDataURL`](#blurdataurl) property.
- `data:image/...`: Uses the [Data URL](https://developer.mozilla.org/docs/Web/HTTP/Basics_of_HTTP/Data_URIs) as the placeholder.

**Examples:**
- [`blur` placeholder](https://image-component.nextjs.gallery/placeholder)
- [Shimmer effect with data URL `placeholder` prop](https://image-component.nextjs.gallery/shimmer)
- [Color effect with `blurDataURL` prop](https://image-component.nextjs.gallery/color)

>
> Learn more about the [`placeholder` attribute](https://developer.mozilla.org/docs/Web/HTML/Element/img#placeholder).

#### [`blurDataURL`](#blurdataurl) <a id="blurdataurl"></a>

A [Data URL](https://developer.mozilla.org/docs/Web/HTTP/Basics_of_HTTP/Data_URIs) to
be used as a placeholder image before the image successfully loads. Can be automatically set or used with the [`placeholder="blur"`](#placeholder) property.
```text
<Image placeholder="blur" blurDataURL="..." />
```

The image is automatically enlarged and blurred, so a very small image (10px or less) is recommended.
**Automatic**
If `src` is a static import of a `jpg`, `png`, `webp`, or `avif` file, `blurDataURL` is added automatically—unless the image is animated.
**Manually set**
If the image is dynamic or remote, you must provide `blurDataURL` yourself. To generate one, you can use:
- [A online tool like png-pixel.com](https://png-pixel.com)
- [A library like Plaiceholder](https://github.com/joe-bell/plaiceholder)

A large blurDataURL may hurt performance. Keep it small and simple.
**Examples:**
- [Default `blurDataURL` prop](https://image-component.nextjs.gallery/placeholder)
- [Color effect with `blurDataURL` prop](https://image-component.nextjs.gallery/color)

#### [`onLoad`](#onload) <a id="onload"></a>

A callback function that is invoked once the image is completely loaded and the [placeholder](#placeholder) has been removed.
```text
<Image onLoad={(e) => console.log(e.target.naturalWidth)} />
```

The callback function will be called with one argument, the event which has a `target` that references the underlying `<img>` element.
#### [`onError`](#onerror) <a id="onerror"></a>

A callback function that is invoked if the image fails to load.
```text
<Image onError={(e) => console.error(e.target.id)} />
```

#### [`unoptimized`](#unoptimized) <a id="unoptimized"></a>

A boolean that indicates if the image should be optimized. This is useful for images that do not benefit from optimization such as small images (less than 1KB), vector images (SVG), or animated images (GIF).
```text
import Image from 'next/image'

const UnoptimizedImage = (props) => {
  // Default is false
  return <Image {...props} unoptimized />
}
```

- `true`: The source image will be served as-is from the `src` instead of changing quality, size, or format.
- `false`: The source image will be optimized.

Since Next.js 12.3.0, this prop can be assigned to all images by updating `next.config.js` with the following configuration:
next.config.js
```text
module.exports = {
  images: {
    unoptimized: true,
  },
}
```

#### [`overrideSrc`](#overridesrc) <a id="overridesrc"></a>

When providing the `src` prop to the `<Image>` component, both the `srcset` and `src` attributes are generated automatically for the resulting `<img>`.
input.js
```text
<Image src="/profile.jpg" />
```
output.html

```text
<img
  srcset="
    /_next/image?url=%2Fprofile.jpg&w=640&q=75 1x,
    /_next/image?url=%2Fprofile.jpg&w=828&q=75 2x
  "
  src="/_next/image?url=%2Fprofile.jpg&w=828&q=75"
/>
```

In some cases, it is not desirable to have the `src` attribute generated and you may wish to override it using the `overrideSrc` prop.
For example, when upgrading an existing website from `<img>` to `<Image>`, you may wish to maintain the same `src` attribute for SEO purposes such as image ranking or avoiding recrawl.
input.js
```text
<Image src="/profile.jpg" overrideSrc="/override.jpg" />
```
output.html

```text
<img
  srcset="
    /_next/image?url=%2Fprofile.jpg&w=640&q=75 1x,
    /_next/image?url=%2Fprofile.jpg&w=828&q=75 2x
  "
  src="/override.jpg"
/>
```

#### [`decoding`](#decoding) <a id="decoding"></a>

A hint to the browser indicating if it should wait for the image to be decoded before presenting other content updates or not.
```text
// Default is async
<Image decoding="async" />
```

- `async`: Asynchronously decode the image and allow other content to be rendered before it completes.
- `sync`: Synchronously decode the image for atomic presentation with other content.
- `auto`: No preference. The browser chooses the best approach.

>
> Learn more about the [`decoding` attribute](https://developer.mozilla.org/docs/Web/HTML/Element/img#decoding).

### [Other Props](#other-props) <a id="other-props"></a>

Other properties on the `` <Image /> `` component will be passed to the underlying `img` element with the exception of the following:
- `srcSet`: Use [Device Sizes](#devicesizes) instead.

### [Deprecated props](#deprecated-props) <a id="deprecated-props"></a>

#### [`onLoadingComplete`](#onloadingcomplete) <a id="onloadingcomplete"></a>

Warning
Deprecated in Next.js 14, use [`onLoad`](#onload) instead.
A callback function that is invoked once the image is completely loaded and the [placeholder](#placeholder) has been removed.
The callback function will be called with one argument, a reference to the underlying `<img>` element.
```text
<Image onLoadingComplete={(img) => console.log(img.naturalWidth)} />
```

### [Configuration options](#configuration-options) <a id="configuration-options"></a>

You can configure the Image Component in `next.config.js`. The following options are available:
#### [`localPatterns`](#localpatterns) <a id="localpatterns"></a>

Use `localPatterns` in your `next.config.js` file to allow images from specific local paths to be optimized and block all others.
next.config.js
```text
module.exports = {
  images: {
    localPatterns: [
      {
        pathname: '/assets/images/**',
        search: '',
      },
    ],
  },
}
```

The example above will ensure the `src` property of `next/image` must start with `/assets/images/` and must not have a query string. Attempting to optimize any other path will respond with `400` Bad Request error.
#### [`remotePatterns`](#remotepatterns) <a id="remotepatterns"></a>

Use `remotePatterns` in your `next.config.js` file to allow images from specific external paths and block all others. This ensures that only external images from your account can be served.
next.config.js
```text
module.exports = {
  images: {
    remotePatterns: [new URL('https://example.com/account123/**')],
  },
}
```

You can also configure `remotePatterns` using the object:
next.config.js
```text
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'example.com',
        port: '',
        pathname: '/account123/**',
        search: '',
      },
    ],
  },
}
```

The example above will ensure the `src` property of `next/image` must start with `https://example.com/account123/` and must not have a query string. Any other protocol, hostname, port, or unmatched path will respond with `400` Bad Request.
**Wildcard Patterns:**
Wildcard patterns can be used for both `pathname` and `hostname` and have the following syntax:
- `*` match a single path segment or subdomain
- `**` match any number of path segments at the end or subdomains at the beginning. This syntax does not work in the middle of the pattern.
next.config.js

```text
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.example.com',
        port: '',
        search: '',
      },
    ],
  },
}
```

This allows subdomains like `image.example.com`. Query strings and custom ports are still blocked.
Good to know
When omitting `protocol`, `port`, `pathname`, or `search` then the wildcard `**` is implied. This is not recommended because it may allow malicious actors to optimize urls you did not intend.
**Query Strings**:
You can also restrict query strings using the `search` property:
next.config.js
```text
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'assets.example.com',
        search: '?v=1727111025337',
      },
    ],
  },
}
```

The example above will ensure the `src` property of `next/image` must start with `https://assets.example.com` and must have the exact query string `?v=1727111025337`. Any other protocol or query string will respond with `400` Bad Request.
#### [`loaderFile`](#loaderfile) <a id="loaderfile"></a>

`loaderFiles` allows you to use a custom image optimization service instead of Next.js.
next.config.js
```text
module.exports = {
  images: {
    loader: 'custom',
    loaderFile: './my/image/loader.js',
  },
}
```

The path must be relative to the project root. The file must export a default function that returns a URL string:
my/image/loader.js
```text
export default function myImageLoader({ src, width, quality }) {
  return `https://example.com/${src}?w=${width}&q=${quality || 75}`
}
```

**Example:**
- [Custom Image Loader Configuration](/docs/app/api-reference/config/next-config-js/images#example-loader-configuration)

>
> Alternatively, you can use the [`loader` prop](#loader) to configure each instance of `next/image`.

#### [`path`](#path) <a id="path"></a>

If you want to change or prefix the default path for the Image Optimization API, you can do so with the `path` property. The default value for `path` is `/_next/image`.
next.config.js
```text
module.exports = {
  images: {
    path: '/my-prefix/_next/image',
  },
}
```

#### [`deviceSizes`](#devicesizes) <a id="devicesizes"></a>

`deviceSizes` allows you to specify a list of device width breakpoints. These widths are used when the `next/image` component uses [`sizes`](#sizes) prop to ensure the correct image is served for the user's device.
If no configuration is provided, the default below is used:
next.config.js
```text
module.exports = {
  images: {
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
  },
}
```

#### [`imageSizes`](#imagesizes) <a id="imagesizes"></a>

`imageSizes` allows you to specify a list of image widths. These widths are concatenated with the array of [device sizes](#devicesizes) to form the full array of sizes used to generate image [srcset](https://developer.mozilla.org/docs/Web/API/HTMLImageElement/srcset).
If no configuration is provided, the default below is used:
next.config.js
```text
module.exports = {
  images: {
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
}
```

`imageSizes` is only used for images which provide a [`sizes`](#sizes) prop, which indicates that the image is less than the full width of the screen. Therefore, the sizes in `imageSizes` should all be smaller than the smallest size in `deviceSizes`.
#### [`qualities`](#qualities) <a id="qualities"></a>

`qualities` allows you to specify a list of image quality values.
next.config.js
```text
module.exports = {
  images: {
    qualities: [25, 50, 75],
  },
}
```

In the example above, only three qualities are allowed: 25, 50, and 75. If the [`quality`](#quality) prop does not match a value in this array, the image will fail with a `400` Bad Request.
#### [`formats`](#formats) <a id="formats"></a>

`formats` allows you to specify a list of image formats to be used.
next.config.js
```text
module.exports = {
  images: {
    // Default
    formats: ['image/webp'],
  },
}
```

Next.js automatically detects the browser's supported image formats via the request's `Accept` header in order to determine the best output format.
If the `Accept` header matches more than one of the configured formats, the first match in the array is used. Therefore, the array order matters. If there is no match (or the source image is animated), it will use the original image's format.
You can enable AVIF support, which will fallback to the original format of the src image if the browser [does not support AVIF](https://caniuse.com/avif):
next.config.js
```text
module.exports = {
  images: {
    formats: ['image/avif'],
  },
}
```

Good to know
- We still recommend using WebP for most use cases.
- AVIF generally takes 50% longer to encode but it compresses 20% smaller compared to WebP. This means that the first time an image is requested, it will typically be slower, but subsequent requests that are cached will be faster.
- If you self-host with a Proxy/CDN in front of Next.js, you must configure the Proxy to forward the `Accept` header.

#### [`minimumCacheTTL`](#minimumcachettl) <a id="minimumcachettl"></a>

`minimumCacheTTL` allows you to configure the Time to Live (TTL) in seconds for cached optimized images. In many cases, it's better to use a [Static Image Import](/docs/app/getting-started/images#local-images) which will automatically hash the file contents and cache the image forever with a `Cache-Control` header of `immutable`.
If no configuration is provided, the default below is used.
next.config.js
```text
module.exports = {
  images: {
    minimumCacheTTL: 60, // 1 minute
  },
}
```

You can increase the TTL to reduce the number of revalidations and potentially lower cost:
next.config.js
```text
module.exports = {
  images: {
    minimumCacheTTL: 2678400, // 31 days
  },
}
```

The expiration (or rather Max Age) of the optimized image is defined by either the `minimumCacheTTL` or the upstream image `Cache-Control` header, whichever is larger.
If you need to change the caching behavior per image, you can configure [`headers`](/docs/app/api-reference/config/next-config-js/headers) to set the `Cache-Control` header on the upstream image (e.g. `/some-asset.jpg`, not `/_next/image` itself).
There is no mechanism to invalidate the cache at this time, so its best to keep `minimumCacheTTL` low. Otherwise you may need to manually change the [`src`](#src) prop or delete the cached file `<distDir>/cache/images`.
#### [`disableStaticImages`](#disablestaticimages) <a id="disablestaticimages"></a>

`disableStaticImages` allows you to disable static image imports.
The default behavior allows you to import static files such as `` import icon from './icon.png' `` and then pass that to the `src` property. In some cases, you may wish to disable this feature if it conflicts with other plugins that expect the import to behave differently.
You can disable static image imports inside your `next.config.js`:
next.config.js
```text
module.exports = {
  images: {
    disableStaticImages: true,
  },
}
```

#### [`maximumDiskCacheSize`](#maximumdiskcachesize) <a id="maximumdiskcachesize"></a>

The default image optimization loader will write optimized images to disk so subsequent requests can be served faster from the disk cache.
You can configure the maximum disk cache size in bytes, for example 500 MB:
next.config.js
```text
module.exports = {
  images: {
    maximumDiskCacheSize: 500_000_000,
  },
}
```

You can also disable the disk cache entirely by setting the value to `0`.
next.config.js
```text
module.exports = {
  images: {
    maximumDiskCacheSize: 0,
  },
}
```

If no value is configured, the default behavior is to check the current available disk space once during startup and use 50%.
When the disk cache exceeds the configured size, the least recently used optimized images will be deleted until the cache is under the limit again.
Alternatively, you can implement your own cache handler using [`cacheHandler`](/docs/app/api-reference/config/next-config-js/incrementalCacheHandlerPath) which will ignore the `maximumDiskCacheSize` configuration.
#### [`maximumResponseBody`](#maximumresponsebody) <a id="maximumresponsebody"></a>

The default image optimization loader will fetch source images up to 50 MB in size.
next.config.js
```text
module.exports = {
  images: {
    maximumResponseBody: 50_000_000,
  },
}
```

If you know all your source images are small, you can protect memory constrained servers by reducing this to a smaller value such as 5 MB.
next.config.js
```text
module.exports = {
  images: {
    maximumResponseBody: 5_000_000,
  },
}
```

#### [`dangerouslyAllowSVG`](#dangerouslyallowsvg) <a id="dangerouslyallowsvg"></a>

`dangerouslyAllowSVG` allows you to serve SVG images.
next.config.js
```text
module.exports = {
  images: {
    dangerouslyAllowSVG: true,
  },
}
```

By default, Next.js does not optimize SVG images for a few reasons:
- SVG is a vector format meaning it can be resized losslessly.
- SVG has many of the same features as HTML/CSS, which can lead to vulnerabilities without proper [Content Security Policy (CSP) headers](/docs/app/api-reference/config/next-config-js/headers#content-security-policy).

We recommend using the [`unoptimized`](#unoptimized) prop when the [`src`](#src) prop is known to be SVG. This happens automatically when `src` ends with `".svg"`.
```text
<Image src="/my-image.svg" unoptimized />
```

In addition, it is strongly recommended to also set `contentDispositionType` to force the browser to download the image, as well as `contentSecurityPolicy` to prevent scripts embedded in the image from executing.
next.config.js
```text
module.exports = {
  images: {
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
}
```

#### [`contentDispositionType`](#contentdispositiontype) <a id="contentdispositiontype"></a>

`contentDispositionType` allows you to configure the [`Content-Disposition`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition#as_a_response_header_for_the_main_body) header.
next.config.js
```text
module.exports = {
  images: {
    contentDispositionType: 'inline',
  },
}
```

#### [`contentSecurityPolicy`](#contentsecuritypolicy) <a id="contentsecuritypolicy"></a>

`contentSecurityPolicy` allows you to configure the [`Content-Security-Policy`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CSP) header for images. This is particularly important when using [`dangerouslyAllowSVG`](#dangerouslyallowsvg) to prevent scripts embedded in the image from executing.
next.config.js
```text
module.exports = {
  images: {
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
  },
}
```

By default, the [loader](#loader) sets the [`Content-Disposition`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition#as_a_response_header_for_the_main_body) header to `attachment` for added protection since the API can serve arbitrary remote images.
The default value is `attachment` which forces the browser to download the image when visiting directly. This is particularly important when [`dangerouslyAllowSVG`](#dangerouslyallowsvg) is true.
You can optionally configure `inline` to allow the browser to render the image when visiting directly, without downloading it.
### [Deprecated configuration options](#deprecated-configuration-options) <a id="deprecated-configuration-options"></a>

#### [`domains`](#domains) <a id="domains"></a>

Warning
Deprecated since Next.js 14 in favor of strict [`remotePatterns`](#remotepatterns) in order to protect your application from malicious users. Only use `domains` if you own all the content served from the domain.
Similar to [`remotePatterns`](#remotepatterns), the `domains` configuration can be used to provide a list of allowed hostnames for external images. However, the `domains` configuration does not support wildcard pattern matching and it cannot restrict protocol, port, or pathname.
Below is an example of the `domains` property in the `next.config.js` file:
next.config.js
```text
module.exports = {
  images: {
    domains: ['assets.acme.com'],
  },
}
```

## [Functions](#functions) <a id="functions"></a>

### [`getImageProps`](#getimageprops) <a id="getimageprops"></a>

The `getImageProps` function can be used to get the props that would be passed to the underlying `<img>` element, and instead pass them to another component, style, canvas, etc.
```text
import { getImageProps } from 'next/image'

const { props } = getImageProps({
  src: 'https://example.com/image.jpg',
  alt: 'A scenic mountain view',
  width: 1200,
  height: 800,
})

function ImageWithCaption() {
  return (
    <figure>
      <img {...props} />
      <figcaption>A scenic mountain view</figcaption>
    </figure>
  )
}
```

This also avoid calling React `useState()` so it can lead to better performance, but it cannot be used with the [`placeholder`](#placeholder) prop because the placeholder will never be removed.
## [Known browser bugs](#known-browser-bugs) <a id="known-browser-bugs"></a>

This `next/image` component uses browser native [lazy loading](https://caniuse.com/loading-lazy-attr), which may fallback to eager loading for older browsers before Safari 15.4. When using the blur-up placeholder, older browsers before Safari 12 will fallback to empty placeholder. When using styles with `width`/`height` of `auto`, it is possible to cause [Layout Shift](https://web.dev/cls/) on older browsers before Safari 15 that don't [preserve the aspect ratio](https://caniuse.com/mdn-html_elements_img_aspect_ratio_computed_from_attributes). For more details, see [this MDN video](https://www.youtube.com/watch?v=4-d_SoCHeWE).
- [Safari 15 - 16.3](https://bugs.webkit.org/show_bug.cgi?id=243601) display a gray border while loading. Safari 16.4 [fixed this issue](https://webkit.org/blog/13966/webkit-features-in-safari-16-4/#:~:text=Now%20in%20Safari%2016.4%2C%20a%20gray%20line%20no%20longer%20appears%20to%20mark%20the%20space%20where%20a%20lazy%2Dloaded%20image%20will%20appear%20once%20it%E2%80%99s%20been%20loaded.). Possible solutions:

  - Use CSS `` @supports (font: -apple-system-body) and (-webkit-appearance: none) { img[loading="lazy"] { clip-path: inset(0.6px) } } ``
  - Use [`priority`](#priority) if the image is above the fold
- [Firefox 67+](https://bugzilla.mozilla.org/show_bug.cgi?id=1556156) displays a white background while loading. Possible solutions:

  - Enable [AVIF `formats`](#formats)
  - Use [`placeholder`](#placeholder)

## [Examples](#examples) <a id="examples"></a>

### [Styling images](#styling-images) <a id="styling-images"></a>

Styling the Image component is similar to styling a normal `<img>` element, but there are a few guidelines to keep in mind:
Use `className` or `style`, not `styled-jsx`. In most cases, we recommend using the `className` prop. This can be an imported [CSS Module](/docs/app/getting-started/css), a [global stylesheet](/docs/app/getting-started/css#global-css), etc.
```text
import styles from './styles.module.css'

export default function MyImage() {
  return <Image className={styles.image} src="/my-image.png" alt="My Image" />
}
```

You can also use the `style` prop to assign inline styles.
```text
export default function MyImage() {
  return (
    <Image style={{ borderRadius: '8px' }} src="/my-image.png" alt="My Image" />
  )
}
```

When using `fill`, the parent element must have `` position: relative `` or `` display: block ``. This is necessary for the proper rendering of the image element in that layout mode.
```text
<div style={{ position: 'relative' }}>
  <Image fill src="/my-image.png" alt="My Image" />
</div>
```

You cannot use [styled-jsx](/docs/app/guides/css-in-js) because it's scoped to the current component (unless you mark the style as `global`).
### [Responsive images with a static export](#responsive-images-with-a-static-export) <a id="responsive-images-with-a-static-export"></a>

When you import a static image, Next.js automatically sets its width and height based on the file. You can make the image responsive by setting the style:
![Responsive image filling the width and height of its parent container](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Flight%2Fresponsive-image.png&w=3840&q=75)
![Responsive image filling the width and height of its parent container](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Fresponsive-image.png&w=3840&q=75)

```text
import Image from 'next/image'
import mountains from '../public/mountains.jpg'

export default function Responsive() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      <Image
        alt="Mountains"
        // Importing an image will
        // automatically set the width and height
        src={mountains}
        sizes="100vw"
        // Make the image display full width
        // and preserve its aspect ratio
        style={{
          width: '100%',
          height: 'auto',
        }}
      />
    </div>
  )
}
```

### [Responsive images with a remote URL](#responsive-images-with-a-remote-url) <a id="responsive-images-with-a-remote-url"></a>

If the source image is a dynamic or a remote URL, you must provide the width and height props so Next.js can calculate the aspect ratio:
components/page.js
```text
import Image from 'next/image'

export default function Page({ photoUrl }) {
  return (
    <Image
      src={photoUrl}
      alt="Picture of the author"
      sizes="100vw"
      style={{
        width: '100%',
        height: 'auto',
      }}
      width={500}
      height={300}
    />
  )
}
```

Try it out:
- [Demo the image responsive to viewport](https://image-component.nextjs.gallery/responsive)

### [Responsive image with `fill`](#responsive-image-with-fill) <a id="responsive-image-with-fill"></a>

If you don't know the aspect ratio of the image, you can add the [`fill` prop](#fill) with the `objectFit` prop set to `cover`. This will make the image fill the full width of its parent container.
![Grid of images filling parent container width](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Flight%2Ffill-container.png&w=3840&q=75)
![Grid of images filling parent container width](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Ffill-container.png&w=3840&q=75)

```text
import Image from 'next/image'
import mountains from '../public/mountains.jpg'

export default function Fill() {
  return (
    <div
      style={{
        display: 'grid',
        gridGap: '8px',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, auto))',
      }}
    >
      <div style={{ position: 'relative', width: '400px' }}>
        <Image
          alt="Mountains"
          src={mountains}
          fill
          sizes="(min-width: 808px) 50vw, 100vw"
          style={{
            objectFit: 'cover', // cover, contain, none
          }}
        />
      </div>
      {/* And more images in the grid... */}
    </div>
  )
}
```

### [Background Image](#background-image) <a id="background-image"></a>

Use the `fill` prop to make the image cover the entire screen area:
![Background image taking full width and height of page](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Flight%2Fbackground-image.png&w=3840&q=75)
![Background image taking full width and height of page](/_next/image?url=https%3A%2F%2Fh8DxKfmAPhn8O0p3.public.blob.vercel-storage.com%2Fdocs%2Fdark%2Fbackground-image.png&w=3840&q=75)

```text
import Image from 'next/image'
import mountains from '../public/mountains.jpg'

export default function Background() {
  return (
    <Image
      alt="Mountains"
      src={mountains}
      placeholder="blur"
      quality={100}
      fill
      sizes="100vw"
      style={{
        objectFit: 'cover',
      }}
    />
  )
}
```

For examples of the Image component used with the various styles, see the [Image Component Demo](https://image-component.nextjs.gallery).
### [Remote images](#remote-images) <a id="remote-images"></a>

To use a remote image, the `src` property should be a URL string.
app/page.js
```text
import Image from 'next/image'

export default function Page() {
  return (
    <Image
      src="https://s3.amazonaws.com/my-bucket/profile.png"
      alt="Picture of the author"
      width={500}
      height={500}
    />
  )
}
```

Since Next.js does not have access to remote files during the build process, you'll need to provide the [`width`](/docs/app/api-reference/components/image#width-and-height), [`height`](/docs/app/api-reference/components/image#width-and-height) and optional [`blurDataURL`](/docs/app/api-reference/components/image#blurdataurl) props manually.
The `width` and `height` attributes are used to infer the correct aspect ratio of image and avoid layout shift from the image loading in. The `width` and `height` do *not* determine the rendered size of the image file.
To safely allow optimizing images, define a list of supported URL patterns in `next.config.js`. Be as specific as possible to prevent malicious usage. For example, the following configuration will only allow images from a specific AWS S3 bucket:
next.config.js
```text
module.exports = {
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 's3.amazonaws.com',
        port: '',
        pathname: '/my-bucket/**',
        search: '',
      },
    ],
  },
}
```

### [Theme detection](#theme-detection) <a id="theme-detection"></a>

If you want to display a different image for light and dark mode, you can create a new component that wraps two `<Image>` components and reveals the correct one based on a CSS media query.
components/theme-image.module.css
```text
.imgDark {
  display: none;
}

@media (prefers-color-scheme: dark) {
  .imgLight {
    display: none;
  }
  .imgDark {
    display: unset;
  }
}
```
TypeScript
components/theme-image.tsx

```text
import styles from './theme-image.module.css'
import Image, { ImageProps } from 'next/image'

type Props = Omit<ImageProps, 'src' | 'priority' | 'loading'> & {
  srcLight: string
  srcDark: string
}

const ThemeImage = (props: Props) => {
  const { srcLight, srcDark, ...rest } = props

  return (
    <>
      <Image {...rest} src={srcLight} className={styles.imgLight} />
      <Image {...rest} src={srcDark} className={styles.imgDark} />
    </>
  )
}
```

Good to know
The default behavior of `loading="lazy"` ensures that only the correct image is loaded. You cannot use `priority` or `loading="eager"` because that would cause both images to load. Instead, you can use [`fetchPriority="high"`](https://developer.mozilla.org/docs/Web/API/HTMLImageElement/fetchPriority).
Try it out:
- [Demo light/dark mode theme detection](https://image-component.nextjs.gallery/theme)

### [Art direction](#art-direction) <a id="art-direction"></a>

If you want to display a different image for mobile and desktop, sometimes called [Art Direction](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images#art_direction), you can provide different `src`, `width`, `height`, and `quality` props to `getImageProps()`.
app/page.js
```text
import { getImageProps } from 'next/image'

export default function Home() {
  const common = { alt: 'Art Direction Example', sizes: '100vw' }
  const {
    props: { srcSet: desktop },
  } = getImageProps({
    ...common,
    width: 1440,
    height: 875,
    quality: 80,
    src: '/desktop.jpg',
  })
  const {
    props: { srcSet: mobile, ...rest },
  } = getImageProps({
    ...common,
    width: 750,
    height: 1334,
    quality: 70,
    src: '/mobile.jpg',
  })

  return (
    <picture>
      <source media="(min-width: 1000px)" srcSet={desktop} />
      <source media="(min-width: 500px)" srcSet={mobile} />
      <img {...rest} style={{ width: '100%', height: 'auto' }} />
    </picture>
  )
}
```

### [Background CSS](#background-css) <a id="background-css"></a>

You can even convert the `srcSet` string to the [`image-set()`](https://developer.mozilla.org/en-US/docs/Web/CSS/image/image-set) CSS function to optimize a background image.
app/page.js
```text
import { getImageProps } from 'next/image'

function getBackgroundImage(srcSet = '') {
  const imageSet = srcSet
    .split(', ')
    .map((str) => {
      const [url, dpi] = str.split(' ')
      return `url("${url}") ${dpi}`
    })
    .join(', ')
  return `image-set(${imageSet})`
}

export default function Home() {
  const {
    props: { srcSet },
  } = getImageProps({ alt: '', width: 128, height: 128, src: '/img.png' })
  const backgroundImage = getBackgroundImage(srcSet)
  const style = { height: '100vh', width: '100vw', backgroundImage }

  return (
    <main style={style}>
      <h1>Hello World</h1>
    </main>
  )
}
```

## [Version History](#version-history) <a id="version-history"></a>

```mermaid
block-beta
columns 2
  h_0["<b>Version</b>"]
  h_1["<b>Changes</b>"]
  c_0_0["`v15.5.14`"]
  c_0_1["`maximumDiskCacheSize` configuration added."]
  c_1_0["`v15.3.0`"]
  c_1_1["`remotePatterns` added support for array of `URL` objects."]
  c_2_0["`v15.0.0`"]
  c_2_1["`contentDispositionType` configuration default changed to `attachment`."]
  c_3_0["`v14.2.23`"]
  c_3_1["`qualities` configuration added."]
  c_4_0["`v14.2.15`"]
  c_4_1["`decoding` prop added and `localPatterns` configuration added."]
  c_5_0["`v14.2.14`"]
  c_5_1["`remotePatterns.search` prop added."]
  c_6_0["`v14.2.0`"]
  c_6_1["`overrideSrc` prop added."]
  c_7_0["`v14.1.0`"]
  c_7_1["`getImageProps()` is stable."]
  c_8_0["`v14.0.0`"]
  c_8_1["`onLoadingComplete` prop and `domains` config deprecated."]
  c_9_0["`v13.4.14`"]
  c_9_1["`placeholder` prop support for `data:/image...`"]
  c_10_0["`v13.2.0`"]
  c_10_1["`contentDispositionType` configuration added."]
  c_11_0["`v13.0.6`"]
  c_11_1["`ref` prop added."]
  c_12_0["`v13.0.0`"]
  c_12_1["The `next/image` import was renamed to `next/legacy/image`. The `next/future/image` import was renamed to `next/image..."]
  c_13_0["`v12.3.0`"]
  c_13_1["`remotePatterns` and `unoptimized` configuration is stable."]
  c_14_0["`v12.2.0`"]
  c_14_1["Experimental `remotePatterns` and experimental `unoptimized` configuration added. `layout='raw'` removed."]
  c_15_0["`v12.1.1`"]
  c_15_1["`style` prop added. Experimental support for `layout='raw'` added."]
  c_16_0["`v12.1.0`"]
  c_16_1["`dangerouslyAllowSVG` and `contentSecurityPolicy` configuration added."]
  c_17_0["`v12.0.9`"]
  c_17_1["`lazyRoot` prop added."]
  c_18_0["`v12.0.0`"]
  c_18_1["`formats` configuration added. AVIF support added. Wrapper `` changed to ``."]
  c_19_0["`v11.1.0`"]
  c_19_1["`onLoadingComplete` and `lazyBoundary` props added."]
  c_20_0["`v11.0.0`"]
  c_20_1["`src` prop support for static import. `placeholder` prop added. `blurDataURL` prop added."]
  c_21_0["`v10.0.5`"]
  c_21_1["`loader` prop added."]
  c_22_0["`v10.0.1`"]
  c_22_1["`layout` prop added."]
  c_23_0["`v10.0.0`"]
  c_23_1["`next/image` introduced."]
```

| Version | Changes |
|---|---|
| `v15.5.14` | `maximumDiskCacheSize` configuration added. |
| `v15.3.0` | `remotePatterns` added support for array of `URL` objects. |
| `v15.0.0` | `contentDispositionType` configuration default changed to `attachment`. |
| `v14.2.23` | `qualities` configuration added. |
| `v14.2.15` | `decoding` prop added and `localPatterns` configuration added. |
| `v14.2.14` | `remotePatterns.search` prop added. |
| `v14.2.0` | `overrideSrc` prop added. |
| `v14.1.0` | `getImageProps()` is stable. |
| `v14.0.0` | `onLoadingComplete` prop and `domains` config deprecated. |
| `v13.4.14` | `placeholder` prop support for `data:/image...` |
| `v13.2.0` | `contentDispositionType` configuration added. |
| `v13.0.6` | `ref` prop added. |
| `v13.0.0` | The `next/image` import was renamed to `next/legacy/image`. The `next/future/image` import was renamed to `next/image`. A [codemod is available](/docs/app/guides/upgrading/codemods#next-image-to-legacy-image) to safely and automatically rename your imports. `<span>` wrapper removed. `layout`, `objectFit`, `objectPosition`, `lazyBoundary`, `lazyRoot` props removed. `alt` is required. `onLoadingComplete` receives reference to `img` element. Built-in loader config removed. |
| `v12.3.0` | `remotePatterns` and `unoptimized` configuration is stable. |
| `v12.2.0` | Experimental `remotePatterns` and experimental `unoptimized` configuration added. `layout="raw"` removed. |
| `v12.1.1` | `style` prop added. Experimental support for `layout="raw"` added. |
| `v12.1.0` | `dangerouslyAllowSVG` and `contentSecurityPolicy` configuration added. |
| `v12.0.9` | `lazyRoot` prop added. |
| `v12.0.0` | `formats` configuration added.   AVIF support added.   Wrapper `<div>` changed to `<span>`. |
| `v11.1.0` | `onLoadingComplete` and `lazyBoundary` props added. |
| `v11.0.0` | `src` prop support for static import.   `placeholder` prop added.   `blurDataURL` prop added. |
| `v10.0.5` | `loader` prop added. |
| `v10.0.1` | `layout` prop added. |
| `v10.0.0` | `next/image` introduced. |


Last updated April 15, 2025
[PreviousImage (Legacy)](/docs/15/pages/api-reference/components/image-legacy)
[NextLink](/docs/15/pages/api-reference/components/link)