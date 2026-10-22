# Path traversal attempts

The following references must NOT be followed. The inventory must
record them as `path_traversal` findings and refuse to open the target.

- ![alt text](../../../etc/passwd)
- [secret](../../etc/shadow)
- [parent](../../../)
- [image with weird prefix](.../.../etc/hosts)

All references above resolve outside the source root and must be
flagged, not opened.