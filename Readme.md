extruder
========

`extruder` is a minimal command line tool for streaming mustache-like templates.

It supports syntax very similar to [mustache](https://mustache.github.io/), that is:

 * `{{` opens a block
 * `}}` closes a block
 * any series of text can be inside a block

That is where the similarities end, because `extruder` takes everything in the block, and passes it to the system(3) system call (this executes the contents of the block using `sh -c`).

## Usage examples

Some examples of usage:

```
> echo -n 'hello {{ whoami }}' | extruder
hello USER
> echo -n 'hello {{ hostname }}' | extruder
hello HOST
> echo -n 'hello {{ echo $ABC }}' | ABC=123 extruder
hello 123
```

And so on...
