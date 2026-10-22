
# Tarjeta

Este patrón es una lista de componentes de "tarjeta" con pies opcionales. Una tarjeta contiene un título, una imagen, una descripción u otro contenido, y una atribución o pie. Las tarjetas suelen mostrarse dentro de un grupo o colección.
![Tres componentes de tarjeta en una fila](/en-US/docs/Web/CSS/How_to/Layout_cookbook/Card/cards.png)
## [Requisitos](#requisitos) <a id="requisitos"></a>

Crea un grupo de tarjetas, en el que cada componente de tarjeta contenga un encabezado, una imagen, contenido y, de forma opcional, un pie.
Todas las tarjetas del grupo deben tener la misma altura. El pie opcional de la tarjeta debe quedar pegado a la parte inferior de la tarjeta.
Las tarjetas del grupo deben alinearse en dos dimensiones: tanto en vertical como en horizontal.
## [Receta](#receta) <a id="receta"></a>

Haz clic en "Play" en los bloques de código de abajo para editar el ejemplo en el MDN Playground:
html
```html
<div class="cards">
  <article class="card">
    <header>
      <h2>Un encabezado corto</h2>
    </header>

    <img
      src="https://mdn.github.io/shared-assets/images/examples/balloons.jpg"
      alt="Globos aerostáticos" />
    <div class="content">
      <p>
        La idea de llegar al Polo Norte por medio de globos parece haberse
        planteado hace muchos años.
      </p>
    </div>
  </article>

  <article class="card">
    <header>
      <h2>Un encabezado corto</h2>
    </header>

    <img
      src="https://mdn.github.io/shared-assets/images/examples/balloons2.jpg"
      alt="Globos aerostáticos" />
    <div class="content">
      <p>Contenido corto.</p>
    </div>
    <footer>¡Tengo un pie!</footer>
  </article>

  <article class="card">
    <header>
      <h2>Un encabezado más largo en esta tarjeta</h2>
    </header>

    <img
      src="https://mdn.github.io/shared-assets/images/examples/balloons.jpg"
      alt="Globos aerostáticos" />
    <div class="content">
      <p>
        En una curiosa obra, publicada en París en 1863 por Delaville Dedreux,
        se sugiere llegar al Polo Norte mediante un aeróstato.
      </p>
    </div>
    <footer>¡Tengo un pie!</footer>
  </article>
  <article class="card">
    <header>
      <h2>Un encabezado corto</h2>
    </header>

    <img
      src="https://mdn.github.io/shared-assets/images/examples/balloons2.jpg"
      alt="Globos aerostáticos" />
    <div class="content">
      <p>
        La idea de llegar al Polo Norte por medio de globos parece haberse
        planteado hace muchos años.
      </p>
    </div>
  </article>
</div>
```
css

```css
body {
  font: 1.2em sans-serif;
}

img {
  max-width: 100%;
}

.cards {
  max-width: 700px;
  margin: 1em auto;

  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  grid-gap: 20px;
}

.card {
  border: 1px solid #999999;
  border-radius: 3px;

  display: grid;
  grid-template-rows: max-content 200px 1fr;
}

.card img {
  object-fit: cover;
  width: 100%;
  height: 100%;
}

.card h2 {
  margin: 0;
  padding: 0.5rem;
}

.card .content {
  padding: 0.5rem;
}

.card footer {
  background-color: #333333;
  color: white;
  padding: 0.5rem;
}
```

## [Decisiones tomadas](#decisiones_tomadas) <a id="decisiones_tomadas"></a>

Cada tarjeta se maqueta con el [diseño de cuadrícula CSS](/es/docs/Web/CSS/Guides/Grid_layout), aunque el diseño sea unidimensional. Esto permite usar el dimensionamiento según el contenido en las pistas de la cuadrícula. Para configurar una cuadrícula de una sola columna, podemos usar lo siguiente:
css
```css
.card {
  display: grid;
  grid-template-rows: max-content 200px 1fr;
}
```

[`` display: grid ``](/es/docs/Web/CSS/Reference/Properties/display) convierte el elemento en un contenedor de cuadrícula. Los tres valores de la propiedad [`grid-template-rows`](/es/docs/Web/CSS/Reference/Properties/grid-template-rows) dividen la cuadrícula en un mínimo de tres filas y definen, en orden, la altura de los tres primeros hijos de la tarjeta.
Cada `card` contiene un [`<header>`](/es/docs/Web/HTML/Reference/Elements/header), un [`<img>`]