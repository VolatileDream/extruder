extruder
========

`extruder` is a minimal command line tool for streaming mustache-like templates.

It supports syntax very similar to [mustache](), that is:

 * `{{` opens a block
 * `}}` closes a block
 * any series of text can be inside a block

There are, however, some important differences:

 * `extruder` takes everything in the block, and passes it to the system(3) system call. This executes the contents of the block using `sh -c`.
 * no other [mustache]() functionality is supported.

## Usage examples

Some examples of usage:

```
> echo -n "hello {{ whoami }}" | extruder
hello USER
> echo -n "hello {{ hostname }}" | extruder
hello HOST
```

And so on...
