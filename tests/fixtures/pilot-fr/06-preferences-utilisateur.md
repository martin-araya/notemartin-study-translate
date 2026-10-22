# Préférences utilisateur

Vous pouvez ajuster votre langue, votre fuseau horaire, votre quota
de stockage et votre thème depuis la page « Préférences ». Vos choix
sont enregistrés automatiquement ; aucune confirmation n'est
demandée.

## Paramètres régionaux

| Paramètre | Valeur par défaut | Valeurs autorisées |
|---|---|---|
| Langue | héritée du serveur | `fr`, `en`, `es`, `de`, ... |
| Fuseau horaire | hérité du serveur | IANA `Europe/Paris`, IANA `UTC`, ... |
| Format de date | hérité du serveur | ISO 8601, régional français, régional US. |
| Premier jour de la semaine | `lundi` | `dimanche`, `lundi` |

> [!NOTE]
> Les changements ne s'appliquent qu'à votre session. Les autres
> utilisateurs conservent leurs propres réglages.

## Espace de stockage

Le quota par défaut est de `5 Go`. Vous pouvez le consulter dans
**Paramètres → Espace personnel**.

```text
Utilisé       : 312 Mo
Disponible   : 4,7 Go
Pourcentage  : 6 %
```

> Les nombres ci-dessus sont des **littéraux** au sens du
> `references/source-language-policy-fr.md` : ils ne sont pas
> localisés. Le séparateur décimal reste celui du tableau.

## Confidentialité

> **Important.** Les données que vous stockez sur le serveur peuvent
> être soumises à un audit interne. Cela vise à protéger l'ensemble
> des utilisateurs, pas à surveiller un usage personnel légitime.

## Thème

Trois thèmes sont disponibles : clair, sombre, automatique. L'option
« Automatique » suit les préférences système.

## Renvois internes

- Espace de stockage et partage :
  [`02-fichiers-et-synchronisation.md`](02-fichiers-et-synchronisation.md).
- Authentification à deux facteurs :
  [`04-configuration-2fa.md`](04-configuration-2fa.md).
- Préface et licence :
  [`01-prelude-et-licence.md`](01-prelude-et-licence.md).

## Mentions contractuelles

> **Note de licence.** Les conditions générales d'utilisation du
> service s'appliquent à toutes les préférences enregistrées ici.
> Cette section ne crée aucune obligation supplémentaire ; elle
> renvoie au document [`01-prelude-et-licence.md`](01-prelude-et-licence.md).

## Fin du document pilote

Le présent corpus n'est pas destiné à remplacer un manuel
d'administration réel. Il sert uniquement à valider la
chaîne de traduction fr→es de la skill.
