# Fichiers et synchronisation

> **Note légale.** Ce chapitre décrit l'interface utilisateur ; il
> n'établit aucun contrat. Les conditions générales d'utilisation
> s'appliquent intégralement : voir
> `01-prelude-et-licence.md` (section « À propos »).

La fonction « Fichiers » de Nextcloud vous permet de gérer vos
documents, images et autres ressources depuis un navigateur ou un
client de bureau. Les fichiers peuvent être partagés, versionnés et
synchronisés sur plusieurs appareils.

## Parcours typique

1. Connexion à l'interface web.
2. Navigation vers le dossier concerné.
3. Sélection et ouverture du fichier.
4. Modification éventuelle, puis enregistrement.

> [!NOTE]
> Les administrateurs peuvent configurer des quotas par utilisateur
> ou par groupe. Les valeurs par défaut sont conservées tant que la
> configuration n'est pas modifiée.

## Actions disponibles

| Action | Raccourci | Effet |
|---|---|---|
| Ouvrir | `Entrée` | Ouvre le fichier dans l'aperçu intégré. |
| Télécharger | `Ctrl + S` | Propose le téléchargement local. |
| Renommer | `F2` | Renomme en ligne, sans modification d'horodatage. |
| Supprimer | `Suppr` | Déplace dans la corbeille, récupérable. |
| Partager | `Ctrl + P` | Ouvre le dialogue de partage. |

## Partage public

```text
Vous pouvez partager un fichier publiquement avec un lien. Le
destinataire n'a pas besoin de compte ; il reçoit une URL stable.
```

L'option « Lien public » se trouve dans le menu d'action du fichier.
Activez-la seulement si la ressource ne contient pas de données
sensibles.

## Exemple d'URL de ressource

```yaml
/uploads/illustration.png
```

Ce chemin est résolu **par rapport à** la racine du serveur. Ne le
traduisez pas : il s'agit d'un identifiant technique.

## Renvois internes

- Voir aussi : [`03-authentification.md`](03-authentification.md),
  section « Connexion à l'interface web ».
- Voir aussi : [`06-preferences-utilisateur.md`](06-preferences-utilisateur.md),
  section « Espace de stockage ».

> **Attention.** Les liens ci-dessus doivent être réécrits lorsque
> les titres de section sont traduits. Le profil de slugs est fixé
> dans `profile.json`.
