
# :-moz-last-node

**No estándar:** Esta función no está estandarizada. No recomendamos usar funciones no estándar en producción, ya que tienen un soporte limitado en los navegadores y pueden cambiar o eliminarse. Sin embargo, pueden ser una alternativa adecuada en casos específicos donde no exista una opción estándar.
## [Resumen](#resumen) <a id="resumen"></a>

La [pseudo-clase](/es/docs/Web/CSS/Reference/Selectors/Pseudo-classes) [CSS](/es/docs/Web/CSS) `:-moz-last-node` selecciona un elemento si es el último nodo hijo de algún otro elemento. Se diferencia de [`:last-child`](/es/docs/Web/CSS/Reference/Selectors/:last-child) en que no selecciona el último elemento hijo si tiene texto (sin contar espacios en blanco) después de él.
**Nota:**
Cualquier espacio en blanco al final de un elemento se ignora al usar `:-moz-last-node`.
## [Síntaxis](#síntaxis) <a id="síntaxis"></a>

```text
span:-moz-last-node {propiedades del estilo }
```

## [Ejemplo](#ejemplo) <a id="ejemplo"></a>

### [CSS](#css) <a id="css"></a>
css

```css
span:-moz-last-node {
  background-color: lime;
}
```

### [HTML](#html) <a id="html"></a>
html

```html
<div>
  <span>:-moz-first-node</span>
  <span>:-moz-last-node</span>
</div>
```

## [Ver además](#ver_además) <a id="ver_además"></a>

- [`:-moz-first-node`](/es/docs/Web/CSS/Reference/Selectors/:-moz-first-node)
- [`:last-child`](/es/docs/Web/CSS/Reference/Selectors/:last-child)

## Ayuda a mejorar MDN <a id="feedback"></a>
[Aprende cómo colaborar](/es/docs/MDN/Community/Getting_started)


    Esta página se modificó por última vez el 31 mar 2026 por [colaboradores de MDN](/es/docs/Web/CSS/Reference/Selectors/:-moz-last-node/contributors.txt).
[Ver esta página en GitHub](https://github.com/mdn/translated-content/blob/main/files/es/web/css/reference/selectors/_colon_-moz-last-node/index.md?plain=1)
 • 
[Informar de un problema con este contenido](https://github.com/mdn/translated-content/issues/new?template=page-report-es.yml&mdn-url=https%3A%2F%2Fdeveloper.mozilla.org%2Fes%2Fdocs%2FWeb%2FCSS%2FReference%2FSelectors%2F%3A-moz-last-node&metadata=%3C%21--+Do+not+make+changes+below+this+line+--%3E%0A%3Cdetails%3E%0A%3Csummary%3EPage+report+details%3C%2Fsummary%3E%0A%0A*+Folder%3A+%60es%2Fweb%2Fcss%2Freference%2Fselectors%2F_colon_-moz-last-node%60%0A*+MDN+URL%3A+https%3A%2F%2Fdeveloper.mozilla.org%2Fes%2Fdocs%2FWeb%2FCSS%2FReference%2FSelectors%2F%3A-moz-last-node%0A*+GitHub+URL%3A+https%3A%2F%2Fgithub.com%2Fmdn%2Ftranslated-content%2Fblob%2Fmain%2Ffiles%2Fes%2Fweb%2Fcss%2Freference%2Fselectors%2F_colon_-moz-last-node%2Findex.md%0A*+Last+commit%3A+https%3A%2F%2Fgithub.com%2Fmdn%2Ftranslated-content%2Fcommit%2F03cd8e77b604d27540a3cc646d240e2457f31b13%0A*+Document+last+modified%3A+2026-03-31T01%3A22%3A11.000Z%0A%0A%3C%2Fdetails%3E)