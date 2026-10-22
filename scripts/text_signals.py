"""Señales de texto compartidas por el núcleo y los módulos opcionales.

Existe por una razón concreta: el núcleo no puede importar de un módulo
opcional, y lo hace si las funciones que necesita viven dentro del módulo.
Estas primitivas se usan en dos sitios opuestos:

- ``scripts/verify_already_target.py`` y ``scripts/resolve_dispositions.py``
  (núcleo) necesitan contar palabras y decidir si un texto parece inglés;
- ``scripts/detect_residual_language.py`` (fase 126) y
  ``scripts/detect_language.py`` (fase 104) necesitan lo mismo para su
  labor específica.

Que las dos rutas compartan la misma función evita el defecto opuesto:
dos copias de la heurística que divergen sin que ninguna suite lo note.

Este módulo no traduce, no escribe en disco y no lee corpus.
"""

from __future__ import annotations

import re

INLINE_CODE_RE = re.compile(r"`[^`]*`")
FENCED_CODE_RE = re.compile(r"```[\s\S]*?```", re.MULTILINE)
EN_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_\-]*\b")
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)

# Stopwords mínimas en español para reducir falsos positivos sobre corpus
# técnico. No es un detector de español: es una lista de palabras que
# nunca deben contarse como residuo inglés.
SPANISH_STOPWORDS = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "durante",
    "e", "el", "ella", "ellas", "ellos", "en", "entre", "era", "erais",
    "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos",
    "esta", "estaba", "estabais", "estaban", "estabas", "estad", "estada",
    "estadas", "estado", "estados", "estais", "estamos", "estan", "estar",
    "estará", "estarán", "estarás", "estaré", "estaréis", "estaríamos",
    "estarían", "estarías", "estas", "este", "esto", "estos", "estoy",
    "está", "están", "estás", "esté", "estén", "estés", "fui", "fuimos",
    "han", "has", "hay", "haya", "hayamos", "hayan", "hayas", "hayáis",
    "he", "hemos", "hube", "hubiera", "hubo", "la", "las", "le", "les",
    "lo", "los", "más", "me", "mi", "mia", "mias", "mio", "mios", "mis",
    "mucho", "muchos", "muy", "nada", "ni", "no", "nos", "nosotras",
    "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "os",
    "otra", "otras", "otro", "otros", "para", "pero", "poco", "por",
    "que", "quien", "quienes", "se", "sea", "seamos", "sean", "seas",
    "ser", "sería", "seáis", "sin", "sobre", "sois", "somos", "son",
    "soy", "su", "sus", "también", "tanto", "te", "tendrá", "tendrán",
    "tendrás", "tendré", "tendríamos", "tendrían", "tendrías", "tened",
    "tenemos", "tenga", "tengamos", "tengan", "tengas", "tengo", "tenida",
    "tenidas", "tenido", "tenidos", "teniendo", "tenía", "teníamos",
    "tenían", "tenías", "ti", "tiene", "tienen", "tienes", "todo", "todos",
    "tu", "tus", "tuya", "tuyas", "tuyo", "tuyos", "un", "una", "uno",
    "unos", "vosotras", "vosotros", "vuestra", "vuestras", "vuestro",
    "vuestros", "y", "ya", "yo",
}

# Palabras funcionales en inglés mínimas: una run que contenga al menos
# una tiene evidencia positiva de ser inglés.
ENGLISH_FUNCTIONAL_WORDS = {
    "the", "and", "for", "with", "from", "this", "that", "into", "onto",
    "must", "not", "shall", "should", "may", "might", "when", "where",
    "while", "because", "since", "until", "of", "in", "on", "to",
    "by", "as", "is", "are", "be", "been", "have", "has", "had", "was",
    "were", "do", "does", "did", "or", "if", "but", "yet", "so", "no",
}

ENGLISH_MORPHOLOGY = (
    "tion", "sion", "ment", "ness", "ing", "ed", "ize", "ise", "ful",
    "less", "able", "ible", "ous", "ive", "ity", "ation", "ings",
)

# Palabras inglesas técnicas de alta frecuencia en documentación de
# frameworks. Una lista cerrada y revisable: no pretende un diccionario,
# recoge las palabras que el corpus real usa a diario y que ninguna otra
# señal del detector detecta. El piloto produjo 273 avisos falsos con una
# heurística anterior que solo buscaba evidencia en contra; una run solo se
# informa si tiene evidencia a favor, y estos términos son evidencia a favor.
DECLARED_ENGLISH_WORDS = {
    "back", "block", "blocks", "body", "break", "buffer", "build", "button",
    "cache", "call", "calls", "callback", "case", "cases", "check", "class",
    "classes", "client", "code", "column", "columns", "component",
    "components", "config", "context", "control", "controls", "custom",
    "data", "default", "defaults", "define", "delete", "deprecated",
    "design", "detail", "details", "display", "document", "documents",
    "edge", "effect", "element", "elements", "entry", "error", "errors",
    "event", "events", "example", "examples", "export", "exports", "false",
    "feature", "features", "fetch", "field", "fields", "file", "files",
    "filter", "flags", "form", "framework", "function", "functions",
    "handler", "header", "headers", "hook", "hooks", "host", "import",
    "imports", "index", "input", "inputs", "install", "item", "items",
    "key", "keys", "label", "labels", "layout", "level", "link", "links",
    "list", "lists", "load", "loader", "lock", "map", "memory", "message",
    "meta", "method", "methods", "mode", "model", "module", "modules",
    "mount", "name", "names", "node", "nodes", "null", "object", "objects",
    "option", "options", "output", "outputs", "package", "packages", "page",
    "param", "params", "parent", "path", "paths", "payload", "platform",
    "plugin", "plugins", "pointer", "props", "query", "queue",
    "redirect", "ref", "render", "renderer", "request", "requests",
    "require", "requires", "reset", "resolve", "response", "responses",
    "result", "results", "return", "returns", "route", "router", "routes",
    "runtime", "schema", "scope", "script", "scripts", "search", "server",
    "service", "services", "session", "set", "setting", "settings",
    "shared", "shell", "signal", "size", "slot", "slots", "source", "space",
    "stack", "state", "states", "static", "status", "storage", "store",
    "stream", "string", "style", "styles", "submit", "subscription",
    "switch", "symbol", "syntax", "table", "tables", "target", "targets",
    "task", "tasks", "template", "templates", "test", "tests", "thread",
    "timeout", "token", "tokens", "tool", "tools", "tree", "true", "type",
    "types", "undefined", "update", "updates", "url", "value", "values",
    "variable", "variables", "version", "view", "views", "warning", "watch",
    "watcher", "worker", "workers", "wrapper", "write", "writer", "yield",
    "zone",
}

SPANISH_ACCENTS = set("áéíóúüñÁÉÍÓÚÜÑ")

SPANISH_SUFFIXES = (
    "ado", "ido", "ada", "ida", "ción", "sión", "dad", "tad",
    "idad", "ar", "er", "ir", "ble", "aje", "al", "nte",
    "ico", "ica", "ando", "iendo", "mente", "ierto", "ierta",
    "tos", "tas", "rio", "ria", "cion", "sion",
    "enda", "ondo", "ible", "os", "as", "es",
    "ura", "uras", "oso", "osa", "anza", "ismo",
)


def word_count(text: str) -> int:
    """Palabras alfabéticas Unicode. No cuenta cifras ni separadores."""
    return len(WORD_RE.findall(text))


def protect_literal_spans(text: str) -> list[tuple[int, int]]:
    """Rangos de código inline y fenced, sin alterar los desplazamientos."""
    spans: list[tuple[int, int]] = []
    for rx in (INLINE_CODE_RE, FENCED_CODE_RE):
        for m in rx.finditer(text):
            spans.append((m.start(), m.end()))
    spans.sort()
    return spans


def in_protected(idx: int, spans: list[tuple[int, int]]) -> bool:
    for start, end in spans:
        if start <= idx < end:
            return True
        if idx < start:
            break
    return False


def english_runs(text: str, preserve: set[str]) -> list[tuple[int, int, list[str]]]:
    """Rangos de tokens consecutivos que no son español ni término preservado."""
    protected = protect_literal_spans(text)
    runs: list[tuple[int, int, list[str]]] = []
    current: list[str] = []
    current_start = -1
    in_run = False
    for m in EN_TOKEN_RE.finditer(text):
        token = m.group(0)
        idx = m.start()
        if in_protected(idx, protected):
            if in_run:
                runs.append((current_start, idx, current))
                current = []
                in_run = False
            continue
        if token.lower() in preserve:
            if in_run:
                runs.append((current_start, idx, current))
                current = []
                in_run = False
            continue
        if token.lower() in SPANISH_STOPWORDS:
            if in_run:
                runs.append((current_start, idx, current))
                current = []
                in_run = False
            continue
        if len(token) < 3:
            continue
        if not in_run:
            in_run = True
            current_start = idx
            current = [token]
        else:
            current.append(token)
    if in_run:
        runs.append((current_start, len(text), current))
    return runs


def looks_english(tokens: list[str]) -> bool:
    """¿Tiene esta run evidencia positiva de ser inglés?

    Exige evidencia **a favor**: una palabra funcional inglesa, una
    terminación inglesa, forma de identificador o un término técnico de la
    lista cerrada. El resto se descarta. Es preferible dejar pasar un
    residuo raro a inundar el informe con prosa española.
    """
    if not tokens:
        return False
    if any(c in SPANISH_ACCENTS for tok in tokens for c in tok):
        return False
    if all(any(tok.lower().endswith(suf) for suf in SPANISH_SUFFIXES) for tok in tokens):
        return False
    if any("_" in tok for tok in tokens) or any("-" in tok for tok in tokens):
        return True
    for tok in tokens:
        lower = tok.lower()
        if lower in ENGLISH_FUNCTIONAL_WORDS:
            return True
        if lower.endswith(ENGLISH_MORPHOLOGY):
            return True
        if any(c.isupper() for c in tok[1:]):
            return True
        if lower in DECLARED_ENGLISH_WORDS:
            return True
    return False


def severity_for(words: list[str]) -> str:
    """``warning`` desde cuatro palabras; antes, ``info``. Señal, no veredicto."""
    return "warning" if len(words) >= 4 else "info"


def file_disposition(counts: dict[str, int]) -> str:
    """Agregado por archivo a partir de los recuentos de disposición.

    Lo consume tanto la clasificación por idioma (fase 104) como
    ``resolve_dispositions.py``. Una sola regla: si las reglas vivieran en
    dos sitios, el agregado del manifiesto mentiría sin que nada lo note.
    """
    total = sum(counts.values()) or 1
    already = counts.get("already_target", 0) / total
    translatable = counts.get("translatable", 0) / total
    if already > 0.5 and translatable < 0.3:
        return "already_target"
    if translatable > 0.5 and already < 0.3:
        return "translatable"
    return "mixed"