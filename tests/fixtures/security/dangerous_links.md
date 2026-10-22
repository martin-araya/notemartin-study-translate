# Dangerous links

The following links use unsafe schemes. The pipeline must record them
without rewriting or following them.

- [click me](javascript:alert(1))
- [read file](file:///etc/passwd)
- [render html](data:text/html,<script>alert(1)</script>)
- [open local](file:///proc/self/environ)
- [normal external](https://example.com/page)

The unsafe links must appear in the report as `unsafe_scheme` findings.