# Client de bureau

Le client de bureau synchronise vos dossiers Nextcloud avec votre
poste de travail. Il prend en charge Windows, macOS et plusieurs
distributions Linux.

> Les paquets d'installation ne sont **pas** traduits. Seuls les
> messages d'interface visibles sont localisables. Voir la politique
> de traduction §5.2 (`AGENTS.md`).

## Plateformes prises en charge

| Plateforme | Version minimale | Remarque |
|---|---|---|
| Windows | `10 21H2` | Architecture `x86_64` ou `arm64`. |
| macOS | `12 (Monterey)` | Notarisé par Apple. |
| Ubuntu LTS | `22.04 LTS` | Dépôt officiel fourni. |
| Fedora | `39` | Paquets `dnf` officiels. |
| Arch | n/a | Paquets communautaires. |

## Configuration initiale

1. Téléchargez l'installateur depuis `https://example.org/client-desktop/`.
2. Lancez l'installation.
3. Saisissez l'URL du serveur et vos identifiants.
4. Choisissez les dossiers à synchroniser.

```text
URL du serveur : https://cloud.example.org
Dossier local  : ~/Nextcloud
Synchronisation : à la demande
```

## Indicateurs d'état

> [!TIP]
> Les icônes dans la barre d'état indiquent l'état courant :
>
> - Vert : synchronisation à jour.
> - Orange : opération en cours.
> - Rouge : erreur, intervention requise.
> - Gris : connexion inactive.

## Désinstallation

Pour supprimer complètement le client :

| Plateforme | Commande |
|---|---|
| Windows | `wmic product where "name='Nextcloud'" call uninstall` |
| macOS | `sudo /usr/local/bin/nextcloud-uninstall` |
| Linux (deb) | `sudo apt remove nextcloud-client` |
| Linux (rpm) | `sudo dnf remove nextcloud-client` |

> Les commandes ci-dessus sont des littéraux. Aucune
> traduction n'est appliquée.

## Renvois internes

- Authentification requise : [`03-authentification.md`](03-authentification.md).
- Préférences : [`06-preferences-utilisateur.md`](06-preferences-utilisateur.md).
- Préface : [`01-prelude-et-licence.md`](01-prelude-et-licence.md).
