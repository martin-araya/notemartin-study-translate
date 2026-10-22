
TypeScript provides several utility types to facilitate common type transformations. These utilities are available globally.
## [](#awaitedtype)`Awaited<Type>` <a id="awaitedtype"></a>

>
> Released:
[4.5](/docs/handbook/release-notes/typescript-4-5.html#the-awaited-type-and-promise-improvements)

This type is meant to model operations like `await` in `async` functions, or the
`.then()` method on `Promise`s - specifically, the way that they recursively
unwrap `Promise`s.
##### [](#example)Example <a id="example"></a>

```text
type A = Awaited<Promise<string>>;    type A = string type B = Awaited<Promise<Promise<number>>>;    type B = number type C = Awaited<boolean | Promise<number>>;    type C = number | boolean
```

## [](#partialtype)`Partial<Type>` <a id="partialtype"></a>

>
> Released:  

[2.1](/docs/handbook/release-notes/typescript-2-1.html#partial-readonly-record-and-pick)

Constructs a type with all properties of `Type` set to optional. This utility will return a type that represents all subsets of a given type.
##### [](#example-1)Example <a id="example-1"></a>

```text
interface Todo {  title: string;  description: string;} function updateTodo(todo: Todo, fieldsToUpdate: Partial<Todo>) {  return { ...todo, ...fieldsToUpdate };} const todo1 = {  title: "organize desk",  description: "clear clutter",}; const todo2 = updateTodo(todo1, {  description: "throw out trash",});
```

## [](#requiredtype)`Required<Type>` <a id="requiredtype"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#improved-control-over-mapped-type-modifiers)

Constructs a type consisting of all properties of `Type` set to required. The opposite of [`Partial`](#partialtype).
##### [](#example-2)Example <a id="example-2"></a>

```text
interface Props {  a?: number;  b?: string;} const obj: Props = { a: 5 }; const obj2: Required<Props> = { a: 5 };Property 'b' is missing in type '{ a: number; }' but required in type 'Required<Props>'.2741Property 'b' is missing in type '{ a: number; }' but required in type 'Required<Props>'.
```

## [](#readonlytype)`Readonly<Type>` <a id="readonlytype"></a>

>
> Released:  

[2.1](/docs/handbook/release-notes/typescript-2-1.html#partial-readonly-record-and-pick)

Constructs a type with all properties of `Type` set to `readonly`, meaning the properties of the constructed type cannot be reassigned.
##### [](#example-3)Example <a id="example-3"></a>

```text
interface Todo {  title: string;} const todo: Readonly<Todo> = {  title: "Delete inactive users",}; todo.title = "Hello";Cannot assign to 'title' because it is a read-only property.2540Cannot assign to 'title' because it is a read-only property.
```

This utility is useful for representing assignment expressions that will fail at runtime (i.e. when attempting to reassign properties of a [frozen object](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Object/freeze)).
##### [](#objectfreeze)`Object.freeze` <a id="objectfreeze"></a>

```text
function freeze<Type>(obj: Type): Readonly<Type>;
```

## [](#recordkeys-type)`` Record<Keys, Type> `` <a id="recordkeys-type"></a>

>
> Released:  

[2.1](/docs/handbook/release-notes/typescript-2-1.html#partial-readonly-record-and-pick)

Constructs an object type whose property keys are `Keys` and whose property values are `Type`. This utility can be used to map the properties of a type to another type.
##### [](#example-4)Example <a id="example-4"></a>

```text
type CatName = "miffy" | "boris" | "mordred"; interface CatInfo {  age: number;  breed: string;} const cats: Record<CatName, CatInfo> = {  miffy: { age: 10, breed: "Persian" },  boris: { age: 5, breed: "Maine Coon" },  mordred: { age: 16, breed: "British Shorthair" },}; cats.boris; const cats: Record<CatName, CatInfo>
```

## [](#picktype-keys)`` Pick<Type, Keys> `` <a id="picktype-keys"></a>

>
> Released:  

[2.1](/docs/handbook/release-notes/typescript-2-1.html#partial-readonly-record-and-pick)

Constructs a type by picking the set of properties `Keys` (string literal or union of string literals) from `Type`.
##### [](#example-5)Example <a id="example-5"></a>

```text
interface Todo {  title: string;  description: string;  completed: boolean;} type TodoPreview = Pick<Todo, "title" | "completed">; const todo: TodoPreview = {  title: "Clean room",  completed: false,}; todo; const todo: TodoPreview
```

## [](#omittype-keys)`` Omit<Type, Keys> `` <a id="omittype-keys"></a>

>
> Released:  

[3.5](/docs/handbook/release-notes/typescript-3-5.html#the-omit-helper-type)

Constructs a type by picking all properties from `Type` and then removing `Keys` (string literal or union of string literals). The opposite of [`Pick`](#picktype-keys).
##### [](#example-6)Example <a id="example-6"></a>

```text
interface Todo {  title: string;  description: string;  completed: boolean;  createdAt: number;} type TodoPreview = Omit<Todo, "description">; const todo: TodoPreview = {  title: "Clean room",  completed: false,  createdAt: 1615544252770,}; todo; const todo: TodoPreview type TodoInfo = Omit<Todo, "completed" | "createdAt">; const todoInfo: TodoInfo = {  title: "Pick up kids",  description: "Kindergarten closes at 5pm",}; todoInfo;   const todoInfo: TodoInfo
```

## [](#excludeuniontype-excludedmembers)`` Exclude<UnionType, ExcludedMembers> `` <a id="excludeuniontype-excludedmembers"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#predefined-conditional-types)

Constructs a type by excluding from `UnionType` all union members that are assignable to `ExcludedMembers`.
##### [](#example-7)Example <a id="example-7"></a>

```text
type T0 = Exclude<"a" | "b" | "c", "a">;     type T0 = "b" | "c"type T1 = Exclude<"a" | "b" | "c", "a" | "b">;     type T1 = "c"type T2 = Exclude<string | number | (() => void), Function>;     type T2 = string | number type Shape =  | { kind: "circle"; radius: number }  | { kind: "square"; x: number }  | { kind: "triangle"; x: number; y: number }; type T3 = Exclude<Shape, { kind: "circle" }>     type T3 = {
    kind: "square";
    x: number;
} | {
    kind: "triangle";
    x: number;
    y: number;
}
```

## [](#extracttype-union)`` Extract<Type, Union> `` <a id="extracttype-union"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#predefined-conditional-types)

Constructs a type by extracting from `Type` all union members that are assignable to `Union`.
##### [](#example-8)Example <a id="example-8"></a>

```text
type T0 = Extract<"a" | "b" | "c", "a" | "f">;     type T0 = "a"type T1 = Extract<string | number | (() => void), Function>;     type T1 = () => void type Shape =  | { kind: "circle"; radius: number }  | { kind: "square"; x: number }  | { kind: "triangle"; x: number; y: number }; type T2 = Extract<Shape, { kind: "circle" }>     type T2 = {
    kind: "circle";
    radius: number;
}
```

## [](#nonnullabletype)`NonNullable<Type>` <a id="nonnullabletype"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#predefined-conditional-types)

Constructs a type by excluding `null` and `undefined` from `Type`.
##### [](#example-9)Example <a id="example-9"></a>

```text
type T0 = NonNullable<string | number | undefined>;     type T0 = string | numbertype T1 = NonNullable<string[] | null | undefined>;     type T1 = string[]
```

## [](#parameterstype)`Parameters<Type>` <a id="parameterstype"></a>

>
> Released:  

[3.1](https://github.com/microsoft/TypeScript/pull/26243)

Constructs a tuple type from the types used in the parameters of a function type `Type`.
For overloaded functions, this will be the parameters of the *last* signature; see [Inferring Within Conditional Types](/docs/handbook/2/conditional-types.html#inferring-within-conditional-types).
##### [](#example-10)Example <a id="example-10"></a>

```text
declare function f1(arg: { a: number; b: string }): void; type T0 = Parameters<() => string>;     type T0 = []type T1 = Parameters<(s: string) => void>;     type T1 = [s: string]type T2 = Parameters<<T>(arg: T) => T>;     type T2 = [arg: unknown]type T3 = Parameters<typeof f1>;     type T3 = [arg: {
    a: number;
    b: string;
}]type T4 = Parameters<any>;     type T4 = unknown[]type T5 = Parameters<never>;     type T5 = nevertype T6 = Parameters<string>;Type 'string' does not satisfy the constraint '(...args: any) => any'.2344Type 'string' does not satisfy the constraint '(...args: any) => any'.     type T6 = nevertype T7 = Parameters<Function>;Type 'Function' does not satisfy the constraint '(...args: any) => any'.
  Type 'Function' provides no match for the signature '(...args: any): any'.2344Type 'Function' does not satisfy the constraint '(...args: any) => any'.
  Type 'Function' provides no match for the signature '(...args: any): any'.     type T7 = never
```

## [](#constructorparameterstype)`ConstructorParameters<Type>` <a id="constructorparameterstype"></a>

>
> Released:  

[3.1](https://github.com/microsoft/TypeScript/pull/26243)

Constructs a tuple or array type from the types of a constructor function type. It produces a tuple type with all the parameter types (or the type `never` if `Type` is not a function).
##### [](#example-11)Example <a id="example-11"></a>

```text
type T0 = ConstructorParameters<ErrorConstructor>;     type T0 = [message?: string]type T1 = ConstructorParameters<FunctionConstructor>;     type T1 = string[]type T2 = ConstructorParameters<RegExpConstructor>;     type T2 = [pattern: string | RegExp, flags?: string]class C {  constructor(a: number, b: string) {}}type T3 = ConstructorParameters<typeof C>;     type T3 = [a: number, b: string]type T4 = ConstructorParameters<any>;     type T4 = unknown[] type T5 = ConstructorParameters<Function>;Type 'Function' does not satisfy the constraint 'abstract new (...args: any) => any'.
  Type 'Function' provides no match for the signature 'new (...args: any): any'.2344Type 'Function' does not satisfy the constraint 'abstract new (...args: any) => any'.
  Type 'Function' provides no match for the signature 'new (...args: any): any'.     type T5 = never
```

## [](#returntypetype)`ReturnType<Type>` <a id="returntypetype"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#predefined-conditional-types)

Constructs a type consisting of the return type of function `Type`.
For overloaded functions, this will be the return type of the *last* signature; see [Inferring Within Conditional Types](/docs/handbook/2/conditional-types.html#inferring-within-conditional-types).
##### [](#example-12)Example <a id="example-12"></a>

```text
declare function f1(): { a: number; b: string }; type T0 = ReturnType<() => string>;     type T0 = stringtype T1 = ReturnType<(s: string) => void>;     type T1 = voidtype T2 = ReturnType<<T>() => T>;     type T2 = unknowntype T3 = ReturnType<<T extends U, U extends number[]>() => T>;     type T3 = number[]type T4 = ReturnType<typeof f1>;     type T4 = {
    a: number;
    b: string;
}type T5 = ReturnType<any>;     type T5 = anytype T6 = ReturnType<never>;     type T6 = nevertype T7 = ReturnType<string>;Type 'string' does not satisfy the constraint '(...args: any) => any'.2344Type 'string' does not satisfy the constraint '(...args: any) => any'.     type T7 = anytype T8 = ReturnType<Function>;Type 'Function' does not satisfy the constraint '(...args: any) => any'.
  Type 'Function' provides no match for the signature '(...args: any): any'.2344Type 'Function' does not satisfy the constraint '(...args: any) => any'.
  Type 'Function' provides no match for the signature '(...args: any): any'.     type T8 = any
```

## [](#instancetypetype)`InstanceType<Type>` <a id="instancetypetype"></a>

>
> Released:  

[2.8](/docs/handbook/release-notes/typescript-2-8.html#predefined-conditional-types)

Constructs a type consisting of the instance type of a constructor function in `Type`.
##### [](#example-13)Example <a id="example-13"></a>

```text
class C {  x = 0;  y = 0;} type T0 = InstanceType<typeof C>;     type T0 = Ctype T1 = InstanceType<any>;     type T1 = anytype T2 = InstanceType<never>;     type T2 = nevertype T3 = InstanceType<string>;Type 'string' does not satisfy the constraint 'abstract new (...args: any) => any'.2344Type 'string' does not satisfy the constraint 'abstract new (...args: any) => any'.     type T3 = anytype T4 = InstanceType<Function>;Type 'Function' does not satisfy the constraint 'abstract new (...args: any) => any'.
  Type 'Function' provides no match for the signature 'new (...args: any): any'.2344Type 'Function' does not satisfy the constraint 'abstract new (...args: any) => any'.
  Type 'Function' provides no match for the signature 'new (...args: any): any'.     type T4 = any
```

## [](#noinfertype)`NoInfer<Type>` <a id="noinfertype"></a>

>
> Released:  

[5.4](/docs/handbook/release-notes/typescript-5-4.html#the-noinfer-utility-type)

Blocks inferences to the contained type. Other than blocking inferences, `NoInfer<Type>` is
identical to `Type`.
##### [](#example-14)Example <a id="example-14"></a>

```text
function createStreetLight<C extends string>(  colors: C[],  defaultColor?: NoInfer<C>,) {  // ...}createStreetLight(["red", "yellow", "green"], "red");  // OKcreateStreetLight(["red", "yellow", "green"], "blue");  // Error
```

## [](#thisparametertypetype)`ThisParameterType<Type>` <a id="thisparametertypetype"></a>

>
> Released:  

[3.3](https://github.com/microsoft/TypeScript/pull/28920)

Extracts the type of the [this](/docs/handbook/functions.html#this-parameters) parameter for a function type, or [unknown](/docs/handbook/release-notes/typescript-3-0.html#new-unknown-top-type) if the function type has no `this` parameter.
##### [](#example-15)Example <a id="example-15"></a>

```text
function toHex(this: Number) {  return this.toString(16);} function numberToString(n: ThisParameterType<typeof toHex>) {  return toHex.apply(n);}
```

## [](#omitthisparametertype)`OmitThisParameter<Type>` <a id="omitthisparametertype"></a>

>
> Released:  

[3.3](https://github.com/microsoft/TypeScript/pull/28920)

Removes the [`this`](/docs/handbook/functions.html#this-parameters) parameter from `Type`. If `Type` has no explicitly declared `this` parameter, the result is simply `Type`. Otherwise, a new function type with no `this` parameter is created from `Type`. Generics are erased and only the last overload signature is propagated into the new function type.
##### [](#example-16)Example <a id="example-16"></a>

```text
function toHex(this: Number) {  return this.toString(16);} const fiveToHex: OmitThisParameter<typeof toHex> = toHex.bind(5); console.log(fiveToHex());
```

## [](#thistypetype)`ThisType<Type>` <a id="thistypetype"></a>

>
> Released:  

[2.3](https://github.com/microsoft/TypeScript/pull/14141)

This utility does not return a transformed type. Instead, it serves as a marker for a contextual [`this`](/docs/handbook/functions.html#this) type. Note that the [`noImplicitThis`](/tsconfig#noImplicitThis) flag must be enabled to use this utility.
##### [](#example-17)Example <a id="example-17"></a>

```text
type ObjectDescriptor<D, M> = {  data?: D;  methods?: M & ThisType<D & M>; // Type of 'this' in methods is D & M}; function makeObject<D, M>(desc: ObjectDescriptor<D, M>): D & M {  let data: object = desc.data || {};  let methods: object = desc.methods || {};  return { ...data, ...methods } as D & M;} let obj = makeObject({  data: { x: 0, y: 0 },  methods: {    moveBy(dx: number, dy: number) {      this.x += dx; // Strongly typed this      this.y += dy; // Strongly typed this    },  },}); obj.x = 10;obj.y = 20;obj.moveBy(5, 5);
```

In the example above, the `methods` object in the argument to `makeObject` has a contextual type that includes `` ThisType<D & M> `` and therefore the type of [this](/docs/handbook/functions.html#this) in methods within the `methods` object is `` { x: number, y: number } & { moveBy(dx: number, dy: number): void } ``. Notice how the type of the `methods` property simultaneously is an inference target and a source for the `this` type in methods.
The `ThisType<T>` marker interface is simply an empty interface declared in `lib.d.ts`. Beyond being recognized in the contextual type of an object literal, the interface acts like any empty interface.
## [](#intrinsic-string-manipulation-types)Intrinsic String Manipulation Types <a id="intrinsic-string-manipulation-types"></a>

### [](#uppercasestringtype)`Uppercase<StringType>` <a id="uppercasestringtype"></a>

### [](#lowercasestringtype)`Lowercase<StringType>` <a id="lowercasestringtype"></a>

### [](#capitalizestringtype)`Capitalize<StringType>` <a id="capitalizestringtype"></a>

### [](#uncapitalizestringtype)`Uncapitalize<StringType>` <a id="uncapitalizestringtype"></a>

To help with string manipulation around template string literals, TypeScript includes a set of types which can be used in string manipulation within the type system. You can find those in the [Template Literal Types](/docs/handbook/2/template-literal-types.html#uppercasestringtype) documentation.