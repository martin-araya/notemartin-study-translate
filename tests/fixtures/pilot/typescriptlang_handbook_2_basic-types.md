
Each and every value in JavaScript has a set of behaviors you can observe from running different operations.
That sounds abstract, but as a quick example, consider some operations we might run on a variable named `message`.
```text
// Accessing the property 'toLowerCase'// on 'message' and then calling itmessage.toLowerCase();// Calling 'message'message();
```

If we break this down, the first runnable line of code accesses a property called `toLowerCase` and then calls it.
The second one tries to call `message` directly.
But assuming we don’t know the value of `message` - and that’s pretty common - we can’t reliably say what results we’ll get from trying to run any of this code.
The behavior of each operation depends entirely on what value we had in the first place.
- Is `message` callable?
- Does it have a property called `toLowerCase` on it?
- If it does, is `toLowerCase` even callable?
- If both of these values are callable, what do they return?

The answers to these questions are usually things we keep in our heads when we write JavaScript, and we have to hope we got all the details right.
Let’s say `message` was defined in the following way.
```text
const message = "Hello World!";
```

As you can probably guess, if we try to run `message.toLowerCase()`, we’ll get the same string only in lower-case.
What about that second line of code?
If you’re familiar with JavaScript, you’ll know this fails with an exception:
```text
TypeError: message is not a function
```

It’d be great if we could avoid mistakes like this.
When we run our code, the way that our JavaScript runtime chooses what to do is by figuring out the *type* of the value - what sorts of behaviors and capabilities it has.
That’s part of what that `TypeError` is alluding to - it’s saying that the string `` "Hello World!" `` cannot be called as a function.
For some values, such as the primitives `string` and `number`, we can identify their type at runtime using the `typeof` operator.
But for other things like functions, there’s no corresponding runtime mechanism to identify their types.
For example, consider this function:
```text
function fn(x) {  return x.flip();}
```

We can *observe* by reading the code that this function will only work if given an object with a callable `flip` property, but JavaScript doesn’t surface this information in a way that we can check while the code is running.
The only way in pure JavaScript to tell what `fn` does with a particular value is to call it and see what happens.
This kind of behavior makes it hard to predict what the code will do before it runs, which means it’s harder to know what your code is going to do while you’re writing it.
Seen in this way, a *type* is the concept of describing which values can be passed to `fn` and which will crash.
JavaScript only truly provides *dynamic* typing - running the code to see what happens.
The alternative is to use a *static* type system to make predictions about what the code is expected to do *before* it runs.
## [](#static-type-checking)Static type-checking <a id="static-type-checking"></a>

Think back to that `TypeError` we got earlier from trying to call a `string` as a function.
*Most people* don’t like to get any sorts of errors when running their code - those are considered bugs!
And when we write new code, we try our best to avoid introducing new bugs.
If we add just a bit of code, save our file, re-run the code, and immediately see the error, we might be able to isolate the problem quickly; but that’s not always the case.
We might not have tested the feature thoroughly enough, so we might never actually run into a potential error that would be thrown!
Or if we were lucky enough to witness the error, we might have ended up doing large refactorings and adding a lot of different code that we’re forced to dig through.
Ideally, we could have a tool that helps us find these bugs *before* our code runs.
That’s what a static type-checker like TypeScript does.
*Static type systems* describe the shapes and behaviors of what our values will b