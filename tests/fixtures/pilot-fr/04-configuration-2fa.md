# Configuration de l'authentification à deux facteurs

L'authentification à deux facteurs (2FA) ajoute une étape de
vérification supplémentaire. Vous l'activez pour un utilisateur, un
groupe ou l'ensemble de l'organisation.

> [!CAUTION]
> L'activation à l'échelle de l'organisation exige que chaque
> utilisateur dispose d'un second facteur valide. Sans cela, vous
> risquez de bloquer l'accès à des comptes critiques.

## Étapes d'activation

1. Connectez-vous à la console d'administration.
2. Allez dans **Sécurité → Authentification à deux facteurs**.
3. Choisissez la portée : utilisateur, groupe ou organisation.
4. Sélectionnez les seconds facteurs autorisés :

| Facteur | Compatible RFC | Remarque |
|---|---|---|
| TOTP (RFC 6238) | oui | Recommandé. |
| Notification mobile | non propriétaire | Dépend du serveur fournisseur. |
| Codes de secours | non | Toujours disponibles, à imprimer. |
| WebAuthn (FIDO2) | oui | Nécessite un navigateur compatible. |

## Codes de secours

Vous recevez initialement **dix codes de secours**. Chaque code est à
usage unique. Distribuez-les par un canal sécurisé ; le courrier
électronique n'est pas considéré comme tel.

> **Important.** Si vous perdez tous vos codes de secours et votre
> second facteur, la procédure de récupération exige la preuve
> d'identité auprès de l'administrateur.

## Désactivation temporaire

Vous pouvez suspendre la 2FA pour un événement particulier
(maintenance, audit). La durée maximale recommandée est de
**vingt-quatre heures**.

```bash
# Désactivation temporaire pour le compte d'astreinte
occ twofactor:disable --user oncall@example.org --until "2026-12-31T23:59:00Z"
```

> La commande ci-dessus est exécutable par un administrateur
> authentifié. Elle n'est jamais exécutée automatiquement.

## Renvois internes

- Méthode par défaut : voir [`03-authentification.md`](03-authentification.md).
- Stockage des codes : voir [`06-preferences-utilisateur.md`](06-preferences-utilisateur.md).
- Préface et licence : voir [`01-prelude-et-licence.md`](01-prelude-et-licence.md).
