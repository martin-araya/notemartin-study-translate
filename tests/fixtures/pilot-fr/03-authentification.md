# Authentification et connexion

L'authentification contrôle l'accès à l'interface d'administration.
Vous ne devez jamais désactiver l'authentification pour un utilisateur
administrateur, sinon vous perdez l'accès au serveur.

## Méthodes prises en charge

| Méthode | Portail | Remarques |
|---|---|---|
| Mot de passe local | `443` (HTTPS) | Méthode par défaut. |
| LDAP | `636` (LDAPS) | Synchronisation centralisée des utilisateurs. |
| SAML 2.0 | `8443` (reverse proxy) | Fédération avec un IdP externe. |
| OpenID Connect | `443` | Jetons signés, rotation automatique. |

> [!WARNING]
> Une coupure du service d'authentification vous empêche de vous
> reconnecter. Configurez au moins une méthode de secours avant
> toute modification.

## Connexion à l'interface web

Vous accédez à l'interface par l'URL fournie par votre administrateur.
Le formulaire de connexion vous demande votre identifiant et votre mot
de passe. Après trois échecs consécutifs, un captcha est imposé.

```bash
# Exemple : ouverture de la console d'administration
curl --silent \
     --user "$USER:$PASS" \
     "$BASE_URL/ocs/v1.php/cloud/users"
```

> La commande ci-dessus est un **littéral technique**. Elle ne doit
> pas être traduite ; seuls ses commentaires éventuels sont
> admissibles au regard de la politique linguistique.

## Politique de mots de passe

| Paramètre | Valeur par défaut | Borne inférieure | Borne supérieure |
|---|---|---|---|
| Longueur minimale | `8` | `6` | `128` |
| Complexité obligatoire | `moyenne` | `faible` | `forte` |
| Renforcement progressif | `désactivé` | n/a | `activé` |
| Expiration | `90 j` | `1 j` | `365 j` |

> [!TIP]
> Activez l'authentification à deux facteurs pour les comptes
> administratifs. Voir [`04-configuration-2fa.md`](04-configuration-2fa.md).

## Audit

Chaque tentative de connexion produit une entrée dans le journal
d'audit. La conservation par défaut est de **trente jours**. Vous
pouvez l'allonger ; notez cependant que cela augmente la quantité de
données personnelles conservées.

> **Important.** L'audit peut être sensible au regard du RGPD.
> Documentez votre base légale avant tout allongement.
