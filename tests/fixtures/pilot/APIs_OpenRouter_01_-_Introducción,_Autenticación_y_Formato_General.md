# 01 - Introducción, Autenticación y Formato General

# 01 - Introducción, Autenticación y Formato General

> Overview de la API, especificación OpenAPI, formato de requests y responses, autenticación, gestión de API Keys y tokens de identidad.
> 

---

# API Reference

> An overview of OpenRouter's API
> 

OpenRouter's request and response schemas are very similar to the OpenAI Chat API, with a few small differences. At a high level, **OpenRouter normalizes the schema across models and providers** so you only need to learn one.

## OpenAPI specification

The complete OpenRouter API is documented using the OpenAPI specification. You can access the specification in either YAML or JSON format:

- **YAML**: [https://openrouter.ai/openapi.yaml](https://openrouter.ai/openapi.yaml)
- **JSON**: [https://openrouter.ai/openapi.json](https://openrouter.ai/openapi.json)

These specifications can be used with tools like [Swagger UI](https://swagger.io/tools/swagger-ui/), [Postman](https://www.postman.com/), or any OpenAPI-compatible code generator to explore the API or generate client libraries.

## Requests

### Completions request format

Here is the request schema as a TypeScript type. This will be the body of your `POST` request to the `/api/v1/chat/completions` endpoint (see the [quick start](https://app.notion.com/docs/quickstart) above for an example).

For a complete list of parameters, see the [Parameters](https://app.notion.com/docs/api_reference/parameters).

<CodeGroup>

```tsx
// Definitions of subtypes are below
type Request = {
  // Either "messages" or "prompt" is required
  messages?: Message[];
  prompt?: string;

  // If "model" is unspecified, uses the user's default
  model?: string; // See "Supported Models" section

  // Allows to force the model to produce specific output format.
  // See "Structured Outputs" section below and models page for which models support it.
  response_format?: ResponseFormat;

  stop?: string | string[];
  stream?: boolean; // Enable streaming

  // Plugins to extend model capabilities (PDF parsing, response healing)
  // See "Plugins" section: openrouter.ai/docs/guides/features/plugins
  plugins?: Plugin[];

  // See LLM Parameters (openrouter.ai/docs/api_reference/parameters)
  max_tokens?: number; // Range: [1, context_length)
  temperature?: number; // Range: [0, 2]

  // Tool calling
  // Will be passed down as-is for providers implementing OpenAI's interface.
  // For providers with custom interfaces, we transform and map the properties.
  // Otherwise, we transform the tools into a YAML template. The model responds with an assistant message.
  // See models supporting tool calling: openrouter.ai/models?supported_parameters=tools
  tools?: Tool[];
  tool_choice?: ToolChoice;

  // Advanced optional parameters
  seed?: number; // Integer only
  top_p?: number; // Range: (0, 1]
  top_k?: number; // Range: [1, Infinity) Not available for OpenAI models
  frequency_penalty?: number; // Range: [-2, 2]
  presence_penalty?: number; // Range: [-2, 2]
  repetition_penalty?: number; // Range: (0, 2]
  logit_bias?: { [key: number]: number };
  top_logprobs: number; // Integer only
  min_p?: number; // Range: [0, 1]
  top_a?: number; // Range: [0, 1]

  // Reduce latency by providing the model with a predicted output
  // <https://platform.openai.com/docs/guides/latency-optimization#use-predicted-outputs>
  prediction?: { type: 'content'; content: string };

  // OpenRouter-only parameters
  // See "Model Routing" section: openrouter.ai/docs/guides/features/model-routing
  models?: string[];
  route?: 'fallback';
  // See "Provider Routing" section: openrouter.ai/docs/guides/routing/provider-selection
  provider?: ProviderPreferences;
  user?: string; // A stable identifier for your end-users. Used to help detect and prevent abuse.

  // Debug options (streaming only)
  debug?: {
    echo_upstream_body?: boolean; // If true, returns the transformed request body sent to the provider
  };
};

// Subtypes:

type TextContent = {
  type: 'text';
  text: string;
};

type ImageContentPart 