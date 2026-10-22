
# Presentation

This page contains information about Mermaid Chart’s Presentation feature.
---

## About <a id="about"></a>

The Presentation feature allows you to create and present slideshows using Markdown syntax. You can easily add diagrams, images, and text to your slides, making it a powerful tool for creating engaging presentations.
![presentation](/docs/presentation/presentations-feature.png)
## Learn Markdown syntax <a id="learn-markdown-syntax"></a>

Markdown is a lightweight markup language that allows you to format text using simple syntax. It is widely used for creating documentation, notes, and presentations.
For more information on Markdown syntax, check out the [Markdown Guide site](https://www.markdownguide.org/basic-syntax/).
## Presentation Editor <a id="presentation-editor"></a>

### Creating slides using Markdown (left panel) <a id="creating-slides-using-markdown-left-panel"></a>

You can write and structure your entire presentation using Markdown in the editor.
To create a new slide, add four dashes (`----`) on a new line. This will create a horizontal slide. You can also add a title and subtitle to each slide using the `#` and `##` symbols, respectively.
It is not necessary to add four dashes at the top of the first slide. The first slide will be created automatically when you start adding content.
You can add as many slides as you want by repeating the process. Each slide will be separated by four dashes.
Make sure you add a blank line before and after the dashes to ensure proper formatting.
For example:
```plaintext
# Slide 1 Title
## Slide 1 Subtitle

----

# Slide 2 Title
## Slide 2 Subtitle
```

## Supported elements <a id="supported-elements"></a>

### Slide titles <a id="slide-titles"></a>

- `` # Title `` – Creates a new **main slide** with a large heading.
- `` ## Subtitle `` – Adds a **subheading** on the same slide.

Heading levels are defined by the number of `#` symbols used. The more `#` symbols, the smaller the heading. Heading levels up to six are supported.
![HeadingAndContent](/docs/presentation/add-headings-and-content.png)
### Vertical Slides (nested slides) <a id="vertical-slides-nested-slides"></a>

The slides are stepped between horizontally by default. These horizontal slides are considered the main, or top-level, slides in your deck.
It’s also possible to nest multiple slides within a single top-level slide to create a vertical stack. This is a great way to logically group content in your presentation and makes it convenient to include optional slides.
To create a **vertical slide** within a parent slide:
- `====`  Splits **vertical slides** within a slides.

```plaintext
# Horizontal Slide 1

----

# Horizontal Slide 2

====

# Vertical Slide 1 Title

====

# Vertical Slide 2 Title

----

# Horizontal Slide 3
```
![add sub slides](/docs/presentation/add-sub-slides.png)

### Bulleted lists <a id="bulleted-lists"></a>

```plaintext
- Point one
- Point two
```
![add bullet points](/docs/presentation/lists-bulleted.png)

### Numbered lists <a id="numbered-lists"></a>

```plaintext
1. First step
2. Second step
```
![add numbered points](/docs/presentation/lists-numbered.png)

### Text Formatting <a id="text-formatting"></a>

```plaintext
- `**bold**` – Bold text
- `_italic_` – Italic text
```
![format text](/docs/presentation/format-text.png)

### Embedding Images <a id="embedding-images"></a>

```plaintext
::img{src="https://example.com/image.png"}
```
![embed images](/docs/presentation/embed-images.png)

### Adding Links <a id="adding-links"></a>

```plaintext
[Click Here](https://your-link.com)
```
![add links](/docs/presentation/add-links.png)

## Main toolbar (top-left corner) <a id="main-toolbar-top-left-corner"></a>
![main toolbar](/docs/presentation/toolbar-main.png)

```mermaid
block-beta
columns 3
  h_0["<b>Numbers</b>"]
  h_1["<b>Function</b>"]
  h_2["<b>Description</b>"]
  c_0_0["1"]
  c_0_1["Add New Slide"]
  c_0_2["Inserts a new slide at the current cursor location."]
  c_1_0["2"]
  c_1_1["Add Sub-Slide"]
  c_1_2["Creates a sub-slide underneath the se