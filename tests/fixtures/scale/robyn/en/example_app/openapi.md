
## [](/documentation/en/example_app/openapi#openapi-docs-aka-swagger)[OpenAPI Docs a.k.a Swagger](/documentation/en/example_app/openapi#openapi-docs-aka-swagger) <a id="openapi-docs-aka-swagger"></a>

After deploying the application, Batman got multiple queries from the users on how to use the endpoints. Robyn showed him how to generate OpenAPI specifications for his application.
Out of the box, the following endpoints are setup for you:
- `/docs` The Swagger UI
- `/openapi.json` The JSON Specification

However, if you don't want to generate the OpenAPI docs, you can disable it by passing `--disable-openapi` flag while starting the application.
To use a custom openapi configuration, you can:
- Place the `openapi.json` config file in the root directory.
- Or, pass the file path to the `openapi_file_path` parameter in the `Robyn()` constructor. (the parameter gets priority over the file).

```bash
python app.py --disable-openapi
```
Copy
Copied!

## [](/documentation/en/example_app/openapi#how-to-use)[How to use?](/documentation/en/example_app/openapi#how-to-use) <a id="how-to-use"></a>

- Query Params: The typing for query params can be added as `` def get(r: Request, query_params: GetRequestParams) `` where `GetRequestParams` is a subclass of `QueryParams`
- Path Params are defaulted to string type (ref: [https://en.wikipedia.org/wiki/Query\_string](https://en.wikipedia.org/wiki/Query_string))

### Basic App

```python
from robyn.robyn import QueryParams

from robyn import Robyn, Request

app = Robyn(
    file_object=__file__,
    openapi=OpenAPI(
        info=OpenAPIInfo(
            title="Sample App",
            description="This is a sample server application.",
            termsOfService="https://example.com/terms/",
            version="1.0.0",
            contact=Contact(
                name="API Support",
                url="https://www.example.com/support",
                email="support@example.com",
            ),
            license=License(
                name="BSD2.0",
                url="https://opensource.org/license/bsd-2-clause",
            ),
            externalDocs=ExternalDocumentation(description="Find more info here", url="https://example.com/"),
            components=Components(),
        ),
    ),
)

@app.get("/")
async def welcome():
    """welcome endpoint"""
    return "hi"

class GetRequestParams(QueryParams):
    appointment_id: str
    year: int

@app.get("/api/v1/name", openapi_name="Name Route", openapi_tags=["Name"])
async def get(r: Request, query_params: GetRequestParams):
    """Get Name by ID"""
    return r.query_params

@app.delete("/users/:name", openapi_tags=["Name"])
async def delete(r: Request):
    """Delete Name by ID"""
    return r.path_params

if __name__ == "__main__":
    app.start()
```
Copy
Copied!

## [](/documentation/en/example_app/openapi#how-does-it-work-with-subrouters)[How does it work with subrouters?](/documentation/en/example_app/openapi#how-does-it-work-with-subrouters) <a id="how-does-it-work-with-subrouters"></a>

### Subrouters

```python
from robyn.robyn import QueryParams

from robyn import Request, SubRouter

subrouter: SubRouter = SubRouter(prefix="/sub")

@subrouter.get("/")
async def subrouter_welcome():
    """welcome subrouter"""
    return "hiiiiii subrouter"

class SubRouterGetRequestParams(QueryParams):
    _id: int
    value: str

@subrouter.get("/name")
async def subrouter_get(r: Request, query_params: SubRouterGetRequestParams):
    """Get Name by ID"""
    return r.query_params

@subrouter.delete("/:name")
async def subrouter_delete(r: Request):
    """Delete Name by ID"""
    return r.path_params

app.include_router(subrouter)
```
Copy
Copied!

## [](/documentation/en/example_app/openapi#other-specification-params)[Other Specification Params](/documentation/en/example_app/openapi#other-specification-params) <a id="other-specification-params"></a>

We support all the params mentioned in the latest OpenAPI specifications ([https://swagger.io/specification/](https://swagger.io/specification/)). See an example using request & response bodies below:
### Request & Response Body

```python
from robyn.types import JSONResponse, Body

class Initial(Body):
    is_present: bool
    letter: Optional[str]

class FullName(Body):
    first: str
    second: str
    initial: Initial

class CreateItemBody(Body):
    name: FullName
    description: str
    price: float
    tax: float

class CreateResponse(JSONResponse):
    success: bool
    items_changed: int

@app.post("/")
def create_item(request: Request, body: CreateItemBody) -> CreateResponse:
    return CreateResponse(success=True, items_changed=2)
```
Copy
Copied!

With the reference documentation deployed and running smoothly, Batman had a powerful new tool at his disposal. The Robyn framework had provided him with the flexibility, scalability, and performance needed to create an effective crime-fighting application, giving him a technological edge in his ongoing battle to protect Gotham City.
[Templates](/documentation/en/example_app/templates)