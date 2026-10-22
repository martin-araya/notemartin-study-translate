# Mixed corpus

This document demonstrates a truly multilingual file with French and
English sections in the same Markdown file, no double translation, and
no double counting.

## Section en français

Cette section est en français. Elle parle d'un sujet technique simple
pour exercer le détecteur de langue sur des segments courts et longs.

The following sentence is in English but lives in the same document.
It serves as the boundary between the French and the English parts.

## Section in English

This section is in English. It covers a related technical point to
exercise language detection on longer prose and to verify that the
detector distinguishes English from French reliably.

## Section imbriquée en français

Après ce paragraphe anglais, nous revenons au français. Cette
section teste la détection par segments alternés.

```bash
# Mixed corpus test
echo "francais et english"
```

The block above mixes a French comment with an English command. The
command must not be translated; the comment is informational and can
be translated without harm.
