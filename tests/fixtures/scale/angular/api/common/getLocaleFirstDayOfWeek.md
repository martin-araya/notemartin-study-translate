@angular/common

# getLocaleFirstDayOfWeek
function
deprecated
since v18.0
[*code*](https://github.com/angular/angular/blob/main/packages/common/src/i18n/locale_data_api.ts#L394-L397)

Retrieves the first day of the week for the given locale.
Deprecation warning
Angular recommends relying on the `Intl` API for i18n.
Intl's [`getWeekInfo`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/Locale/getWeekInfo) has partial support (Chromium M99 & Safari 17).
You may want to rely on the following alternatives:

  
    Libraries like [`Luxon`](https://moment.github.io/luxon/#/) rely on `Intl` but fallback on the ISO 8601 definition (monday) if `getWeekInfo` is not supported.
Other librairies like [`date-fns`](https://date-fns.org/), [`day.js`](https://day.js.org/en/) or [`weekstart`](https://www.npmjs.com/package/weekstart) library provide their own locale based data for the first day of the week.

  
  
![](assets/images/angie/orthos-back.svg)
## [API](#api) <a id="api"></a>

```text
function getLocaleFirstDayOfWeek(locale: string): WeekDay;
```
@deprecated
Angular recommends relying on the `Intl` API for i18n.
Intl's [`getWeekInfo`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/Locale/getWeekInfo) has partial support (Chromium M99 & Safari 17).
You may want to rely on the following alternatives:

  
    Libraries like [`Luxon`](https://moment.github.io/luxon/#/) rely on `Intl` but fallback on the ISO 8601 definition (monday) if `getWeekInfo` is not supported.
Other librairies like [`date-fns`](https://date-fns.org/), [`day.js`](https://day.js.org/en/) or [`weekstart`](https://www.npmjs.com/package/weekstart) library provide their own locale based data for the first day of the week.

  
  
@param
locale
`string`

A locale code for the locale format rules to use.
@returns
`WeekDay`
A day index number, using the 0-based week-day index for `en-US`
(Sunday = 0, Monday = 1, ...).
For example, for `fr-FR`, returns 1 to indicate that the first day is Monday.