
# Diseños de columnas

A menudo necesitarás crear un diseño con varias columnas, y CSS ofrece varias formas de hacerlo. Usar el diseño [multicolumna](/es/docs/Web/CSS/Guides/Multicol_layout), [flexbox](/es/docs/Web/CSS/Guides/Flexible_box_layout) o [grid](/es/docs/Web/CSS/Guides/Grid_layout) dependerá de lo que quieras lograr, y en esta receta exploramos estas opciones.
![Tres estilos distintos de diseño con dos columnas en el contenedor.](/en-US/docs/Web/CSS/How_to/Layout_cookbook/Column_layouts/cookbook-multiple-columns.png)
## [Requisitos](#requisitos) <a id="requisitos"></a>

Hay varios patrones de diseño que podrías querer lograr con tus columnas:
- [Un flujo continuo de contenido dividido en columnas al estilo de un periódico](#un_flujo_continuo_de_contenido_—_diseño_multicolumna).
- [Una sola fila de elementos dispuestos como columnas, todos con la misma altura](#una_sola_fila_de_elementos_con_la_misma_altura_—_flexbox).
- [Varias filas de columnas alineadas por fila y por columna](#alinear_elementos_en_filas_y_columnas_—_diseño_de_cuadrícula).

## [Las recetas](#las_recetas) <a id="las_recetas"></a>

Tienes que elegir distintos métodos de maquetación según lo que necesites lograr.
### [Un flujo continuo de contenido — diseño multicolumna](#un_flujo_continuo_de_contenido_—_diseño_multicolumna) <a id="un_flujo_continuo_de_contenido_—_diseño_multicolumna"></a>

Si creas columnas con el diseño multicolumna, tu texto seguirá siendo un flujo continuo que va llenando cada columna por turnos. Todas las columnas deben tener el mismo tamaño, y no puedes seleccionar una columna concreta ni el contenido de una columna concreta.
Puedes controlar el espacio entre columnas con las propiedades [`column-gap`](/es/docs/Web/CSS/Reference/Properties/column-gap) o [`gap`](/es/docs/Web/CSS/Reference/Properties/gap), y añadir una línea entre columnas con [`column-rule`](/en-US/docs/Web/CSS/Reference/Properties/column-rule).
Haz clic en "Play" en los bloques de código de abajo para editar el ejemplo en el MDN Playground:
html
```html
<div class="container">
  <p>
    Veggies es bonus vobis, proinde vos postulo essum magis kohlrabi welsh onion
    daikon amaranth tatsoi tomatillo melon azuki bean garlic.
  </p>
  <p>
    Gumbo beet greens corn soko endive gumbo gourd. Parsley shallot courgette
    tatsoi pea sprouts fava bean collard greens dandelion okra wakame tomato.
    Dandelion cucumber earthnut pea peanut soko zucchini.
  </p>
  <p>
    Turnip greens yarrow ricebean rutabaga endive cauliflower sea lettuce
    kohlrabi amaranth water spinach avocado daikon napa cabbage asparagus winter
    purslane kale. Celery potato scallion desert raisin horseradish spinach
  </p>
</div>
```
css

```css
.container {
  border: 2px solid rgb(75 70 74);
  border-radius: 0.5em;
  padding: 20px;
  font: 1.2em sans-serif;

  column-width: 10em;
  column-rule: 1px solid rgb(75 70 74);
}
```

En este ejemplo, usamos la propiedad [`column-width`](/en-US/docs/Web/CSS/Reference/Properties/column-width) para establecer el ancho mínimo que deben tener las columnas antes de que el navegador añada una columna más. La propiedad abreviada [`columns`](/en-US/docs/Web/CSS/Reference/Properties/columns) permite establecer las propiedades `column-width` y [`column-count`](/es/docs/Web/CSS/Reference/Properties/column-count), y cualquiera de ellas puede definir el número máximo de columnas permitido.
Usa el diseño multicolumna cuando:
- Quieras que tu texto se muestre en columnas como las de un periódico.
- Tengas un conjunto de elementos pequeños que quieras dividir en columnas.
- No necesites seleccionar cajas de columna concretas para darles estilo.

### [Una sola fila de elementos con la misma altura — flexbox](#una_sola_fila_de_elementos_con_la_misma_altura_—_flexbox) <a id="una_sola_fila_de_elementos_con_la_misma_altura_—_flexbox"></a>

Flexbox permite dividir el contenido en columnas estableciendo [`` display: flex; ``](/es/docs/Web/CSS/Reference/Properties/display) para convertir un elemento padre en un contenedor flexible. Con solo añadir esta propiedad, todos los hijos (elementos hijos, pseudoelementos y nodos de texto) se convierten en elementos flexibles dispuestos en una sola línea. Si se establece la misma propiedad abreviada [`flex`](/es/docs/Web/CSS/Reference/Properties/flex) con un único valor numérico, todo el espacio disponible se reparte a partes iguales, lo que suele hacer que todos los elementos flexibles tengan el mismo tamaño, siempre que ninguno tenga contenido que no se ajuste y obligue a que el elemento sea más grande.
Se pueden usar márgenes o la propiedad `gap` para crear espacios entre los elementos, pero por ahora no hay ninguna propiedad CSS que añada líneas entre los elementos flexibles.
html
```html
<div class="container">
  <p>
    Veggies es bonus vobis, proinde vos postulo essum magis kohlrabi welsh onion
    daikon amaranth tatsoi tomatillo melon azuki bean garlic.
  </p>

  <p>
    Gumbo beet greens corn soko endive gumbo gourd. Parsley shallot courgette
    tatsoi pea sprouts fava bean collard greens dandelion okra wakame tomato.
    Dandelion cucumber earthnut pea peanut soko zucchini.
  </p>

  <p>
    Turnip greens yarrow ricebean rutabaga endive cauliflower sea lettuce
    kohlrabi amaranth water spinach avocado daikon napa cabbage asparagus winter
    purslane kale. Celery potato scallion desert raisin horseradish spinach
    carrot soko.
  </p>
</div>
```
css

```css
.container {
  border: 2px solid rgb(75 70 74);
  border-radius: 0.5em;
  padding: 20px 10px;
  font: 1.2em sans-serif;

  display: flex;
}

.container > * {
  padding: 10px;
  border: 2px solid rgb(95 97 110);
  border-radius: 0.5em;

  margin: 0 10px;
  flex: 1;
}
```

Para crear un diseño con elementos flexibles que pasen a nuevas filas, establece la propiedad [`flex-wrap`](/es/docs/Web/CSS/Reference/Properties/flex-wrap) del contenedor en `wrap`. Ten en cuenta que cada línea flexible reparte el espacio solo para esa línea. Los elementos de una línea no se alinearán necesariamente con los de otras líneas, como verás en el ejemplo siguiente. Por eso se dice que flexbox es unidimensional: está pensado para controlar el diseño como una fila o como una columna, pero no ambas a la vez.
html
```html
<div class="container">
  <p>
    Veggies es bonus vobis, proinde vos postulo essum magis kohlrabi welsh onion
    daikon amaranth tatsoi tomatillo melon azuki bean garlic.
  </p>

  <p>
    Gumbo beet greens corn soko endive gumbo gourd. Parsley shallot courgette
    tatsoi pea sprouts fava bean collard greens dandelion okra wakame tomato.
    Dandelion cucumber earthnut pea peanut soko zucchini.
  </p>

  <p>
    Turnip greens yarrow ricebean rutabaga endive cauliflower sea lettuce
    kohlrabi amaranth water spinach avocado daikon napa cabbage asparagus winter
    purslane kale. Celery potato scallion desert raisin horseradish spinach
    carrot soko.
  </p>
</div>
```
css

```css
.container {
  border: 2px solid rgb(75 70 74);
  border-radius: 0.5em;
  padding: 20px 10px;
  width: 500px;
  font: 1.2em sans-serif;

  display: flex;
  flex-wrap: wrap;
}

.container > * {
  padding: 10px;
  border: 2px solid rgb(95 97 110);
  border-radius: 0.5em;

  margin: 0 10px;
  flex: 1 1 200px;
}
```

Usa flexbox:
- Para filas o columnas únicas de elementos.
- Cuando quieras alinear en el eje transversal después de disponer los elementos.
- Cuando te parezca bien que los elementos que pasan a otra línea repartan el espacio solo en su propia línea y no se alineen con los elementos de otras líneas.

### [Alinear elementos en filas y columnas — diseño de cuadrícula](#alinear_elementos_en_filas_y_columnas_—_diseño_de_cuadrícula) <a id="alinear_elementos_en_filas_y_columnas_—_diseño_de_cuadrícula"></a>

Si quieres una cuadrícula bidimensional en la que los elementos se alineen en filas *y* columnas, deberías elegir el diseño de cuadrícula CSS. Al igual que flexbox actúa sobre los hijos directos del contenedor flexible, el diseño de cuadrícula actúa sobre los hijos directos del contenedor de cuadrícula. Solo tienes que establecer [`` display: grid; ``](/es/docs/Web/CSS/Reference/Properties/display) en el contenedor. Las propiedades que se establecen en este contenedor, como [`grid-template-columns`](/es/docs/Web/CSS/Reference/Properties/grid-template-columns) y [`grid-template-rows`](/es/docs/Web/CSS/Reference/Properties/grid-template-rows), definen cómo se reparten los elementos en filas y columnas.
Haz clic en "Play" en los bloques de código de abajo para editar el ejemplo en el MDN Playground:
html
```html
<div class="container">
  <p>
    Veggies es bonus vobis, proinde vos postulo essum magis kohlrabi welsh onion
    daikon amaranth tatsoi.
  </p>

  <p>
    Gumbo beet greens corn soko endive gumbo gourd. Parsley shallot courgette
    tatsoi pea sprouts fava bean collard greens.
  </p>

  <p>
    Nori grape silver beet broccoli kombu beet greens fava bean potato quandong
    celery. Bunya nuts black-eyed pea prairie turnip leek lentil turnip greens
    parsnip. .
  </p>
</div>
```
css

```css
.container {
  border: 2px solid rgb(75 70 74);
  border-radius: 0.5em;
  padding: 20px;
  width: 500px;
  font: 1.2em sans-serif;

  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-gap: 20px;
}

.container > * {
  padding: 10px;
  border: 2px solid rgb(95 97 110);
  border-radius: 0.5em;
  margin: 0;
}
```

Usa grid:
- Para varias filas o columnas de elementos.
- Cuando quieras poder alinear los elementos en los ejes de bloque y en línea.
- Cuando quieras que los elementos se alineen en filas y columnas.

## [Recursos en MDN](#recursos_en_mdn) <a id="recursos_en_mdn"></a>

- [Guía del diseño multicolumna](/es/docs/Web/CSS/Guides/Multicol_layout)
- [Guía de flexbox](/es/docs/Web/CSS/Guides/Flexible_box_layout)
- [Guía del diseño de cuadrícula CSS](/es/docs/Web/CSS/Guides/Grid_layout)

## Ayuda a mejorar MDN <a id="feedback"></a>
[Aprende cómo colaborar](/es/docs/MDN/Community/Getting_started)


    Esta página se modificó por última vez el 30 sept 2026 por [colaboradores de MDN](/es/docs/Web/CSS/How_to/Layout_cookbook/Column_layouts/contributors.txt).
[Ver esta página en GitHub](https://github.com/mdn/translated-content/blob/main/files/es/web/css/how_to/layout_cookbook/column_layouts/index.md?plain=1)
 • 
[Informar de un problema con este contenido](https://github.com/mdn/translated-content/issues/new?template=page-report-es.yml&mdn-url=https%3A%2F%2Fdeveloper.mozilla.org%2Fes%2Fdocs%2FWeb%2FCSS%2FHow_to%2FLayout_cookbook%2FColumn_layouts&metadata=%3C%21--+Do+not+make+changes+below+this+line+--%3E%0A%3Cdetails%3E%0A%3Csummary%3EPage+report+details%3C%2Fsummary%3E%0A%0A*+Folder%3A+%60es%2Fweb%2Fcss%2Fhow_to%2Flayout_cookbook%2Fcolumn_layouts%60%0A*+MDN+URL%3A+https%3A%2F%2Fdeveloper.mozilla.org%2Fes%2Fdocs%2FWeb%2FCSS%2FHow_to%2FLayout_cookbook%2FColumn_layouts%0A*+GitHub+URL%3A+https%3A%2F%2Fgithub.com%2Fmdn%2Ftranslated-content%2Fblob%2Fmain%2Ffiles%2Fes%2Fweb%2Fcss%2Fhow_to%2Flayout_cookbook%2Fcolumn_layouts%2Findex.md%0A*+Last+commit%3A+https%3A%2F%2Fgithub.com%2Fmdn%2Ftranslated-content%2Fcommit%2Fdf12639b1fb7740e365e71d0eb51d64fb8f285a0%0A*+Document+last+modified%3A+2026-09-30T05%3A59%3A50.000Z%0A%0A%3C%2Fdetails%3E)