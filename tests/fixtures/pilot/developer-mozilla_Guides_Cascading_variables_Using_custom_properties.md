
# Uso de propiedades personalizadas (variables) en CSS

En CSS, las **propiedades personalizadas** (también conocidas como **variables**) son entidades definidas por autores de CSS que contienen valores específicos que se pueden volver a utilizar en un documento. Se establecen mediante la notación de propiedades personalizadas (por ejemplo, **`` --main-color: black; ``**) y se acceden mediante la función [`var()`](/es/docs/Web/CSS/Reference/Values/var) (por ejemplo, color: **`` var (--main-color); ``**).
Sitios web complejos tienen cantidades muy grandes de CSS, a menudo con una gran cantidad de valores repetidos. Por ejemplo, el mismo color se puede utilizar en cientos de lugares diferentes, lo cual requiere buscar y reemplazar globalmente si necesitamos cambiar ese color. Las variables CSS permiten que un valor se almacene en un lugar y luego se haga referencia en varios otros lugares. Un beneficio adicional son los identificadores semánticos. Por ejemplo **`--main-text-color`** es más fácil de entender que **`#00ff00`**, especialmente si este mismo color también se utiliza en otro contexto.
Las variables CSS están sujetas a la cascada, y heredan su valor de su padre.
## [Uso Básico](#uso_básico) <a id="uso_básico"></a>

Para declarar propiedades personalizadas (variables) usamos un nombre que comienze con dos guiones (`--`), y un valor que puede ser cualquier valor válido de CSS. Como cualquier otra propiedad, la escribimos dentro de un set de reglas de estilo, algo así:
css
```css
elemento {
  --main-bg-color: brown;
}
```

Ten en cuenta que el selector que usemos para las reglas de estilo define el ámbito (scope) en el que podremos usar la propiedad personalizada (variable). Una buena práctica común es declarar variables en la pseudo-clase [`:root`](/es/docs/Web/CSS/Reference/Selectors/:root), y así aplicarlas globalmente al documento HTML:
css
```css
:root {
  --main-bg-color: brown;
}
```

Sin embargo, esto no tiene por qué ser siempre así: podrían haber muy buenas razones para querer limitar el ámbito de tus propiedades personalizadas.
**Nota:**
Los nombres de propiedades personalizadas son case sensitive (distinguen entre mayúsuculas y minúsculas) — `--my-color` será tratado como una propiedad personalizada distinta a `--My-color`.
Como mencionamos anteriormente, para acceder al valor de una propiedad personalizada usamos el nombre de la propiedad dentro de la función [`var()`](/es/docs/Web/CSS/Reference/Values/var), en lugar de cualquier otro valor normal:
css
```css
elemento {
  background-color: var(--main-bg-color);
}
```

## [Primeros pasos con propiedades personalizadas (variables)](#primeros_pasos_con_propiedades_personalizadas_variables) <a id="primeros_pasos_con_propiedades_personalizadas_variables"></a>

Comencemos con este simple CSS que colorea elementos de diferentes clases con el mismo color:
css
```css
.uno {
  color: white;
  background-color: brown;
  margin: 10px;
  width: 50px;
  height: 50px;
  display: inline-block;
}

.dos {
  color: white;
  background-color: black;
  margin: 10px;
  width: 150px;
  height: 70px;
  display: inline-block;
}
.tres {
  color: white;
  background-color: brown;
  margin: 10px;
  width: 75px;
}
.cuatro {
  color: white;
  background-color: brown;
  margin: 10px;
  width: 100px;
}

.cinco {
  background-color: brown;
}
```

Lo aplicaremos a este HTML:
html
```html
<div>
  <div class="uno">1:</div>
  <div class="dos">2: Texto <span class="cinco">5 - más texto</span></div>
  <input class="tres" />
  <textarea class="cuatro">4: Lorem Ipsum</textarea>
</div>
```

... lo cual nos lleva a esto:
Observa la repetición en el CSS. El color de fondo se pone a marrón (`brown`) en varios lugares. Para algunas declaraciones CSS, es posible declarar esto más alto en la cascada y dejar que la herencia CSS resuelva este problema de forma natural. Para proyectos no triviales, esto no siempre es posible. Al declarar una variable en la pseudo-clase [`:root`](/es/docs/Web/CSS/Reference/Selectors/:root), podemos evitar repetición usando la variable.
c